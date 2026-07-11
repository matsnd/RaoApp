"""
RAO-P2-059 (Faza 1): Migracja legacy `umowa2.oplaty` (plain text) -> `contract_service_fees` (structured).

Standalone, idempotentny skrypt migracji danych. Przeznaczony do uruchomienia po
`migrate.py` step2 (import dumpa) a przed step6 (DROP old tables) — albo na
odtworzonej bazie z legacy dumpem.

ALGORYTM (best-effort, forward-only):
  1. Sprawdź czy `umowa2` istnieje — jeśli nie, nic do zrobienia (exit 0).
  2. SELECT id, OPLATY FROM umowa2 WHERE OPLATY IS NOT NULL AND TRIM(OPLATY) != ''
  3. Dla każdego kontraktu: parsuj OPLATY (multiline free-text) -> list[dict]
     - Każda niepusta linia -> jeden fee (name, amount_from, amount_to, unit, description)
     - Regex rozpoznaje formaty: "Transport 280,00 zł", "1. Transport - 500,00 zł/dzień",
       "Dostawa 100 zł - 200 zł/odbiór", "Opłata: 150 zł (opis)" itp.
     - Nieparsowane linie są logowane (WARN) ale NIE crashują migracji.
  4. Dla każdego fee:
     a. Znajdź artykuł-usługę po nazwie (case-insensitive, preferuj is_service=1).
        Jeśli nie istnieje -> utwórz (is_service=1, article_type='usluga_dodatkowa').
     b. UPSERT do contract_service_fees po (contract_id, sort_order):
        - SELECT istniejący wiersz -> UPDATE jeśli istnieje, INSERT jeśli nie.
        - article_id + default_price = COALESCE(amount_from, amount_to).
  5. Loguje statystyki: contracts, fees inserted/updated, articles created, unparseable.

IDEMPOTENCJA:
  - Re-run bezpieczny: istniejące wiersze (contract_id, sort_order) są UPDATE-owane,
    nowe INSERT-owane. Brak DROP, brak DELETE.
  - Artykuły tworzone tylko IF NOT EXISTS (po nazwie).

Użycie:
    python migrate_service_fees.py             # pełna migracja
    python migrate_service_fees.py --dry-run   # tylko statystyki, bez zapisu
    python migrate_service_fees.py --verify    # weryfikacja stanu po migracji
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Windows: konsola cp1250 nie zna ✓/✗ — wymuś UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import aiomysql

# Domyślne credentiale z .env (fallback na wartości z migrate.py dla spójności)
DB_HOST = os.environ.get("RAO_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("RAO_DB_PORT", "3306"))
DB_USER = os.environ.get("RAO_DB_USER", "rao_user")
DB_PASS = os.environ.get("RAO_DB_PASSWORD", "")
DB_NAME = os.environ.get("RAO_DB_NAME", "rao_new")


# ===========================================================================
# PARSER — best-effort regex dla legacy `umowa2.oplaty` (free-text multiline)
# ===========================================================================
# Wzorzec kwoty: "280", "1 200", "1 200,50", "1200.50"
_A = r'([\d]+(?:\s[\d]{3})*(?:[,.][\d]+)?)'

_RE_DOSTAWA  = re.compile(rf'^{_A}\s*z[łl]\s*[-–]?\s*(.{{1,30}}?)\s*/\s*{_A}\s*z[łl]\s*[-–]?\s*(odbi[oó]r\S*)', re.I | re.U)
_RE_H_RANGE  = re.compile(rf'^{_A}\s*z[łl]\s*/\s*(\S+)\s*[-–]\s*{_A}\s*z[łl]\s*/\s*\S+')
_RE_PER_UNIT = re.compile(rf'^{_A}\s*z[łl]\s*/\s*(\S+)')
_RE_RANGE    = re.compile(rf'^{_A}\s*z[łl]\s*[-–]\s*{_A}\s*z[łl]')
_RE_PARENS   = re.compile(rf'^{_A}\s*z[łl]\s*\(([^)]+)\)')
_RE_SINGLE   = re.compile(rf'^{_A}\s*z[łl](.*)')
_RE_NOCOL    = re.compile(rf'^(.+?)\s+{_A}\s*z[łl]\s*/\s*(\S+)\s*$')
# "Transport 280,00 zł" — nazwa + kwota bez jednostki (fallback dla no-colon)
_RE_NOCOL_AMT = re.compile(rf'^(.+?)\s+{_A}\s*z[łl]\s*$')
_RE_SKIP     = re.compile(
    r'^(-zedytowane|1[-\s]*2\s*dni|powyżej\s*2|praca do \d|czas trwania|'
    r'opłata w gotówce|do \d+ godzin\s*-)',
    re.I,
)
# Numeracja listy: "1. ", "2) ", "- " — strip przed parsowaniem
_RE_LIST_PREFIX = re.compile(r'^\s*(?:\d+[.)]\s*|[-•]\s*)')


def _to_dec(s: str | None) -> Decimal | None:
    if not s:
        return None
    try:
        return Decimal(s.strip().replace(' ', '').replace(',', '.'))
    except InvalidOperation:
        return None


def _parse_fee_line(raw: str) -> dict | None:
    """Parsuje pojedynczą linię z `umowa2.oplaty` -> dict fee lub None (pomiń)."""
    raw_s = raw.strip()
    if not raw_s or _RE_SKIP.match(raw_s):
        return None
    # Strip list prefix ("1. ", "- ", "2) ")
    line = _RE_LIST_PREFIX.sub('', raw_s).strip()
    if not line:
        return None

    out = dict(name=line[:200], amount_from=None, amount_to=None,
               unit=None, description=None, is_active=True)

    if ':' in line:
        idx = line.index(':')
        name_part = line[:idx].strip()
        value     = line[idx + 1:].strip()
        if not name_part:
            return None
        out['name'] = name_part[:200]
    else:
        m = _RE_NOCOL.match(line)
        if m:
            out['name']        = m.group(1).strip()[:200]
            out['amount_from'] = _to_dec(m.group(2))
            out['unit']        = m.group(3)
            return out
        # Fallback: "Transport 280,00 zł" — nazwa + kwota bez jednostki
        m = _RE_NOCOL_AMT.match(line)
        if m:
            out['name']        = m.group(1).strip()[:200]
            out['amount_from'] = _to_dec(m.group(2))
            return out
        return out

    if not value:
        return out

    m = _RE_DOSTAWA.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        out['description'] = f"{m.group(2).strip()} / {m.group(4).strip()}"
        return out

    m = _RE_H_RANGE.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        out['amount_to']   = _to_dec(m.group(3))
        out['unit']        = m.group(2)
        return out

    m = _RE_PER_UNIT.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        out['unit']        = m.group(2)
        return out

    m = _RE_RANGE.match(value)
    if m and _to_dec(m.group(2)) is not None:
        out['amount_from'] = _to_dec(m.group(1))
        out['amount_to']   = _to_dec(m.group(2))
        return out

    m = _RE_PARENS.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        out['description'] = m.group(2).strip()
        return out

    m = _RE_SINGLE.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        trailing = m.group(2).strip().strip('-– ').strip()
        if trailing:
            out['description'] = trailing[:400]
        return out

    out['description'] = value[:400]
    return out


def parse_text_to_fees(text: str) -> tuple[list[dict], list[str]]:
    """Parsuje cały blob `umowa2.oplaty` -> (fees, unparsed_lines).

    fees: lista dictów z sort_order ustawionym.
    unparsed_lines: linie które nie przeszły parsowania (do logowania WARN).
    """
    fees: list[dict] = []
    unparsed: list[str] = []
    if not text:
        return fees, unparsed
    sort_order = 0
    for raw in text.replace('\r\n', '\n').replace('\r', '\n').splitlines():
        fee = _parse_fee_line(raw)
        if fee:
            fee['sort_order'] = sort_order
            sort_order += 1
            fees.append(fee)
        elif raw.strip():
            unparsed.append(raw.strip()[:120])
    return fees, unparsed


# ===========================================================================
# MIGRACJA
# ===========================================================================

async def _table_exists(cur, table_name: str) -> bool:
    await cur.execute(
        "SELECT 1 FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
        (DB_NAME, table_name),
    )
    return bool(await cur.fetchone())


async def _find_or_create_service_article(cur, name: str) -> tuple[int | None, bool]:
    """Znajdź artykuł-usługę po nazwie (case-insensitive, preferuj is_service=1).
    Jeśli nie istnieje -> utwórz. Zwraca (article_id, created).
    """
    if not name:
        return None, False
    # Exact match (case-insensitive) — preferuj is_service=1
    await cur.execute(
        "SELECT id FROM articles WHERE LOWER(name) = LOWER(%s) "
        "ORDER BY is_service DESC, id ASC LIMIT 1",
        (name[:200],),
    )
    row = await cur.fetchone()
    if row:
        return int(row[0]), False
    # Prefix match (pierwsze 30 znaków)
    await cur.execute(
        "SELECT id FROM articles WHERE LOWER(name) LIKE LOWER(%s) "
        "ORDER BY is_service DESC, id ASC LIMIT 1",
        (name[:30] + "%",),
    )
    row = await cur.fetchone()
    if row:
        return int(row[0]), False
    # Utwórz nowy artykuł-usługę
    await cur.execute(
        "INSERT INTO articles (name, is_service, article_type, created_at, updated_at) "
        "VALUES (%s, 1, 'usluga_dodatkowa', NOW(), NOW())",
        (name[:200],),
    )
    return int(cur.lastrowid), True


async def _upsert_service_fee(cur, contract_id: int, fee: dict, article_id: int | None) -> str:
    """UPSERT po (contract_id, sort_order). Zwraca 'inserted' lub 'updated'."""
    default_price = fee['amount_from'] if fee['amount_from'] is not None else fee['amount_to']
    await cur.execute(
        "SELECT id FROM contract_service_fees "
        "WHERE contract_id=%s AND sort_order=%s LIMIT 1",
        (contract_id, fee['sort_order']),
    )
    existing = await cur.fetchone()
    if existing:
        await cur.execute(
            """UPDATE contract_service_fees
               SET name=%s, amount_from=%s, amount_to=%s, unit=%s,
                   description=%s, is_active=%s, article_id=%s, default_price=%s
               WHERE id=%s""",
            (fee['name'], fee['amount_from'], fee['amount_to'], fee['unit'],
             fee['description'], fee['is_active'], article_id, default_price,
             existing[0]),
        )
        return 'updated'
    await cur.execute(
        """INSERT INTO contract_service_fees
           (contract_id, sort_order, name, amount_from, amount_to, unit,
            description, is_active, article_id, default_price)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (contract_id, fee['sort_order'], fee['name'], fee['amount_from'],
         fee['amount_to'], fee['unit'], fee['description'], fee['is_active'],
         article_id, default_price),
    )
    return 'inserted'


