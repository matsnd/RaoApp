# 04 — Business Logic — Algorytmy (Python pseudocode)

> **INSTRUKCJA DLA AGENTA:** Implementuj te algorytmy dokładnie jak opisane.
> Są to bezpośrednie tłumaczenia logiki z WinForms C# na Python.

## 1. Generowanie numeru umowy

```python
async def generate_contract_number(
    db: AsyncSession,
    contract_type: Literal["S", "U"],
    branch_id: int | None = None
) -> tuple[str, int]:
    """
    Źródło w WinForms: FormU4.cs → generowanie numeru przy nowej umowie.

    Logika:
    1. Pobierz `numeracja` z tabeli `company` (id=1)
    2. Pobierz `max(auto_number)` z tabeli `contracts`
    3. new_auto = max(numeracja, max_auto) + 1
    4. Jeśli branch_id wskazuje na oddział GDAŃSK (case-insensitive) → suffix = "G"
    5. Format: "{type}{new_auto:03d}/{year}{suffix}"
       - type="S" → umowa najmu
       - type="U" → umowa usługi
    6. Zwróć (numer_str, new_auto)

    Przykład: S001/2026, S002/2026G (Gdańsk), U003/2026
    """
    result = await db.execute(
        select(Company.numbering_start).where(Company.id == 1)
    )
    start = result.scalar() or 1

    result = await db.execute(select(func.max(Contract.auto_number)))
    max_auto = result.scalar() or 0

    new_auto = max(start, max_auto) + 1
    year = datetime.now().year

    suffix = ""
    if branch_id:
        branch_result = await db.execute(select(Branch.name).where(Branch.id == branch_id))
        branch_name = branch_result.scalar_one_or_none()
        if branch_name and branch_name.upper() == "GDAŃSK":
            suffix = "G"

    number = f"{contract_type}{new_auto:03d}/{year}{suffix}"

    return number, new_auto
```

## 2. Kalkulacja wartości umowy

```python
async def calculate_position_value(
    rental_days: int | None,
    billing_frequency: str | None,
    unit_price: Decimal | None,
    quantity: int | None,
    conditions: list[dict],
    is_service: bool = False,
) -> Decimal:
    """
    Faza 2: źródłem prawdy są period_from/period_to/rate1/minimum.
    period_count/rate2 są kolumnami pochodnymi (backward compatibility).

    Dla umów najmu (S):
      - period = ceil(rental_days / dni_na_okres)
      - quantity = liczba maszyn (mnożnik)
    Dla umów usług (U):
      - period = quantity (liczba godzin)
      - quantity jest już okresem, nie mnoży się drugi raz

    Algorytm:
    1. Określ liczbę okresów (period) i pomnóż przez quantity dla S.
    2. Zastosuj globalne minimum (max z conditions.minimum).
    3. Dla każdego warunku (posortowanego po period_from):
       - start = max(period_from, 1)
       - end   = period_to lub period (dla open-ended)
       - periods = max(0, min(end, total_periods) - start + 1)
       - total += rate1 * periods
    4. Fallback do rate2/ostatniej stawki gdy brak nowych pól.
    """
    if not conditions:
        if unit_price and quantity:
            return Decimal(str(unit_price)) * int(quantity)
        return Decimal("0.00")

    if is_service:
        periods_raw = quantity or 0
    else:
        days = rental_days or 0
        if days <= 0:
            return Decimal("0.00")
        dpp = get_days_per_period(billing_frequency or "dziennie")
        periods_raw = math.ceil(days / dpp) if dpp > 0 else 0

    min_periods = max((c.get("minimum") or 0 for c in conditions), default=0)
    total_periods = max(periods_raw, min_periods)

    if total_periods <= 0:
        return Decimal("0.00")

    tiers = extract_rate_tiers(conditions)  # preferuje period_from/period_to/rate1
    total = Decimal("0.00")
    remaining = total_periods

    for start, end, rate in tiers:
        if remaining <= 0:
            break
        if start > total_periods:
            continue
        effective_end = end if end is not None else total_periods
        periods = min(effective_end, total_periods) - start + 1
        periods = max(0, periods)
        if periods > remaining:
            periods = remaining
        if periods <= 0:
            continue
        total += rate * periods
        remaining -= periods

    return total * (1 if is_service else (quantity or 1))


def get_days_per_period(billing_frequency: str) -> int:
    """Mapowanie częstotliwości rozliczania na liczbę dni/godzin."""
    mapping = {
        "dziennie": 1,
        "tygodniowo": 7,
        "dwutygodniowo": 14,
        "miesięcznie": 30,
        "godzinowo": 1,
        "jednorazowo": 1,
    }
    return mapping.get(billing_frequency, 1)
```

## 3. Generowanie opisu warunku

```python
def format_position_conditions_cascading(
    conditions: list[PositionCondition],
    contract_type: str = "S",
) -> str:
    """
    Faza 2: źródłem prawdy są period_from/period_to/rate1/minimum.
    period_count/rate2 są kolumnami pochodnymi.

    Przykłady:
    - najem (S):  "1 - 3 dni - 540,00 / doba"
    - najem (S):  "17 dni i więcej - 350,00 / doba"
    - usługa (U): "do 8 godz. - 100,00 / godz."
    - usługa (U): "8 godz. i więcej - 80,00 / godz."
    """
    if not conditions:
        return ""

    lines = []
    for cond in conditions:
        rate = cond.rate1 if cond.rate1 else cond.rate2
        if not rate or rate <= 0:
            continue

        label = cond.billing_label or ("doba" if contract_type == "S" else "godzina")
        count_unit = "godz." if "godz" in label.lower() else "dni"
        rate_unit = "godz." if "godz" in label.lower() else "doba"

        pf = cond.period_from or 1
        pt = cond.period_to
        if pt is not None:
            if pf == 0:
                text = f"do {pt} {count_unit}"
            else:
                text = f"{pf} - {pt} {count_unit}"
        else:
            text = f"{pf} {count_unit} i więcej"

        rate_str = f"{rate:.2f}".replace(".", ",")
        lines.append(f"{text} - {rate_str} / {rate_unit}")

    return "\n".join(lines)
```

## 4. Duplikacja artykułu

