"""
RAO-P2-061: Demo data seeding — kompletny skrypt seedujący dane demo.

Idempotentny (re-run bezpieczny): sprawdza istnienie po nazwie/numerze przed INSERT.
Deterministyczny: fixed dane, bez random.

Zasila:
- Kategorie (hierarchiczne)
- Artykuły (5 maszyn + 6 usług, bez duplikatów)
- Kontrahenci (8 firm demo)
- Handlowcy (2)
- Oddziały (1)
- Rate types (3)
- Umowy (24 szt, różne typy/okresy/stany)
- Pozycje umów (z warunkami rozliczeniowymi)
- Usługi dodatkowe (z article_id)
- Rozliczenia (80% source=fakturownia, 20% source=manual/estimate)
- Mapowanie Article.fakturownia_product_id ↔ produkty FA

Użycie:
    cd backend && python seed_demo_data.py

Wymaga:
    - Backend NIE musi działać (skrypt łączy się bezpośrednio z DB)
    - .env z RAO_FAKTUROWNIA_ENC_KEY i DB credentials
"""
import asyncio
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Dodaj backend do path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, AsyncSessionLocal
from categories.models import Category
from articles.models import Article
from contractors.models import Contractor, ContractorAddress
from settings.models import Salesperson, Branch, RateType
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from settlements.models import ContractSettlement

# Import wszystkich modeli żeby SQLAlchemy skonfigurowało relacje
import auth.models  # noqa: F401
import contractors.models  # noqa: F401
import articles.models  # noqa: F401
import contracts.models  # noqa: F401
import settings.models  # noqa: F401
import categories.models  # noqa: F401
import settlements.models  # noqa: F401
import archive.models  # noqa: F401
import audit.models  # noqa: F401
import contract_costs.models  # noqa: F401
import deliveries.models  # noqa: F401
import reservations.models  # noqa: F401
import integrations.fakturownia.models  # noqa: F401
import integrations.models  # noqa: F401 — PostalCode potrzebny dla Contract.postal_code_ref

# ── Dane demo (deterministyczne) ──────────────────────────────────────────────

KATEGORIE = [
    # Maszyny
    {"name": "Koparki", "code": "KOP", "level": "main"},
    {"name": "Koparki gąsienicowe", "code": "KOP-GAS", "level": "sub1", "parent_name": "Koparki"},
    {"name": "Ładowarki Teleskopowe", "code": "LAD-TEL", "level": "main"},
    {"name": "Ładowarki Teleskopowe Sztywne", "code": "LAD-TEL-SZW", "level": "sub1", "parent_name": "Ładowarki Teleskopowe"},
    {"name": "Podnośniki", "code": "POD", "level": "main"},
    {"name": "Podnośnik koszowy na samochodzie", "code": "POD-KOSZ", "level": "sub1", "parent_name": "Podnośniki"},
    {"name": "Spychacze", "code": "SPY", "level": "main"},
    {"name": "Spychacze frezujące", "code": "SPY-FREZ", "level": "sub1", "parent_name": "Spychacze"},
    {"name": "Zagęszczarki", "code": "ZAG", "level": "main"},
    {"name": "Zagęszczarki płytowe", "code": "ZAG-PLT", "level": "sub1", "parent_name": "Zagęszczarki"},
    # Usługi
    {"name": "Usługi dodatkowe", "code": "USL", "level": "main"},
    {"name": "Transport", "code": "USL-TRA", "level": "sub1", "parent_name": "Usługi dodatkowe"},
    {"name": "Czyszczenie", "code": "USL-CZY", "level": "sub1", "parent_name": "Usługi dodatkowe"},
    {"name": "Tankowanie", "code": "USL-TAN", "level": "sub1", "parent_name": "Usługi dodatkowe"},
    {"name": "Przestój", "code": "USL-PZT", "level": "sub1", "parent_name": "Usługi dodatkowe"},
    {"name": "Serwis", "code": "USL-SER", "level": "sub1", "parent_name": "Usługi dodatkowe"},
]

