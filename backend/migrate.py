"""
Migration: old dump (toolsmart_roa) → rao_new
Step 5b added: migrate umowa2.OPLATY → contract_service_fees (free-text parsing).

Verified source tables from dump:
  firma(41)  kategoria(4)  oddzial(7)  handlowiec(4)  stawka(4)
  kontrahent2(24)  artykul3(17)  uzytkownik(8)
  umowa2(34)  umowa_pozycja3(15)  umowa_pozycja2_warunek(9)
  adres_dostawy(16) — linked to umowa, not kontrahent

Strategy:
  1. DROP+CREATE rao_new
  2. Import dump via mysql CLI  → old Polish tables appear
  3. CREATE new English tables  → SQLAlchemy models
  4. INSERT…SELECT old→new      → deterministic column mapping
  5. Build service_fee_templates from firma.oplata_* columns
  6. DROP old tables + views
  7. Rehash plaintext passwords with bcrypt

Usage: python migrate.py
"""
import asyncio
import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation

import bcrypt
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine

from database import Base
import auth.models         # noqa
import contractors.models  # noqa
import articles.models     # noqa
import contracts.models    # noqa
import settings.models     # noqa
import categories.models   # noqa

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "rao_user"
DB_PASS = "RaoPass2026!"
DB_NAME = "rao_new"
DUMP_PATH = r"c:\dbdump\dump-toolsmart_roa-202603141415-full.sql"

# Every object imported from the dump (tables + views) to drop at the end
OLD_OBJECTS = [
    # views first (DROP VIEW)
    "artykuly", "artykulyy", "dane", "imp_kontrahentow", "imp_przedmiotow",
    "kontrahenci", "nr_umowy", "oplaty", "pozycje", "pozycje2",
    "rao_dshb", "rozliczenie_rpt", "umowy", "umowy1", "warunki",
    # tables
    "a", "adres", "adres_dostawy", "artykul", "artykul2", "artykul3",
    "dostawa", "firma", "handlowiec", "imp", "imp_kontrahent",
    "imp_przedmiot", "imp_rozliczenie", "kategoria", "kontakt",
    "kontrahent", "kontrahent2", "koszt", "koszt_typ", "lp", "oddo",
    "oddzial", "rozliczenie", "stawka", "temp", "u",
    "umowa", "umowa2", "umowa_oddzial", "umowa_pozycja", "umowa_pozycja2",
    "umowa_pozycja2_warunek", "umowa_pozycja3", "uzytkownik", "zdarzenie",
]