```python
async def duplicate_article(db: AsyncSession, article_id: int) -> int:
    """
    Źródło: procedura DuplikujArtykul2 w MariaDB.

    Algorytm:
    1. SELECT * FROM articles WHERE id = article_id
    2. INSERT nowy rekord z:
       - name = original.name + " (kopia)"
       - registration_no = NULL (nie kopiuj rejestracj.)
       - serial_no = NULL
       - created_at = now()
       - Reszta pól = kopia
    3. Return new_id
    """
    original = await db.get(Article, article_id)
    if not original:
        raise HTTPException(404, "Artykuł nie znaleziony")

    new_article = Article(
        name=f"{original.name} (kopia)",
        is_service=original.is_service,
        registration_no=None,
        serial_no=None,
        brand=original.brand,
        model=original.model,
        replacement_value=original.replacement_value,
        category_id=original.category_id,
        owner_id=original.owner_id,
        branch_id=original.branch_id,
        description=original.description,
        notes=original.notes,
        rental_days=original.rental_days,
        article_type=original.article_type,
    )
    db.add(new_article)
    await db.flush()
    return new_article.id
```

## 5. Sprawdzenie dostępności artykułu (Zamiennik d. `sprDostepnosc` i `sprUmowyArtykulu6`)

```python
async def check_availability(
    db: AsyncSession,
    article_id: int,
    proposed_date_from: date,
    rental_days: int,
    exclude_position_id: int | None = None
) -> AvailabilityResponse:
    """
    Źródło: FormAwybor.cs (zastępuje wywołania `sprUmowyArtykulu6` oraz `sprDostepnosc`).
    Używane przy dodawaniu / edycji pozycji na umowie.

    Algorytm:
    Oblicza datę końcową: `proposed_date_to = proposed_date_from + days(rental_days)`.
    Sprawdza, czy artykuł znajduje się na jakichkolwiek innych aktywnych umowach, 
    gdzie daty "Od - Do" (obliczone z `data_dostawy` i `liczba_dni`) nakładają się
    na podany przedział `[proposed_date_from, proposed_date_to]`.
    """
    
    # 1. Oblicz planowaną datę zwrotu
    proposed_date_to = proposed_date_from + timedelta(days=rental_days)

    # 2. Szukaj konfliktów z innymi pozycjami na umowach
    # Zwróć uwagę, że daty trwania dotyczą *pozycji* (od kiedy do kiedy wynajęty konkretny artykuł)
    # Warunek Overlap: (existing_START <= proposed_END) AND (existing_END >= proposed_START)
    
    query = (
        select(ContractPosition.id, Contract.number, ContractPosition.delivery_date,
               ContractPosition.rental_days, Contractor.name)
        .join(Contract, ContractPosition.contract_id == Contract.id)
        .join(Contractor, Contract.contractor_id == Contractor.id)
        .where(
            ContractPosition.article_id == article_id,
            # Zakładamy, że delivery_date to START, a delivery_date + rental_days to END
            ContractPosition.delivery_date <= proposed_date_to,
            func.date_add(ContractPosition.delivery_date, text(f"INTERVAL ContractPosition.rental_days DAY")) >= proposed_date_from
        )
    )
    if exclude_position_id:
        query = query.where(ContractPosition.id != exclude_position_id)

    result = await db.execute(query)
    conflicts = []
    
    for row in result.all():
        existing_start = row.delivery_date
        existing_end = existing_start + timedelta(days=row.rental_days or 0)
        conflicts.append(
            ConflictingContract(
                position_id=row.id,
                contract_number=row.number,
                date_from=existing_start,
                date_to=existing_end,
                contractor_name=row.name,
            )
        )

    # 3. Zwróć wynik (True jeśli brak konfliktów)
    return AvailabilityResponse(
        is_available=len(conflicts) == 0,
        conflicting_contracts=conflicts
    )
```

## 6. GUS API (SOAP)

```python
import httpx
from lxml import etree

GUS_WSDL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnworki.svc"
GUS_ACTION_LOGIN = "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/Zaloguj"
GUS_ACTION_SEARCH = "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/DaneSzukajPodmioty"
GUS_ACTION_REPORT = "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/DanePobierzPelnyRaport"
GUS_ACTION_LOGOUT = "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/Wyloguj"

async def gus_lookup(nip: str, api_key: str) -> GusLookupResponse:
    """
    Źródło: FormK.cs → button GUS click.

    Kroki:
    1. Zaloguj(pKluczUzytkownika=api_key) → sid
    2. DaneSzukajPodmioty(pParametryWyszukiwania={Nip: nip}) → REGON, basic data
    3. DanePobierzPelnyRaport(pRegon=regon, pNazwaRaportu="BIR11OsFizycznaDzworkalnosci")
       LUB "BIR11OsPrawna" w zależnosci od typu
    4. Wyloguj(pIdentyfikatorSesji=sid)
    5. Parse XML odpowiedzi
    """
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_xml = build_soap_envelope(
            GUS_ACTION_LOGIN,
            f"<bir:Zaloguj><bir:pKluczUzytkownika>{api_key}</bir:pKluczUzytkownika></bir:Zaloguj>"
        )
        resp = await client.post(GUS_WSDL, content=login_xml,
            headers={"Content-Type": "application/soap+xml", "SOAPAction": GUS_ACTION_LOGIN})
        sid = extract_soap_value(resp.text, "ZalogujResult")

        # 2. Search
        search_xml = build_soap_envelope(
            GUS_ACTION_SEARCH,
            f"<bir:DaneSzukajPodmioty><bir:pParametryWyszukiwania>"
            f"<dat:Nip>{nip}</dat:Nip></bir:pParametryWyszukiwania></bir:DaneSzukajPodmioty>"
        )
        headers = {"Content-Type": "application/soap+xml", "sid": sid}
        resp = await client.post(GUS_WSDL, content=search_xml, headers=headers)
        data = parse_gus_response(resp.text)

        # 3. Full report (optional, for full address)
        # ... (similar pattern)

        # 4. Logout
        # ...

        return GusLookupResponse(
            name=data.get("Nazwa"),
            street=data.get("Ulica"),
            building_number=data.get("NrNieruchomosci"),
            apartment_number=data.get("NrLokalu"),
            postal_code=data.get("KodPocztowy"),
            city=data.get("Miejscowosc"),
            regon=data.get("Regon"),
            province=data.get("Wojewodztwo"),
            county=data.get("Powiat"),
            community=data.get("Gmina"),
        )
```

## 7. Reverse Geocoding (Nominatim)

```python
async def reverse_geocode(lat: Decimal, lng: Decimal) -> dict:
    """
    Źródło: FormU4.cs → pobieranie adresu po współrzędnych.

    URL: https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1
    Headers: User-Agent: RAO-App/1.0, Accept-Language: pl
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.nominatim_base_url}/reverse",
            params={"lat": str(lat), "lon": str(lng), "format": "json", "addressdetails": "1"},
            headers={"User-Agent": "RAO-App/1.0", "Accept-Language": "pl"},
            timeout=10.0
        )
        if resp.status_code == 200:
            data = resp.json()
            address = data.get("address", {})
            # Zapis do delivery_addresses
            return {
                "street": address.get("road"),
                "house_number": address.get("house_number"),
                "postal_code": address.get("postcode"),
                "hamlet": address.get("hamlet"),
                "city": address.get("city"),
                "town": address.get("town"),
                "village": address.get("village"),
                "county": address.get("county"),
                "municipality": address.get("municipality"),
                "province": address.get("state"),
                "district": address.get("suburb") or address.get("city_district"),
                "neighbourhood": address.get("neighbourhood"),
            }
        return {}
```