MASZYNY = [
    {
        "name": "Koparka gąsienicowa JCB 8035",
        "is_service": False, "internal_number": "KOP-001",
        "registration_no": "RAO 12345", "serial_no": "JCB8035Z2021001",
        "brand": "JCB", "model": "8035 ZTS", "replacement_value": Decimal("280000.00"),
        "category_main": "Koparki", "category_sub1": "Koparki gąsienicowe",
        "article_type": "artykuł", "udzwig_t": Decimal("3.5"),
        "dodatki": "Łyżka standardowa, szybkozłącze hydrauliczne",
        "fakturownia_product_id": 8845156432567,  # KOP001
    },
    {
        "name": "Ładowarka teleskopowa Manuscop 6.36",
        "is_service": False, "internal_number": "LAD-002",
        "registration_no": "RAO 23456", "serial_no": "MAN6362022001",
        "brand": "Manitou", "model": "Manuscop 6.36", "replacement_value": Decimal("420000.00"),
        "category_main": "Ładowarki Teleskopowe", "category_sub1": "Ładowarki Teleskopowe Sztywne",
        "article_type": "artykuł", "zasieg_m": Decimal("6.0"), "udzwig_t": Decimal("3.6"),
        "dodatki": "Widły paletowe, łyżka objętościowa 1.2m³",
        "fakturownia_product_id": 8845156436442,  # LAD001
    },
    {
        "name": "Podnośnik koszowy Haulotte HA16PX",
        "is_service": False, "internal_number": "POD-003",
        "registration_no": "RAO 34567", "serial_no": "HAU16PX2021001",
        "brand": "Haulotte", "model": "HA16 PX", "replacement_value": Decimal("380000.00"),
        "category_main": "Podnośniki", "category_sub1": "Podnośnik koszowy na samochodzie",
        "article_type": "artykuł", "zasieg_m": Decimal("16.0"),
        "dodatki": "Kosz 230kg, wysięgnik obrotowy 360°",
        "fakturownia_product_id": 8845156436443,  # POD001
    },
    {
        "name": "Spychar Wirtgen W100CFi",
        "is_service": False, "internal_number": "SPY-004",
        "registration_no": "RAO 45678", "serial_no": "WIR100CFI2022001",
        "brand": "Wirtgen", "model": "W 100 CFi", "replacement_value": Decimal("1200000.00"),
        "category_main": "Spychacze", "category_sub1": "Spychacze frezujące",
        "article_type": "artykuł",
        "dodatki": "Frez 1.0m, system chłodzenia wodnego",
        "fakturownia_product_id": 8845156436444,  # SPY001
    },
    {
        "name": "Zagęszczarka Ammann APF 15/50",
        "is_service": False, "internal_number": "ZAG-005",
        "registration_no": "RAO 56789", "serial_no": "AMM15502023001",
        "brand": "Ammann", "model": "APF 15/50", "replacement_value": Decimal("35000.00"),
        "category_main": "Zagęszczarki", "category_sub1": "Zagęszczarki płytowe",
        "article_type": "artykuł",
        "dodatki": "Ruch w przód i tył, nóż dociskowy",
        "fakturownia_product_id": 8845156436446,  # ZAG001
    },
]

USLUGI = [
    {
        "name": "Transport maszyny", "is_service": True, "internal_number": "USL-001",
        "replacement_value": Decimal("350.00"),
        "category_main": "Usługi dodatkowe", "category_sub1": "Transport",
        "article_type": "usluga_dodatkowa",
        "fakturownia_product_id": 8845156432587,  # TRA001
    },
    {
        "name": "Czyszczenie maszyny — drobne", "is_service": True, "internal_number": "USL-002",
        "replacement_value": Decimal("80.00"),
        "category_main": "Usługi dodatkowe", "category_sub1": "Czyszczenie",
        "article_type": "usluga_dodatkowa",
        "fakturownia_product_id": 8845156432589,  # CZY001
    },
    {
        "name": "Czyszczenie maszyny — trudne zabrudzenia", "is_service": True, "internal_number": "USL-003",
        "replacement_value": Decimal("200.00"),
        "category_main": "Usługi dodatkowe", "category_sub1": "Czyszczenie",
        "article_type": "usluga_dodatkowa",
        "fakturownia_product_id": 8845156436448,  # CZY002
    },
    {
        "name": "Tankowanie paliwa", "is_service": True, "internal_number": "USL-004",
        "replacement_value": Decimal("250.00"),
        "category_main": "Usługi dodatkowe", "category_sub1": "Tankowanie",
        "article_type": "usluga_dodatkowa",
        "fakturownia_product_id": 8845156432620,  # TAN001
    },
    {
        "name": "Przestój maszyny", "is_service": True, "internal_number": "USL-005",
        "replacement_value": Decimal("100.00"),
        "category_main": "Usługi dodatkowe", "category_sub1": "Przestój",
        "article_type": "usluga_dodatkowa",
        "fakturownia_product_id": 8845156436449,  # PZT001
    },
    {
        "name": "Serwis maszyny", "is_service": True, "internal_number": "USL-006",
        "replacement_value": Decimal("300.00"),
        "category_main": "Usługi dodatkowe", "category_sub1": "Serwis",
        "article_type": "usluga_dodatkowa",
        "fakturownia_product_id": 8845156436450,  # SER001
    },
]

