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
- Umowy (56 szt: 24 historia 2025 + 24 bieżące 2026 + 8 FA-pending)
  z predefiniowanymi cennikami kaskadowymi per maszyna (1-3 dni, 4-16 dni,
  powyżej 16 dni) — jak w starej aplikacji WinForms
- Pozycje umów (z warunkami rozliczeniowymi kaskadowymi)
- Usługi dodatkowe
- Rozliczenia (80% source=fakturownia, 20% source=manual/estimate)
- Mapowanie Article.fakturownia_product_id ↔ produkty FA

Użycie:
    cd backend && python seed_demo_data.py

Wymaga:
    - Backend NIE musi działać (skrypt łączy się bezpośrednio z DB)
    - .env z RAO_FAKTUROWNIA_ENC_KEY i DB credentials
"""
import asyncio
import io
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# RAO: UTF-8 stdout — Python 3.14 na Windows cp1250 crashuje przy print polskich znaków
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Dodaj backend do path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, AsyncSessionLocal
from categories.models import Category
from machines.models import Machine
from services.models import Service
from additional_services.models import AdditionalService
from contractors.models import Contractor, ContractorAddress
from settings.models import Salesperson, Branch, RateType, MachineRatePreset, MachineRatePresetItem
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from settlements.models import ContractSettlement

# Import wszystkich modeli żeby SQLAlchemy skonfigurowało relacje
import auth.models  # noqa: F401
import contractors.models  # noqa: F401
import machines.models  # noqa: F401
import services.models  # noqa: F401
import additional_services.models  # noqa: F401
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
        "internal_number": "KOP-001",
        "registration_no": "RAO 12345", "serial_no": "JCB8035Z2021001",
        "brand": "JCB", "model": "8035 ZTS", "replacement_value": Decimal("280000.00"),
        "category_main": "Koparki", "category_sub1": "Koparki gąsienicowe",
        "capacity_t": Decimal("3.5"),
        "accessories": "Łyżka standardowa, szybkozłącze hydrauliczne",
        "power_type": "diesel",
        "fakturownia_product_id": 8845156432567,  # KOP001
    },
    {
        "name": "Ładowarka teleskopowa Manuscop 6.36",
        "internal_number": "LAD-002",
        "registration_no": "RAO 23456", "serial_no": "MAN6362022001",
        "brand": "Manitou", "model": "Manuscop 6.36", "replacement_value": Decimal("420000.00"),
        "category_main": "Ładowarki Teleskopowe", "category_sub1": "Ładowarki Teleskopowe Sztywne",
        "reach_m": Decimal("6.0"), "capacity_t": Decimal("3.6"),
        "accessories": "Widły paletowe, łyżka objętościowa 1.2m³",
        "power_type": "diesel",
        "fakturownia_product_id": 8845156436442,  # LAD001
    },
    {
        "name": "Podnośnik koszowy Haulotte HA16PX",
        "internal_number": "POD-003",
        "registration_no": "RAO 34567", "serial_no": "HAU16PX2021001",
        "brand": "Haulotte", "model": "HA16 PX", "replacement_value": Decimal("380000.00"),
        "category_main": "Podnośniki", "category_sub1": "Podnośnik koszowy na samochodzie",
        "reach_m": Decimal("16.0"),
        "accessories": "Kosz 230kg, wysięgnik obrotowy 360°",
        "power_type": "diesel",
        "fakturownia_product_id": 8845156436443,  # POD001
    },
    {
        "name": "Spychar Wirtgen W100CFi",
        "internal_number": "SPY-004",
        "registration_no": "RAO 45678", "serial_no": "WIR100CFI2022001",
        "brand": "Wirtgen", "model": "W 100 CFi", "replacement_value": Decimal("1200000.00"),
        "category_main": "Spychacze", "category_sub1": "Spychacze frezujące",
        "accessories": "Frez 1.0m, system chłodzenia wodnego",
        "power_type": "diesel",
        "fakturownia_product_id": 8845156436444,  # SPY001
    },
    {
        "name": "Zagęszczarka Ammann APF 15/50",
        "internal_number": "ZAG-005",
        "registration_no": "RAO 56789", "serial_no": "AMM15502023001",
        "brand": "Ammann", "model": "APF 15/50", "replacement_value": Decimal("35000.00"),
        "category_main": "Zagęszczarki", "category_sub1": "Zagęszczarki płytowe",
        "accessories": "Ruch w przód i tył, nóż dociskowy",
        "power_type": "elektryk",
        "fakturownia_product_id": 8845156436446,  # ZAG001
    },
]

USLUGI = [
    {
        "name": "Transport",
        "display_name": "Transport",
        "default_amount": Decimal("1200.00"),
        "fakturownia_product_id": 8845156432587,  # TRA001
    },
    {
        "name": "Czyszczenie",
        "display_name": "Czyszczenie maszyny (zabrudzenia ponadnormatywne)",
        "default_amount": Decimal("0.00"),
        "fakturownia_product_id": 8845156432589,  # CZY001
    },
    {
        "name": "Tankowanie",
        "display_name": "Usługa tankowania",
        "default_amount": Decimal("200.00"),
        "fakturownia_product_id": 8845156432620,  # TAN001
    },
    {
        "name": "Przestój",
        "display_name": "Ponadnormatywny przestój transportu",
        "default_amount": Decimal("250.00"),
        "fakturownia_product_id": 8845156436449,  # PZT001
    },
    {
        "name": "Serwis",
        "display_name": "Nieuzasadnione wezwanie serwisowe",
        "default_amount": Decimal("280.00"),
        "fakturownia_product_id": 8845156436450,  # SER001
    },
    {
        "name": "Przegląd Diesel",
        "display_name": "Przegląd techniczny i czyszczenie maszyny",
        "default_amount": Decimal("150.00"),
        "fakturownia_product_id": 8845156436451,  # DIE001
    },
    {
        "name": "Przegląd Elektryk",
        "display_name": "Przegląd techniczny, ładowanie akumulatorów oraz czyszczenie maszyny",
        "default_amount": Decimal("35.00"),
        "fakturownia_product_id": 8845156436452,  # ELE001
    },
]

# P1-115: Usługi zwykłe (services table) — przedmiot umowy typu U (usługi)
# Odrębne od additional_services (USLUGI) — to są usługi główne, nie dodatkowe.
USLUGI_ZWYKLE = [
    {
        "name": "Praca operatora koparki",
        "description": "Obsługa operatora dla koparki gąsienicowej (stawka dniowa)",
        "replacement_value": Decimal("600.00"),
        "fakturownia_product_id": 8845156436460,  # OPR001
    },
    {
        "name": "Praca operatora ładowarki",
        "description": "Obsługa operatora dla ładowarki teleskopowej (stawka dniowa)",
        "replacement_value": Decimal("550.00"),
        "fakturownia_product_id": 8845156436461,  # OPR002
    },
    {
        "name": "Praca operatora podnośnika",
        "description": "Obsługa operatora dla podnośnika koszowego (stawka dniowa)",
        "replacement_value": Decimal("450.00"),
        "fakturownia_product_id": 8845156436462,  # OPR003
    },
    {
        "name": "Frezowanie asfaltu",
        "description": "Usługa frezowania asfaltu z użyciem spychacza frezującego",
        "replacement_value": Decimal("1200.00"),
        "fakturownia_product_id": 8845156436463,  # FRZ001
    },
    {
        "name": "Zagęszczanie podłoża",
        "description": "Usługa zagęszczania podłoża z użyciem zagęszczarki płytowej",
        "replacement_value": Decimal("350.00"),
        "fakturownia_product_id": 8845156436464,  # ZAG001
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
    {"name": "WARSZAWA", "city": "Warszawa", "street": "ul. Przykładowa 1", "postal_code": "00-001"},
    {"name": "GDAŃSK", "city": "Gdańsk", "street": "ul. Portowa 5", "postal_code": "80-001"},
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
    """Maszyny + usługi dodatkowe z mapowaniem FA."""
    created = 0
    art_by_name = {}
    now = datetime.now()
    # Maszyny → Machine
    for m in MASZYNY:
        m_with_ts = {**m, "created_at": now, "updated_at": now}
        obj, was_created = await get_or_create(db, Machine, {"name": m["name"]}, m_with_ts)
        art_by_name[m["name"]] = obj
        if was_created:
            created += 1
    # Usługi dodatkowe → AdditionalService
    for u in USLUGI:
        u_with_ts = {**u, "created_at": now, "updated_at": now}
        obj, was_created = await get_or_create(db, AdditionalService, {"name": u["name"]}, u_with_ts)
        art_by_name[u["name"]] = obj
        if was_created:
            created += 1
    await db.commit()
    maszyny_count = len(MASZYNY)
    uslugi_count = len(USLUGI)
    print(f"  Maszyny + usługi: {created} nowych ({maszyny_count} maszyn + {uslugi_count} usług dodatkowych)")
    return art_by_name


async def seed_uslugi_zwykle(db: AsyncSession):
    """P1-115: Usługi zwykłe (services table) — przedmiot umowy typu U."""
    created = 0
    svc_by_name = {}
    now = datetime.now()
    for s in USLUGI_ZWYKLE:
        s_with_ts = {**s, "created_at": now, "updated_at": now}
        obj, was_created = await get_or_create(db, Service, {"name": s["name"]}, s_with_ts)
        svc_by_name[s["name"]] = obj
        if was_created:
            created += 1
    await db.commit()
    print(f"  Usługi zwykłe: {created} nowych ({len(USLUGI_ZWYKLE)} usług)")
    return svc_by_name


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


# RAO-P2-071: Demo users (admin/admin123) — dla fresh database
DEMO_USERS = [
    {"login": "admin", "password": "admin123", "email": "admin@rao.local",
     "first_name": "Admin", "last_name": "System", "role": "admin", "branch": "WARSZAWA"},
    {"login": "lukasz", "password": "lukasz123", "email": "lukasz@rao.local",
     "first_name": "Łukasz", "last_name": "Kowalski", "role": "admin", "branch": "WARSZAWA"},
    {"login": "test", "password": "test123", "email": "test@rao.local",
     "first_name": "Test", "last_name": "User", "role": "user", "branch": "GDAŃSK"},
    {"login": "patrycja", "password": "patrycja123", "email": "patrycja@rao.local",
     "first_name": "Patrycja", "last_name": "Nowak", "role": "user", "branch": "GDAŃSK"},
]


async def seed_users(db: AsyncSession, br_by_name: dict):
    """RAO-P2-071: Seed demo users z bcrypt hasłami. Idempotentny po login."""
    import bcrypt
    from auth.models import User

    created = 0
    now = datetime.now()
    for u in DEMO_USERS:
        existing = await db.execute(select(User).where(User.login == u["login"]))
        if existing.scalar_one_or_none():
            continue
        branch = br_by_name.get(u["branch"])
        hashed = bcrypt.hashpw(u["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            login=u["login"],
            email=u["email"],
            password=hashed,
            first_name=u["first_name"],
            last_name=u["last_name"],
            role=u["role"],
            branch_id=branch.id if branch else None,
            is_active=True,
            must_change_password=False,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        created += 1
    await db.commit()
    print(f"  Użytkownicy: {created} nowych (admin/admin123, lukasz/lukasz123, test/test123, patrycja/patrycja123)")
    return created


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

def _build_positions_and_fees(i, days, maszyny, uslugi, rt_dniowy, contract_type="S", uslugi_zwykle=None):
    """Wspólny generator pozycji + usług dodatkowych dla umowy o indeksie i.

    RAO-P2-068: Pozycje używają predefiniowanych cenników kaskadowych per
    maszyna (1-3 dni, 4-16 dni, powyżej 16 dni) — jak w starej aplikacji.
    User klika maszynę i ma gotowe warunki rozliczenia, nie musi wpisywać.

    P1-115: Dla umów typu U (usługi) pozycje używają service_id (services table),
    nie machine_id. uslugi_zwykle = lista obiektów Service.
    """
    positions = []
    num_positions = 1 if i % 3 != 0 else 2

    if contract_type == "U" and uslugi_zwykle:
        # P1-115: Umowa usługi — pozycje z service_id
        for j in range(num_positions):
            usluga = uslugi_zwykle[(i + j) % len(uslugi_zwykle)]
            stawka_efektywna = usluga.replacement_value or Decimal("500.00")
            conditions = [
                {"rate1": stawka_efektywna, "rate2": None, "period_count": days, "minimum": 1, "billing_label": "doba"},
            ]
            positions.append({
                "machine_id": None,
                "service_id": usluga.id,
                "article_name": usluga.name,
                "rental_days": days,
                "quantity": 1,
                "unit_price": stawka_efektywna,
                "rate_type_id": rt_dniowy.id if rt_dniowy else None,
                "billing_frequency": "dniowa",
                "billing_unit": "doba",
                "conditions": conditions,
            })
    else:
        # Umowa najmu (S) — pozycje z machine_id
        for j in range(num_positions):
            maszyna = maszyny[(i + j) % len(maszyny)]
            # Stawka "skuteczna" dla rozliczenia = stawka średnioterminowa (4-16 dni)
            # z cennika kaskadowego. Jeśli maszyna nie ma cennika — fallback do CENY_WYNAJMU.
            stawka_efektywna = STAWKA_EFEKTYWNA.get(maszyna.name, CENY_WYNAJMU.get(maszyna.name, Decimal("500.00")))
            # Warunki kaskadowe z cennika (jeśli dostępne) — inaczej płaska stawka
            cennik = CENNIKI_KASKADOWE.get(maszyna.name)
            if cennik:
                conditions = [
                    {**w}
                    for w in cennik["warunki"]
                ]
            else:
                conditions = [
                    {"rate1": stawka_efektywna, "rate2": None, "period_count": days, "minimum": 1, "billing_label": "doba"},
                ]
            positions.append({
                "machine_id": maszyna.id,
                "service_id": None,
                "article_name": maszyna.name,
                "rental_days": days,
                "quantity": 1,
                "unit_price": stawka_efektywna,  # do rozliczenia (kalkulacja wartości)
                "rate_type_id": rt_dniowy.id if rt_dniowy else None,
                "billing_frequency": "dniowa",
                "billing_unit": "doba",
                "conditions": conditions,
            })

    # RAO-P1-100/P1-113: $1/$2 placeholdery podmieniane na amount_from/amount_to
    # na umowie i PDF. $1 = kwota od, $2 = kwota do (jeśli brak → puste).
    DEMO_FEE_DESCRIPTION = {
        "Transport": "$1 zł dostawa / $2 zł odbiór",
        "Czyszczenie": "wycena indywidualna",
        "Tankowanie": "$1 zł (plus koszt paliwa)",
        "Przestój": "$1 zł / h - $2 zł / h",
        "Serwis": "$1 zł (plus transport)",
        "Przegląd Diesel": "$1 zł",
        "Przegląd Elektryk": "$1 zł",
    }
    fees = []
    num_fees = 2 + (i % 3)  # 2, 3, 4
    for j in range(num_fees):
        usluga = uslugi[(i + j) % len(uslugi)]
        cena_usl = usluga.default_amount if usluga.default_amount is not None else Decimal("100")
        fee_desc = DEMO_FEE_DESCRIPTION.get(usluga.name)
        # P1-113: $2 wymaga amount_to dla Transport (odbiór) i Przestój (górna widełka)
        amount_to = None
        if usluga.name == "Transport":
            amount_to = Decimal("1200.00")  # odbiór = dostawa
        elif usluga.name == "Przestój":
            amount_to = Decimal("300.00")  # górna widełka
        # P1-120: name = display_name (długa nazwa do umowy), additional_service_id = FK
        display_name = usluga.display_name if hasattr(usluga, 'display_name') and usluga.display_name else usluga.name
        fees.append({
            "additional_service_id": usluga.id,  # P1-120: FK do additional_services
            "name": display_name,  # P1-120: długa nazwa do umowy/PDF
            "amount_from": cena_usl,
            "amount_to": amount_to,
            "unit": "szt" if usluga.name == "Transport" else "kpl",
            "description": fee_desc,
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


def generate_contracts(con_by_name, sp_by_name, br_by_name, art_by_name, rt_by_name, svc_by_name=None):
    """Generuje umowy demo (RAO-P2-067): 4 pule.

    Pula A — historia 2025 (24 umowy, 12-24 mies. wstecz, wszystkie rozliczone)
             → bogate statystyki roczne, wykresy by-period, lokalizacje.
    Pula B — bieżące 2026 (24 umowy):
             B1: 10 AKTYWNYCH FA-pending (date_to >= today, is_settled=False, faktura w FA)
                 → demo rozliczeń: user klika "Pobierz z Fakturowni" → rozliczenia na żywo.
             B2: 14 historii 2026 (1-7 mies. wstecz, mix rozliczone / FA-pending zakończone).
    Pula C — FA-pending zakończone (16 umów, NIEROZLICZONE, faktura czeka w FA)
             → demo integracji na umowach zakończonych.
    """
    contractors = list(con_by_name.values())
    salespeople = list(sp_by_name.values())
    branches = list(br_by_name.values())
    maszyny = [art_by_name[m["name"]] for m in MASZYNY]
    uslugi = [art_by_name[u["name"]] for u in USLUGI]
    uslugi_zwykle = list(svc_by_name.values()) if svc_by_name else []
    rt_dniowy = rt_by_name.get("Stawka dniowa")

    contracts = []
    today = date.today()

    def _add(number, i, date_from, days, contract_type, is_settled, fa_pending=False, branch_idx=0):
        date_to = date_from + timedelta(days=days)
        is_active = date_to >= today
        positions, fees = _build_positions_and_fees(
            i, days, maszyny, uslugi, rt_dniowy,
            contract_type=contract_type, uslugi_zwykle=uslugi_zwykle,
        )
        # RAO-P1-022: numer zawsze zaczyna się na S, G na końcu jeśli Gdańsk (branch_id != 1)
        branch = branches[branch_idx % len(branches)]
        suffix = "G" if branch.id != 1 else ""
        # Wymuś prefiks S (nawet dla umów typu U) — zgodne z generate_contract_number
        if number[0] != "S":
            number = "S" + number[1:]
        if suffix and not number.endswith(suffix):
            # Wstaw G przed rok (np. S001/2026 → S001/2026G)
            parts = number.split("/")
            if len(parts) == 2:
                number = f"{parts[0]}/{parts[1]}{suffix}"
        contracts.append({
            "number": number,
            "contractor_id": contractors[i % len(contractors)].id,
            "branch_id": branch.id,
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
    # Co 4 umowa z Gdańska (branch_idx=1 → suffix G w numerze)
    for i in range(24):
        contract_type = "S" if i % 3 != 2 else "U"
        months_back = 12 + i // 2  # 12,12,13,13,...,23,23
        date_from = today - timedelta(days=months_back * 30 + (i % 2) * 15)
        days = 7 + (i % 4) * 7
        number = f"{contract_type}{i + 1:03d}/2025"
        _add(number, i, date_from, days, contract_type, is_settled=True, branch_idx=i % 4)

    # ── Pula B1: 10 AKTYWNYCH FA-pending (date_to >= today, faktura w FA) ────
    # Demo rozliczeń: user otwiera aktywną umowę → "Pobierz z Fakturowni" →
    # rozliczenia tworzą się na żywo → zapisz → następna umowa.
    # date_from = today - (i*2) dni (0,2,4,...,18 dni temu)
    # days = 21 + (i%3)*7 (21,28,35,21,28,35,21,28,35,21) → date_to w przyszłości
    for i in range(10):
        contract_type = "S" if i % 3 != 2 else "U"
        date_from = today - timedelta(days=i * 2)
        days = 21 + (i % 3) * 7
        number = f"{contract_type}{i + 1:03d}/2026"
        _add(number, i, date_from, days, contract_type, is_settled=False, fa_pending=True, branch_idx=i % 4)

    # ── Pula B2: 14 historii 2026 (1-7 mies. wstecz, mix rozliczone / FA-pending) ──
    for i in range(10, 24):
        contract_type = "S" if i % 3 != 2 else "U"
        months_back = (i - 10) // 2 + 1  # 1,1,2,2,...,7,7
        date_from = today - timedelta(days=months_back * 30 + (i % 2) * 15)
        days = 7 + (i % 4) * 7
        date_to = date_from + timedelta(days=days)
        is_active = date_to >= today
        is_settled = (not is_active) and (i % 5 != 4)  # 80% zakończonych rozliczone
        number = f"{contract_type}{i + 1:03d}/2026"
        _add(number, i, date_from, days, contract_type, is_settled=is_settled, branch_idx=i % 4)

    # ── Pula C: FA-pending — zakończone, NIEROZLICZONE, faktura czeka w FA ──
    # (demo integracji: "Pobierz z Fakturowni" tworzy rozliczenia na żywo)
    for k in range(16):
        i = k + 3  # offset — inne kombinacje maszyn/kontrahentów niż pula B
        contract_type = "S" if k % 4 != 3 else "U"
        date_from = today - timedelta(days=20 + k * 9)  # zakończone niedawno
        days = 7 + (k % 3) * 7
        number = f"{contract_type}{k + 25:03d}/2026"  # S025..S040/2026 — kontynuacja numeracji
        _add(number, i, date_from, days, contract_type, is_settled=False, fa_pending=True, branch_idx=k % 4)

    return contracts


# ── Konfiguracja "jak od klienta" (RAO-P2-067) ────────────────────────────────
# Zestawy usług dodatkowych do wydruku umowy — prawdziwy cennik (jak w legacy
# firma.uslugi1/2), skonfigurowany tak jakby klient sam ustawił w Ustawieniach.
# Ceny/opisy z produkcyjnego cennika Toolsmart 2026.

ZESTAWY_USLUG = [
    {
        "group_name": "Najem — Diesel",
        "contract_type": "S",
        "is_default": False,
        "description": "Pełny zestaw opłat Diesel: transport + przegląd + czyszczenie + tankowanie + przestój + serwis",
        "templates": [
            {"article": "Transport", "name": "Transport", "amount_from": Decimal("1200.00"), "amount_to": Decimal("1200.00"), "unit": "dostawa", "description": "$1 zł dostawa / $2 zł odbiór"},
            {"article": "Przegląd Diesel", "name": "Przegląd techniczny i czyszczenie maszyny", "amount_from": Decimal("150.00"), "amount_to": None, "unit": "sztuka", "description": "$1 zł"},
            {"article": "Czyszczenie", "name": "Czyszczenie maszyny (zabrudzenia ponadnormatywne)", "amount_from": None, "amount_to": None, "unit": None, "description": "wycena indywidualna"},
            {"article": "Tankowanie", "name": "Usługa tankowania", "amount_from": Decimal("200.00"), "amount_to": None, "unit": "tankowanie", "description": "$1 zł (plus koszt paliwa)"},
            {"article": "Przestój", "name": "Ponadnormatywny przestój transportu", "amount_from": Decimal("200.00"), "amount_to": Decimal("300.00"), "unit": "h", "description": "$1 zł / h - $2 zł / h"},
            {"article": "Serwis", "name": "Nieuzasadnione wezwanie serwisowe", "amount_from": Decimal("280.00"), "amount_to": None, "unit": "wizyta", "description": "$1 zł (plus transport)"},
        ],
    },
    {
        "group_name": "Najem — Elektryk",
        "contract_type": "S",
        "is_default": False,
        "description": "Pełny zestaw opłat Elektryk: transport + przegląd + czyszczenie + tankowanie + przestój + serwis",
        "templates": [
            {"article": "Transport", "name": "Transport", "amount_from": Decimal("1200.00"), "amount_to": Decimal("1200.00"), "unit": "dostawa", "description": "$1 zł dostawa / $2 zł odbiór"},
            {"article": "Przegląd Elektryk", "name": "Przegląd techniczny, ładowanie akumulatorów oraz czyszczenie maszyny", "amount_from": Decimal("35.00"), "amount_to": None, "unit": "sztuka", "description": "$1 zł"},
            {"article": "Czyszczenie", "name": "Czyszczenie maszyny (zabrudzenia ponadnormatywne)", "amount_from": None, "amount_to": None, "unit": None, "description": "wycena indywidualna"},
            {"article": "Tankowanie", "name": "Usługa tankowania", "amount_from": Decimal("200.00"), "amount_to": None, "unit": "tankowanie", "description": "$1 zł (plus koszt paliwa)"},
            {"article": "Przestój", "name": "Ponadnormatywny przestój transportu", "amount_from": Decimal("200.00"), "amount_to": Decimal("300.00"), "unit": "h", "description": "$1 zł / h - $2 zł / h"},
            {"article": "Serwis", "name": "Nieuzasadnione wezwanie serwisowe", "amount_from": Decimal("280.00"), "amount_to": None, "unit": "wizyta", "description": "$1 zł (plus transport)"},
        ],
    },
]


async def seed_konfiguracja(db: AsyncSession, art_by_name):
    """Konfiguracja zestawów usług do wydruku — jak gdyby klient ustawił w Ustawieniach.

    - Upsert grup presetów po nazwie (nie duplikuje istniejących default z main.py —
      przejmuje flagę is_default: stare defaulty tracą flagę na rzecz nowych).
    - Szablony idempotentne po (preset_id, name), z additional_service_id (bez default_price).
    """
    from settings.models import FeePresetGroup, ServiceFeeTemplate

    created_groups = 0
    created_templates = 0

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
                # Idempotent update: nadpisz wszystkie pola (KISS redesign)
                existing_obj.sort_order = idx
                existing_obj.additional_service_id = article.id if article else existing_obj.additional_service_id
                existing_obj.name = tpl["name"]
                existing_obj.amount_from = tpl["amount_from"]
                existing_obj.amount_to = tpl["amount_to"]
                existing_obj.description = tpl["description"]
                existing_obj.is_active = True
                existing_obj.contract_type = zestaw["contract_type"]
                tpl_obj = existing_obj
            else:
                tpl_obj = ServiceFeeTemplate(
                    company_id=1,
                    preset_id=group.id,
                    contract_type=zestaw["contract_type"],
                    sort_order=idx,
                    additional_service_id=article.id if article else None,
                    name=tpl["name"],
                    amount_from=tpl["amount_from"],
                    amount_to=tpl["amount_to"],
                    description=tpl["description"],
                    is_active=True,
                )
                db.add(tpl_obj)
                await db.flush()
                created_templates += 1

    await db.commit()
    print(f"  Zestawy usług: {created_groups} nowych grup, {created_templates} szablonów")


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


async def seed_article_rate_presets(db: AsyncSession, art_by_name: dict, rt_by_name: dict = None):
    """RAO-P1-001: Predefiniowane cenniki kaskadowe per maszyna z CENNIKI_KASKADOWE."""
    from settings.models import MachineRatePreset, MachineRatePresetItem
    from sqlalchemy import select

    # RAO-P2-071: dynamiczne rate_type_id (hardcoded 5 był błędny — ID zależy od stanu DB)
    rt_dniowy = None
    if rt_by_name:
        rt_dniowy = rt_by_name.get("Stawka dniowa")
    if not rt_dniowy:
        # Fallback: znajdź po nazwie w DB
        from settings.models import RateType
        result = await db.execute(
            select(RateType).where(RateType.name == "Stawka dniowa").limit(1)
        )
        rt_dniowy = result.scalar_one_or_none()
    rt_dniowy_id = rt_dniowy.id if rt_dniowy else None

    created_presets = 0
    created_items = 0

    for machine_name, cennik in CENNIKI_KASKADOWE.items():
        article = art_by_name.get(machine_name)
        if not article:
            print(f"  [SKIP] {machine_name} — brak w art_by_name (demo maszyna nie istnieje)")
            continue

        # Sprawdź czy preset już istnieje (idempotentny)
        existing = await db.execute(
            select(MachineRatePreset).where(
                MachineRatePreset.machine_id == article.id,
                MachineRatePreset.name == "Standard"
            )
        )
        if existing.scalar_one_or_none():
            print(f"  [SKIP] {machine_name} — preset 'Standard' już istnieje")
            continue

        # Utwórz preset
        preset = MachineRatePreset(
            company_id=1,
            machine_id=article.id,
            name="Standard",
            description="Cennik kaskadowy standardowy (1-3 dni, 4-16 dni, powyżej 16 dni)",
            is_default=True,
            sort_order=0,
        )
        db.add(preset)
        await db.flush()
        created_presets += 1

        # Dodaj warunki (items)
        for idx, warunek in enumerate(cennik["warunki"], start=1):
            item = MachineRatePresetItem(
                preset_id=preset.id,
                rate_type_id=rt_dniowy_id,  # RAO-P2-071: dynamic ID (nie hardcoded)
                description=warunek["description"],
                rate1=warunek["rate1"],
                rate2=warunek["rate2"],
                billing_label=warunek["billing_label"],
                period_count=warunek["period_count"],
                minimum=warunek["minimum"],
                sort_order=idx,
            )
            db.add(item)
            created_items += 1

    await db.commit()
    print(f"  Cenniki kaskadowe: {created_presets} presetów, {created_items} warunków")
    return created_presets


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
            # RAO-P2-071 fix: sprawdzaj postal_code_id (nie city) — city może być
            # ustawione z pierwszego seeda, ale postal_code_id NULL jeśli postal_codes
            # był pusty w momencie tworzenia umowy.
            if not contract.postal_code_id and pna_id:
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
                machine_id=pos_data.get("machine_id"),
                service_id=pos_data.get("service_id"),
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

            # Warunki — RAO-P0-048: wyliczamy period_from/period_to kaskadowo
            sorted_conds = sorted(
                pos_data["conditions"],
                key=lambda c: (c["period_count"] is None, c["period_count"] or 0)
            )
            current_end = 0
            for i, cond_data in enumerate(sorted_conds):
                pc = cond_data["period_count"]
                has_rate1 = cond_data.get("rate1") is not None and cond_data["rate1"] > 0
                has_rate2 = cond_data.get("rate2") is not None and cond_data["rate2"] > 0

                next_pc = None
                for j in range(i + 1, len(sorted_conds)):
                    npc = sorted_conds[j]["period_count"]
                    if npc is not None:
                        next_pc = npc
                        break

                if has_rate1 and pc is not None:
                    period_from_r1 = current_end + 1
                    period_to_r1 = pc
                    current_end = pc
                    cond = PositionCondition(
                        position_id=pos.id,
                        rate1=cond_data["rate1"],
                        rate2=None,
                        period_count=pc,
                        period_from=period_from_r1,
                        period_to=period_to_r1,
                        billing_label=cond_data["billing_label"],
                    )
                    db.add(cond)
                    created_conditions += 1

                if has_rate2:
                    r2_from = (pc + 1) if has_rate1 and pc is not None else (current_end + 1)
                    r2_to = (next_pc - 1) if next_pc is not None else None
                    if r2_to is None or r2_from <= r2_to:
                        cond = PositionCondition(
                            position_id=pos.id,
                            rate1=None,
                            rate2=cond_data["rate2"],
                            period_count=None,
                            period_from=r2_from,
                            period_to=r2_to,
                            billing_label=cond_data["billing_label"],
                        )
                        db.add(cond)
                        created_conditions += 1
                        if r2_to is not None:
                            current_end = r2_to

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
                additional_service_id=fee_data.get("additional_service_id"),  # P1-120
                name=fee_data["name"],
                amount_from=fee_data["amount_from"],
                amount_to=fee_data["amount_to"],
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


# Rezerwacje demo — RAO-P2-071: dla pokazania kalendarza
REZERWACJE_DEMO = [
    # Aktywne rezerwacje (confirmed) — różne maszyny, różne kontrahenci
    {"article": "Koparka gąsienicowa JCB 8035", "contractor": "Bud-Plus Sp. z o.o.",
     "reserved_from": date.today() + timedelta(days=5),
     "reserved_to": date.today() + timedelta(days=12),
     "note": "Rezerwacja na budowę Mokotów"},
    {"article": "Ładowarka teleskopowa Manuscop 6.36", "contractor": "Invest S.A.",
     "reserved_from": date.today() + timedelta(days=3),
     "reserved_to": date.today() + timedelta(days=10),
     "note": "Kontrakt Q3 2026"},
    {"article": "Podnośnik koszowy Haulotte HA16PX", "contractor": None,
     "reserved_from": date.today() + timedelta(days=14),
     "reserved_to": date.today() + timedelta(days=18),
     "note": "Serwis planowany"},
    {"article": "Spychar Wirtgen W100CFi", "contractor": "Terra-Masz Budownictwo",
     "reserved_from": date.today() + timedelta(days=20),
     "reserved_to": date.today() + timedelta(days=35),
     "note": "Frezowanie asfaltu A2"},
    {"article": "Zagęszczarka Ammann APF 15/50", "contractor": None,
     "reserved_from": date.today() + timedelta(days=2),
     "reserved_to": date.today() + timedelta(days=4),
     "note": "Test maszyny"},
    # Przeszłe rezerwacje (archiwalne)
    {"article": "Koparka gąsienicowa JCB 8035", "contractor": "Wod-Bud Sp. z o.o.",
     "reserved_from": date.today() - timedelta(days=30),
     "reserved_to": date.today() - timedelta(days=20),
     "note": "Zakończona rezerwacja"},
    {"article": "Ładowarka teleskopowa Manuscop 6.36", "contractor": "Fundament Sp. z o.o.",
     "reserved_from": date.today() - timedelta(days=15),
     "reserved_to": date.today() - timedelta(days=5),
     "note": "Zakończona rezerwacja"},
    # Konflikt z aktywną umową (dla demo modala konfliktu)
    {"article": "Podnośnik koszowy Haulotte HA16PX", "contractor": "Eko-Bud Nowoczesne Budownictwo",
     "reserved_from": date.today() + timedelta(days=7),
     "reserved_to": date.today() + timedelta(days=14),
     "note": "Oczekuje na potwierdzenie"},
]


async def seed_rezerwacje(db: AsyncSession, art_by_name: dict, con_by_name: dict):
    """RAO-P2-071: Rezerwacje maszyn demo — dla pokazania kalendarza."""
    from reservations.models import MachineReservation
    created = 0
    for r in REZERWACJE_DEMO:
        article = art_by_name.get(r["article"])
        if not article:
            print(f"  [SKIP] {r['article']} — brak w art_by_name")
            continue
        contractor = None
        if r["contractor"]:
            contractor = con_by_name.get(r["contractor"])
            if not contractor:
                print(f"  [SKIP] kontrahent {r['contractor']} — brak")
                continue
        # Idempotent: sprawdź po (machine_id, reserved_from, reserved_to, note)
        existing = await db.execute(
            select(MachineReservation).where(
                MachineReservation.machine_id == article.id,
                MachineReservation.reserved_from == r["reserved_from"],
                MachineReservation.reserved_to == r["reserved_to"],
                MachineReservation.note == r["note"],
            )
        )
        if existing.scalar_one_or_none():
            continue
        reservation = MachineReservation(
            machine_id=article.id,
            contractor_id=contractor.id if contractor else None,
            reserved_from=r["reserved_from"],
            reserved_to=r["reserved_to"],
            note=r["note"],
            created_by=1,  # admin
        )
        db.add(reservation)
        created += 1
    await db.commit()
    print(f"  Rezerwacje: {created} nowych")
    return created


async def main():
    print("=" * 60)
    print("RAO-P2-061/068: Demo data seeding")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        print("\n[1/9] Kategorie...")
        await seed_kategorie(db)

        print("\n[2/9] Maszyny + usługi dodatkowe...")
        art_by_name = await seed_artykuly(db)

        print("\n[2.5/9] Usługi zwykłe (P1-115)...")
        svc_by_name = await seed_uslugi_zwykle(db)

        print("\n[3/9] Kontrahenci...")
        con_by_name = await seed_kontrahenci(db)

        print("\n[4/9] Handlowcy...")
        sp_by_name = await seed_handlowcy(db)

        print("\n[5/9] Oddziały...")
        br_by_name = await seed_oddzialy(db)

        print("\n[5.5/9] Użytkownicy demo (admin/admin123)...")
        await seed_users(db, br_by_name)

        print("\n[6/9] Rate types (6 typów — jak w starej aplikacji)...")
        rt_by_name = await seed_rate_types(db)

        print("\n[7/9] Konfiguracja firmy (NIP, konto, header_text)...")
        await seed_company(db)

        print("\n[7.1/9] Integracja Fakturownia (bootstrap z env)...")
        from integrations.fakturownia.service import get_or_create_settings
        fa_settings = await get_or_create_settings(db)
        print(f"  FA: enabled={fa_settings.enabled}, domain={fa_settings.domain_subdomain}")

        print("\n[7.5/9] Cenniki kaskadowe per maszyna (RAO-P1-001)...")
        await seed_article_rate_presets(db, art_by_name, rt_by_name)

        print("\n[8/9] Konfiguracja zestawów usług (4 presety)...")
        await seed_konfiguracja(db, art_by_name)

        print("\n[9/9] Umowy + pozycje + warunki kaskadowe + usługi + rozliczenia...")
        contracts_data = generate_contracts(con_by_name, sp_by_name, br_by_name, art_by_name, rt_by_name, svc_by_name)
        await seed_umowy(db, contracts_data, art_by_name)

        print("\n[10/10] Rezerwacje maszyn demo (RAO-P2-071)...")
        await seed_rezerwacje(db, art_by_name, con_by_name)

    print("\n" + "=" * 60)
    print("DONE — demo data seeded")
    print("=" * 60)
    print("\nNastępny krok: wystaw faktury FA dla rozliczonych umów")
    print("(uruchom: python seed_fa_invoices.py)")


if __name__ == "__main__":
    asyncio.run(main())