## 8. Konwersja decimal (locale PL)

```python
def parse_polish_decimal(text: str) -> Decimal:
    """
    Źródło: convtodec() w WinForms — konwertuje polskie formaty na Decimal.
    W WinForms: text.Replace(",", ".") → decimal.Parse()

    "5 000,50" → Decimal("5000.50")
    "5000.50"  → Decimal("5000.50")
    ""         → Decimal("0.00")
    """
    if not text or not text.strip():
        return Decimal("0.00")
    cleaned = text.replace(" ", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except Exception:
        return Decimal("0.00")


def format_polish_currency(value: Decimal) -> str:
    """Format decimal jako polską walutę: 5 000,50 zł"""
    return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " zł"
```

## 9. Kaskadowe usuwanie umowy

```python
async def delete_contract_cascade(db: AsyncSession, contract_id: int) -> None:
    """
    Źródło: Form2.cs → usuwanie umowy z context menu.

    Kolejność usuwania (FK dependencies):
    1. position_conditions (WHERE position_id IN (SELECT id FROM contract_positions WHERE contract_id=X))
    2. costs (WHERE position_id IN (...))
    3. settlements (WHERE position_id IN (...))
    4. contract_positions (WHERE contract_id=X)
    5. deliveries (WHERE contract_id=X)
    6. delivery_addresses (WHERE contract_id=X)
    7. contracts (WHERE id=X)

    UWAGA: Dzięki ON DELETE CASCADE w DDL, wystarczy usunąć contracts,
    ale explicite usuwamy dla bezpieczeństwa i zgodności z WinForms.
    """
    position_ids = select(ContractPosition.id).where(
        ContractPosition.contract_id == contract_id
    )

    # 1-3: warunki + koszty + rozliczenia
    await db.execute(delete(PositionCondition).where(
        PositionCondition.position_id.in_(position_ids)
    ))
    await db.execute(delete(Cost).where(Cost.position_id.in_(position_ids)))
    await db.execute(delete(Settlement).where(Settlement.position_id.in_(position_ids)))

    # 4: pozycje
    await db.execute(delete(ContractPosition).where(
        ContractPosition.contract_id == contract_id
    ))

    # 5-6: dostawa + adresy dostawy
    await db.execute(delete(Delivery).where(Delivery.contract_id == contract_id))
    await db.execute(delete(DeliveryAddress).where(
        DeliveryAddress.contract_id == contract_id
    ))

    # 7: umowa
    await db.execute(delete(Contract).where(Contract.id == contract_id))
    await db.commit()
```

## 10. Kaskadowe usuwanie kontrahenta

```python
async def delete_contractor_cascade(db: AsyncSession, contractor_id: int) -> None:
    """
    Źródło: Form2.cs → usuwanie kontrahenta.

    1. Sprawdź czy nie ma aktywnych umów
    2. Usuń adresy (ON DELETE CASCADE)
    3. Usuń kontrahenta
    """
    active = await db.execute(
        select(func.count()).select_from(Contract)
        .where(Contract.contractor_id == contractor_id)
        .where(Contract.date_to >= func.current_date())
    )
    if active.scalar() > 0:
        raise HTTPException(409, "Kontrahent ma aktywne umowy — nie można usunąć")

    # Adresy usunięte automatycznie przez CASCADE
    await db.execute(delete(Contractor).where(Contractor.id == contractor_id))
    await db.commit()
```

## 11. Kalkulacja "pozostało" w umowie

```python
def calculate_remaining(
    total_value: Decimal,
    prepayment_amount: Decimal,
    invoice_amount: Decimal
) -> Decimal:
    """
    Źródło: FormU4.cs → pole "Pozostało".
    remaining = total_value - prepayment_amount - invoice_amount
    """
    return (total_value or Decimal("0")) - (prepayment_amount or Decimal("0")) - (invoice_amount or Decimal("0"))
```

## 12. Linkowanie szablonów usług dodatkowych z artykułami (RAO-P1-011)

> **RAO-P2-059 (2026-07-01, done):** Model per-artikel jest **source of truth**.
> `ServiceFeeTemplate.article_id` + `default_price` = podstawowa relacja szablon↔artykuł.
> `ServiceFeeTemplateItem` (N:M, osobna tabela) jest **DEPRECATED** — 0 wierszy, 0 odwołań w kodzie,
> nie rozwijać. `ServiceFeeTemplate` z `article_id` daje ten sam rezultat relacyjnie.
> Migracja legacy `umowa2.oplaty → contract_service_fees` wykonana historycznie (migrate.py step5b,
> 3396 wierszy → archive_contract_service_fees przez P2-062). Artykuły usług id 14137-14141
> (Tankowanie, Transport, Przestój, Czyszczenie 1, Czyszczenie 2).
>
> **P1-007 fix (2026-07-05):** Demo seed (`seed_demo_data.py`) zapisuje usługi również jako
> `ContractPosition` (is_service=1, article_id → artykuł usługowy), nie tylko jako
> `ContractServiceFee`. Powód: `compute_position_revenues()` w `shared/revenue.py` zapytania
> tylko `contract_positions` JOIN `articles` — usługi zapisane wyłącznie w
> `contract_service_fees` były niewidoczne dla wszystkich endpointów statystyk
> (`/stats/positions?type=services`, `/stats/additional-fees`, `/stats/by-category`).

```python
async def resolve_article_name_for_template(
    db: AsyncSession,
    article_id: int | None,
    name_override: str | None = None
) -> str:
    """
    RAO-P1-011: Jeśli article_id ustawiony, pobierz nazwę z articles.name.
    Jeśli name_override podany, użyj go (ale snapshot z articles.name jest zachowany w polu name).

    Strategia:
    1. Jeśli article_id NULL → zwróć name_override lub pusty string
    2. Jeśli article_id ustawiony:
       - Pobierz artykuł po ID
       - Jeśli artykuł nie istnieje → raise 404
       - Zwróć articles.name (snapshot w polu name ServiceFeeTemplate)
    """
    if not article_id:
        return name_override or ""

    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    return article.name

async def sync_template_with_article(
    db: AsyncSession,
    template: ServiceFeeTemplate,
    data: ServiceFeeTemplateCreate
) -> None:
    """
    RAO-P1-011: Synchronizacja szablonu z artykułem przy tworzeniu/edycji.

    Logika:
    1. Jeśli data.article_id ustawiony:
       - Pobierz nazwę z articles.name
       - Ustaw template.name = articles.name (snapshot)
       - Ustaw template.article_id = data.article_id
       - Ustaw template.default_price = data.default_price lub article.price
    2. Jeśli data.article_id NULL:
       - Ustaw template.name = data.name (manual input)
       - Ustaw template.article_id = NULL
       - Ustaw template.default_price = data.default_price lub NULL
    """
    if data.article_id:
        name = await resolve_article_name_for_template(db, data.article_id)
        template.name = name
        template.article_id = data.article_id
        template.default_price = data.default_price
    else:
        template.name = data.name
        template.article_id = None
        template.default_price = data.default_price
```