KONTRAHENCI = [
    {"name": "Bud-Plus Sp. z o.o.", "nip": "7010001234", "city": "Warszawa", "street": "ul. Budowlana 12", "postal_code": "02-100", "phone1": "22 123 45 67", "email": "biuro@budplus.pl"},
    {"name": "Invest S.A.", "nip": "5260005678", "city": "Kraków", "street": "ul. Inwestycyjna 5", "postal_code": "30-001", "phone1": "12 345 67 89", "email": "kontakt@invest.pl"},
    {"name": "Terra-Masz Budownictwo", "nip": "7790009012", "city": "Poznań", "street": "ul. Przemysłowa 22", "postal_code": "61-001", "phone1": "61 234 56 78", "email": "biuro@terra-masz.pl"},
    {"name": "Wod-Bud Sp. z o.o.", "nip": "9510003456", "city": "Wrocław", "street": "ul. Wodna 8", "postal_code": "50-001", "phone1": "71 345 67 89", "email": "kontakt@wodbud.pl"},
    {"name": "Fundament Sp. z o.o.", "nip": "1460007890", "city": "Łódź", "street": "ul. Solidna 3", "postal_code": "93-001", "phone1": "42 456 78 90", "email": "biuro@fundament.pl"},
    {"name": "Trakcja-Polska S.A.", "nip": "6790002345", "city": "Gdynia", "street": "ul. Kolejowa 15", "postal_code": "81-001", "phone1": "58 567 89 01", "email": "kontakt@trakcja.pl"},
    {"name": "Eko-Bud Nowoczesne Budownictwo", "nip": "2580006789", "city": "Katowice", "street": "ul. Zielona 7", "postal_code": "40-001", "phone1": "32 678 90 12", "email": "biuro@ekobud.pl"},
    {"name": "Miejskie Inwestycje Sp. z o.o.", "nip": "8350001230", "city": "Bydgoszcz", "street": "ul. Miejska 1", "postal_code": "85-001", "phone1": "52 789 01 23", "email": "kontakt@mi.pl"},
]

HANDLOWCY = [
    {"name": "Mateusz Wiatrak", "phone": "+48 500 123 456", "commission_rate": Decimal("5.00")},
    {"name": "Anna Kowalska", "phone": "+48 600 654 321", "commission_rate": Decimal("3.50")},
]

ODDZIALY = [
    {"name": "RAO Warszawa (HQ)", "city": "Warszawa", "street": "ul. Przykładowa 1", "postal_code": "00-001"},
]

RATE_TYPES = [
    {"name": "Stawka dniowa", "description": "Rozliczenie za dzień roboczy"},
    {"name": "Stawka godzinowa", "description": "Rozliczenie za godzinę pracy"},
    {"name": "Stawka km", "description": "Rozliczenie za kilometr"},
]

# Cena wynajmu/doba per maszyna (do warunków rozliczeniowych)
CENY_WYNAJMU = {
    "Koparka gąsienicowa JCB 8035": Decimal("800.00"),
    "Ładowarka teleskopowa Manuscop 6.36": Decimal("650.00"),
    "Podnośnik koszowy Haulotte HA16PX": Decimal("450.00"),
    "Spychar Wirtgen W100CFi": Decimal("1200.00"),
    "Zagęszczarka Ammann APF 15/50": Decimal("150.00"),
}


async def get_or_create(db: AsyncSession, model, filter_dict, create_dict=None):
    """Idempotent get-or-create."""
    stmt = select(model)
    for k, v in filter_dict.items():
        stmt = stmt.where(getattr(model, k) == v)
    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj, False
    data = {**(create_dict or filter_dict)}
    obj = model(**data)
    db.add(obj)
    await db.flush()
    return obj, True


