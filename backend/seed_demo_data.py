"""
RAO-P2-061/068: Demo data seeding — kompletny skrypt seedujący dane demo.

Idempotentny (re-run bezpieczny): sprawdza istnienie po nazwie/numerze przed INSERT.
Deterministyczny: fixed dane, bez random.

Zasila:
- Kategorie (hierarchiczne)
- Artykuły (5 maszyn + 6 usług, bez duplikatów)
- Kontrahenci (8 firm demo)
- Handlowcy (2)
- Oddziały (1)
- Rate types (6 typów — dniowa, godzinowa, km, tygodniowa, miesięczna, jednorazowa)
- Konfiguracja firmy (NIP, adres, konto bankowe, header_text do PDF)
- Zestawy usług dodatkowych (6 presetów: najem, usługa z operatorem,
  kontrakt długoterminowy, weekend, kontrakt zagraniczny, operator premium)
  + ServiceFeeTemplateItem (relacja N:M preset → artykuł z domyślną ceną)
- Umowy (56 szt: 24 historia 2025 + 24 bieżące 2026 + 8 FA-pending)
  z predefiniowanymi cennikami kaskadowymi per maszyna (1-3 dni, 4-16 dni,
  powyżej 16 dni) — jak w starej aplikacji WinForms
- Pozycje umów (z warunkami rozliczeniowymi kaskadowymi)
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
    {"name": "RAO Gdańsk", "city": "Gdańsk", "street": "ul. Portowa 5", "postal_code": "80-001"},
]

RATE_TYPES = [
    {"name": "Stawka dniowa", "description": "Rozliczenie za dzień roboczy (doba)"},
    {"name": "Stawka godzinowa", "description": "Rozliczenie za godzinę pracy"},
    {"name": "Stawka km", "description": "Rozliczenie za kilometr przebiegu"},
    {"name": "Stawka tygodniowa", "description": "Rozliczenie za tydzień (7 dni) — dla umów średnioterminowych"},
    {"name": "Stawka miesięczna", "description": "Rozliczenie za miesiąc (30 dni) — dla kontraktów długoterminowych"},
    {"name": "Stawka jednorazowa", "description": "Płatność jednorazowa (transport, czyszczenie, serwis)"},
]

# Cena wynajmu/doba per maszyna (do warunków rozliczeniowych)
CENY_WYNAJMU = {
    "Koparka gąsienicowa JCB 8035": Decimal("800.00"),
    "Ładowarka teleskopowa Manuscop 6.36": Decimal("650.00"),
    "Podnośnik koszowy Haulotte HA16PX": Decimal("450.00"),
    "Spychar Wirtgen W100CFi": Decimal("1200.00"),
    "Zagęszczarka Ammann APF 15/50": Decimal("150.00"),
}

# ── Cenniki kaskadowe per maszyna (RAO-P2-068) ────────────────────────────────
# Predefiniowane warunki rozliczeń jak w starej aplikacji WinForms — user klika
# maszynę i ma gotowy cennik kaskadowy (1-3 dni wyższa stawka, 4-16 dni niższa,
# powyżej 16 dni najniższa). Nie musi ręcznie wpisywać każdego warunku.
#
# Format: 3 warunki kaskadowe per maszyna:
#   Warunek 1: rate1 = stawka "krótkoterminowa", period_count = 3 (1-3 dni)
#   Warunek 2: rate1 = stawka "średnioterminowa", period_count = 16 (4-16 dni)
#   Warunek 3: rate2 = stawka "długoterminowa" (powyżej 16 dni, bez period_count)
#
# Stawki pochodzą z produkcyjnego cennika Toolsmart 2026 (realistyczne rynkowo).
# Koparka/ładowarka/spychacz = maszyny premium (wyższe stawki).
# Podnośnik = maszyna średnia. Zagęszczarka = maszyna budżetowa.

CENNIKI_KASKADOWE = {
    "Koparka gąsienicowa JCB 8035": {
        # 1-3 dni: 900 zł/doba (krótkoterminowa premium)
        # 4-16 dni: 750 zł/doba (średnioterminowa)
        # powyżej 16 dni: 600 zł/doba (długoterminowa kontraktowa)
        "warunki": [
            {"rate1": Decimal("900.00"), "rate2": None, "period_count": 3,  "minimum": 1, "billing_label": "doba", "description": "1 - 3 dni - 900,00 / doba"},
            {"rate1": Decimal("750.00"), "rate2": None, "period_count": 16, "minimum": 1, "billing_label": "doba", "description": "4 - 16 dni - 750,00 / doba"},
            {"rate1": None, "rate2": Decimal("600.00"), "period_count": None, "minimum": 1, "billing_label": "doba", "description": "powyżej 16 dni - 600,00 / doba"},
        ],
    },
    "Ładowarka teleskopowa Manuscop 6.36": {
        # 1-3 dni: 720 zł/doba, 4-16 dni: 600 zł/doba, powyżej 16 dni: 480 zł/doba
        "warunki": [
            {"rate1": Decimal("720.00"), "rate2": None, "period_count": 3,  "minimum": 1, "billing_label": "doba", "description": "1 - 3 dni - 720,00 / doba"},
            {"rate1": Decimal("600.00"), "rate2": None, "period_count": 16, "minimum": 1, "billing_label": "doba", "description": "4 - 16 dni - 600,00 / doba"},
            {"rate1": None, "rate2": Decimal("480.00"), "period_count": None, "minimum": 1, "billing_label": "doba", "description": "powyżej 16 dni - 480,00 / doba"},
        ],
    },
    "Podnośnik koszowy Haulotte HA16PX": {
        # 1-3 dni: 500 zł/doba, 4-16 dni: 420 zł/doba, powyżej 16 dni: 340 zł/doba
        "warunki": [
            {"rate1": Decimal("500.00"), "rate2": None, "period_count": 3,  "minimum": 1, "billing_label": "doba", "description": "1 - 3 dni - 500,00 / doba"},
            {"rate1": Decimal("420.00"), "rate2": None, "period_count": 16, "minimum": 1, "billing_label": "doba", "description": "4 - 16 dni - 420,00 / doba"},
            {"rate1": None, "rate2": Decimal("340.00"), "period_count": None, "minimum": 1, "billing_label": "doba", "description": "powyżej 16 dni - 340,00 / doba"},
        ],
    },
    "Spychar Wirtgen W100CFi": {
        # 1-3 dni: 1300 zł/doba (premium frezowanie), 4-16 dni: 1100 zł/doba, powyżej 16 dni: 900 zł/doba
        "warunki": [
            {"rate1": Decimal("1300.00"), "rate2": None, "period_count": 3,  "minimum": 1, "billing_label": "doba", "description": "1 - 3 dni - 1300,00 / doba"},
            {"rate1": Decimal("1100.00"), "rate2": None, "period_count": 16, "minimum": 1, "billing_label": "doba", "description": "4 - 16 dni - 1100,00 / doba"},
            {"rate1": None, "rate2": Decimal("900.00"),  "period_count": None, "minimum": 1, "billing_label": "doba", "description": "powyżej 16 dni - 900,00 / doba"},
        ],
    },
    "Zagęszczarka Ammann APF 15/50": {
        # 1-3 dni: 180 zł/doba (budżetowa), 4-16 dni: 150 zł/doba, powyżej 16 dni: 120 zł/doba
        "warunki": [
            {"rate1": Decimal("180.00"), "rate2": None, "period_count": 3,  "minimum": 1, "billing_label": "doba", "description": "1 - 3 dni - 180,00 / doba"},
            {"rate1": Decimal("150.00"), "rate2": None, "period_count": 16, "minimum": 1, "billing_label": "doba", "description": "4 - 16 dni - 150,00 / doba"},
            {"rate1": None, "rate2": Decimal("120.00"), "period_count": None, "minimum": 1, "billing_label": "doba", "description": "powyżej 16 dni - 120,00 / doba"},
        ],
    },
}

# Stawka "skuteczna" per maszyna — używana do rozliczeń (średnia z cennika
# kaskadowego dla typowego wynajmu 7-14 dni = stawka średnioterminowa).
STAWKA_EFEKTYWNA = {
    name: data["warunki"][1]["rate1"]  # stawka 4-16 dni (typowy wynajem)
    for name, data in CENNIKI_KASKADOWE.items()
}

# ── Konfiguracja firmy (RAO-P2-068) ───────────────────────────────────────────
# Pełne dane firmy jak gdyby klient sam ustawił w Ustawieniach — NIP, adres,
# konto bankowe, header_text do PDF, numeracja umów. main.py tworzy tylko
# pusty Company(id=1, name="RAO — Wynajem Maszyn") — seed wzbogaca o pełne dane.

FIRMA_CONFIG = {
    "name": "RAO Sp. z o.o.",
    "name_short": "RAO",
    "nip": "1234563218",
    "regon": "012345678",
    "postal_code": "00-001",
    "city": "Warszawa",
    "street": "ul. Przykładowa 1",
    "header_text": "RAO Sp. z o.o.\nul. Przykładowa 1\n00-001 Warszawa\nNIP: 123-45-63-218\nKonto: PL 12 1020 1026 0000 1234 5678 9012",
    "bank_name": "PKO BP",
    "bank_account": "PL 12 1020 1026 0000 1234 5678 9012",
    "numbering_start": 1,
    "increment_step": Decimal("50.00"),
    "report_folder": "C:\\RAO\\Raporty",
    "protocol_folder": "C:\\RAO\\Protokoly",
    "app_version": "2.0.0",
}

# ── Lokalizacje budów (RAO-P2-067) ────────────────────────────────────────────
# PNA ZWERYFIKOWANE w tabeli postal_codes (city = prawdziwa nazwa miasta,
# nie placówka FUP/UP) — dzięki temu zakładka Lokalizacje pokazuje ranking miast
# z rollup gmina/powiat/województwo.
LOKALIZACJE_BUDOWY = [
    {"city": "Warszawa",  "postal_code": "00-002", "street": "ul. Świętokrzyska 14"},
    {"city": "Kraków",    "postal_code": "30-001", "street": "ul. Wielicka 28"},
    {"city": "Poznań",    "postal_code": "60-001", "street": "ul. Głogowska 108"},
    {"city": "Wrocław",   "postal_code": "50-001", "street": "ul. Legnicka 55"},
    {"city": "Łódź",      "postal_code": "90-002", "street": "ul. Piotrkowska 200"},
    {"city": "Gdynia",    "postal_code": "81-001", "street": "ul. Morska 81"},
    {"city": "Gdańsk",    "postal_code": "80-001", "street": "ul. Grunwaldzka 301"},
    {"city": "Katowice",  "postal_code": "40-002", "street": "ul. Chorzowska 12"},
    {"city": "Bydgoszcz", "postal_code": "85-004", "street": "ul. Fordońska 44"},
    {"city": "Lublin",    "postal_code": "20-002", "street": "ul. Kraśnicka 31"},
    {"city": "Szczecin",  "postal_code": "70-001", "street": "ul. Gdańska 15"},
    {"city": "Radom",     "postal_code": "26-603", "street": "ul. Kielecka 78"},
]


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

def _build_positions_and_fees(i, days, maszyny, uslugi, rt_dniowy):
    """Wspólny generator pozycji + usług dodatkowych dla umowy o indeksie i.

    RAO-P2-068: Pozycje używają predefiniowanych cenników kaskadowych per
    maszyna (1-3 dni, 4-16 dni, powyżej 16 dni) — jak w starej aplikacji.
    User klika maszynę i ma gotowe warunki rozliczenia, nie musi wpisywać.
    """
    positions = []
    num_positions = 1 if i % 3 != 0 else 2
    for j in range(num_positions):
        maszyna = maszyny[(i + j) % len(maszyny)]
        # Stawka "skuteczna" dla rozliczenia = stawka średnioterminowa (4-16 dni)
        # z cennika kaskadowego. Jeśli maszyna nie ma cennika — fallback do CENY_WYNAJMU.
        stawka_efektywna = STAWKA_EFEKTYWNA.get(maszyna.name, CENY_WYNAJMU.get(maszyna.name, Decimal("500.00")))
        # Warunki kaskadowe z cennika (jeśli dostępne) — inaczej płaska stawka
        cennik = CENNIKI_KASKADOWE.get(maszyna.name)
        if cennik:
            conditions = [
                {**w, "rate_type_id": rt_dniowy.id if rt_dniowy else None}
                for w in cennik["warunki"]
            ]
        else:
            conditions = [
                {"rate1": stawka_efektywna, "rate2": None, "period_count": days, "minimum": 1, "billing_label": "doba", "description": f"Wynajem {maszyna.name}", "rate_type_id": rt_dniowy.id if rt_dniowy else None},
            ]
        positions.append({
            "article_id": maszyna.id,
            "article_name": maszyna.name,
            "rental_days": days,
            "quantity": 1,
            "unit_price": stawka_efektywna,  # do rozliczenia (kalkulacja wartości)
            "rate_type_id": rt_dniowy.id if rt_dniowy else None,
            "billing_frequency": "dniowa",
            "billing_unit": "doba",
            "conditions": conditions,
        })

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
    return positions, fees


def _lokalizacja(i):
    """Deterministyczna lokalizacja budowy dla umowy o indeksie i."""
    loc = LOKALIZACJE_BUDOWY[i % len(LOKALIZACJE_BUDOWY)]
    return {
        "city": loc["city"],
        "postal_code": loc["postal_code"],
        "delivery_address": f"{loc['street']}, {loc['postal_code']} {loc['city']}",
    }


def generate_contracts(con_by_name, sp_by_name, br_by_name, art_by_name, rt_by_name):
    """Generuje umowy demo (RAO-P2-067): 3 pule.

    Pula A — historia 2025 (24 umowy, 12-24 mies. wstecz, wszystkie rozliczone)
             → bogate statystyki roczne, wykresy by-period, lokalizacje.
    Pula B — bieżące 2026 (24 umowy, 0-12 mies. wstecz, mix stanów)
             → aktywne wynajmy, flota teraz, KPI.
    Pula C — FA-pending (8 umów, zakończone NIEROZLICZONE, bez settlements w RAO)
             → faktury czekają w Fakturowni (seed_fa_invoices) — demo integracji:
               user klika "Pobierz z Fakturowni" → rozliczenia się tworzą na żywo.
    """
    contractors = list(con_by_name.values())
    salespeople = list(sp_by_name.values())
    branches = list(br_by_name.values())
    maszyny = [art_by_name[m["name"]] for m in MASZYNY]
    uslugi = [art_by_name[u["name"]] for u in USLUGI]
    rt_dniowy = rt_by_name.get("Stawka dniowa")

    contracts = []
    today = date.today()

    def _add(number, i, date_from, days, contract_type, is_settled, fa_pending=False, branch_id=None):
        date_to = date_from + timedelta(days=days)
        is_active = date_to >= today
        positions, fees = _build_positions_and_fees(i, days, maszyny, uslugi, rt_dniowy)
        contracts.append({
            "number": number,
            "contractor_id": contractors[i % len(contractors)].id,
            "branch_id": branch_id if branch_id is not None else branches[0].id,
            "salesperson_id": salespeople[i % len(salespeople)].id,
            "contract_type": contract_type,
            "date_from": date_from,
            "date_to": date_to,
            "is_settled": is_settled,
            "settled_at": datetime.combine(date_to, datetime.min.time()) if is_settled else None,
            "positions": positions,
            "fees": fees,
            "is_active_contract": is_active,
            "fa_pending": fa_pending,
            **_lokalizacja(i),
        })

    # ── Pula A: historia 2025 (12-24 miesiące wstecz, wszystkie rozliczone) ──
    for i in range(24):
        contract_type = "S" if i % 3 != 2 else "U"
        months_back = 12 + i // 2  # 12,12,13,13,...,23,23
        date_from = today - timedelta(days=months_back * 30 + (i % 2) * 15)
        days = 7 + (i % 4) * 7
        number = f"{contract_type}{i + 1:03d}/2025"
        _add(number, i, date_from, days, contract_type, is_settled=True)

    # ── Pula B: bieżące 2026 (0-12 miesięcy wstecz, mix stanów) ──────────────
    for i in range(24):
        contract_type = "S" if i % 3 != 2 else "U"
        months_back = i // 2  # 0,0,1,1,...,11,11
        date_from = today - timedelta(days=months_back * 30 + (i % 2) * 15)
        days = 7 + (i % 4) * 7
        date_to = date_from + timedelta(days=days)
        is_active = date_to >= today
        is_settled = (not is_active) and (i % 5 != 4)  # 80% zakończonych rozliczone
        number = f"{contract_type}{i + 1:03d}/2026"
        _add(number, i, date_from, days, contract_type, is_settled=is_settled)

    # ── Pula C: FA-pending — zakończone, NIEROZLICZONE, faktura czeka w FA ──
    # (demo integracji: "Pobierz z Fakturowni" tworzy rozliczenia na żywo)
    for k in range(8):
        i = k + 3  # offset — inne kombinacje maszyn/kontrahentów niż pula B
        contract_type = "S" if k % 4 != 3 else "U"
        date_from = today - timedelta(days=20 + k * 9)  # zakończone niedawno
        days = 7 + (k % 3) * 7
        number = f"{contract_type}{k + 25:03d}/2026"  # S025..S032/2026 — kontynuacja numeracji
        _add(number, i, date_from, days, contract_type, is_settled=False, fa_pending=True)

    # ── Pula D: umowy gdańskie (branch_id ≠ 1, suffix "G" w numerze) ──────────
    # RAO-P1-055: demo /stats/by-branch — umowy z oddziału Gdańsk.
    # Format numeru: S{NNN}/{ROK}G (G na końcu, zgodnie ze starą aplikacją WinForms).
    # 6 umów: 3 historia 2025 (rozliczone) + 3 bieżące 2026 (mix stanów).
    gdansk_branch = branches[1].id if len(branches) > 1 else branches[0].id
    for k in range(6):
        if k < 3:
            # Historia 2025 — rozliczone
            contract_type = "S" if k % 2 == 0 else "U"
            months_back = 14 + k * 3
            date_from = today - timedelta(days=months_back * 30)
            days = 10 + k * 5
            number = f"{contract_type}{k + 40:03d}/2025G"
            _add(number, k + 5, date_from, days, contract_type, is_settled=True, branch_id=gdansk_branch)
        else:
            # Bieżące 2026 — mix stanów
            contract_type = "S" if k % 2 == 0 else "U"
            months_back = (k - 3) * 4
            date_from = today - timedelta(days=months_back * 30 + 10)
            days = 14 + k * 3
            date_to = date_from + timedelta(days=days)
            is_active = date_to >= today
            number = f"{contract_type}{k + 40:03d}/2026G"
            _add(number, k + 5, date_from, days, contract_type, is_settled=(not is_active), branch_id=gdansk_branch)

    return contracts


# ── Konfiguracja "jak od klienta" (RAO-P2-067) ────────────────────────────────
# Zestawy usług dodatkowych do wydruku umowy — prawdziwy cennik (jak w legacy
# firma.uslugi1/2), skonfigurowany tak jakby klient sam ustawił w Ustawieniach.
# Ceny/opisy z produkcyjnego cennika Toolsmart 2026.

ZESTAWY_USLUG = [
    {
        "group_name": "Cennik usług — najem 2026",
        "contract_type": "S",
        "is_default": True,
        "description": "Standardowy cennik usług dodatkowych do umów najmu (aktualizacja 2026)",
        "templates": [
            {"article": "Transport maszyny", "name": "Transport", "amount_from": Decimal("500.00"), "amount_to": Decimal("500.00"), "unit": "dostawa", "description": "500.00 zł dostawa / 500.00 zł odbiór", "default_price": Decimal("500.00")},
            {"article": "Czyszczenie maszyny — drobne", "name": "Czyszczenie maszyny po wynajmie (zabrudzenia drobne)", "amount_from": Decimal("150.00"), "amount_to": Decimal("400.00"), "unit": "sztuka", "description": "150.00 zł - 400.00 zł", "default_price": Decimal("150.00")},
            {"article": "Czyszczenie maszyny — trudne zabrudzenia", "name": "Czyszczenie maszyny po wynajmie (zabrudzenia trudnościeralne)", "amount_from": Decimal("400.00"), "amount_to": Decimal("1500.00"), "unit": "sztuka", "description": "400.00 zł - 1500.00 zł", "default_price": Decimal("400.00")},
            {"article": "Tankowanie paliwa", "name": "Usługa tankowania", "amount_from": Decimal("200.00"), "amount_to": None, "unit": "tankowanie", "description": "200.00 zł (plus koszt paliwa)", "default_price": Decimal("200.00")},
            {"article": "Przestój maszyny", "name": "Ponadnormatywny przestój transportu", "amount_from": Decimal("200.00"), "amount_to": Decimal("300.00"), "unit": "godzina", "description": "200.00 zł / h - 300.00 zł / h", "default_price": Decimal("200.00")},
            {"article": "Serwis maszyny", "name": "Nieuzasadnione wezwanie serwisowe", "amount_from": Decimal("280.00"), "amount_to": None, "unit": "wizyta", "description": "280.00 zł (plus transport)", "default_price": Decimal("280.00")},
        ],
    },
    {
        "group_name": "Cennik usług — usługa z operatorem 2026",
        "contract_type": "U",
        "is_default": True,
        "description": "Cennik usług dodatkowych do umów usługowych (praca z operatorem)",
        "templates": [
            {"article": "Transport maszyny", "name": "Transport", "amount_from": Decimal("350.00"), "amount_to": None, "unit": "dostawa", "description": "350.00 zł", "default_price": Decimal("350.00")},
            {"article": None, "name": "Praca operatora", "amount_from": None, "amount_to": None, "unit": "dzień", "description": "Minimum 8 h / w ciągu dnia", "default_price": None},
            {"article": "Tankowanie paliwa", "name": "Usługa tankowania", "amount_from": Decimal("200.00"), "amount_to": None, "unit": "tankowanie", "description": "200.00 zł (plus koszt paliwa)", "default_price": Decimal("200.00")},
        ],
    },
    {
        "group_name": "Kontrakt długoterminowy (rabat)",
        "contract_type": "S",
        "is_default": False,
        "description": "Zestaw dla umów 30+ dni — obniżone stawki usług (do wyboru przy wydruku)",
        "templates": [
            {"article": "Transport maszyny", "name": "Transport", "amount_from": Decimal("350.00"), "amount_to": Decimal("350.00"), "unit": "dostawa", "description": "350.00 zł dostawa / 350.00 zł odbiór (rabat kontraktowy)", "default_price": Decimal("350.00")},
            {"article": "Czyszczenie maszyny — drobne", "name": "Czyszczenie maszyny po wynajmie (zabrudzenia drobne)", "amount_from": Decimal("100.00"), "amount_to": Decimal("300.00"), "unit": "sztuka", "description": "100.00 zł - 300.00 zł", "default_price": Decimal("100.00")},
            {"article": "Tankowanie paliwa", "name": "Usługa tankowania", "amount_from": Decimal("150.00"), "amount_to": None, "unit": "tankowanie", "description": "150.00 zł (plus koszt paliwa)", "default_price": Decimal("150.00")},
            {"article": "Serwis maszyny", "name": "Przegląd okresowy w cenie", "amount_from": Decimal("0.00"), "amount_to": None, "unit": "wizyta", "description": "W ramach kontraktu długoterminowego", "default_price": Decimal("0.00")},
        ],
    },
    {
        "group_name": "Weekend / krótkoterminowy (1-3 dni)",
        "contract_type": "S",
        "is_default": False,
        "description": "Zestaw dla wynajmu weekendowego — wyższe stawki transportu, brak rabatów",
        "templates": [
            {"article": "Transport maszyny", "name": "Transport ekspresowy", "amount_from": Decimal("650.00"), "amount_to": Decimal("650.00"), "unit": "dostawa", "description": "650.00 zł dostawa + 650.00 zł odbiór (weekend)", "default_price": Decimal("650.00")},
            {"article": "Czyszczenie maszyny — drobne", "name": "Czyszczenie maszyny po wynajmie", "amount_from": Decimal("200.00"), "amount_to": Decimal("400.00"), "unit": "sztuka", "description": "200.00 zł - 400.00 zł", "default_price": Decimal("200.00")},
            {"article": "Tankowanie paliwa", "name": "Usługa tankowania", "amount_from": Decimal("250.00"), "amount_to": None, "unit": "tankowanie", "description": "250.00 zł (plus koszt paliwa)", "default_price": Decimal("250.00")},
        ],
    },
    {
        "group_name": "Kontrakt zagraniczny (export)",
        "contract_type": "S",
        "is_default": False,
        "description": "Zestaw dla umów zagranicznych — transport międzynarodowy, ubezpieczenie transportu",
        "templates": [
            {"article": "Transport maszyny", "name": "Transport międzynarodowy", "amount_from": Decimal("1500.00"), "amount_to": Decimal("3500.00"), "unit": "dostawa", "description": "1500.00 zł - 3500.00 zł (zależnie od kraju)", "default_price": Decimal("2000.00")},
            {"article": "Czyszczenie maszyny — drobne", "name": "Czyszczenie maszyny po wynajmie", "amount_from": Decimal("200.00"), "amount_to": Decimal("500.00"), "unit": "sztuka", "description": "200.00 zł - 500.00 zł", "default_price": Decimal("300.00")},
            {"article": "Tankowanie paliwa", "name": "Usługa tankowania", "amount_from": Decimal("300.00"), "amount_to": None, "unit": "tankowanie", "description": "300.00 zł (plus koszt paliwa)", "default_price": Decimal("300.00")},
            {"article": "Serwis maszyny", "name": "Assistance zagraniczny", "amount_from": Decimal("500.00"), "amount_to": None, "unit": "wizyta", "description": "500.00 zł (plus transport międzynarodowy)", "default_price": Decimal("500.00")},
        ],
    },
    {
        "group_name": "Usługa z operatorem — premium",
        "contract_type": "U",
        "is_default": False,
        "description": "Premium: doświadczony operator + serwis 24/7 + paliwo w cenie",
        "templates": [
            {"article": "Transport maszyny", "name": "Transport premium", "amount_from": Decimal("500.00"), "amount_to": None, "unit": "dostawa", "description": "500.00 zł (transport niskopodwoziowy)", "default_price": Decimal("500.00")},
            {"article": None, "name": "Praca operatora (premium)", "amount_from": Decimal("450.00"), "amount_to": None, "unit": "dzień", "description": "450.00 zł/dzień — operator z uprawnieniami (minimum 8h)", "default_price": Decimal("450.00")},
            {"article": "Tankowanie paliwa", "name": "Paliwo w cenie", "amount_from": Decimal("0.00"), "amount_to": None, "unit": "tankowanie", "description": "W ramach stawki premium", "default_price": Decimal("0.00")},
            {"article": "Serwis maszyny", "name": "Serwis 24/7", "amount_from": Decimal("0.00"), "amount_to": None, "unit": "wizyta", "description": "Assistance 24/7 w ramach kontraktu premium", "default_price": Decimal("0.00")},
        ],
    },
]


async def seed_konfiguracja(db: AsyncSession, art_by_name):
    """Konfiguracja zestawów usług do wydruku — jak gdyby klient ustawił w Ustawieniach.

    - Upsert grup presetów po nazwie (nie duplikuje istniejących default z main.py —
      przejmuje flagę is_default: stare defaulty tracą flagę na rzecz nowych).
    - Szablony idempotentne po (preset_id, name), z article_id + default_price.
    - RAO-P2-068: wypełnia ServiceFeeTemplateItem (relacja N:M preset → artykuł
      z domyślną ceną) — frontend pokazuje konkretne artykuły w pickerze presetów.
    """
    from settings.models import FeePresetGroup, ServiceFeeTemplate, ServiceFeeTemplateItem

    created_groups = 0
    created_templates = 0
    created_items = 0

    for zestaw in ZESTAWY_USLUG:
        result = await db.execute(
            select(FeePresetGroup).where(FeePresetGroup.name == zestaw["group_name"])
        )
        group = result.scalar_one_or_none()
        if not group:
            group = FeePresetGroup(
                company_id=1,
                name=zestaw["group_name"],
                contract_type=zestaw["contract_type"],
                description=zestaw["description"],
                is_default=False,  # flagę ustawiamy niżej (po zdjęciu ze starych)
                sort_order=0,
            )
            db.add(group)
            await db.flush()
            created_groups += 1

        # is_default: nowy zestaw przejmuje flagę default dla swojego typu
        if zestaw["is_default"] and not group.is_default:
            old_defaults = await db.execute(
                select(FeePresetGroup).where(
                    FeePresetGroup.contract_type == zestaw["contract_type"],
                    FeePresetGroup.is_default == True,  # noqa: E712
                    FeePresetGroup.id != group.id,
                )
            )
            for old in old_defaults.scalars().all():
                old.is_default = False
            group.is_default = True

        for idx, tpl in enumerate(zestaw["templates"], start=1):
            existing_tpl = await db.execute(
                select(ServiceFeeTemplate).where(
                    ServiceFeeTemplate.preset_id == group.id,
                    ServiceFeeTemplate.name == tpl["name"],
                )
            )
            existing_obj = existing_tpl.scalar_one_or_none()
            article = art_by_name.get(tpl["article"]) if tpl["article"] else None
            if existing_obj:
                # Enrich: uzupełnij article_id/default_price jeśli brak (stare rekordy)
                if not existing_obj.article_id and article:
                    existing_obj.article_id = article.id
                if not existing_obj.default_price and tpl["default_price"]:
                    existing_obj.default_price = tpl["default_price"]
                tpl_obj = existing_obj
            else:
                tpl_obj = ServiceFeeTemplate(
                    company_id=1,
                    preset_id=group.id,
                    contract_type=zestaw["contract_type"],
                    sort_order=idx,
                    article_id=article.id if article else None,
                    default_price=tpl["default_price"],
                    name=tpl["name"],
                    amount_from=tpl["amount_from"],
                    amount_to=tpl["amount_to"],
                    unit=tpl["unit"],
                    description=tpl["description"],
                    is_active=True,
                )
                db.add(tpl_obj)
                await db.flush()
                created_templates += 1

            # RAO-P2-068: ServiceFeeTemplateItem — relacja N:M preset → artykuł
            # z domyślną ceną. Frontend pokazuje konkretne artykuły w pickerze.
            if article:
                existing_item = await db.execute(
                    select(ServiceFeeTemplateItem).where(
                        ServiceFeeTemplateItem.template_id == group.id,
                        ServiceFeeTemplateItem.article_id == article.id,
                    )
                )
                if not existing_item.scalar_one_or_none():
                    db.add(ServiceFeeTemplateItem(
                        template_id=group.id,
                        article_id=article.id,
                        default_price=tpl["default_price"],
                        sort_order=idx,
                    ))
                    created_items += 1

    await db.commit()
    print(f"  Zestawy usług: {created_groups} nowych grup, {created_templates} szablonów, {created_items} item-relacji")


async def seed_company(db: AsyncSession):
    """RAO-P2-068: Pełna konfiguracja firmy — jak gdyby klient ustawił w Ustawieniach.

    main.py tworzy tylko pusty Company(id=1, name="RAO — Wynajem Maszyn").
    Seed wzbogaca o pełne dane: NIP, adres, konto bankowe, header_text do PDF,
    numeracja umów. Idempotentny update-in-place.
    """
    from settings.models import Company

    result = await db.execute(select(Company).where(Company.id == 1))
    company = result.scalar_one_or_none()
    if not company:
        company = Company(id=1, name=FIRMA_CONFIG["name"])
        db.add(company)
        await db.flush()

    # Update-in-place (idempotentny — nadpisuje puste pola)
    updated = 0
    for k, v in FIRMA_CONFIG.items():
        current = getattr(company, k, None)
        if current != v:
            setattr(company, k, v)
            updated += 1

    await db.commit()
    print(f"  Firma: {updated} pól zaktualizowanych (NIP={FIRMA_CONFIG['nip']}, konto={FIRMA_CONFIG['bank_account'][:12]}...)")
    return company


async def _resolve_postal_code_id(db: AsyncSession, postal_code: str) -> int | None:
    """Znajdź FK do postal_codes po PNA (deterministyczna lokalizacja — RAO-P2-028)."""
    from integrations.models import PostalCode
    result = await db.execute(
        select(PostalCode.id).where(PostalCode.postal_code == postal_code).limit(1)
    )
    row = result.scalar_one_or_none()
    return row


async def seed_umowy(db: AsyncSession, contracts_data, art_by_name):
    """Tworzy umowy + pozycje + warunki + usługi dodatkowe + rozliczenia.

    Idempotentne + enrich: istniejące umowy bez lokalizacji dostają
    city/postal_code/delivery_address/postal_code_id (update-in-place).
    Umowy fa_pending NIE dostają rozliczeń (faktura czeka w FA — demo integracji).
    """
    created_contracts = 0
    created_positions = 0
    created_conditions = 0
    created_fees = 0
    created_settlements = 0
    enriched_contracts = 0

    for cd in contracts_data:
        pna_id = await _resolve_postal_code_id(db, cd["postal_code"])

        # Sprawdź czy umowa istnieje po numerze
        existing = await db.execute(select(Contract).where(Contract.number == cd["number"]))
        contract = existing.scalar_one_or_none()
        if contract:
            # Enrich: uzupełnij lokalizację jeśli brak (idempotentny update)
            if not contract.city:
                contract.city = cd["city"]
                contract.postal_code = cd["postal_code"]
                contract.delivery_address = cd["delivery_address"]
                contract.postal_code_id = pna_id
                enriched_contracts += 1
            continue

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
            city=cd["city"],
            postal_code=cd["postal_code"],
            postal_code_id=pna_id,
            delivery_address=cd["delivery_address"],
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

            # Rozliczenie dla pozycji (80% source=fakturownia, 20% manual).
            # fa_pending → BEZ rozliczeń (faktura czeka w FA — "Pobierz z Fakturowni" na demo)
            is_settled = cd["is_settled"]
            if is_settled and not cd.get("fa_pending"):
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

            # Rozliczenie usługi (jeśli umowa rozliczona; fa_pending → bez rozliczeń)
            if is_settled and not cd.get("fa_pending"):
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
    print(f"  Umowy: {created_contracts} nowych, {enriched_contracts} wzbogaconych o lokalizację")
    print(f"  Pozycje: {created_positions} nowych")
    print(f"  Warunki: {created_conditions} nowych")
    print(f"  Usługi dodatkowe: {created_fees} nowych")
    print(f"  Rozliczenia: {created_settlements} nowych")
    return created_contracts


async def main():
    print("=" * 60)
    print("RAO-P2-061/068: Demo data seeding")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        print("\n[1/9] Kategorie...")
        await seed_kategorie(db)

        print("\n[2/9] Artykuły (maszyny + usługi)...")
        art_by_name = await seed_artykuly(db)

        print("\n[3/9] Kontrahenci...")
        con_by_name = await seed_kontrahenci(db)

        print("\n[4/9] Handlowcy...")
        sp_by_name = await seed_handlowcy(db)

        print("\n[5/9] Oddziały...")
        br_by_name = await seed_oddzialy(db)

        print("\n[6/9] Rate types (6 typów — jak w starej aplikacji)...")
        rt_by_name = await seed_rate_types(db)

        print("\n[7/9] Konfiguracja firmy (NIP, konto, header_text)...")
        await seed_company(db)

        print("\n[8/9] Konfiguracja zestawów usług (6 presetów + ServiceFeeTemplateItem)...")
        await seed_konfiguracja(db, art_by_name)

        print("\n[9/9] Umowy + pozycje + warunki kaskadowe + usługi + rozliczenia...")
        contracts_data = generate_contracts(con_by_name, sp_by_name, br_by_name, art_by_name, rt_by_name)
        await seed_umowy(db, contracts_data, art_by_name)

    print("\n" + "=" * 60)
    print("DONE — demo data seeded")
    print("=" * 60)
    print("\nNastępny krok: wystaw faktury FA dla rozliczonych umów")
    print("(uruchom: python seed_fa_invoices.py)")


if __name__ == "__main__":
    asyncio.run(main())