async def migrate(dry_run: bool = False) -> int:
    print("=" * 64)
    print("RAO-P2-059 — migrate_service_fees.py")
    print(f"  target: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"  mode:   {'DRY-RUN (no writes)' if dry_run else 'LIVE (writes enabled)'}")
    print("=" * 64)

    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # 1. Sprawdź czy umowa2 istnieje
    if not await _table_exists(cur, "umowa2"):
        print("\n✓ Tabela `umowa2` nie istnieje — migracja już wykonana lub brak legacy dumpa.")
        print("  Nic do zrobienia (idempotentne — exit 0).")
        await cur.close()
        conn.close()
        return 0

    # 2. Wczytaj OPLATY
    await cur.execute(
        "SELECT id, OPLATY FROM umowa2 WHERE OPLATY IS NOT NULL AND TRIM(OPLATY) != ''"
    )
    rows = await cur.fetchall()
    print(f"\n[1/3] Wczytano {len(rows)} umów z niepustym `umowa2.oplaty`")

    # 3. Parsuj + UPSERT
    stats = dict(contracts=0, inserted=0, updated=0, articles_created=0,
                 unparseable_contracts=0, unparseable_lines=0)

    for contract_id, oplaty in rows:
        fees, unparsed = parse_text_to_fees(oplaty)
        if not fees:
            stats['unparseable_contracts'] += 1
            if unparsed:
                stats['unparseable_lines'] += len(unparsed)
                print(f"  WARN contract_id={contract_id}: 0 fees, {len(unparsed)} unparsed lines:")
                for line in unparsed[:3]:
                    print(f"       • {line!r}")
            continue

        stats['contracts'] += 1
        if unparsed:
            stats['unparseable_lines'] += len(unparsed)
            print(f"  WARN contract_id={contract_id}: {len(unparsed)} unparsed lines (fees parsed: {len(fees)})")
            for line in unparsed[:2]:
                print(f"       • {line!r}")

        if dry_run:
            # W dry-run tylko symuluj — znajdź artykuły ale nie zapisuj
            for fee in fees:
                article_id, created = await _find_or_create_service_article(cur, fee['name'])
                if created:
                    stats['articles_created'] += 1
                    # W dry-run cofnij INSERT artykułu (symulacja)
                    if article_id:
                        await cur.execute("DELETE FROM articles WHERE id=%s", (article_id,))
                        article_id = None
            continue

        for fee in fees:
            article_id, created = await _find_or_create_service_article(cur, fee['name'])
            if created:
                stats['articles_created'] += 1
            op = await _upsert_service_fee(cur, contract_id, fee, article_id)
            stats[op] += 1

    if not dry_run:
        await conn.commit()

    # 4. Statystyki
    print(f"\n[2/3] Statystyki:")
    print(f"  contracts parsed:      {stats['contracts']}")
    print(f"  fees inserted:         {stats['inserted']}")
    print(f"  fees updated:          {stats['updated']}")
    print(f"  articles created:      {stats['articles_created']}")
    print(f"  unparseable contracts: {stats['unparseable_contracts']}")
    print(f"  unparseable lines:     {stats['unparseable_lines']}")

    # 5. Weryfikacja post-migration
    print(f"\n[3/3] Weryfikacja:")
    await cur.execute("SELECT COUNT(*) FROM contract_service_fees")
    total = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM contract_service_fees WHERE article_id IS NOT NULL")
    with_art = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM articles WHERE is_service=1")
    svc_art = (await cur.fetchone())[0]
    pct = (with_art * 100 // total) if total else 0
    print(f"  contract_service_fees: {total} (with article_id: {with_art}, {pct}%)")
    print(f"  service articles (is_service=1): {svc_art}")

    await cur.close()
    conn.close()
    print("\n✓ migrate_service_fees: zakończone." if not dry_run else "\n✓ migrate_service_fees: dry-run zakończony (bez zapisów).")
    return 0


async def verify() -> int:
    print("=" * 64)
    print("RAO-P2-059 — verify (stan po migracji)")
    print("=" * 64)
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    await cur.execute("SELECT COUNT(*) FROM contract_service_fees")
    total = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM contract_service_fees WHERE article_id IS NOT NULL")
    with_art = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM articles WHERE is_service=1")
    svc_art = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM service_fee_templates WHERE article_id IS NOT NULL")
    tpl_art = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM service_fee_templates")
    tpl_total = (await cur.fetchone())[0]

    print(f"contract_service_fees:       {total}")
    print(f"  with article_id:           {with_art} ({(with_art*100//total if total else 0)}%)")
    print(f"articles is_service=1:       {svc_art}")
    print(f"service_fee_templates:       {tpl_total} (with article_id: {tpl_art})")

    # Sample niepudłowane
    await cur.execute(
        "SELECT csf.id, csf.contract_id, csf.sort_order, csf.name, csf.article_id, a.name "
        "FROM contract_service_fees csf LEFT JOIN articles a ON a.id=csf.article_id "
        "WHERE csf.article_id IS NOT NULL ORDER BY csf.id LIMIT 5"
    )
    print("\nSample (contract_service_fees z article_id):")
    for row in await cur.fetchall():
        print(f"  csf#{row[0]} contract={row[1]} order={row[2]} name={row[3]!r} -> article#{row[4]} ({row[5]!r})")

    await cur.close()
    conn.close()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="RAO-P2-059 — migracja umowa2.oplaty -> contract_service_fees")
    ap.add_argument("--dry-run", action="store_true", help="Tylko statystyki, bez zapisu do DB")
    ap.add_argument("--verify", action="store_true", help="Tylko weryfikacja stanu (read-only)")
    args = ap.parse_args()

    if args.verify:
        return asyncio.run(verify())
    return asyncio.run(migrate(dry_run=args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