async def seed_kategorie(db: AsyncSession):
    """Kategorie hierarchiczne."""
    created = 0
    name_to_id = {}
    # Najpierw main
    for k in KATEGORIE:
        if k["level"] == "main":
            obj, was_created = await get_or_create(db, Category, {"name": k["name"]}, {
                "name": k["name"], "code": k["code"], "level": "main",
            })
            name_to_id[k["name"]] = obj.id
            if was_created:
                created += 1
    # Potem sub1 (z parent_id)
    for k in KATEGORIE:
        if k["level"] == "sub1":
            parent_id = name_to_id.get(k["parent_name"])
            obj, was_created = await get_or_create(db, Category, {"name": k["name"]}, {
                "name": k["name"], "code": k["code"], "level": "sub1", "parent_id": parent_id,
            })
            name_to_id[k["name"]] = obj.id
            if was_created:
                created += 1
    await db.commit()
    print(f"  Kategorie: {created} nowych, {len(KATEGORIE)} total")
    return name_to_id


async def seed_artykuly(db: AsyncSession):
    """Artykuły (maszyny + usługi) z mapowaniem FA."""
    created = 0
    art_by_name = {}
    all_articles = MASZYNY + USLUGI
    for a in all_articles:
        a_with_ts = {**a, "created_at": datetime.now(), "updated_at": datetime.now()}
        obj, was_created = await get_or_create(db, Article, {"name": a["name"]}, a_with_ts)
        art_by_name[a["name"]] = obj
        if was_created:
            created += 1
    await db.commit()
    maszyny_count = sum(1 for a in all_articles if not a["is_service"])
    uslugi_count = sum(1 for a in all_articles if a["is_service"])
    print(f"  Artykuły: {created} nowych ({maszyny_count} maszyn + {uslugi_count} usług)")
    return art_by_name


async def seed_kontrahenci(db: AsyncSession):
    """Kontrahenci demo."""
    created = 0
    con_by_name = {}
    for c in KONTRAHENCI:
        obj, was_created = await get_or_create(db, Contractor, {"name": c["name"]}, {
            **c, "is_supplier": False, "created_at": datetime.now(),
        })
        con_by_name[c["name"]] = obj
        if was_created:
            created += 1
    await db.commit()
    print(f"  Kontrahenci: {created} nowych, {len(KONTRAHENCI)} total")
    return con_by_name


async def seed_handlowcy(db: AsyncSession):
    created = 0
    sp_by_name = {}
    for s in HANDLOWCY:
        obj, was_created = await get_or_create(db, Salesperson, {"name": s["name"]}, s)
        sp_by_name[s["name"]] = obj
        if was_created:
            created += 1
    await db.commit()
    print(f"  Handlowcy: {created} nowych")
    return sp_by_name


async def seed_oddzialy(db: AsyncSession):
    created = 0
    br_by_name = {}
    for b in ODDZIALY:
        obj, was_created = await get_or_create(db, Branch, {"name": b["name"]}, b)
        br_by_name[b["name"]] = obj
        if was_created:
            created += 1
    await db.commit()
    print(f"  Oddziały: {created} nowych")
    return br_by_name


async def seed_rate_types(db: AsyncSession):
    created = 0
    rt_by_name = {}
    for r in RATE_TYPES:
        obj, was_created = await get_or_create(db, RateType, {"name": r["name"]}, r)
        rt_by_name[r["name"]] = obj
        if was_created:
            created += 1
    await db.commit()
    print(f"  Rate types: {created} nowych")
    return rt_by_name


# ── Umowy demo ────────────────────────────────────────────────────────────────

