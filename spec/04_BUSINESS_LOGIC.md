# 04 — Business Logic — Algorytmy (Python pseudocode)

> **INSTRUKCJA DLA AGENTA:** Implementuj te algorytmy dokładnie jak opisane.
> Są to bezpośrednie tłumaczenia logiki z WinForms C# na Python.

## 1. Generowanie numeru umowy

```python
async def generate_contract_number(
    db: AsyncSession,
    contract_type: Literal["S", "U"]
) -> tuple[str, int]:
    """
    Źródło w WinForms: FormU4.cs → generowanie numeru przy nowej umowie.

    Logika:
    1. Pobierz `numeracja` z tabeli `company` (id=1)
    2. Pobierz `max(auto_number)` z tabeli `contracts`
    3. new_auto = max(numeracja, max_auto) + 1
    4. Format: "{type}{new_auto:03d}/{year}"
       - type="S" → umowa najmu
       - type="U" → umowa usługi
    5. Zwróć (numer_str, new_auto)

    Przykład: S001/2026, S002/2026, U003/2026
    """
    result = await db.execute(
        select(Company.numbering_start).where(Company.id == 1)
    )
    start = result.scalar() or 1

    result = await db.execute(select(func.max(Contract.auto_number)))
    max_auto = result.scalar() or 0

    new_auto = max(start, max_auto) + 1
    year = datetime.now().year
    number = f"{contract_type}{new_auto:03d}/{year}"

    return number, new_auto
```

## 2. Kalkulacja wartości umowy

```python
async def calculate_contract_value(
    db: AsyncSession,
    contract_id: int
) -> Decimal:
    """
    Źródło w WinForms: FormU4.cs → obliczanie wartości.

    Algorytm:
    1. Pobierz wszystkie pozycje umowy
    2. Dla każdej pozycji:
       a. Pobierz warunki (position_conditions) posortowane wg period_count ASC
       b. Oblicz wartość pozycji na podstawie algorytmu rate_type
    3. Zwróć sumę wartości pozycji

    Wartość pozycji = f(rental_days, billing_frequency, conditions)
    """
    positions = await db.execute(
        select(ContractPosition)
        .where(ContractPosition.contract_id == contract_id)
    )

    total = Decimal("0.00")
    for pos in positions.scalars():
        value = await calculate_position_value(db, pos)
        total += value

    # Zapisz nową wartość
    await db.execute(
        update(Contract)
        .where(Contract.id == contract_id)
        .values(total_value=total, updated_at=func.now())
    )
    return total


async def calculate_position_value(
    db: AsyncSession,
    position: ContractPosition
) -> Decimal:
    """
    Algorytm obliczenia wartości jednej pozycji.

    Typy stawek (rate_type_id):
    - 1: Stawka jednorazowa (CENA × ILOSC)
    - 2: Stawka z progami (obliczenie progowe)
    - 3: Stawka prosta (OPLATA1 × ilość_okresów)
    - (4: nieużywany - excluded w WHERE)

    Obliczenie progowe (typ 2):
    Warunki posortowane wg period_count ASC:
    Warunek 1: { period_count: 5, rate1: 5000, billing: "tygodniowo" }
    Warunek 2: { period_count: 99, rate1: 4000, billing: "tygodniowo" }

    Przykład: rental_days = 45, billing = tygodniowo (7 dni/okres)
    - Liczba tygodni = ceil(45 / 7) = 7
    - Warunek 1: 5 tygodni × 5000 = 25000
    - Warunek 2: 2 tygodnie × 4000 = 8000
    - Suma = 33000
    """
    conditions = await db.execute(
        select(PositionCondition)
        .where(PositionCondition.position_id == position.id)
        .order_by(PositionCondition.period_count.asc())
    )
    conds = conditions.scalars().all()

    if not conds:
        # Brak warunków → cena × ilość
        if position.unit_price and position.quantity:
            return position.unit_price * position.quantity
        return Decimal("0.00")

    # Oblicz liczbę okresów
    days = position.rental_days or 0
    freq = position.billing_frequency or "dziennie"
    days_per_period = get_days_per_period(freq)
    total_periods = math.ceil(days / days_per_period) if days_per_period > 0 else 0

    # Zaaplikuj minimum (z pierwszego warunku)
    min_periods = conds[0].minimum or 0
    if total_periods < min_periods:
        total_periods = min_periods

    # Oblicz wartość progową
    total_value = Decimal("0.00")
    remaining = total_periods

    for i, cond in enumerate(conds):
        if remaining <= 0:
            break

        # Ile okresów w tym progu
        if i == 0:
            periods_in_tier = min(remaining, cond.period_count or remaining)
        else:
            prev_count = conds[i-1].period_count or 0
            periods_in_tier = min(remaining, (cond.period_count or 999) - prev_count)

        rate = cond.rate1 or Decimal("0.00")
        total_value += rate * periods_in_tier
        remaining -= periods_in_tier

    return total_value


def get_days_per_period(billing_frequency: str) -> int:
    """Mapowanie częstotliwości rozliczania na liczbę dni."""
    mapping = {
        "dziennie": 1,
        "tygodniowo": 7,
        "dwutygodniowo": 14,
        "miesięcznie": 30,
        "godzinowo": 1,  # special case
        "jednorazowo": 1,
    }
    return mapping.get(billing_frequency, 1)
```

## 3. Generowanie opisu warunku

```python
def generate_condition_description(
    period_count: int,
    rate1: Decimal,
    rate2: Decimal | None,
    billing_frequency: str,
    billing_unit: str,
    is_first: bool
) -> str:
    """
    Źródło: FormW.cs → budowanie tekstu warunku (tbxwarunek).

    Przykłady wygenerowanych opisów:
    - "stawka 5000,00 zł/tyg. do 5 tygodni"
    - "stawka 4000,00 zł/tyg. powyżej 5 tygodni"
    - "stawka 100,00 zł/dzień do 30 dni, min. 5 dni"
    """
    unit_map = {
        "tydzień": "tyg.",
        "doba": "dzień",
        "godzina": "godz.",
        "miesiąc": "mies.",
    }
    unit_short = unit_map.get(billing_unit, billing_unit)

    rate_str = f"{rate1:,.2f}".replace(",", " ").replace(".", ",")
    text = f"stawka {rate_str} zł/{unit_short}"

    if is_first:
        text += f" do {period_count} {get_period_label(period_count, billing_unit)}"
    else:
        text += f" powyżej {period_count} {get_period_label(period_count, billing_unit)}"

    if rate2 and rate2 > 0:
        rate2_str = f"{rate2:,.2f}".replace(",", " ").replace(".", ",")
        text += f", stawka dodatkowa {rate2_str} zł"

    return text


def get_period_label(count: int, unit: str) -> str:
    """Polska odmiana: 1 tydzień, 2-4 tygodnie, 5+ tygodni."""
    if unit in ("tydzień", "tyg."):
        if count == 1: return "tydzień"
        if 2 <= count <= 4: return "tygodnie"
        return "tygodni"
    if unit in ("doba", "dzień"):
        if count == 1: return "dzień"
        return "dni"
    if unit in ("godzina", "godz."):
        if count == 1: return "godzina"
        if 2 <= count <= 4: return "godziny"
        return "godzin"
    if unit in ("miesiąc", "mies."):
        if count == 1: return "miesiąc"
        if 2 <= count <= 4: return "miesiące"
        return "miesięcy"
    return unit
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

## 12. Walidacja NIP (checksum)

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
```