**Migration (backend/migrate.py step5d):**
- Mapowanie service_fee_templates.name → articles.id (po nazwie, case-insensitive)
- Preferuj artykuły z is_service=1
- Jeśli artykuł nie istnieje → utwórz (is_service=1)
- Ustaw article_id i default_price
- Idempotentne: pomija rekordy z już ustawionym article_id

## 13. Auto-creowanie rozliczeń umowy (RAO-P1-012)

```python
async def auto_create_settlements_for_contract(
    db: AsyncSession,
    contract_id: int,
    position_ids: list[int]
) -> None:
    """
    RAO-P1-012: Auto-create settlement records for all contract positions.
    Wywoływane po utworzeniu umowy (POST /contracts).

    Logika:
    1. Dla każdej pozycji umowy (position_id):
       - Sprawdź czy istnieje settlement record (contract_id, position_id)
       - Jeśli nie → utwórz z cost_client=NULL, cost_company=NULL
    2. Idempotentne: pomija istniejące rekordy
    """
    for position_id in position_ids:
        existing = await db.execute(
            select(ContractSettlement).where(
                ContractSettlement.contract_id == contract_id,
                ContractSettlement.position_id == position_id,
            )
        )
        if not existing.scalar_one_or_none():
            settlement = ContractSettlement(
                contract_id=contract_id,
                position_id=position_id,
                cost_client=None,
                cost_company=None,
                notes=None,
            )
            db.add(settlement)
    await db.commit()
```

## 14. Inicjalizacja rozliczeń - 2 gałęzie (RAO-P1-012, RAO-P2-012)

### Gałąź 1: Pobierz z umowy (RAO-P1-012)

**Endpoint:** `POST /settlements/contract/{contract_id}/init`

**Logika:**
```python
async def init_contract_settlements_from_contract(
    db: AsyncSession,
    contract_id: int
):
    """
    RAO-P1-012: Inicjuj rozliczenia dla umowy (dla istniejących umów bez settlements).
    
    Oblicza cost_client automatycznie z pozycji umowy:
    - cost_client = position.unit_price * position.rental_days * position.quantity
    - cost_company = NULL (do ręcznego uzupełnienia)
    - Tworzy lub aktualizuje settlement records (upsert)
    """
    positions = await db.execute(
        select(ContractPosition).where(ContractPosition.contract_id == contract_id)
    )
    position_list = positions.scalars().all()
    
    for position in position_list:
        existing = await db.execute(
            select(ContractSettlement).where(
                ContractSettlement.contract_id == contract_id,
                ContractSettlement.position_id == position.id,
            )
        )
        existing_settlement = existing.scalar_one_or_none()
        
        # Oblicz cost_client z pozycji umowy
        cost_client = None
        if position.unit_price and position.rental_days and position.quantity:
            cost_client = float(position.unit_price * position.rental_days * position.quantity)
        
        if existing_settlement:
            existing_settlement.cost_client = cost_client
            existing_settlement.updated_at = datetime.utcnow()
        else:
            settlement = ContractSettlement(
                contract_id=contract_id,
                position_id=position.id,
                cost_client=cost_client,
                cost_company=None,
                notes=None
            )
            db.add(settlement)
    
    await db.commit()
```

### Gałąź 2: Pobierz z Fakturownia (RAO-P2-012)

**Endpoint:** `POST /settlements/contract/{contract_id}/init-from-fakturownia`