def generate_contracts(con_by_name, sp_by_name, br_by_name, art_by_name, rt_by_name):
    """Generuje 24 umowy demo z różnymi typami/okresami/stanami."""
    contractors = list(con_by_name.values())
    salespeople = list(sp_by_name.values())
    branches = list(br_by_name.values())
    maszyny = [art_by_name[m["name"]] for m in MASZYNY]
    uslugi = [art_by_name[u["name"]] for u in USLUGI]
    rt_dniowy = rt_by_name.get("Stawka dniowa")
    rt_km = rt_by_name.get("Stawka km")

    contracts = []
    today = date.today()

    # 24 umów: różne okresy (ostatnie 12 miesięcy), różne stany
    for i in range(24):
        contractor = contractors[i % len(contractors)]
        salesperson = salespeople[i % len(salespeople)]
        branch = branches[0]
        contract_type = "S" if i % 3 != 2 else "U"  # 2/3 typ S, 1/3 typ U
        is_legacy = i >= 21  # ostatnie 3 umowy = legacy (oznaczone w rozliczeniach source=legacy)

        # Okres: cofaj się w czasie
        months_back = i // 2  # 0,0,1,1,2,2,...,11,11
        date_from = today - timedelta(days=months_back * 30 + (i % 2) * 15)
        days = 7 + (i % 4) * 7  # 7, 14, 21, 28 dni
        date_to = date_from + timedelta(days=days)

        # Stan: aktywne (data_do >= today), zakończone, przeterminowane
        is_active = date_to >= today
        is_settled = (not is_active) and (i % 5 != 4)  # 80% zakończonych rozliczone

        number = f"{'S' if contract_type == 'S' else 'U'}{i+1:03d}/2026"

        # Pozycje: 1-2 maszyny per umowa
        positions = []
        num_positions = 1 if i % 3 != 0 else 2
        for j in range(num_positions):
            maszyna = maszyny[(i + j) % len(maszyny)]
            cena = CENY_WYNAJMU[maszyna.name]
            positions.append({
                "article_id": maszyna.id,
                "article_name": maszyna.name,
                "rental_days": days,
                "quantity": 1,
                "unit_price": cena,
                "rate_type_id": rt_dniowy.id if rt_dniowy else None,
                "billing_frequency": "dniowa",
                "billing_unit": "doba",
                "conditions": [
                    {"rate1": cena, "rate2": None, "period_count": days, "minimum": 1, "billing_label": "doba", "description": f"Wynajem {maszyna.name}", "rate_type_id": rt_dniowy.id if rt_dniowy else None},
                ],
            })

        # Usługi dodatkowe: 2-4 per umowa
        fees = []
        num_fees = 2 + (i % 3)  # 2, 3, 4
        for j in range(num_fees):
            usluga = uslugi[(i + j) % len(uslugi)]
            cena_usl = usluga.replacement_value or Decimal("100")
            fees.append({
                "name": usluga.name,
                "article_id": usluga.id,
                "default_price": cena_usl,
                "amount_from": cena_usl,
                "amount_to": None,
                "unit": "szt" if "Transport" in usluga.name else "kpl",
                "description": f"{usluga.name} — usługa dodatkowa",
                "is_active": True,
            })

        contracts.append({
            "number": number,
            "contractor_id": contractor.id,
            "branch_id": branch.id,
            "salesperson_id": salesperson.id,
            "contract_type": contract_type,
            "date_from": date_from,
            "date_to": date_to,
            "is_legacy": is_legacy,
            "is_settled": is_settled,
            "settled_at": datetime.combine(date_to, datetime.min.time()) if is_settled else None,
            "positions": positions,
            "fees": fees,
            "is_active_contract": is_active,
        })

    return contracts