async def step1_recreate_db():
    print("[1/7] DROP + CREATE rao_new …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS)
    cur = await conn.cursor()
    await cur.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`")
    await cur.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    await conn.commit()
    await cur.close()
    conn.close()
    print("   OK")


def step2_import_dump():
    print("[2/7] Import dump via mysql CLI …")
    cmd = f'cmd /c "mysql -h {DB_HOST} -P {DB_PORT} -u {DB_USER} -p{DB_PASS} {DB_NAME} < {DUMP_PATH}"'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"   WARN: {r.stderr[:300]}")
    else:
        print("   OK")


async def step3_create_schema():
    print("[3/7] CREATE new tables from SQLAlchemy models …")
    engine = create_async_engine(
        f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        echo=False,
    )
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("   OK")


async def step4_migrate_data():
    """Deterministic column-by-column mapping verified against dump schema."""
    print("[4/7] INSERT … SELECT  old → new …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # Diagnostic: show rodzaj distribution to verify is_service mapping
    await cur.execute("SELECT rodzaj, COUNT(*) FROM artykul3 GROUP BY rodzaj ORDER BY COUNT(*) DESC")
    print("   [diag] artykul3.rodzaj distribution:")
    for row in await cur.fetchall():
        print(f"          {row[0]!r}: {row[1]}")

    await cur.execute("SET FOREIGN_KEY_CHECKS = 0")

    # ── firma → company ──
    # firma: id, nazwa, nazwa_krotka, nip, regon, kod_pocztowy, miejscowosc,
    #        ulica_lokal, naglowek, logo, bank, rachunek, numeracja, interwal,
    #        folder, wersja, folder2
    M = [
        ("company", """
            INSERT INTO company
                (id, name, name_short, nip, regon, postal_code, city, street,
                 header_text, logo, bank_name, bank_account,
                 numbering_start, increment_step,
                 report_folder, app_version, protocol_folder)
            SELECT
                id, nazwa, nazwa_krotka, nip, regon, kod_pocztowy, miejscowosc, ulica_lokal,
                naglowek, logo, bank, rachunek,
                numeracja, interwal,
                folder, wersja, folder2
            FROM firma
        """),

        # ── kategoria → categories ──
        ("categories", """
            INSERT INTO categories (id, name, code, description)
            SELECT id, nazwa, kod, opis FROM kategoria
        """),

        # ── oddzial → branches ──
        # oddzial: id, nazwa, adres, kod_pocztowy, miejscowosc, ulica_lokal, haslo
        ("branches", """
            INSERT INTO branches (id, name, address, postal_code, city, street, created_at)
            SELECT id, nazwa, adres, kod_pocztowy, miejscowosc, ulica_lokal, NOW()
            FROM oddzial
        """),

        # ── handlowiec → salespeople ──
        # handlowiec: id, nazwa, telefon, aktywny
        ("salespeople", """
            INSERT INTO salespeople (id, name, phone, is_active)
            SELECT id, nazwa, telefon, aktywny FROM handlowiec
        """),

        # ── stawka → rate_types ──
        # stawka: id, nazwa, opis, zalezna
        ("rate_types", """
            INSERT INTO rate_types (id, name, description, is_dependent)
            SELECT id, nazwa, opis, zalezna FROM stawka
        """),

        # ── kontrahent2 → contractors ──
        # kontrahent2: id, nazwa, nip, regon, pesel, kod_pocztowy, miejscowosc,
        #   ulica, lokal, uwagi, data, dostawca, email, osoba_kontaktowa, telefon,
        #   telefon2, osoba_kontaktowa2, data_gus, data_zakonczenia, nazwa_krotka,
        #   telefon_stac, www, folder, data_modyfikacji
        ("contractors", """
            INSERT INTO contractors
                (id, name, name_short, nip, regon, pesel,
                 postal_code, city, street, unit, notes, is_supplier,
                 email, contact_person1, phone1, contact_person2, phone2,
                 landline_phone, website, files_folder, gus_date,
                 created_at, updated_at)
            SELECT
                id, nazwa, nazwa_krotka, nip, regon, pesel,
                kod_pocztowy, miejscowosc, ulica, lokal, uwagi, dostawca,
                email, osoba_kontaktowa, telefon, osoba_kontaktowa2, telefon2,
                telefon_stac, www, folder, data_gus,
                COALESCE(data, NOW()), COALESCE(data_modyfikacji, NOW())
            FROM kontrahent2
        """),

        # ── adres_dostawy → contractor_addresses ──
        # adres_dostawy: id, id_umowy, nazwa, ulica, numer, kod_pocztowy,
        #   hamlet, miejscowosc, miasto, wioska, powiat, gmina, wojewodztwo, …
        # JOIN umowa2 to get id_kontrahenta → contractor_id
        ("contractor_addresses", """
            INSERT INTO contractor_addresses
                (id, contractor_id, name, country_code, postal_code, city, street,
                 notes, is_default_delivery, is_headquarters, created_at)
            SELECT
                a.id,
                u.id_kontrahenta,
                a.nazwa,
                'PL',
                a.kod_pocztowy,
                COALESCE(a.miejscowosc, a.miasto, a.hamlet, a.wioska),
                CONCAT_WS(' ', a.ulica, a.numer),
                CONCAT_WS(', ', NULLIF(a.powiat,''), NULLIF(a.gmina,''), NULLIF(a.wojewodztwo,'')),
                0, 0, NOW()
            FROM adres_dostawy a
            JOIN umowa2 u ON u.id = a.id_umowy
        """),

        # ── artykul3 → articles ──
        # artykul3: id, nazwa, usluga(varchar), nr_rejestracyjny, id_kategorii,
        #   opis, marka, model, uwagi, data_dodania, id_wlasciciel, wartosc,
        #   nr_seryjny, data_modyfikacji, liczba_dni, rodzaj, id_oddzialu
        ("articles", """
            INSERT INTO articles
                (id, name, is_service, registration_no, category_id,
                 description, brand, model, notes, created_at,
                 owner_id, replacement_value, serial_no, updated_at,
                 rental_days, article_type, branch_id)
            SELECT
                id, nazwa,
                CASE WHEN LOWER(rodzaj) = 'usługa' OR LOWER(rodzaj) = 'usluga' THEN 1 ELSE 0 END,
                nr_rejestracyjny, NULLIF(id_kategorii, 0),
                opis, marka, model, uwagi,
                COALESCE(data_dodania, NOW()),
                NULLIF(id_wlasciciel, 0), wartosc, nr_seryjny,
                COALESCE(data_modyfikacji, NOW()),
                liczba_dni, rodzaj, NULLIF(id_oddzialu, 0)
            FROM artykul3
        """),

        # ── uzytkownik → users ──
        # uzytkownik: id, login, haslo, imie, nazwisko, id_grupy, data, id_oddzialu
        # No email column. id_grupy=1 → admin, else → user
        ("users", """
            INSERT INTO users
                (id, login, password, first_name, last_name,
                 role, is_active, must_change_password,
                 branch_id, created_at)
            SELECT
                id, login, haslo, imie, nazwisko,
                CASE WHEN id_grupy = 1 THEN 'admin' ELSE 'user' END,
                1, 1,
                NULLIF(id_oddzialu, 0),
                COALESCE(data, NOW())
            FROM uzytkownik
        """),

        # ── umowa2 → contracts ──
        # umowa2: id, id_kontrahenta, numer, opis, adres, data_od, data_do,
        #   wartosc, przedplata_kwota, przedplata_dokument, uwagi,
        #   faktura_kwota, faktura_dokument, data_wprowadzenia, data_modyfikacji,
        #   email, osoba1, telefon2, telefon1, osoba2, id_firmy, oplaty,
        #   nazwa, sciezka_wydruku, data_wydruku, liczba_dni,
        #   pokaz_osobe1, pokaz_osobe2, telefon, typ, ilepoz, pz_bez,
        #   autonumer, id_handlowca
        ("contracts", """
            INSERT INTO contracts
                (id, contractor_id, salesperson_id,
                 number, auto_number, contract_type,
                 delivery_address, date_from, date_to,
                 total_value, prepayment_amount, prepayment_document,
                 invoice_amount, invoice_document,
                 notes, contact_person1, contact_phone1, show_person1,
                 contact_person2, contact_phone2, show_person2,
                 email, phone, contractor_name,
                 print_path, print_date, report_without_data,
                 working_days_per_week, position_count,
                 created_at, updated_at)
            SELECT
                id, id_kontrahenta, NULLIF(id_handlowca, 0),
                numer, autonumer, COALESCE(typ, 'S'),
                adres, data_od, data_do,
                wartosc, przedplata_kwota, przedplata_dokument,
                faktura_kwota, faktura_dokument,
                uwagi, osoba1, telefon1, COALESCE(pokaz_osobe1, 1),
                osoba2, telefon2, COALESCE(pokaz_osobe2, 1),
                email, telefon, nazwa,
                sciezka_wydruku, data_wydruku, COALESCE(pz_bez, 0),
                COALESCE(liczba_dni, 6), ilepoz,
                COALESCE(data_wprowadzenia, NOW()),
                COALESCE(data_modyfikacji, NOW())
            FROM umowa2
        """),

        # ── umowa_pozycja3 → contract_positions ──
        # umowa_pozycja3: id, id_umowy, id_artykulu, typ_wynajmu, koszty, opis,
        #   liczba_dni, id_stawki, rozliczanie, oplataza, ilosc, cena,
        #   id_dostawcy, data_dostawy, nazwa
        ("contract_positions", """
            INSERT INTO contract_positions
                (id, contract_id, article_id, rental_type, costs, description,
                 rental_days, rate_type_id, billing_frequency, billing_unit,
                 quantity, unit_price, supplier_id, delivery_date, article_name)
            SELECT
                id, id_umowy, id_artykulu, typ_wynajmu, koszty, opis,
                liczba_dni, NULLIF(id_stawki, 0), rozliczanie, oplataza,
                ilosc, cena, NULLIF(id_dostawcy, 0), data_dostawy, nazwa
            FROM umowa_pozycja3
        """),

        # ── umowa_pozycja2_warunek → position_conditions ──
        # umowa_pozycja2_warunek: id, id_pozycji, id_stawki, opis,
        #   oplata1, oplata2, rozliczana, liczba_dni, minimum
        # id_pozycji references umowa_pozycja3.id (verified: 875/897 match)
        # Filter to only rows whose id_pozycji exists in contract_positions
        ("position_conditions", """
            INSERT INTO position_conditions
                (id, position_id, rate_type_id, description,
                 rate1, rate2, billing_label, period_count, minimum)
            SELECT
                w.id, w.id_pozycji, NULLIF(w.id_stawki, 0), w.opis,
                w.oplata1, w.oplata2, w.rozliczana, w.liczba_dni, w.minimum
            FROM umowa_pozycja2_warunek w
            WHERE w.id_pozycji IN (SELECT id FROM contract_positions)
        """),
    ]

    for i, (tbl, sql) in enumerate(M, 1):
        try:
            await cur.execute(sql)
            print(f"   [{i:2d}/{len(M)}] {tbl}: {cur.rowcount} rows")
        except Exception as e:
            print(f"   [{i:2d}/{len(M)}] {tbl}: ERROR — {e}")

    await cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    await conn.commit()
    await cur.close()
    conn.close()


async def step5_service_fee_templates():
    """Build service_fee_templates from firma.oplata_* columns (5 standard fee types)."""
    print("[5/7] Building service fee templates from firma …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # Read firma fees
    await cur.execute("""
        SELECT
            czy_oplata_tankowanie, oplata_tankowanie_od, oplata_tankowanie_do, oplata_tankowanie_opis,
            czy_oplata_transport, oplata_tarnsport_od, oplata_tarnsport_do, oplata_transport_opis,
            czy_oplata_ponadnormatywny, oplata_ponadnormatywny_przestuj_od, oplata_ponadnormatywny_przestuj_do, oplata_ponadnormatywny_przestuj_opis,
            czy_oplata_czyszczenie1, oplata_czyszczenie1_od, oplata_czyszczenie1_do, oplata_czyszczenie1_opis,
            czy_oplata_czyszczenie2, oplata_czyszczenie2_od, oplata_czyszczenie2_do, oplata_czyszczenie2_opis
        FROM firma LIMIT 1
    """)
    row = await cur.fetchone()
    if row:
        fees = [
            ("Tankowanie",                  row[0], row[1], row[2], row[3]),
            ("Transport",                   row[4], row[5], row[6], row[7]),
            ("Ponadnormatywny przestój",    row[8], row[9], row[10], row[11]),
            ("Czyszczenie 1",               row[12], row[13], row[14], row[15]),
            ("Czyszczenie 2",               row[16], row[17], row[18], row[19]),
        ]
        count = 0
        for i, (name, active, amt_from, amt_to, desc) in enumerate(fees):
            await cur.execute("""
                INSERT INTO service_fee_templates
                    (company_id, contract_type, sort_order, name, amount_from, amount_to, description, is_active)
                VALUES (1, 'S', %s, %s, %s, %s, %s, %s)
            """, (i, name, amt_from, amt_to, desc, 1 if active else 0))
            # Also create for U type
            await cur.execute("""
                INSERT INTO service_fee_templates
                    (company_id, contract_type, sort_order, name, amount_from, amount_to, description, is_active)
                VALUES (1, 'U', %s, %s, %s, %s, %s, %s)
            """, (i, name, amt_from, amt_to, desc, 1 if active else 0))
            count += 2
        await conn.commit()
        print(f"   {count} fee templates created (5 × S + 5 × U)")
    else:
        print("   WARN: no firma row found")

    await cur.close()
    conn.close()


# ---------------------------------------------------------------------------
# Fee-text parsing helpers (for step5b)
# ---------------------------------------------------------------------------

_A = r'([\d]+(?:\s[\d]{3})*(?:[,.][\d]+)?)'

_RE_DOSTAWA  = re.compile(rf'^{_A}\s*z[łl]\s*[-–]?\s*(.{{1,30}}?)\s*/\s*{_A}\s*z[łl]\s*[-–]?\s*(odbi[oó]r\S*)', re.I | re.U)
_RE_H_RANGE  = re.compile(rf'^{_A}\s*z[łl]\s*/\s*(\S+)\s*[-–]\s*{_A}\s*z[łl]\s*/\s*\S+')
_RE_PER_UNIT = re.compile(rf'^{_A}\s*z[łl]\s*/\s*(\S+)')
_RE_RANGE    = re.compile(rf'^{_A}\s*z[łl]\s*[-–]\s*{_A}\s*z[łl]')
_RE_PARENS   = re.compile(rf'^{_A}\s*z[łl]\s*\(([^)]+)\)')
_RE_SINGLE   = re.compile(rf'^{_A}\s*z[łl](.*)')
_RE_NOCOL    = re.compile(rf'^(.+?)\s+{_A}\s*z[łl]\s*/\s*(\S+)\s*$')
_RE_SKIP     = re.compile(
    r'^(-zedytowane|1[-\s]*2\s*dni|powyżej\s*2|praca do \d|czas trwania|'
    r'opłata w gotówce|do \d+ godzin\s*-)',
    re.I,
)


def _to_dec(s: str) -> Decimal | None:
    if not s:
        return None
    try:
        return Decimal(s.strip().replace(' ', '').replace(',', '.'))
    except InvalidOperation:
        return None


def _parse_fee_line(raw: str) -> dict | None:
    line = raw.strip().lstrip('- ').strip()
    if not line or _RE_SKIP.match(line):
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


def _parse_text_to_fees(text: str) -> list[dict]:
    result = []
    if not text:
        return result
    sort_order = 0
    for raw in text.replace('\r\n', '\n').replace('\r', '\n').splitlines():
        fee = _parse_fee_line(raw)
        if fee:
            fee['sort_order'] = sort_order
            sort_order += 1
            result.append(fee)
    return result


async def step5b_contract_service_fees():
    """Parse umowa2.OPLATY free-text → contract_service_fees rows."""
    print("[5b] Migrating umowa2.OPLATY → contract_service_fees …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur  = await conn.cursor()

    await cur.execute(
        "SELECT id, OPLATY FROM umowa2 WHERE OPLATY IS NOT NULL AND TRIM(OPLATY) != ''"
    )
    rows = await cur.fetchall()

    inserted = 0
    skipped  = 0
    for contract_id, oplaty in rows:
        fees = _parse_text_to_fees(oplaty)
        for fee in fees:
            await cur.execute(
                """INSERT INTO contract_service_fees
                   (contract_id, sort_order, name,
                    amount_from, amount_to, unit, description, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (contract_id, fee['sort_order'], fee['name'],
                 fee['amount_from'], fee['amount_to'],
                 fee['unit'], fee['description'], fee['is_active'])
            )
            inserted += 1
        if not fees:
            skipped += 1

    await conn.commit()
    await cur.close()
    conn.close()
    print(f"   {inserted} service fee rows from {len(rows)} contracts ({skipped} unparseable skipped)")


async def step6_drop_old():
    print("[6/7] DROP old tables + views …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()
    await cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    dropped = 0
    for obj in OLD_OBJECTS:
        for kind, ttype in (("VIEW", "VIEW"), ("TABLE", "BASE TABLE")):
            try:
                await cur.execute(
                    "SELECT COUNT(*) FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND TABLE_TYPE=%s",
                    (DB_NAME, obj, ttype),
                )
                (exists,) = await cur.fetchone()
                if exists:
                    await cur.execute(f"DROP {kind} `{obj}`")
                    dropped += 1
            except Exception:
                pass
    await cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    await conn.commit()
    await cur.close()
    conn.close()
    print(f"   dropped {dropped} objects")


async def step7_rehash():
    print("[7/7] Rehash plaintext passwords → bcrypt …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()
    await cur.execute("SELECT id, password FROM users")
    rows = await cur.fetchall()
    n = 0
    for uid, pwd in rows:
        if not pwd or pwd.startswith("$2"):
            continue
        # bcrypt max 72 bytes
        pwd_bytes = pwd.encode("utf-8")[:72]
        h = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")
        await cur.execute("UPDATE users SET password=%s, must_change_password=1 WHERE id=%s", (h, uid))
        n += 1
    await conn.commit()
    await cur.close()
    conn.close()
    print(f"   {n} passwords rehashed")


async def verify():
    """Quick row-count verification."""
    print("\n── Verification ──")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()
    for tbl in ["company","categories","branches","salespeople","rate_types",
                "contractors","contractor_addresses","articles","users",
                "contracts","contract_positions","position_conditions",
                "service_fee_templates","contract_service_fees"]:
        await cur.execute(f"SELECT COUNT(*) FROM `{tbl}`")
        cnt = (await cur.fetchone())[0]
        print(f"   {tbl}: {cnt}")
    await cur.close()
    conn.close()


async def main():
    print("=" * 60)
    print("RAO Migration  —  deterministic dump → rao_new")
    print("=" * 60)
    try:
        await step1_recreate_db()
        step2_import_dump()
        await step3_create_schema()
        await step4_migrate_data()
        await step5_service_fee_templates()
        await step5b_contract_service_fees()
        await step6_drop_old()
        await step7_rehash()
        await verify()
        print("\n✓ Migration complete!")
    except Exception as e:
        print(f"\n✗ FATAL: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