**Logika:**
```python
async def init_contract_settlements_from_fakturownia(
    db: AsyncSession,
    contract_id: int,
    user: User
):
    """
    RAO-P2-012: Inicjuj rozliczenia dla umowy z Fakturownia.
    
    Pobiera faktury z Fakturownia dla umowy (przez OID) i mapuje pozycje faktury
    na pozycje umowy przez fakturownia_product_id (1:N mapping).
    
    RAO-P2-012: Również pobiera usługi dodatkowe (contract_service_fees) z Fakturownia.
    
    Logika mapowania:
    - Pobiera faktury z Fakturownia przez integrations/fakturownia/service
    - Dla pozycji umowy: sprawdza czy są artykuły RAO ze zmapowanym fakturownia_product_id
      Jeśli artykuł jest na umowie → tworzy/aktualizuje settlement z cost_client z faktury
    - Dla usług dodatkowych: sprawdza czy service_fee_templates mają article_id z fakturownia_product_id
      Jeśli artykuł jest zmapowany → tworzy/aktualizuje settlement z service_fee_id
    - Semantyka 1:N: jeśli produkt FA jest przypisany do wielu artykułów RAO,
      każdy artykuł na umowie dostaje pełną wartość z faktury (multiplikacja OK)
    """
    from integrations.fakturownia.service import fetch_invoices_for_contract
    from articles.models import Article
    from contracts.models import ContractServiceFee
    from settings.models import ServiceFeeTemplate
    
    # Pobierz faktury z Fakturownia
    try:
        invoices = await fetch_invoices_for_contract(db, contract_id, user)
    except HTTPException as e:
        if e.status_code == 422:
            raise HTTPException(
                status_code=422, 
                detail="Umowa nie posiada numeru OID (zamówienie Fakturownia). Wpisz OID w polu 'OID (zamówienie Fakturownia)' przed pobraniem."
            )
        raise
    
    if not invoices:
        raise HTTPException(status_code=404, detail="Brak faktur w Fakturownia dla tej umowy")
    
    # Pobierz pozycje umowy z artykułami (dla mapowania)
    positions = await db.execute(
        select(ContractPosition, Article)
        .join(Article, ContractPosition.article_id == Article.id)
        .where(ContractPosition.contract_id == contract_id)
    )
    position_articles = positions.all()
    
    # Map: position_id -> (position, article)
    pos_to_article = {pa[0].id: (pa[0], pa[1]) for pa in position_articles}
    
    # Map: fakturownia_product_id -> list[position_id]
    pid_to_positions = {}
    for pos, art in pos_to_article.values():
        if art.fakturownia_product_id:
            pid_to_positions.setdefault(art.fakturownia_product_id, []).append(pos.id)
    
    # Pobierz usługi dodatkowe umowy z szablonami (dla mapowania)
    service_fees = await db.execute(
        select(ContractServiceFee, ServiceFeeTemplate)
        .join(ServiceFeeTemplate, ContractServiceFee.name == ServiceFeeTemplate.name)
        .where(ContractServiceFee.contract_id == contract_id)
    )
    fee_templates = service_fees.all()
    
    # Map: service_fee_id -> (fee, template)
    fee_to_template = {ft[0].id: (ft[0], ft[1]) for ft in fee_templates}
    
    # Map: fakturownia_product_id -> list[service_fee_id]
    pid_to_service_fees = {}
    for fee, template in fee_to_template.values():
        if template.article_id:
            article_result = await db.execute(select(Article).where(Article.id == template.article_id))
            article = article_result.scalar_one_or_none()
            if article and article.fakturownia_product_id:
                pid_to_service_fees.setdefault(article.fakturownia_product_id, []).append(fee.id)
    
    # Przetwórz faktury i utwórz/aktualizuj settlements dla pozycji
    for invoice in invoices:
        for line in invoice.lines:
            pid = line.fakturownia_product_id
            position_ids = pid_to_positions.get(pid, [])
            
            if not position_ids:
                continue  # Brak pozycji umowy z tym produktem FA
            
            # Semantyka 1:N: każda pozycja umowy dostaje pełną wartość z faktury
            cost_client = float(line.total_net)
            
            for position_id in position_ids:
                existing = await db.execute(
                    select(ContractSettlement).where(
                        ContractSettlement.contract_id == contract_id,
                        ContractSettlement.position_id == position_id,
                    )
                )
                existing_settlement = existing.scalar_one_or_none()
                
                if existing_settlement:
                    existing_settlement.cost_client = cost_client
                    existing_settlement.updated_at = datetime.utcnow()
                else:
                    settlement = ContractSettlement(
                        contract_id=contract_id,
                        position_id=position_id,
                        service_fee_id=None,
                        cost_client=cost_client,
                        cost_company=None,
                        notes=f"Pobrano z faktury {line.invoice_number}"
                    )
                    db.add(settlement)
    
    # Przetwórz faktury i utwórz/aktualizuj settlements dla usług dodatkowych
    for invoice in invoices:
        for line in invoice.lines:
            pid = line.fakturownia_product_id
            service_fee_ids = pid_to_service_fees.get(pid, [])
            
            if not service_fee_ids:
                continue  # Brak usług dodatkowych z tym produktem FA
            
            # Semantyka 1:N: każda usługa dodatkowa dostaje pełną wartość z faktury
            cost_client = float(line.total_net)
            
            for service_fee_id in service_fee_ids:
                existing = await db.execute(
                    select(ContractSettlement).where(
                        ContractSettlement.contract_id == contract_id,
                        ContractSettlement.service_fee_id == service_fee_id,
                    )
                )
                existing_settlement = existing.scalar_one_or_none()
                
                if existing_settlement:
                    existing_settlement.cost_client = cost_client
                    existing_settlement.updated_at = datetime.utcnow()
                else:
                    settlement = ContractSettlement(
                        contract_id=contract_id,
                        position_id=None,
                        service_fee_id=service_fee_id,
                        cost_client=cost_client,
                        cost_company=None,
                        notes=f"Pobrano z faktury {line.invoice_number}"
                    )
                    db.add(settlement)
    
    await db.commit()
```

### Frontend - logika dezaktywacji guzika Fakturownia

**Computed property w ContractFormView.vue:**
```typescript
const fakturowniaConfigured = computed(() => {
  const s = fakturowniaStore.settings
  return s && s.enabled && s.domain_subdomain && s.api_token_preview
})
```

**Guzik "Pobierz z Fakturownia" jest nieaktywny jeśli:**
- Fakturownia nie jest skonfigurowana (brak enabled, domain_subdomain lub api_token_preview)
- Tooltip: "Fakturownia nie jest skonfigurowana (Ustawienia → Fakturownia)"

**Pobieranie ustawień w onMounted:**
```typescript
onMounted(async () => {
  await Promise.all([
    settingsStore.fetchSalespeople(),
    settingsStore.fetchBranches(),
    settingsStore.fetchRateTypes(),
    fakturowniaStore.fetchSettings(),  // RAO-P2-012
  ])
  // ...
})
```

## 15. Kopiowanie szablonów usług dodatkowych do umowy

