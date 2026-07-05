"""
RAO-P2-061: Wystawia faktury w Fakturownia dla rozliczonych umów z source=fakturownia.

Dla każdej umowy z rozliczeniami source=fakturownia:
1. Pobiera kontrahenta (NIP -> FA client_id)
2. Pobiera pozycje/usługi z mapowaniem article_id -> FA product_id
3. Tworzy fakturę w FA z pozycjami (OID = numer umowy)
4. Zapisuje invoice_id w contract_settlements.fakturownia_invoice_id

Idempotentny: sprawdza czy faktura już istnieje po OID (numer umowy).

Użycie:
    cd backend && python seed_fa_invoices.py
"""
import asyncio
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, text
from database import AsyncSessionLocal

# Import modeli
import auth.models  # noqa
import contractors.models  # noqa
import articles.models  # noqa
import contracts.models  # noqa
import settings.models  # noqa
import categories.models  # noqa
import settlements.models  # noqa
import archive.models  # noqa
import audit.models  # noqa
import contract_costs.models  # noqa
import deliveries.models  # noqa
import reservations.models  # noqa
import integrations.fakturownia.models  # noqa
import integrations.models  # noqa

from contracts.models import Contract
from contractors.models import Contractor
from articles.models import Article
from settlements.models import ContractSettlement

# FA config — token WYŁĄCZNIE z env (nigdy hardcoded — bezpieczeństwo).
# Akceptuje FA_TOKEN lub FAKTUROWNIA_API_TOKEN (root .env).
FA_TOKEN = os.environ.get("FA_TOKEN") or os.environ.get("FAKTUROWNIA_API_TOKEN")
FA_DOMAIN = os.environ.get("FA_DOMAIN", "matsnd")
FA_BASE = f"https://{FA_DOMAIN}.fakturownia.pl"

# ── Faza 2d (opcja E): demo scenariusz unmapped ──────────────────────────────
# Numer umowy demo (musi zgadzać się z DEMO_UNMAPPED_CONTRACT_NUMBER w seed_demo_data.py).
# Dla tej umowy faktura FA dostaje 3. pozycję "Praca operatora" z product_id NIEZMAPOWANYM
# w RAO (articles.fakturownia_product_id) → init-from-fakturownia tworzy unmapped settlement.
DEMO_UNMAPPED_CONTRACT_NUMBER = "S099/2026"

# ID produktu "Praca operatora" w FA — NIE może być w articles.fakturownia_product_id w RAO.
# Konfigurowalne z env (FA_UNMAPPED_PRODUCT_ID). Jeśli brak — skrypt spróbuje utworzyć
# produkt "Praca operatora" w FA (ensure_unmapped_fa_product) i użyć jego ID.
FA_UNMAPPED_PRODUCT_ID = os.environ.get("FA_UNMAPPED_PRODUCT_ID")
FA_UNMAPPED_PRODUCT_NAME = os.environ.get("FA_UNMAPPED_PRODUCT_NAME", "Praca operatora")
FA_UNMAPPED_PRODUCT_PRICE_NET = float(os.environ.get("FA_UNMAPPED_PRODUCT_PRICE_NET", "650.41"))  # 800/1.23


def _require_token() -> None:
    if not FA_TOKEN:
        print("BŁĄD: brak tokenu Fakturownia. Ustaw FA_TOKEN lub FAKTUROWNIA_API_TOKEN w env/.env")
        sys.exit(1)

# Mapowanie NIP -> FA client ID
NIP_TO_FA_CLIENT = {
    "7010001234": 260564893,  # Bud-Plus
    "5260005678": 260564910,  # Invest
    "7790009012": 260564912,  # Terra-Masz
    "9510003456": 260564913,  # Wod-Bud
    "1460007890": 260564914,  # Fundament
    "6790002345": 260564915,  # Trakcja
    "2580006789": 260564917,  # Eko-Bud
    "8350001230": 260564918,  # Miejskie
}


async def get_article_fa_product_map(db):
    """Mapowanie article_id -> FA product_id."""
    result = await db.execute(select(Article.id, Article.fakturownia_product_id, Article.name))
    art_map = {}
    for row in result:
        art_map[row[0]] = {"fa_product_id": row[1], "name": row[2]}
    return art_map


