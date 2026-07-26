"""
RAO-P2-061: Wystawia faktury w Fakturownia dla rozliczonych umów z source=fakturownia.

Dla każdej umowy z rozliczeniami source=fakturownia:
1. Pobiera kontrahenta (NIP -> FA client_id)
2. Pobiera pozycje/usługi z mapowaniem machine_id -> FA product_id
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

# Windows: cp1250 crashuje przy polskich znakach — wymuś UTF-8 (jak seed_demo_data.py)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

# Załaduj root .env (FAKTUROWNIA_API_TOKEN) — deterministyczne uruchomienie
_root_env = Path(__file__).parent.parent / ".env"
if _root_env.exists():
    for _line in _root_env.read_text(encoding="utf-8").splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from sqlalchemy import select, text
from database import AsyncSessionLocal

# Import modeli
import auth.models  # noqa
import contractors.models  # noqa
import machines.models  # noqa
import services.models  # noqa
import additional_services.models  # noqa
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
from machines.models import Machine
from settlements.models import ContractSettlement

# FA config — token WYŁĄCZNIE z env (nigdy hardcoded — bezpieczeństwo).
# Akceptuje FA_TOKEN lub FAKTUROWNIA_API_TOKEN (root .env).
FA_TOKEN = os.environ.get("FA_TOKEN") or os.environ.get("FAKTUROWNIA_API_TOKEN")
FA_DOMAIN = os.environ.get("FA_DOMAIN", "matsnd")
FA_BASE = f"https://{FA_DOMAIN}.fakturownia.pl"

# ── Faza 2d (opcja E): demo scenariusz unmapped ──────────────────────────────
# Numer umowy demo (musi zgadzać się z DEMO_UNMAPPED_CONTRACT_NUMBER w seed_demo_data.py).
# Dla tej umowy faktura FA dostaje 3. pozycję "Praca operatora" z product_id NIEZMAPOWANYM
# w RAO (machines.fakturownia_product_id) → init-from-fakturownia tworzy unmapped settlement.
DEMO_UNMAPPED_CONTRACT_NUMBER = "S099/2026"

# ID produktu "Praca operatora" w FA — NIE może być w machines.fakturownia_product_id w RAO.
# Konfigurowalne z env (FA_UNMAPPED_PRODUCT_ID). Jeśli brak — skrypt spróbuje utworzyć
# produkt "Praca operatora" w FA (ensure_unmapped_fa_product) i użyć jego ID.
FA_UNMAPPED_PRODUCT_ID = os.environ.get("FA_UNMAPPED_PRODUCT_ID")
FA_UNMAPPED_PRODUCT_NAME = os.environ.get("FA_UNMAPPED_PRODUCT_NAME", "Praca operatora")
FA_UNMAPPED_PRODUCT_PRICE_NET = float(os.environ.get("FA_UNMAPPED_PRODUCT_PRICE_NET", "650.41"))  # 800/1.23


def _require_token() -> None:
    if not FA_TOKEN:
        print("BŁĄD: brak tokenu Fakturownia. Ustaw FA_TOKEN lub FAKTUROWNIA_API_TOKEN w env/.env")
        sys.exit(1)

# ── Faza A/B: dynamiczne mapowanie NIP → FA client_id i FA product_id ────────
# Stare hardcoded NIP_TO_FA_CLIENT (stare konto FA) zostało zastąpione funkcjami
# ensure_fa_clients / ensure_fa_products, które tworzą klientów i produkty w FA
# na żądanie (obsługa PUSTEGO konta FA — nowe konto ma 0 klientów/produktów/faktur).


async def ensure_fa_clients(client, db):
    """Faza A: synchronizuje kontrahentów RAO → klienci FA po NIP.

    Dla każdego kontrahenta z DB (SELECT id, name, nip FROM contractors WHERE nip IS NOT NULL):
    1. Sprawdź czy klient istnieje w FA po NIP (GET /clients.json?tax_no=<nip>).
    2. Jeśli nie — utwórz (POST /clients.json z {name, tax_no, country}).
    Kraj: "PL" (polskie NIP).

    Zwraca dict NIP → fa_client_id.
    """
    result = await db.execute(
        text("SELECT id, name, nip FROM contractors WHERE nip IS NOT NULL ORDER BY id")
    )
    contractors = result.fetchall()
    print(f"\n[ensure_fa_clients] {len(contractors)} kontrahentów z NIP do synchronizacji z FA")
    nip_to_fa = {}
    created = 0
    for cid, name, nip in contractors:
        if not nip:
            continue
        # Krok 1: sprawdź czy klient istnieje w FA po NIP
        try:
            resp = await client.get(
                f"{FA_BASE}/clients.json",
                params={"api_token": FA_TOKEN, "tax_no": nip},
                timeout=15.0,
            )
            resp.raise_for_status()
            existing = resp.json()
        except Exception as e:
            print(f"  [client] WARN: błąd szukania NIP={nip}: {e} — próbuję utworzyć")
            existing = []

        if isinstance(existing, list) and existing:
            fa_id = int(existing[0]["id"])
            nip_to_fa[nip] = fa_id
            print(f"  [client] EXISTS '{name}' NIP={nip} -> FA ID={fa_id}")
            continue

        # Krok 2: utwórz nowego klienta w FA
        body = {
            "api_token": FA_TOKEN,
            "client": {
                "name": name,
                "tax_no": nip,
                "country": "PL",
            },
        }
        try:
            resp = await client.post(f"{FA_BASE}/clients.json", json=body, timeout=20.0)
            resp.raise_for_status()
            data = resp.json()
            fa_id = int(data["id"])
            nip_to_fa[nip] = fa_id
            created += 1
            print(f"  [client] CREATED '{name}' NIP={nip} -> FA ID={fa_id}")
        except Exception as e:
            err_body = ""
            if hasattr(e, "response") and e.response is not None:
                err_body = e.response.text[:200]
            print(f"  [client] FAIL '{name}' NIP={nip}: {e} | {err_body}")
    print(f"[ensure_fa_clients] gotowe: {len(nip_to_fa)} mapowań, {created} utworzonych")
    return nip_to_fa


async def ensure_fa_products(client, db):
    """Faza B: synchronizuje artykuły RAO → produkty FA (od zera).

    FA wyczyszczone — tworzymy produkty dla WSZYSTKICH maszyn
    i WSZYSTKICH usług dodatkowych (z fakturownia_product_id IS NOT NULL lub NULL).

    Dla każdej maszyny:
    1. Jeśli fakturownia_product_id IS NOT NULL — sprawdź czy produkt istnieje w FA.
       Jeśli tak — zostaw. Jeśli nie — utwórz nowy + zaktualizuj ID.
    2. Jeśli fakturownia_product_id IS NULL — utwórz nowy produkt + zaktualizuj ID.

    Cena: replacement_value / 30 (dzienna stawka bazowa), fallback 100.00.
    Tax: 23. Code: internal_number z artykułu.

    Zwraca dict old_fa_id → new_fa_id.
    """
    # WSZYSTKIE maszyny (nie tylko z fakturownia_product_id IS NOT NULL)
    result = await db.execute(text(
        "SELECT id, name, internal_number, fakturownia_product_id, replacement_value "
        "FROM machines ORDER BY id"
    ))
    machines = result.fetchall()
    print(f"\n[ensure_fa_products] {len(machines)} maszyn do synchronizacji z FA")
    old_to_new = {}
    created = 0
    for mach_id, name, internal_number, old_fa_id, replacement_value in machines:
        # Krok 1: jeśli maszyna ma fakturownia_product_id — sprawdź czy produkt istnieje w FA
        if old_fa_id is not None:
            old_fa_id_int = int(old_fa_id)
            try:
                resp = await client.get(
                    f"{FA_BASE}/products/{old_fa_id_int}.json",
                    params={"api_token": FA_TOKEN},
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    new_fa_id = int(data["id"])
                    old_to_new[old_fa_id_int] = new_fa_id
                    print(f"  [product] EXISTS '{name}' FA ID={old_fa_id_int}")
                    continue
            except Exception:
                pass  # produkt nie istnieje — tworzymy nowy

        # Krok 2: utwórz nowy produkt w FA
        price_net = 100.00
        if replacement_value is not None:
            try:
                rv = float(replacement_value)
                if rv > 0:
                    price_net = round(rv / 30, 2)  # dzienna stawka bazowa
            except (TypeError, ValueError):
                pass

        body = {
            "api_token": FA_TOKEN,
            "product": {
                "name": name,
                "price_net": price_net,
                "tax": 23,
                "code": internal_number or f"RAO-{mach_id}",
            },
        }
        try:
            resp = await client.post(f"{FA_BASE}/products.json", json=body, timeout=20.0)
            resp.raise_for_status()
            data = resp.json()
            new_fa_id = int(data["id"])
            if old_fa_id is not None:
                old_to_new[int(old_fa_id)] = new_fa_id
            # Krok 3: zaktualizuj machines.fakturownia_product_id na nowe ID
            await db.execute(text(
                "UPDATE machines SET fakturownia_product_id = :new_id WHERE id = :mach_id"
            ), {"new_id": new_fa_id, "mach_id": mach_id})
            await db.commit()
            created += 1
            old_id_str = str(int(old_fa_id)) if old_fa_id is not None else "NULL"
            print(f"  [product] CREATED '{name}' old_fa={old_id_str} -> new_fa={new_fa_id} (price_net={price_net})")
        except Exception as e:
            err_body = ""
            if hasattr(e, "response") and e.response is not None:
                err_body = e.response.text[:200]
            old_id_str = str(int(old_fa_id)) if old_fa_id is not None else "NULL"
            print(f"  [product] FAIL '{name}' old_fa={old_id_str}: {e} | {err_body}")
    print(f"[ensure_fa_products] maszyny gotowe: {len(old_to_new)} mapowań, {created} utworzonych")

    # Sync additional_services (usługi dodatkowe) — WSZYSTKIE (nie tylko z ID)
    from additional_services.models import AdditionalService
    result = await db.execute(text(
        "SELECT id, name, fakturownia_product_id, default_amount "
        "FROM additional_services ORDER BY id"
    ))
    addsvcs = result.fetchall()
    print(f"\n[ensure_fa_products] {len(addsvcs)} usług dodatkowych do synchronizacji z FA")
    svc_created = 0
    for svc_id, name, old_fa_id, default_amount in addsvcs:
        # Jeśli ma ID — sprawdź czy produkt istnieje w FA
        if old_fa_id is not None:
            old_fa_id_int = int(old_fa_id)
            try:
                resp = await client.get(
                    f"{FA_BASE}/products/{old_fa_id_int}.json",
                    params={"api_token": FA_TOKEN},
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    new_fa_id = int(data["id"])
                    old_to_new[old_fa_id_int] = new_fa_id
                    print(f"  [product] EXISTS '{name}' FA ID={old_fa_id_int}")
                    continue
            except Exception:
                pass

        price_net = float(default_amount) if default_amount else 100.00
        body = {
            "api_token": FA_TOKEN,
            "product": {
                "name": name,
                "price_net": price_net,
                "tax": 23,
                "code": f"ADDSVC-{svc_id}",
            },
        }
        try:
            resp = await client.post(f"{FA_BASE}/products.json", json=body, timeout=20.0)
            resp.raise_for_status()
            data = resp.json()
            new_fa_id = int(data["id"])
            if old_fa_id is not None:
                old_to_new[int(old_fa_id)] = new_fa_id
            await db.execute(text(
                "UPDATE additional_services SET fakturownia_product_id = :new_id WHERE id = :svc_id"
            ), {"new_id": new_fa_id, "svc_id": svc_id})
            await db.commit()
            svc_created += 1
            old_id_str = str(int(old_fa_id)) if old_fa_id is not None else "NULL"
            print(f"  [product] CREATED '{name}' old_fa={old_id_str} -> new_fa={new_fa_id}")
        except Exception as e:
            err_body = ""
            if hasattr(e, "response") and e.response is not None:
                err_body = e.response.text[:200]
            old_id_str = str(int(old_fa_id)) if old_fa_id is not None else "NULL"
            print(f"  [product] FAIL '{name}' old_fa={old_id_str}: {e} | {err_body}")
    print(f"[ensure_fa_products] usługi dodatkowe gotowe: {svc_created} utworzonych")

    return old_to_new


async def get_machine_fa_product_map(db):
    """Mapowanie machine_id -> FA product_id."""
    result = await db.execute(select(Machine.id, Machine.fakturownia_product_id, Machine.name))
    art_map = {}
    for row in result:
        art_map[row[0]] = {"fa_product_id": row[1], "name": row[2]}
    return art_map


async def get_service_fee_fa_product_map(db):
    """Mapowanie service_fee_id -> FA product_id (via additional_services.fakturownia_product_id)."""
    from contracts.models import ContractServiceFee
    from additional_services.models import AdditionalService
    result = await db.execute(
        select(
            ContractServiceFee.id,
            AdditionalService.fakturownia_product_id,
            ContractServiceFee.name,
        )
        .join(AdditionalService, AdditionalService.id == ContractServiceFee.additional_service_id)
    )
    fee_map = {}
    for row in result:
        fee_map[row[0]] = {"fa_product_id": row[1], "name": row[2]}
    return fee_map


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
               cp.machine_id as pos_machine_id, cp.article_name as pos_article_name,
               csf.name as fee_name
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
            "pos_machine_id": row[11],
            "pos_article_name": row[12],
            "fee_name": row[13],
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
               cp.id as position_id, cp.machine_id, cp.article_name,
               cp.unit_price, cp.rental_days,
               NULL as service_fee_id, NULL as fee_name, NULL as fee_amount
        FROM contracts c
        JOIN contractors ct ON c.contractor_id = ct.id
        JOIN contract_positions cp ON cp.contract_id = c.id
        WHERE c.is_settled = 0
          AND NOT EXISTS (SELECT 1 FROM contract_settlements cs WHERE cs.contract_id = c.id)
        UNION ALL
        SELECT c.id, c.number, c.date_from, c.date_to,
               ct.id, ct.nip, ct.name,
               NULL, NULL, NULL, NULL, NULL,
               csf.id, csf.name, csf.amount_from
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
                "pos_machine_id": row[8],
                "pos_article_name": row[9],
                "fee_name": None,
            })
        elif row[13] is not None:  # usługa dodatkowa
            contracts[cid]["settlements"].append({
                "settlement_id": None,
                "position_id": None,
                "service_fee_id": row[12],
                "cost_client": float(row[14] or 0),
                "pos_machine_id": None,
                "pos_article_name": None,
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
    4. Weryfikacja: product_id NIE może być w machines.fakturownia_product_id w RAO.

    Zwraca FA product_id (int). Rzuca RuntimeError jeśli konflikt mapowania.
    """
    # Krok 1: env override
    if FA_UNMAPPED_PRODUCT_ID:
        pid = int(FA_UNMAPPED_PRODUCT_ID)
        # Weryfikacja: nie może być zmapowany w RAO
        mapped = await db.execute(
            select(Machine.id).where(Machine.fakturownia_product_id == pid).limit(1)
        )
        if mapped.scalar_one_or_none():
            raise RuntimeError(
                f"FA_UNMAPPED_PRODUCT_ID={pid} jest zmapowany w RAO (machines.fakturownia_product_id) "
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
                    select(Machine.id).where(Machine.fakturownia_product_id == pid).limit(1)
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
        "total_price_gross": round(FA_UNMAPPED_PRODUCT_PRICE_NET * 1.23, 2),
        "product_id": unmapped_pid,
    })
    print(f"  [unmapped] Dodano pozycję '{FA_UNMAPPED_PRODUCT_NAME}' (FA product_id={unmapped_pid}, "
          f"~800 zł brutto) — niezmapowaną w RAO")
    return positions


