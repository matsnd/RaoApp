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

# FA config
FA_TOKEN = os.environ.get("FA_TOKEN", "sejjNboMz7zZ3fFLxtoW")
FA_DOMAIN = "matsnd"
FA_BASE = f"https://{FA_DOMAIN}.fakturownia.pl"

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


async def check_invoice_exists_by_oid(client, oid):
    """Sprawdza czy faktura z danym OID już istnieje w FA."""
    # FA nie ma bezpośredniego endpointu do szukania po OID,
    # ale możemy pobrać wszystkie faktury i sprawdzić description
    resp = await client.get(
        f"{FA_BASE}/invoices.json",
        params={"api_token": FA_TOKEN, "per_page": 100},
        timeout=15.0,
    )
    resp.raise_for_status()
    invoices = resp.json()
    for inv in invoices:
        # OID jest zapisany w opisie lub w polu description
        desc = inv.get("description", "") or ""
        number = inv.get("number", "") or ""
        if oid in desc or oid in number:
            return inv["id"]
    return None


async def create_fa_invoice(client, contract_data, art_map):
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
    print("RAO-P2-061: Fakturownia invoices seeding")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        art_map = await get_article_fa_product_map(db)
        print(f"\nArtykuły z mapowaniem FA: {len(art_map)}")

        contracts = await get_contracts_with_fa_settlements(db)
        print(f"Umów z rozliczeniami fakturownia (bez faktury): {len(contracts)}")

        if not contracts:
            print("Brak umów do zafakturowania. Done.")
            return

        created = 0
        skipped = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            for cd in contracts:
                print(f"\n[{cd['contract_number']}] {cd['contractor_name']} (NIP {cd['contractor_nip']})")
                print(f"  Rozliczenia: {len(cd['settlements'])}")

                # Sprawdź czy faktura już istnieje
                existing_inv = await check_invoice_exists_by_oid(client, cd["contract_number"])
                if existing_inv:
                    print(f"  EXISTS: Faktura ID={existing_inv} już istnieje — aktualizuję rozliczenia")
                    await update_settlements_with_invoice_id(db, cd["contract_id"], existing_inv)
                    skipped += 1
                    continue

                # Utwórz fakturę
                inv_id = await create_fa_invoice(client, cd, art_map)
                if inv_id:
                    await update_settlements_with_invoice_id(db, cd["contract_id"], inv_id)
                    created += 1
                else:
                    failed += 1

        print(f"\n{'=' * 60}")
        print(f"Podsumowanie: {created} utworzonych, {skipped} istniejących, {failed} błędów")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