async def get_contracts_with_fa_settlements(db):
    """Pobiera umowy z rozliczeniami source=fakturownia, pogrupowane po umowie."""
    # Najpierw sprawdź czy kolumna fakturownia_invoice_id istnieje
    try:
        await db.execute(text("SELECT fakturownia_invoice_id FROM contract_settlements LIMIT 1"))
    except Exception:
        # Dodaj kolumnę jeśli nie istnieje
        await db.execute(text(
            "ALTER TABLE contract_settlements ADD COLUMN IF NOT EXISTS fakturownia_invoice_id INT NULL"
        ))
        await db.commit()

    query = text("""
        SELECT cs.id, cs.contract_id, cs.position_id, cs.service_fee_id, cs.cost_client,
               c.number as contract_number, c.date_from, c.date_to,
               ct.id as contractor_id, ct.nip, ct.name as contractor_name,
               cp.article_id as pos_article_id, cp.article_name as pos_article_name,
               csf.article_id as fee_article_id, csf.name as fee_name
        FROM contract_settlements cs
        JOIN contracts c ON cs.contract_id = c.id
        JOIN contractors ct ON c.contractor_id = ct.id
        LEFT JOIN contract_positions cp ON cs.position_id = cp.id
        LEFT JOIN contract_service_fees csf ON cs.service_fee_id = csf.id
        WHERE cs.source = 'fakturownia' AND cs.fakturownia_invoice_id IS NULL
        ORDER BY cs.contract_id, cs.id
    """)
    result = await db.execute(query)
    rows = result.fetchall()

    # Pogrupuj po contract_id
    contracts = {}
    for row in rows:
        cid = row[1]
        if cid not in contracts:
            contracts[cid] = {
                "contract_id": cid,
                "contract_number": row[5],
                "date_from": row[6],
                "date_to": row[7],
                "contractor_id": row[8],
                "contractor_nip": row[9],
                "contractor_name": row[10],
                "settlements": [],
            }
        contracts[cid]["settlements"].append({
            "settlement_id": row[0],
            "position_id": row[2],
            "service_fee_id": row[3],
            "cost_client": float(row[4]),
            "pos_article_id": row[11],
            "pos_article_name": row[12],
            "fee_article_id": row[13],
            "fee_name": row[14],
        })
    return list(contracts.values())


async def get_fa_pending_contracts(db):
    """RAO-P2-067 + P1-004: umowy NIEROZLICZONE bez żadnych settlements w RAO.

    Obejmuje BOTH:
    - umowy zakończone (date_to < CURDATE()) — oryginalna Pula C
    - umowy aktywne (date_to >= CURDATE() lub NULL) — Pula D (P1-004):
      aktywne umowy w trakcie wynajmu z fakturami w FA gotowymi do pobrania.

    Dla nich wystawiamy fakturę w FA (OID = numer umowy), ale NIE tworzymy
    rozliczeń w RAO — to zrobi user na demo klikając "Pobierz z Fakturowni"
    (POST /settlements/contract/{id}/init-from-fakturownia).

    Pozycje faktury liczone z warunków umowy:
    - pozycje maszyn: unit_price × rental_days
    - usługi dodatkowe: amount_from
    """
    # P1-004: usunięto filtr date_to < CURDATE() — teraz obejmuje też aktywne
    # umowy (date_to >= CURDATE() lub NULL = umowa na czas nieokreślony).
    # Warunek: is_settled=0 AND brak settlements — to definiuje "FA-pending".
    query = text("""
        SELECT c.id, c.number, c.date_from, c.date_to,
               ct.id as contractor_id, ct.nip, ct.name as contractor_name,
               cp.id as position_id, cp.article_id, cp.article_name,
               cp.unit_price, cp.rental_days,
               NULL as fee_article_id, NULL as fee_name, NULL as fee_amount
        FROM contracts c
        JOIN contractors ct ON c.contractor_id = ct.id
        JOIN contract_positions cp ON cp.contract_id = c.id
        WHERE c.is_settled = 0
          AND NOT EXISTS (SELECT 1 FROM contract_settlements cs WHERE cs.contract_id = c.id)
        UNION ALL
        SELECT c.id, c.number, c.date_from, c.date_to,
               ct.id, ct.nip, ct.name,
               NULL, NULL, NULL, NULL, NULL,
               csf.article_id, csf.name, csf.amount_from
        FROM contracts c
        JOIN contractors ct ON c.contractor_id = ct.id
        JOIN contract_service_fees csf ON csf.contract_id = c.id
        WHERE c.is_settled = 0
          AND NOT EXISTS (SELECT 1 FROM contract_settlements cs WHERE cs.contract_id = c.id)
        ORDER BY 1
    """)
    result = await db.execute(query)
    rows = result.fetchall()

    contracts = {}
    for row in rows:
        cid = row[0]
        if cid not in contracts:
            contracts[cid] = {
                "contract_id": cid,
                "contract_number": row[1],
                "date_from": row[2],
                "date_to": row[3],
                "contractor_id": row[4],
                "contractor_nip": row[5],
                "contractor_name": row[6],
                "settlements": [],  # kompatybilny kształt dla create_fa_invoice
            }
        if row[7] is not None:  # pozycja maszyny
            amount = float(row[10] or 0) * int(row[11] or 0)
            contracts[cid]["settlements"].append({
                "settlement_id": None,
                "position_id": row[7],
                "service_fee_id": None,
                "cost_client": amount,
                "pos_article_id": row[8],
                "pos_article_name": row[9],
                "fee_article_id": None,
                "fee_name": None,
            })
        elif row[13] is not None:  # usługa dodatkowa
            contracts[cid]["settlements"].append({
                "settlement_id": None,
                "position_id": None,
                "service_fee_id": None,
                "cost_client": float(row[14] or 0),
                "pos_article_id": None,
                "pos_article_name": None,
                "fee_article_id": row[12],
                "fee_name": row[13],
            })
    return list(contracts.values())