async def seed_umowy(db: AsyncSession, contracts_data, art_by_name):
    """Tworzy umowy + pozycje + warunki + usługi dodatkowe + rozliczenia."""
    created_contracts = 0
    created_positions = 0
    created_conditions = 0
    created_fees = 0
    created_settlements = 0

    for cd in contracts_data:
        # Sprawdź czy umowa istnieje po numerze
        existing = await db.execute(select(Contract).where(Contract.number == cd["number"]))
        contract = existing.scalar_one_or_none()
        if contract:
            continue  # idempotent — skip

        contract = Contract(
            number=cd["number"],
            contractor_id=cd["contractor_id"],
            branch_id=cd["branch_id"],
            salesperson_id=cd["salesperson_id"],
            contract_type=cd["contract_type"],
            date_from=cd["date_from"],
            date_to=cd["date_to"],
            is_settled=cd["is_settled"],
            settled_at=cd["settled_at"],
            auto_number=int(cd["number"].split("/")[0].split("S")[-1].split("U")[-1]),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(contract)
        await db.flush()
        created_contracts += 1

        # Pozycje
        for pos_data in cd["positions"]:
            pos = ContractPosition(
                contract_id=contract.id,
                article_id=pos_data["article_id"],
                article_name=pos_data["article_name"],
                rental_days=pos_data["rental_days"],
                quantity=pos_data["quantity"],
                unit_price=pos_data["unit_price"],
                rate_type_id=pos_data["rate_type_id"],
                billing_frequency=pos_data["billing_frequency"],
                billing_unit=pos_data["billing_unit"],
            )
            db.add(pos)
            await db.flush()
            created_positions += 1

            # Warunki
            for cond_data in pos_data["conditions"]:
                cond = PositionCondition(
                    position_id=pos.id,
                    rate_type_id=cond_data["rate_type_id"],
                    description=cond_data["description"],
                    rate1=cond_data["rate1"],
                    rate2=cond_data["rate2"],
                    period_count=cond_data["period_count"],
                    minimum=cond_data["minimum"],
                    billing_label=cond_data["billing_label"],
                )
                db.add(cond)
                created_conditions += 1

            # Rozliczenie dla pozycji (80% source=fakturownia, 20% estimate/manual)
            is_settled = cd["is_settled"]
            if is_settled and not cd["is_legacy"]:
                # 80% faktura, 20% manual
                source = "fakturownia" if (created_contracts % 5 != 4) else "manual"
                cost_client = pos_data["unit_price"] * pos_data["rental_days"]
                cost_company = cost_client * Decimal("0.6")  # 60% koszt własny
                settlement = ContractSettlement(
                    contract_id=contract.id,
                    position_id=pos.id,
                    cost_client=cost_client,
                    cost_company=cost_company,
                    source=source,
                    settled_at=cd["date_to"],
                    notes=f"Rozliczenie {source} — {cd['number']}",
                )
                db.add(settlement)
                created_settlements += 1
            elif cd["is_legacy"] and is_settled:
                # Legacy — source=legacy (szacunek)
                cost_client = pos_data["unit_price"] * pos_data["rental_days"]
                settlement = ContractSettlement(
                    contract_id=contract.id,
                    position_id=pos.id,
                    cost_client=cost_client,
                    cost_company=cost_client * Decimal("0.5"),
                    source="legacy",
                    settled_at=cd["date_to"],
                    notes=f"Rozliczenie legacy — {cd['number']}",
                )
                db.add(settlement)
                created_settlements += 1

        # Usługi dodatkowe
        for fee_data in cd["fees"]:
            # sort_order = kolejny
            max_order = await db.execute(
                select(func.max(ContractServiceFee.sort_order))
                .where(ContractServiceFee.contract_id == contract.id)
            )
            next_order = (max_order.scalar_one_or_none() or 0) + 1
            fee = ContractServiceFee(
                contract_id=contract.id,
                sort_order=next_order,
                name=fee_data["name"],
                article_id=fee_data["article_id"],
                default_price=fee_data["default_price"],
                amount_from=fee_data["amount_from"],
                amount_to=fee_data["amount_to"],
                unit=fee_data["unit"],
                description=fee_data["description"],
                is_active=fee_data["is_active"],
            )
            db.add(fee)
            await db.flush()
            created_fees += 1

            # Rozliczenie usługi (jeśli umowa rozliczona)
            if is_settled and not cd["is_legacy"]:
                source = "fakturownia" if (created_contracts % 5 != 4) else "manual"
                cost_client = fee_data["amount_from"] or Decimal("0")
                settlement = ContractSettlement(
                    contract_id=contract.id,
                    service_fee_id=fee.id,
                    cost_client=cost_client,
                    cost_company=cost_client * Decimal("0.7"),
                    source=source,
                    settled_at=cd["date_to"],
                    notes=f"Rozliczenie usługi {source} — {fee_data['name']}",
                )
                db.add(settlement)
                created_settlements += 1

    await db.commit()
    print(f"  Umowy: {created_contracts} nowych")
    print(f"  Pozycje: {created_positions} nowych")
    print(f"  Warunki: {created_conditions} nowych")
    print(f"  Usługi dodatkowe: {created_fees} nowych")
    print(f"  Rozliczenia: {created_settlements} nowych")
    return created_contracts


async def main():
    print("=" * 60)
    print("RAO-P2-061: Demo data seeding")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        print("\n[1/7] Kategorie...")
        await seed_kategorie(db)

        print("\n[2/7] Artykuły (maszyny + usługi)...")
        art_by_name = await seed_artykuly(db)

        print("\n[3/7] Kontrahenci...")
        con_by_name = await seed_kontrahenci(db)

        print("\n[4/7] Handlowcy...")
        sp_by_name = await seed_handlowcy(db)

        print("\n[5/7] Oddziały...")
        br_by_name = await seed_oddzialy(db)

        print("\n[6/7] Rate types...")
        rt_by_name = await seed_rate_types(db)

        print("\n[7/7] Umowy + pozycje + warunki + usługi + rozliczenia...")
        contracts_data = generate_contracts(con_by_name, sp_by_name, br_by_name, art_by_name, rt_by_name)
        await seed_umowy(db, contracts_data, art_by_name)

    print("\n" + "=" * 60)
    print("DONE — demo data seeded")
    print("=" * 60)
    print("\nNastępny krok: wystaw faktury FA dla rozliczonych umów")
    print("(uruchom: python seed_fa_invoices.py)")


if __name__ == "__main__":
    asyncio.run(main())