```python
async def copy_service_fee_templates_to_contract(
    db: AsyncSession,
    contract_id: int,
    contract_type: Literal["S", "U"]
) -> None:
    """
    Wywoływane ZAWSZE po utworzeniu nowej umowy (POST /contracts).
    Źródło w WinForms: FormU4.cs linia 1868/1903 — tbxuslugi.Text = uslugi1/2 z firma.

    Logika:
    1. Pobierz wszystkie aktywne szablony dla (company_id=1, contract_type)
       posortowane po sort_order
    2. Dla każdego szablonu utwórz wiersz w contract_service_fees
    3. Jeśli brak szablonów — OK, umowa powstaje bez usług dodatkowych

    UWAGA: Jeśli umowa już ma usługi (np. PUT /reset) — najpierw usuń wszystkie.
    """
    # Usuń istniejące (dla reset)
    await db.execute(
        delete(ContractServiceFee).where(ContractServiceFee.contract_id == contract_id)
    )
    # Pobierz szablony
    result = await db.execute(
        select(ServiceFeeTemplate)
        .where(
            ServiceFeeTemplate.company_id == 1,
            ServiceFeeTemplate.contract_type == contract_type,
        )
        .order_by(ServiceFeeTemplate.sort_order)
    )
    for t in result.scalars():
        db.add(ContractServiceFee(
            contract_id=contract_id,
            sort_order=t.sort_order,
            name=t.name,
            amount_from=t.amount_from,
            amount_to=t.amount_to,
            unit=t.unit,
            description=t.description,
            is_active=t.is_active,
        ))
    await db.commit()


"""
UWAGA - różnice między typem S (najmu) a U (usługi) wg RAO-P1-004:
- Umowa Najmu (typ S): klient sam obsługuje maszynę, więc płaci za transport/tankowanie/czyszczenie.
  Szablon `contract.html` zawiera sekcję "Cennik usług dodatkowych" (Inne usługi).
- Umowa Usługi (typ U): Toolsmart wykonuje pracę z operatorem, koszty operacyjne są wewnętrzne.
  Szablon `contract_u.html` NIE zawiera sekcji "Cennik usług dodatkowych".
  Funkcja `copy_service_fee_templates_to_contract` może nadal kopiować usługi do bazy dla typu U,
  ale nie są one wyświetlane w PDF (szablon contract_u.html usunął sekcję FEES).
"""

## Seed domyślnych usług dodatkowych dla umów najmu (RAO-P2-001)

**Cel:** Zautomatyzować dodawanie domyślnych usług dodatkowych do nowych umów najmu (typ S) zgodnie z wymaganiami klienta.

**Lista i kolejność usług (wg klienta):**
1. Transport: 500.00 zł / dostawa (500.00 zł odbiór)
2. Czyszczenie maszyny po wynajmie (zabrudzenia drobne): 150.00 zł - 400.00 zł
3. Czyszczenie maszyny po wynajmie (zabrudzenia trudnościeralne): 400.00 zł - 1500.00 zł
4. Usługa tankowania: 200.00 zł (plus koszt paliwa)
5. Ponadnormatywny przestój transportu: 200.00 zł / h - 300.00 zł / h
6. Nieuzasadnione wezwanie serwisowe: 280.00 zł (plus transport)

**Implementacja:**
- Seed w `backend/main.py::startup_migrations` tworzy `FeePresetGroup` z `contract_type='S'` i `is_default=True`
- Dodaje 6 `ServiceFeeTemplate` rekordów z powyższymi wartościami i kolejnością
- Seed jest idempotentny (sprawdza czy preset istnieje przed utworzeniem)
- Przy tworzeniu nowej umowy typu S, funkcja `copy_fee_templates` automatycznie kopiuje te usługi

**Użycie:**
- Nowa umowa najmu (typ S) → automatycznie ma 6 usług dodatkowych
- Klient może modyfikować/usuwać/usuwać konkretne usługi w formularzu umowy
- Można zresetować do domyślnych przez `POST /contracts/{id}/service-fees/reset`

## Formatowanie warunków kaskadowych rozliczenia (RAO-P1-008)

```python
def format_position_conditions_cascading(conditions: list[PositionCondition]) -> str:
    """Buduje opis kaskadowych warunków rozliczenia jak w starej aplikacji WinForms.

    Przykład wyjścia (3 warunki):
      1 - 3 dni - 540,00 / doba
      4 - 16 dni - 410,00 / doba
      powyżej 16 dni - 350,00 / doba

    Algorytm:
    1. Sortuj warunki rosnąco po period_count (NULL na końcu)
    2. Dla każdego warunku z period_count i rate1:
       - Oblicz zakres: (prev_period + 1) do period_count
       - Formatuj: "X - Y dni - kwota / label"
       - Użyj polskiego formatu kwoty (przecinek dziesiętny)
    3. Dla warunku z rate2 (NULL period_count):
       - Formatuj: "powyżej X dni - kwota / label"
    """
    if not conditions:
        return ""

    sorted_conds = sorted(
        conditions,
        key=lambda c: (c.period_count is None, c.period_count or 0)
    )
    lines = []
    prev_period = 0
    for i, c in enumerate(sorted_conds):
        label = c.billing_label or 'doba'
        if c.period_count is not None and c.rate1 is not None:
            start = prev_period + 1
            end = c.period_count
            if start == end:
                range_text = f"{start} {label}"
            else:
                range_text = f"{start} - {end} dni"
            rate_text = f"{c.rate1:.2f}".replace('.', ',')
            lines.append(f"{range_text} - {rate_text} / {label}")
            prev_period = c.period_count
        elif c.rate2 is not None and prev_period > 0:
            rate_text = f"{c.rate2:.2f}".replace('.', ',')
            lines.append(f"powyżej {prev_period} dni - {rate_text} / {label}")
    return '\n'.join(lines)
```

**Użycie w PDF:**
- `backend/reports/service.py::build_contract_data` wywołuje `format_position_conditions_cascading(conditions)` dla każdej pozycji
- Wynik jest przekazywany do szablonu jako `conditions_text`
- Szablon używa `{{ p.conditions_text }}` z CSS `white-space: pre-line`


def generate_fees_text_for_pdf(fees: list) -> str:
    """
    Generuje tekst usług dodatkowych do wydruku PDF/raportu.
    Identyczny format jak stary umowa2.oplaty.
    Tylko aktywne (is_active=True) pozycje.
    """
    lines = []
    for f in sorted(fees, key=lambda x: x.sort_order):
        if not f.is_active:
            continue
        if f.amount_from and f.amount_to:
            kwota = f"{f.amount_from:.2f} zł - {f.amount_to:.2f} zł"
        elif f.amount_from:
            kwota = f"{f.amount_from:.2f} zł"
        else:
            kwota = ""
        unit_str = f" / {f.unit}" if f.unit else ""
        desc_str = f" ({f.description})" if f.description else ""
        line = f"- {f.name}: {kwota}{unit_str}{desc_str}".strip().rstrip(":")
        lines.append(line)
    return "\n".join(lines)
```

## 15. Statusy umowy (RAO-P2-022)

Umowa NIE posiada kolumny `status` (enum). Stan jest obliczany deterministycznie z `is_settled` + `date_to` + dziś.

### Tabela stanów

| Stan | Warunek | Kolor w liście | Dotyczy alarmów |
|------|---------|---------------|-----------------|
| `active` | `is_settled=0`, `date_to >= dziś` | biały | tak |
| `expiring` | `is_settled=0`, `0 < days_left <= 14` | żółte tło | tak |
| `overdue` | `is_settled=0`, `date_to < dziś` | czerwone tło | tak |
| `settled` | `is_settled=1`, dowolne `date_to` | szare/wyciszone | **NIE** |

### Reguły

- **Rozliczona = manualna decyzja użytkownika.** Klikając "Oznacz jako rozliczoną" w sekcji Rozliczenie umowy, ustawia się `is_settled=TRUE` i `settled_at=now()`.
- **Cofnięcie:** przycisk "Cofnij rozliczenie" → `is_settled=FALSE`, `settled_at=NULL`.
- **Lista umów:** domyślny filtr to `is_settled=false` (widok "Aktywne"). Aktywne = nie rozliczone AND date_to >= dzisiaj. Użytkownik może przełączyć na "Rozliczone" lub "Wszystkie". Zamknięte umowy (date_to < dzisiaj i is_settled=false) są dostępne w endpoint /overdue.
- **Alarmy (HomeView):** endpointy `/stats/expiring-contracts` i `/stats/overdue-contracts` **wykluczają** rozliczone (`is_settled=FALSE`).
- **Brak auto-rozliczenia:** nie ma automatycznego triggera na podstawie daty ani warunków finansowych.
- **Migracja:** wszystkie umowy migrowane ze starej bazy są automatycznie oznaczane jako `is_settled=TRUE` i `settled_at=date_to` (dane historyczne).