async def check_invoice_exists_by_oid(client, oid):
    """Sprawdza czy faktura z danym OID już istnieje w FA.

    RAO-P2-067 fix: FA MA wyszukiwanie po OID (GET /invoices.json?oid=...) —
    to samo pole używa integracja RAO (get_invoices_by_oid). Wcześniejsze
    skanowanie po description nie zgadzało się z mechanizmem syncu.
    """
    resp = await client.get(
        f"{FA_BASE}/invoices.json",
        params={"api_token": FA_TOKEN, "oid": oid},
        timeout=15.0,
    )
    resp.raise_for_status()
    invoices = resp.json()
    if isinstance(invoices, list) and invoices:
        return invoices[0]["id"]
    return None


async def ensure_unmapped_fa_product(client, db) -> int:
    """Faza 2d (opcja E): zwraca ID produktu "Praca operatora" w FA, NIEzmapowanego w RAO.

    Kolejność:
    1. Jeśli FA_UNMAPPED_PRODUCT_ID w env → użyj go (po weryfikacji że nie jest w RAO).
    2. W przeciwnym razie szukaj w FA po nazwie (GET /products.json?name=...).
    3. Jeśli nie znaleziono → utwórz nowy produkt w FA (POST /products.json).
    4. Weryfikacja: product_id NIE może być w articles.fakturownia_product_id w RAO.

    Zwraca FA product_id (int). Rzuca RuntimeError jeśli konflikt mapowania.
    """
    # Krok 1: env override
    if FA_UNMAPPED_PRODUCT_ID:
        pid = int(FA_UNMAPPED_PRODUCT_ID)
        # Weryfikacja: nie może być zmapowany w RAO
        mapped = await db.execute(
            select(Article.id).where(Article.fakturownia_product_id == pid).limit(1)
        )
        if mapped.scalar_one_or_none():
            raise RuntimeError(
                f"FA_UNMAPPED_PRODUCT_ID={pid} jest zmapowany w RAO (articles.fakturownia_product_id) "
                f"— to MUSI być niezmapowany produkt. Ustaw inny ID w env."
            )
        print(f"  [unmapped] Używam FA_UNMAPPED_PRODUCT_ID z env: {pid}")
        return pid

    # Krok 2: szukaj w FA po nazwie
    resp = await client.get(
        f"{FA_BASE}/products.json",
        params={"api_token": FA_TOKEN, "name": FA_UNMAPPED_PRODUCT_NAME},
        timeout=15.0,
    )
    resp.raise_for_status()
    products = resp.json()
    if isinstance(products, list):
        for p in products:
            if p.get("name", "").strip().lower() == FA_UNMAPPED_PRODUCT_NAME.strip().lower():
                pid = int(p["id"])
                # Weryfikacja: nie zmapowany w RAO
                mapped = await db.execute(
                    select(Article.id).where(Article.fakturownia_product_id == pid).limit(1)
                )
                if mapped.scalar_one_or_none():
                    print(f"  [unmapped] Produkt FA '{p['name']}' (ID={pid}) jest zmapowany w RAO — szukam dalej")
                    continue
                print(f"  [unmapped] Znaleziono niezmapowany produkt FA: '{p['name']}' (ID={pid})")
                return pid

    # Krok 3: utwórz nowy produkt w FA
    print(f"  [unmapped] Tworzę nowy produkt FA '{FA_UNMAPPED_PRODUCT_NAME}'...")
    body = {
        "api_token": FA_TOKEN,
        "product": {
            "name": FA_UNMAPPED_PRODUCT_NAME,
            "price_net": FA_UNMAPPED_PRODUCT_PRICE_NET,
            "tax": 23,
        },
    }
    resp = await client.post(f"{FA_BASE}/products.json", json=body, timeout=20.0)
    resp.raise_for_status()
    data = resp.json()
    pid = int(data["id"])
    print(f"  [unmapped] Utworzono produkt FA '{FA_UNMAPPED_PRODUCT_NAME}' (ID={pid})")
    return pid