async def create_fa_invoice(client, contract_data, art_map, fee_map=None, db=None, nip_to_fa_client=None):
    """Tworzy fakturę w FA dla jednej umowy."""
    nip = contract_data["contractor_nip"]
    fa_client_id = (nip_to_fa_client or {}).get(nip)
    if not fa_client_id:
        print(f"  SKIP: Brak mapowania FA dla NIP {nip} (uruchom ensure_fa_clients)")
        return None

    # Buduj pozycje faktury
    positions = []
    for s in contract_data["settlements"]:
        # Ustal machine_id i nazwę
        machine_id = s.get("pos_machine_id")
        service_fee_id = s.get("service_fee_id")
        article_name = s["pos_article_name"] or s["fee_name"]
        art_info = art_map.get(machine_id, {})
        fa_product_id = art_info.get("fa_product_id")

        # BUG FIX: dla usług dodatkowych użyj fee_map (service_fee_id → additional_service.fakturownia_product_id)
        # Bez tego FA tworzy nowy produkt z nowym ID → init-from-fakturownia nie mapuje
        if not fa_product_id and service_fee_id and fee_map:
            fee_info = fee_map.get(service_fee_id, {})
            fa_product_id = fee_info.get("fa_product_id")

        price_net = s["cost_client"] / 1.23  # netto z brutto (23% VAT)
        quantity = 1
        pos = {
            "name": article_name,
            "quantity": quantity,
            "price_net": price_net,
            "tax": 23,
            # FA API wymaga total_price_gross per pozycja (422 jeśli puste)
            "total_price_gross": round(price_net * 1.23 * quantity, 2),
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
            # UWAGA: nie używamy client_id na fakturze — FA waliduje checksum NIP (mod 11)
            # pobrany z rekordu klienta, a demo NIP-y (np. 7010001234) nie przechodzą.
            # Zamiast tego przekazujemy buyer_name + buyer_tax_no_kind="other" — FA tworzy
            # fakturę z nabywcą bez NIP (buyer_tax_no=null). Klienci są utworzeni w FA
            # (ensure_fa_clients) dla innych celów, ale faktura ich nie referencjuje.
            "buyer_name": contract_data.get("contractor_name", ""),
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
        art_map = await get_machine_fa_product_map(db)
        print(f"\nMaszyny z mapowaniem FA: {len(art_map)}")

        created = 0
        skipped = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            # ── Faza A: utwórz klientów FA (dynamiczne mapowanie NIP → fa_client_id) ──
            # Obsługa pustego konta FA — stare hardcoded NIP_TO_FA_CLIENT nie istnieją.
            nip_to_fa_client = await ensure_fa_clients(client, db)

            # ── Faza B: utwórz produkty FA + zaktualizuj machines.fakturownia_product_id ──
            # Stare ID produktów nie istnieją na nowym koncie — tworzymy nowe.
            await ensure_fa_products(client, db)
            # Odśwież art_map po aktualizacji machines.fakturownia_product_id
            art_map = await get_machine_fa_product_map(db)
            fee_map = await get_service_fee_fa_product_map(db)
            print(f"\nMaszyny z mapowaniem FA (po sync): {len(art_map)}")
            print(f"Usługi dodatkowe z mapowaniem FA: {len(fee_map)}")

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

                inv_id = await create_fa_invoice(
                    client, cd, art_map, fee_map=fee_map, db=db, nip_to_fa_client=nip_to_fa_client
                )
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

                inv_id = await create_fa_invoice(
                    client, cd, art_map, fee_map=fee_map, db=db, nip_to_fa_client=nip_to_fa_client
                )
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