### API

```
PATCH /contracts/{id}/settle
Body: { "is_settled": true | false }
Response: ContractDetail
```

### Decyzja projektowa

Wybrano model `is_settled` (boolean) zamiast kolumny `status` (enum `active|settled|expired|cancelled`) ze względu na:
1. Prostotę — stan obliczany, nie przechowywany
2. Brak migracji danych przy zmianie definicji statusów
3. Jedyna "twarda" decyzja użytkownika to rozliczenie — reszta jest pochodną dat

---

## 13. Walidacja NIP (checksum)

```python
def validate_nip(nip: str) -> bool:
    """
    Walidacja polskiego NIP (10 cyfr + checksum).
    Wagi: [6, 5, 7, 2, 3, 4, 5, 6, 7]
    Suma kontrolna = (sum(wagi[i] * nip[i]) for i in 0..8) % 11
    Jeśli == nip[9] → poprawny
    """
    nip = nip.replace("-", "").replace(" ", "")
    if len(nip) != 10 or not nip.isdigit():
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(w * int(d) for w, d in zip(weights, nip[:9])) % 11
    return checksum == int(nip[9])

## 14. System prowizyjny (RAO-P1-018)

```python
async def calculate_salesperson_commission(
    db: AsyncSession,
    salesperson_id: int,
    date_from: date,
    date_to: date
) -> Decimal:
    """
    Oblicz prowizję handlowca od marży, nie od przychodu (RAO-P1-018).
    
    Stara formuła (przed RAO-P1-018):
        commission = revenue * commission_rate / 100
    
    Nowa formuła (RAO-P1-018):
        commission = margin * commission_rate / 100
        gdzie margin = SUM(cost_client - cost_company) dla umów handlowca
    
    Backward compatibility:
        - Jeśli brak danych settlement (cost_client/cost_company),
          użyj starej formuły (revenue)
        - Jeśli marża = 0 lub None, prowizja = 0
    
    Źródło danych:
        - contract_settlements (RAO-P1-012) → cost_client, cost_company
        - salespeople.commission_rate → stawka prowizji (%)
        - contracts → date_from, date_to, salesperson_id
    """
    from settlements.models import ContractSettlement
    
    # Oblicz marżę z contract_settlements
    settlement_q = await db.execute(
        select(
            func.sum(ContractSettlement.cost_client - ContractSettlement.cost_company).label("total_margin")
        )
        .join(Contract, Contract.id == ContractSettlement.contract_id)
        .where(Contract.salesperson_id == salesperson_id)
        .where(and_(Contract.date_from <= date_to, Contract.date_to >= date_from))
        .where(ContractSettlement.cost_client.isnot(None))
        .where(ContractSettlement.cost_company.isnot(None))
    )
    margin = settlement_q.scalar()
    
    # Pobierz stawkę prowizji handlowca
    sp_q = await db.execute(
        select(Salesperson.commission_rate)
        .where(Salesperson.id == salesperson_id)
    )
    commission_rate = sp_q.scalar() or Decimal(0)
    
    # Jeśli brak danych settlement, użyj revenue (backward compatibility)
    if margin is None or margin == 0:
        # Oblicz revenue ze starych danych
        revenue_q = await db.execute(
            select(func.sum(ContractPosition.unit_price * ContractPosition.quantity))
            .join(Contract, Contract.id == ContractPosition.contract_id)
            .where(Contract.salesperson_id == salesperson_id)
            .where(and_(Contract.date_from <= date_to, Contract.date_to >= date_from))
        )
        revenue = revenue_q.scalar() or Decimal(0)
        commission = (revenue * commission_rate / Decimal(100)).quantize(Decimal("0.01"))
    else:
        # Nowa formuła: prowizja od marży
        commission = (margin * commission_rate / Decimal(100)).quantize(Decimal("0.01"))

    return commission
```

---

## 13. Ekstrakcja kodów pocztowych i miast (RAO-P1-008)

```python
async def extract_postal_code_and_city(
    delivery_address: str,
    db: AsyncSession
) -> tuple[str | None, str | None]:
    """
    RAO-P1-008: Ekstrakcja kodu pocztowego i miasta z adresu dostawy.

    Logika:
    1. Enhanced regex patterns dla różnych formatów kodów pocztowych:
       - XX-XXX (standard)
       - XX XXX (spacja zamiast myślnika)
       - XXXXXX (bez separatora)
       - XX-XX-XXX (błędne formaty)

    2. Normalizacja kodu pocztowego do formatu XX-XXX

    3. Lookup miasta w tabeli postal_codes po kodzie pocztowym

    4. Jeśli brak miasta w słowniku, ekstrakcja z adresu:
       - Lista 200+ polskich miast (w tym Mazovia + okoliczne)
       - Case-insensitive matching

    5. Zwróć (postal_code, city)

    Coverage: 76% umów (postal_code OR city)
    """
    import re

    # Enhanced regex patterns
    postal_patterns = [
        re.compile(r"(\d{2}-\d{3})"),     # Standard: XX-XXX
        re.compile(r"(\d{2}\s\d{3})"),     # Space: XX XXX
        re.compile(r"(\d{6})"),            # No separator: XXXXXX
        re.compile(r"(\d{2}-\d{2}-\d{3})"), # Error: XX-XX-XXX
    ]

    # Extract postal code
    postal_code = None
    for pattern in postal_patterns:
        match = pattern.search(delivery_address)
        if match:
            postal_code = match.group(1)
            # Normalize to XX-XXX format
            if len(postal_code) == 6 and '-' not in postal_code:
                postal_code = f"{postal_code[:2]}-{postal_code[2:]}"
            elif ' ' in postal_code:
                postal_code = postal_code.replace(' ', '-')
            elif len(postal_code) == 9 and postal_code.count('-') == 2:
                # Fix XX-XX-XXX → XX-XXX
                parts = postal_code.split('-')
                postal_code = f"{parts[0]}-{parts[2]}"
            break

    # Lookup city from postal_codes
    city = None
    if postal_code:
        result = await db.execute(
            select(PostalCode.city).where(PostalCode.code == postal_code)
        )
        city = result.scalar_one_or_none()

    # If no city from postal_codes, extract from address
    if not city:
        polish_cities = [
            "Warszawa", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk", "Szczecin", "Bydgoszcz", "Lublin",
            # ... (200+ miast)
        ]
        address_lower = delivery_address.lower()
        for polish_city in polish_cities:
            if polish_city.lower() in address_lower:
                city = polish_city
                break

    # Normalize city (trim, title case)
    if city:
        city = city.strip().title()

    return postal_code, city