def _is_demo_unmapped_contract(contract_data) -> bool:
    """Czy ta umowa to demo scenariusz unmapped (opcja E)?"""
    return contract_data.get("contract_number") == DEMO_UNMAPPED_CONTRACT_NUMBER


async def _append_demo_unmapped_position(client, db, contract_data, positions):
    """Faza 2d (opcja E): dodaje 3. pozycję "Praca operatora" (niezmapowaną) do faktury demo.

    Pozycja 1 + 2 pochodzą z umowy (Transport + Tankowanie — zmapowane).
    Pozycja 3 = "Praca operatora" z product_id NIEzmapowanym w RAO → unmapped settlement.
    Kwota brutto: 800 zł (price_net = 800/1.23 ≈ 650.41).
    """
    unmapped_pid = await ensure_unmapped_fa_product(client, db)
    positions.append({
        "name": FA_UNMAPPED_PRODUCT_NAME,
        "quantity": 1,
        "price_net": FA_UNMAPPED_PRODUCT_PRICE_NET,  # 800 zł brutto / 1.23
        "tax": 23,
        "product_id": unmapped_pid,
    })
    print(f"  [unmapped] Dodano pozycję '{FA_UNMAPPED_PRODUCT_NAME}' (FA product_id={unmapped_pid}, "
          f"~800 zł brutto) — niezmapowaną w RAO")
    return positions


async def create_fa_invoice(client, contract_data, art_map, db=None):
    """Tworzy fakturę w FA dla jednej umowy."""
    fa_client_id = NIP_TO_FA_CLIENT.get(contract_data["contractor_nip"])
    if not fa_client_id:
        print(f"  SKIP: Brak mapowania FA dla NIP {contract_data['contractor_nip']}")
        return None

    # Buduj pozycje faktury
    positions = []
    for s in contract_data["settlements"]:
        # Ustal article_id i nazwę
        article_id = s["pos_article_id"] or s["fee_article_id"]
        article_name = s["pos_article_name"] or s["fee_name"]
        art_info = art_map.get(article_id, {})
        fa_product_id = art_info.get("fa_product_id")

        pos = {
            "name": article_name,
            "quantity": 1,
            "price_net": s["cost_client"] / 1.23,  # netto z brutto (23% VAT)
            "tax": 23,
        }
        if fa_product_id:
            pos["product_id"] = fa_product_id
        positions.append(pos)

    if not positions:
        print(f"  SKIP: Brak pozycji dla {contract_data['contract_number']}")
        return None

    # Faza 2d (opcja E): dla umowy demo unmapped — dodaj 3. pozycję niezmapowaną
    if _is_demo_unmapped_contract(contract_data):
        if db is None:
            print(f"  WARN: brak sesji DB — pomijam pozycję unmapped dla {contract_data['contract_number']}")
        else:
            positions = await _append_demo_unmapped_position(client, db, contract_data, positions)

    # OID = numer umowy (zapisany w description)
    oid = contract_data["contract_number"]
    issue_date = contract_data["date_to"] or date.today()
    if isinstance(issue_date, date):
        issue_date_str = issue_date.strftime("%Y-%m-%d")
    else:
        issue_date_str = str(issue_date)[:10]

    invoice_body = {
        "api_token": FA_TOKEN,
        "invoice": {
            "kind": "vat",
            "number": None,  # FA auto-numeracja
            "issue_date": issue_date_str,
            "payment_to": issue_date_str,
            "client_id": fa_client_id,
            "buyer_tax_no_kind": "other",  # omija walidację NIP (demo NIP-y nie w GUS)
            # RAO-P2-067 fix: OID w dedykowanym polu — integracja RAO szuka
            # faktur przez GET /invoices.json?oid=<numer umowy> (nie po description!)
            "oid": oid,
            "description": f"Rozliczenie umowy {oid}",
            "positions": positions,
        },
    }

    try:
        resp = await client.post(
            f"{FA_BASE}/invoices.json",
            json=invoice_body,
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        inv_id = data.get("id")
        inv_number = data.get("number", "?")
        print(f"  OK: Faktura {inv_number} (ID={inv_id}) dla {oid} — {len(positions)} pozycji")
        return inv_id
    except Exception as e:
        err_body = ""
        if hasattr(e, "response") and e.response is not None:
            err_body = e.response.text[:300]
        print(f"  FAIL: {oid} — {e} | {err_body}")
        return None


async def update_settlements_with_invoice_id(db, contract_id, invoice_id):
    """Aktualizuje rozliczenia z source=fakturownia dla danej umowy — ustawia fakturownia_invoice_id."""
    await db.execute(text(
        "UPDATE contract_settlements SET fakturownia_invoice_id = :inv_id "
        "WHERE contract_id = :cid AND source = 'fakturownia' AND fakturownia_invoice_id IS NULL"
    ), {"inv_id": invoice_id, "cid": contract_id})
    await db.commit()


async def main():
    print("=" * 60)
    print("RAO-P2-061/067: Fakturownia invoices seeding")
    print("=" * 60)
    _require_token()

    async with AsyncSessionLocal() as db:
        art_map = await get_article_fa_product_map(db)
        print(f"\nArtykuły z mapowaniem FA: {len(art_map)}")

        created = 0
        skipped = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            # ── Część 1: umowy rozliczone source=fakturownia (backfill invoice_id) ──
            contracts = await get_contracts_with_fa_settlements(db)
            print(f"\n[1/2] Umowy z rozliczeniami fakturownia (bez faktury): {len(contracts)}")
            for cd in contracts:
                print(f"\n[{cd['contract_number']}] {cd['contractor_name']} (NIP {cd['contractor_nip']})")
                print(f"  Rozliczenia: {len(cd['settlements'])}")

                existing_inv = await check_invoice_exists_by_oid(client, cd["contract_number"])
                if existing_inv:
                    print(f"  EXISTS: Faktura ID={existing_inv} już istnieje — aktualizuję rozliczenia")
                    await update_settlements_with_invoice_id(db, cd["contract_id"], existing_inv)
                    skipped += 1
                    continue

                inv_id = await create_fa_invoice(client, cd, art_map, db=db)
                if inv_id:
                    await update_settlements_with_invoice_id(db, cd["contract_id"], inv_id)
                    created += 1
                else:
                    failed += 1

            # ── Część 2 (RAO-P2-067): FA-pending — faktury dla umów NIEROZLICZONYCH ──
            # Faktura powstaje w FA (OID = numer umowy), rozliczeń w RAO NIE tworzymy —
            # user na demo klika "Pobierz z Fakturowni" i widzi jak wpadają.
            # Faza 2d (opcja E): umowa S099/2026 dostaje 3. pozycję niezmapowaną.
            pending = await get_fa_pending_contracts(db)
            print(f"\n[2/2] Umowy FA-pending (nierozliczone, faktura czeka w FA): {len(pending)}")
            for cd in pending:
                print(f"\n[{cd['contract_number']}] {cd['contractor_name']} — FA-pending")
                print(f"  Pozycje faktury: {len(cd['settlements'])}")

                existing_inv = await check_invoice_exists_by_oid(client, cd["contract_number"])
                if existing_inv:
                    print(f"  EXISTS: Faktura ID={existing_inv} już czeka w FA — OK (demo ready)")
                    skipped += 1
                    continue

                inv_id = await create_fa_invoice(client, cd, art_map, db=db)
                if inv_id:
                    print(f"  READY: faktura czeka w FA — demo 'Pobierz z Fakturowni' dla {cd['contract_number']}")
                    created += 1
                else:
                    failed += 1

        print(f"\n{'=' * 60}")
        print(f"Podsumowanie: {created} utworzonych, {skipped} istniejących, {failed} błędów")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