```

---

## 14. Auto-uzupełnianie miasta po kodzie pocztowym (RAO-P1-008)

```python
async def auto_fill_city_by_postal_code(
    postal_code: str,
    db: AsyncSession
) -> str | None:
    """
    RAO-P1-008: Auto-uzupełnianie miasta po kodzie pocztowym.

    Logika:
    1. Walidacja formatu kodu pocztowego (XX-XXX)
    2. Lookup w tabeli postal_codes
    3. Zwróć nazwę miasta lub None jeśli nie znaleziono

    Endpoint: GET /integrations/postal-codes/{code}
    """
    # Walidacja formatu
    if not re.match(r"^\d{2}-\d{3}$", postal_code):
        raise HTTPException(422, "Invalid postal code format (expected XX-XXX)")

    # Lookup w tabeli postal_codes
    result = await db.execute(
        select(PostalCode.city).where(PostalCode.code == postal_code)
    )
    city = result.scalar_one_or_none()

    return city
```

## Demo data lifecycle (RAO-P2-061 + RAO-P2-067)

**Cel:** Zapewnić spójne, realistyczne dane demo do showcase statystyk, lokalizacji i integracji Fakturownia.

**Orchestrator `migrate_all.py`:**

```bash
cd backend
python migrate_all.py --steps recreate_db,import_dump,seed_demo_data,seed_fa_invoices,verify
python migrate_all.py --list  # wyświetla dostępne kroki
```

**Kroki (idempotentne, re-run safe):**
1. `recreate_db` — DROP + CREATE database (czysty start)
2. `import_dump` — import legacy dump (jeśli dostępny)
3. `seed_demo_data` — umowy, pozycje, kontrahenci, artykuły, warunki, usługi dodatkowe, `delivery_address`
4. `seed_fa_invoices` — faktury FA (wymaga `FAKTUROWNIA_API_TOKEN` w env)
5. `verify` — sprawdź spójność (count umów, pozycji, rozliczeń, faktur FA, lokalizacji)

**Dane demo (po P2-067):**
- **Umowy:** 24 rozliczone (2024-10 → 2026-07) + 12 FA-pending (2026, nierozliczone)
- **`delivery_address`:** wszystkie umowy mają realistyczne adresy (10 miast PL z PNA: Warszawa, Gdańsk, Kraków, Wrocław, Poznań, Łódź, Lublin, Katowice, Bydgoszcz, Szczecin)
- **Faktury FA:** 31 (19 backfill + 12 FA-pending czekających na "Pobierz z Fakturowni")
- **Konfiguracja:** default service fee presets (S/U), dane firmy, warunki rozliczeń

**FA-pending flow (demo "Pobierz z Fakturowni"):**
1. `seed_demo_data.py` tworzy umowę z `is_settled=0` (brak `contract_settlements`)
2. `seed_fa_invoices.py` tworzy fakturę w FA z `oid=contract.number` (bez tworzenia settlements)
3. User w UI klika "Pobierz z Fakturowni" → sync pobiera fakturę → tworzy `contract_settlements` z `source='fakturownia'`

**Security:** `FAKTUROWNIA_API_TOKEN` czytane z env (brak hardcoded w kodzie). Brak tokenu → error z instrukcją.

**Cleanup po prezentacji:**
```bash
mariadb-dump rao_new > backup_pre_wipe.sql
sudo mariadb -e "DROP DATABASE rao_new; CREATE DATABASE rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"
# Re-run migrate.py (legacy migration od zera) lub migrate_all.py
```

## Predefiniowane cenniki kaskadowe + pełna konfiguracja (RAO-P2-068)

**Cel:** User klika maszynę i ma gotowy cennik kaskadowy (1-3 dni, 4-16 dni, powyżej 16 dni) — nie musi ręcznie wpisywać każdego warunku rozliczenia. Jak w starej aplikacji WinForms: "rozliczenie = cennik".

**CENNIKI_KASKADOWE per maszyna** (w `seed_demo_data.py`):

Każda maszyna ma 3 warunki kaskadowe:
- Warunek 1: `rate1` = stawka krótkoterminowa, `period_count=3` (1-3 dni)
- Warunek 2: `rate1` = stawka średnioterminowa, `period_count=16` (4-16 dni)
- Warunek 3: `rate2` = stawka długoterminowa, `period_count=None` (powyżej 16 dni)

| Maszyna | 1-3 dni | 4-16 dni | powyżej 16 dni |
|---------|---------|----------|----------------|
| Koparka JCB 8035 | 900 zł/doba | 750 zł/doba | 600 zł/doba |
| Ładowarka Manuscop 6.36 | 720 zł/doba | 600 zł/doba | 480 zł/doba |
| Podnośnik Haulotte HA16PX | 500 zł/doba | 420 zł/doba | 340 zł/doba |
| Spychacz Wirtgen W100CFi | 1300 zł/doba | 1100 zł/doba | 900 zł/doba |
| Zagęszczarka Ammann APF 15/50 | 180 zł/doba | 150 zł/doba | 120 zł/doba |

**STAWKA_EFEKTYWNA** (do rozliczeń): stawka średnioterminowa (4-16 dni) — typowy wynajem.

**Zestawy usług dodatkowych (6 presetów):**

| Preset | Typ | Default | Szablonów | Scenariusz |
|--------|-----|---------|-----------|------------|
| Cennik usług — najem 2026 | S | ✓ | 6 | Standardowy najem (transport, czyszczenie, tankowanie, przestój, serwis) |
| Cennik usług — usługa z operatorem 2026 | U | ✓ | 3 | Praca z operatorem (transport, operator, tankowanie) |
| Kontrakt długoterminowy (rabat) | S | – | 4 | Umowy 30+ dni (obniżone stawki) |
| Weekend / krótkoterminowy (1-3 dni) | S | – | 3 | Wynajem weekendowy (wyższy transport) |
| Kontrakt zagraniczny (export) | S | – | 4 | Umowy zagraniczne (transport międzynarodowy) |
| Usługa z operatorem — premium | U | – | 4 | Premium: operator + serwis 24/7 + paliwo w cenie |

**ServiceFeeTemplateItem** (relacja N:M preset → artykuł): 22 relacji — frontend pokazuje konkretne artykuły w pickerze presetów.

**Rate types (6 typów):**
- Stawka dniowa, godzinowa, km (istniejące)
- Stawka tygodniowa, miesięczna, jednorazowa (nowe — ułatwiają tworzenie umów)

**Konfiguracja firmy** (pełne dane w `company` table):
- NIP: 1234563218, REGON: 012345678
- Adres: ul. Przykładowa 1, 00-001 Warszawa
- Bank: PKO BP, konto: PL 12 1020 1026 0000 1234 5678 9012
- header_text do PDF: pełne dane firmy (NIP, konto, adres)
- numbering_start=1, increment_step=50
