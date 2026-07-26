# 08 — Plan migracji danych (stara baza → nowa baza)

> **INSTRUKCJA DLA AGENTA:** Wykonaj migrację w dokładnej kolejności.
> Wszystkie dane przenoszone są przez INSERT...SELECT — BEZ procedur.

---

## ⚠️ DECYZJA ARCHITEKTONICZNA: Linia odcięcia (Data Cut-off)

> **Data decyzji:** 2026-05-24
> **Decydent:** Właściciel Toolsmart Sp. z o.o.
> **Cytat:** „To nie jest bug — odcięcie linia zmigrowanych starych wadliwych danych od nowych. Kontynuuj.”

### Co to oznacza

Wszystkie dane zmigrowane z legacy WinForms (701 umów, 633 kontrahentów, 418 artykułów) są **świadomie oznaczone jako archiwum tylko-do-odczytu**. Aplikacja nie próbuje rekonstruować brakujących pól (`total_value`, `cost_company`) — zamiast tego rozróżnia dwa światy:

| Świat | Zakres | Stan danych | Liczy się do KPI? | Edytowalne? |
|-------|--------|-------------|-------------------|-------------|
| **Legacy** (pre-cutoff) | Wszystko z `migrate.py` (2026-05) | `total_value=NULL`, `is_settled=1`, `is_archival=1` | NIE | NIE (admin override) |
| **Active** (post-cutoff) | Nowe umowy/artykuły od cut-off date | Walidowane, wypełnione poprawnie | TAK | TAK |

### Stan po migracji (potwierdzenie z DB 2026-05-24)

```sql
-- Wszystkie umowy z legacy są zamknięte
SELECT is_settled, COUNT(*) FROM contracts GROUP BY is_settled;
-- → 1: 701   (100% rozliczone — by-design)

-- Wszystkie umowy z legacy nie mają total_value
SELECT COUNT(*) - SUM(CASE WHEN total_value IS NULL THEN 1 ELSE 0 END) AS not_null
FROM contracts;
-- → 0/701   (100% NULL — by-design, revenue jest w position_conditions.rate1)

-- Wszystkie artykuły z legacy są archiwalne
SELECT is_archival, COUNT(*) FROM articles GROUP BY is_archival;
-- → 1: 418   (100% archiwalne — by-design, jeśli aktywna maszyna fizyczna istnieje, wprowadź ją od zera)
```

### Wymagania na aplikację (RAO-P0-009 w BACKLOG)

Po migracji aplikacja **MUSI** zaimplementować:

1. **Mechanizm flagowania:** dodaj `is_legacy BOOLEAN` na `contracts`, `contractors`, `articles`. Wszystkie istniejące rekordy → `is_legacy=true`.
2. **Filter domyślny:** wszystkie listy (`/contracts`, `/contractors`, `/articles`) i raporty (`/stats/*`) **domyślnie** filtrują `WHERE is_legacy=false`.
3. **Toggle/banner:** użytkownik może wyłączyć filtr ("Pokaż archiwum") świadomie.
4. **Walidacja nowych:** `is_legacy=false` jako domyślna wartość przy `POST /contracts` itp. — Pydantic validator zabrania ustawiania `is_legacy=true` z UI.
5. **Walidacja `total_value`:** nowe umowy MUSZĄ mieć `total_value > 0` (auto-kalkulacja z `position_conditions.rate1 * period_count`).
6. **Read-only legacy:** edycja legacy contracts/articles zablokowana (HTTP 403 lub admin override z `?force=true`).

### Pytania otwarte (decyzje wymagane od Właściciela)

- **Cut-off date:** `2026-05-24` (dziś), `2026-06-01`, `2026-07-01`?
- **Selektywne odznaczenie maszyn:** czy fizycznie aktywne maszyny (te wciąż wynajmowane) odznaczyć z legacy automatycznie, czy wprowadzić od zera?
- **Edycja legacy:** czy admin może w razie korekty (np. nazwa kontrahenta zmieniła się prawnie)?
- **Marża historyczna:** wypełniać `cost_company` retroaktywnie czy zostawić NULL?
- **Archive offload:** po stabilizacji przenieść legacy do osobnej DB schema `rao_legacy`?

### Powiązane dokumenty

- [STRATEGIC_ROADMAP.md sekcja 1.5](../STRATEGIC_ROADMAP.md#15-fundament-architektoniczny-linia-odcięcia-data-cut-off) — kontekst biznesowy
- [BACKLOG.md RAO-P0-009](../backlog/BACKLOG.md#rao-p0-009) — task implementacyjny
- [BACKLOG.md RAO-P1-036](../backlog/BACKLOG.md#rao-p1-036) — toggle archiwalnych
- [BACKLOG.md RAO-P1-037](../backlog/BACKLOG.md#rao-p1-037) — walidacja nowych umów
- [BACKLOG.md RAO-P2-062](../backlog/BACKLOG.md#rao-p2-062) — archiwum: migracja legacy do `archive_*`

---

## RAO-P2-062 Faza 0 — Offload legacy do tabel `archive_*` (WYKONANE 2026-07-01)

> **Status:** DONE. Migracja danych wykonana skryptem `scripts/migrate_to_archive.py`.
> **Backup:** `backup_pre_archive_split.sql` (2.96 MB, mariadb-dump --single-transaction).
> **Faza 1 (backend — modele + endpointy):** TODO.

### Co zostało zrobione

1. **Backup** `rao_new` → `backup_pre_archive_split.sql` (PRZED migracją, krytyczne).
2. **Utworzono 7 tabel `archive_*`** (`CREATE TABLE IF NOT EXISTS`) w `rao_new`:
   `archive_categories`, `archive_articles`, `archive_contracts`,
   `archive_contract_positions`, `archive_position_conditions`,
   `archive_contract_service_fees`, `archive_contract_settlements`.
   Schema = mirror oryginalnych tabel; `archive_contracts` bez kolumny `is_legacy`.
   FK wewnętrzne archiwum (np. `archive_contract_positions.article_id` →
   `archive_articles.id`) + FK do współdzielonych (`contractors`, `branches`,
   `salespeople`, `rate_types`, `postal_codes`).
3. **Skopiowano legacy dane** (`INSERT IGNORE`, idempotentne):
   - `archive_categories`: 64 (wszystkie — używane przez legacy maszyny)
   - `archive_articles`: 351 (tylko maszyny z legacy pozycji)
   - `archive_contracts`: 742 (legacy umowy)
   - `archive_contract_positions`: 878
   - `archive_position_conditions`: 1274
   - `archive_contract_service_fees`: 3396
   - `archive_contract_settlements`: 1945
4. **Usunięto legacy z tabel oryginalnych** (kolejność cascade-safe, w jednej transakcji):
   `contract_settlements` → `contract_service_fees` → `position_conditions` →
   `contract_positions` → `contracts` (WHERE `is_legacy=1`).
5. **Weryfikacja COUNT** — wszystkie zaliczone (poza 3 pre-existing orphan pozycjami).

### Czego NIE zrobiono (Faza 1 — backend)

- Modele SQLAlchemy `archive_*` w `backend/archive/models.py`
- Endpointy read-only + CRUD kategorii archiwum w `backend/archive/router.py`
- `ALTER TABLE contracts DROP COLUMN is_legacy` + usunięcie z modelu
- Czyszczenie `articles` / `categories` (współdzielone/zostają — decyzja usera)
- Frontend: widok Archiwum w sidebarze

### Idempotentność

Skrypt można re-run: `CREATE TABLE IF NOT EXISTS` + `INSERT IGNORE` + `DELETE`
(no-op po pierwszym uruchomieniu — brak `is_legacy=1` wierszy). Weryfikowane:
drugi run — brak błędów, brak duplikatów, COUNT identyczny.

### Uwaga: 3 osierocone pozycje

3 wiersze w `contract_positions` (contract_id=9204) nie mają pasującego
rekordu w `contracts` (pre-existing data issue z `migrate.py`). Nie są legacy,
nie zostały zmigrowane do `archive_*` ani usunięte. Pozostają w `contract_positions`.

---

## Kolejność migracji (dependencies-first)

```
1. company (firma → company + additional_fees)
2. branches (oddzial → branches)
3. users (uzytkownik → users)
4. categories (kategoria → categories)
5. salespeople (handlowiec → salespeople)
6. rate_types (stawka → rate_types)
7. cost_types (koszt_typ → cost_types)
8. contractors (kontrahent2 → contractors)
9. contractor_addresses (adres → contractor_addresses)
10. articles (artykul3 → articles)
11. contracts (umowa2 → contracts)
12. deliveries (dostawa → deliveries)
13. delivery_addresses (adres_dostawy → delivery_addresses)
14. contract_positions (umowa_pozycja3 → contract_positions)
15. position_conditions (umowa_pozycja2_warunek → position_conditions)
16. costs (koszt → costs)
17. settlements (rozliczenie → settlements)
```

## Skrypty migracyjne

```sql
-- ============================================================
-- UWAGA: Uruchom na nowej bazie rao_new AFTER DDL z 01_DATABASE_DDL.md
-- Stara baza: rao (existing)
-- Nowa baza: rao_new
-- ============================================================

-- 1. COMPANY (firma → company)
INSERT INTO rao_new.company (
    id, name, name_short, nip, regon, postal_code, city, street,
    header_text, logo, bank_name, bank_account, numbering_start,
    increment_step, report_folder, protocol_folder, app_version
)
SELECT
    ID, NAZWA, NAZWA_KROTKA, NIP, REGON, KOD_POCZTOWY, MIEJSCOWOSC,
    ULICA_LOKAL, NAGLOWEK, LOGO, BANK, RACHUNEK, numeracja,
    INTERWAL, FOLDER, FOLDER2, wersja
FROM toolsmart_roa_fake.firma;
-- UWAGA: Uslugi1/Uslugi2 migrowane do service_fee_templates (krok 1b poniżej)

-- 1b. SERVICE FEE TEMPLATES (firma.uslugi1/2 → service_fee_templates)
-- UWAGA: Tekst "- Transport: 400zł\n- Czyszcz..." rozdzielamy na wiersze.
-- Wymaga skryptu Python (SQL nie może parsoć multiline text po liniach).
-- Uruchom: python migrator/migrate_service_fees.py

-- Skrypt migrator/migrate_service_fees.py:
```python
"""
Migracja usług dodatkowych ze starej bazy do nowej.
Parsuje firma.uslugi1/2 i umowa2.OPLATY — każda linia "-" → oddzielny wiersz
z wyciągniętymi polami: name, amount_from, amount_to, unit, description.

Wzorce (zweryfikowane na toolsmart_roa_fake):
  1. Transport: 400.00 zł dostawa / 400.00 zł odbiór  → amount=400, desc="dostawa / odbiór"
  2. Czyszcz.: 150.00 zł - 400.00 zł                 → amount_from=150, amount_to=400
  3. Ponadnorm.: 200.00 zł / h - 300.00 zł / h       → amount_from=200, to=300, unit="h"
  4. Zawiesia: 50,00 zł / doba                        → amount_from=50, unit="doba"
  5. Tankowanie: 200.00 zł (plus koszt paliwa)        → amount_from=200, desc="plus koszt paliwa"
  6. Transport: 400.00 zł                             → amount_from=400
  7. Transport: 950.00 zł - zamiana Ładowarek         → amount_from=950, desc="zamiana Ładowarek"
  8. Transport: odbiór własny                         → desc="odbiór własny" (brak kwoty)
  9. Ładowarka - wynajem 900,00 zł / doba             → brak dwukropka, kwota w środku
"""
import re
import asyncio
import aiomysql
from decimal import Decimal, InvalidOperation

OLD_DB = dict(host='localhost', user='root', password='<<OLD_DB_PASS>>',
              db='toolsmart_roa_fake', charset='utf8mb4')
NEW_DB = dict(host='localhost', user='rao_user', password='<<NEW_DB_PASS>>',
              db='rao_new', charset='utf8mb4')

# Polska kwota: "400", "400.00", "400,00", "1 000,00", "1 000.00"
_A = r'([\d]+(?:\s[\d]{3})*(?:[,.][\d]+)?)'

# Wzorce kompilowane raz
# 1. KWOTA zł [- ] OPIS_DOSTAWY / KWOTA zł [- ] odbiór
RE_DOSTAWA = re.compile(
    rf'^{_A}\s*z[łl]\s*[-–]?\s*(.{{1,30}}?)\s*/\s*{_A}\s*z[łl]\s*[-–]?\s*(odbi[oó]r\S*)',
    re.I | re.U
)
# 2. KWOTA zł / UNIT - KWOTA zł / UNIT (zakres godzinowy/dobowy)
RE_H_RANGE = re.compile(rf'^{_A}\s*z[łl]\s*/\s*(\S+)\s*[-–]\s*{_A}\s*z[łl]\s*/\s*\S+')
# 3. KWOTA zł / UNIT (stawka jednostkowa)
RE_PER_UNIT = re.compile(rf'^{_A}\s*z[łl]\s*/\s*(\S+)')
# 4. KWOTA zł - KWOTA zł (zakres bez jednostki) — drugi człon musi być liczbą
RE_RANGE = re.compile(rf'^{_A}\s*z[łl]\s*[-–]\s*{_A}\s*z[łl]')
# 5. KWOTA zł (opis w nawiasach)
RE_PARENS = re.compile(rf'^{_A}\s*z[łl]\s*\(([^)]+)\)')
# 6. KWOTA zł [opcjonalny trailing opis]
RE_SINGLE = re.compile(rf'^{_A}\s*z[łl](.*)')
# 7. Brak dwukropka, kwota w środku: "Nazwa ... KWOTA zł / UNIT"
RE_NOCOL = re.compile(rf'^(.+?)\s+{_A}\s*z[łl]\s*/\s*(\S+)\s*$')
# 8. Linie do pominięcia (nagłówki/śmieci)
RE_SKIP = re.compile(
    r'^(-zedytowane|1[-\s]*2\s*dni|powyżej\s*2|praca do \d|czas trwania|'
    r'opłata w gotówce|do \d+ godzin\s*-)',
    re.I
)

def to_decimal(s: str) -> Decimal | None:
    if not s:
        return None
    try:
        return Decimal(s.strip().replace(' ', '').replace(',', '.'))
    except InvalidOperation:
        return None

def parse_fee_line(raw: str) -> dict | None:
    """Parsuje jedną linię na {name, amount_from, amount_to, unit, description, is_active}."""
    line = raw.strip().lstrip('- ').strip()
    if not line or RE_SKIP.match(line):
        return None

    out = dict(name=line[:200], amount_from=None, amount_to=None,
               unit=None, description=None, is_active=True)

    # Rozdziel na nazwę i wartość po pierwszym dwukropku
    if ':' in line:
        idx = line.index(':')
        name_part = line[:idx].strip()
        value = line[idx + 1:].strip()
        if not name_part:
            return None
        out['name'] = name_part[:200]
    else:
        # Brak dwukropka — szukamy "TEKST KWOTA zł / UNIT"
        m = RE_NOCOL.match(line)
        if m:
            out['name']        = m.group(1).strip()[:200]
            out['amount_from'] = to_decimal(m.group(2))
            out['unit']        = m.group(3)
        # else: cały tekst zostaje jako name, bez kwoty
        return out

    if not value:
        return out  # tylko nazwa, bez wartości

    # --- Dopasowywanie wartości ---

    # Wzorzec 1: KWOTA zł dostawa / KWOTA zł odbiór (symetryczny transport)
    m = RE_DOSTAWA.match(value)
    if m:
        out['amount_from'] = to_decimal(m.group(1))
        # Kwota dostawy i odbioru jest zawsze taka sama — nie potrzeba amount_to
        out['description'] = f"{m.group(2).strip()} / {m.group(4).strip()}"
        return out

    # Wzorzec 2: KWOTA zł / h - KWOTA zł / h (zakres godzinowy)
    m = RE_H_RANGE.match(value)
    if m:
        out['amount_from'] = to_decimal(m.group(1))
        out['amount_to']   = to_decimal(m.group(3))
        out['unit']        = m.group(2)
        return out

    # Wzorzec 3: KWOTA zł / UNIT (stawka jednostkowa)
    m = RE_PER_UNIT.match(value)
    if m:
        out['amount_from'] = to_decimal(m.group(1))
        out['unit']        = m.group(2)
        return out

    # Wzorzec 4: KWOTA zł - KWOTA zł (zakres bez jednostki)
    # Sprawdź czy drugi człon to naprawdę liczba (nie "zamiana Ładowarek")
    m = RE_RANGE.match(value)
    if m and to_decimal(m.group(2)) is not None:
        out['amount_from'] = to_decimal(m.group(1))
        out['amount_to']   = to_decimal(m.group(2))
        return out

    # Wzorzec 5: KWOTA zł (opis w nawiasach)
    m = RE_PARENS.match(value)
    if m:
        out['amount_from'] = to_decimal(m.group(1))
        out['description'] = m.group(2).strip()
        return out

    # Wzorzec 6: KWOTA zł [trailing tekst]
    m = RE_SINGLE.match(value)
    if m:
        out['amount_from'] = to_decimal(m.group(1))
        trailing = m.group(2).strip().strip('-– ').strip()
        if trailing:
            out['description'] = trailing[:400]
        return out

    # Wzorzec 7: czysto tekstowy opis (brak kwoty)
    out['description'] = value[:400]
    return out


def parse_text_to_fees(text: str) -> list[dict]:
    """Rozbija cały blok tekstu na listę sparsowanych pozycji."""
    result = []
    if not text:
        return result
    sort_order = 0
    for raw in text.replace('\r\n', '\n').replace('\r', '\n').splitlines():
        fee = parse_fee_line(raw)
        if fee:
            fee['sort_order'] = sort_order
            sort_order += 1
            result.append(fee)
    return result


async def migrate():
    old = await aiomysql.connect(**OLD_DB)
    new = await aiomysql.connect(**NEW_DB)

    # 1. Szablony z firma.uslugi1 (S=najem) i uslugi2 (U=usługa)
    async with old.cursor() as cur:
        await cur.execute('SELECT uslugi1, uslugi2 FROM firma WHERE id=1')
        uslugi1, uslugi2 = await cur.fetchone()

    async with new.cursor() as cur:
        for contract_type, text in [('S', uslugi1), ('U', uslugi2)]:
            for fee in parse_text_to_fees(text):
                await cur.execute(
                    '''INSERT INTO service_fee_templates
                       (company_id, contract_type, sort_order, name,
                        amount_from, amount_to, unit, description, is_active)
                       VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (contract_type, fee['sort_order'], fee['name'],
                     fee['amount_from'], fee['amount_to'],
                     fee['unit'], fee['description'], fee['is_active'])
                )
        await new.commit()
    print('✓ service_fee_templates: OK')

    # 2. Usługi per umowa z umowa2.OPLATY → contract_service_fees
    async with old.cursor() as cur:
        await cur.execute(
            "SELECT id, OPLATY FROM umowa2 WHERE OPLATY IS NOT NULL AND TRIM(OPLATY) != ''"
        )
        rows = await cur.fetchall()

    async with new.cursor() as cur:
        for contract_id, oplaty in rows:
            for fee in parse_text_to_fees(oplaty):
                await cur.execute(
                    '''INSERT INTO contract_service_fees
                       (contract_id, sort_order, name,
                        amount_from, amount_to, unit, description, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                    (contract_id, fee['sort_order'], fee['name'],
                     fee['amount_from'], fee['amount_to'],
                     fee['unit'], fee['description'], fee['is_active'])
                )
        await new.commit()
    print(f'✓ contract_service_fees: {len(rows)} umów, OK')

    old.close()
    new.close()


if __name__ == '__main__':
    asyncio.run(migrate())
```

-- 1c. WERYFIKACJA MIGRACJI USŁUG DODATKOWYCH
-- Uruchom te selecty po wykonaniu migrate_service_fees.py
-- i porównaj z oczekiwanymi wynikami ze starej bazy.

-- [V1] Ile pozycji zostało wygenerowanych z uslugi1 (najem)?
-- Oczekiwane: tyle ile linii z "-" w firmie.uslugi1
SELECT COUNT(*) AS template_najem_count
FROM rao_new.service_fee_templates
WHERE contract_type = 'S';
-- Weryfikacja w starej bazie:
-- SELECT LENGTH(uslugi1) - LENGTH(REPLACE(uslugi1, '\n', '')) + 1 FROM toolsmart_roa_fake.firma WHERE id=1;

-- [V2] Ile pozycji zostało wygenerowanych z uslugi2 (usługi)?
SELECT COUNT(*) AS template_uslugi_count
FROM rao_new.service_fee_templates
WHERE contract_type = 'U';

-- [V3] Podgląd szablonu najem (czy nazwy się zgadzają z oryginałem)?
SELECT sort_order, name, amount_from, amount_to, unit, is_active
FROM rao_new.service_fee_templates
WHERE contract_type = 'S'
ORDER BY sort_order;
-- Porównaj ręcznie z:
-- SELECT uslugi1 FROM toolsmart_roa_fake.firma WHERE id=1;

-- [V4] Ile umów ma przeniesione usługi dodatkowe?
SELECT COUNT(DISTINCT contract_id) AS contracts_with_fees
FROM rao_new.contract_service_fees;
-- Oczekiwane: ile umów miało niepuste pole OPLATY:
-- SELECT COUNT(*) FROM toolsmart_roa_fake.umowa2 WHERE OPLATY IS NOT NULL AND OPLATY != '';

-- [V5] Czy żadna umowa nie zgubiła pozycji? (max/min/avg dla cross-check)
SELECT
    MIN(cnt) AS min_fees_per_contract,
    MAX(cnt) AS max_fees_per_contract,
    AVG(cnt) AS avg_fees_per_contract
FROM (
    SELECT contract_id, COUNT(*) AS cnt
    FROM rao_new.contract_service_fees
    GROUP BY contract_id
) sub;

-- [V6] Próbka: 3 losowe umowy — porównaj tekst oryginału z nową listą
SELECT u.id, u.OPLATY AS stary_tekst
FROM toolsmart_roa_fake.umowa2 u
WHERE u.OPLATY IS NOT NULL AND u.OPLATY != ''
ORDER BY RAND() LIMIT 3;
-- Następnie dla każdego id:
-- SELECT name FROM rao_new.contract_service_fees WHERE contract_id = <id> ORDER BY sort_order;

-- 2. BRANCHES (oddzial → branches)
INSERT INTO rao_new.branches (id, name, address, postal_code, city, street)
SELECT ID, NAZWA, ADRES, KOD_POCZTOWY, MIEJSCOWOSC, ULICA_LOKAL
FROM rao.oddzial;

-- 3. USERS (uzytkownik → users)
-- UWAGA: Stare hasła są PLAINTEXT! Trzeba je zahashować bcrypt.
-- Ten skrypt przenosi plaintext, ale aplikacja musi wymóc zmianę hasła
-- przy pierwszym logowaniu lub admin musi zresetować hasła.
INSERT INTO rao_new.users (
    id, login, password, first_name, last_name, role, branch_id, created_at
)
SELECT
    ID, LOGIN,
    CONCAT('$PLAINTEXT$', HASLO),  -- Marker: app musi wykryć i wymusić zmianę
    IMIE, NAZWISKO,
    CASE WHEN ID_GRUPY = 1 THEN 'admin' ELSE 'user' END,
    id_oddzialu,
    COALESCE(DATA, NOW())
FROM rao.uzytkownik;

-- 4. CATEGORIES (kategoria → categories)
INSERT INTO rao_new.categories (id, name, code, description)
SELECT ID, NAZWA, KOD, OPIS
FROM rao.kategoria;

-- 5. SALESPEOPLE (handlowiec → salespeople)
INSERT INTO rao_new.salespeople (id, name, phone, is_active)
SELECT ID, NAZWA, TELEFON, COALESCE(AKTYWNY, 1) = 1
FROM rao.handlowiec;

-- 6. RATE TYPES (stawka → rate_types)
INSERT INTO rao_new.rate_types (id, name, description, is_dependent)
SELECT ID, NAZWA, OPIS, COALESCE(ZALEZNA, 0) = 1
FROM rao.stawka;

-- 7. COST TYPES (koszt_typ → cost_types)
INSERT INTO rao_new.cost_types (id, name, description, amount1, amount2)
SELECT ID, NAZWA, OPIS, kwota1, kwota2
FROM rao.koszt_typ;

-- 8. CONTRACTORS (kontrahent2 → contractors)
INSERT INTO rao_new.contractors (
    id, name, name_short, nip, regon, pesel, postal_code, city, street, unit,
    notes, is_supplier, email, contact_person1, phone1, contact_person2, phone2,
    landline_phone, website, files_folder, gus_date, created_at, updated_at
)
SELECT
    ID, NAZWA, nazwa_krotka, NIP, REGON, PESEL, KOD_POCZTOWY, MIEJSCOWOSC,
    ULICA, LOKAL, UWAGI, COALESCE(DOSTAWCA, 0) = 1, EMAIL,
    OSOBA_KONTAKTOWA, TELEFON, OSOBA_KONTAKTOWA2, TELEFON2,
    telefon_stac, www, FOLDER, DATA_GUS,
    COALESCE(DATA, NOW()), data_modyfikacji
FROM rao.kontrahent2;

-- 9. CONTRACTOR ADDRESSES (adres → contractor_addresses)
INSERT INTO rao_new.contractor_addresses (
    id, contractor_id, name, country_code, postal_code, city, street,
    notes, contact_person, phone, email, is_default_delivery, is_headquarters,
    latitude, longitude
)
SELECT
    ID, ID_KONTRAHENTA, NAZWA, COALESCE(SYM_KRAJU, 'PL'),
    KOD_POCZTOWY, MIEJSCOWOSC, ULICA_LOKAL,
    UWAGI, OSOBA, TELEFON, MAIL,
    COALESCE(DOMYSLNA_DOSTAWA, 0) = 1,
    COALESCE(SIEDZIBA, 0) = 1,
    LTT, LNG
FROM rao.adres;

-- 10. ARTICLES (artykul3 → articles)
INSERT INTO rao_new.articles (
    id, name, is_service, registration_no, serial_no, brand, model,
    replacement_value, category_id, owner_id, branch_id, description,
    notes, rental_days, article_type, created_at, updated_at
)
SELECT
    ID, NAZWA,
    CASE WHEN USLUGA IS NOT NULL AND USLUGA != '' THEN TRUE ELSE FALSE END,
    NR_REJESTRACYJNY, nr_seryjny, MARKA, MODEL,
    wartosc, ID_KATEGORII, ID_WLASCICIEL, ID_ODDZIALU,
    OPIS, UWAGI, LICZBA_DNI, rodzaj,
    COALESCE(DATA_DODANIA, NOW()), DATA_MODYFIKACJI
FROM rao.artykul3;

-- 11. CONTRACTS (umowa2 → contracts)
INSERT INTO rao_new.contracts (
    id, contractor_id, branch_id, salesperson_id, number, auto_number,
    contract_type, description, delivery_address, date_from, date_to,
    total_value, prepayment_amount, prepayment_document,
    invoice_amount, invoice_document, notes, additional_fees_text,
    contact_person1, contact_phone1, show_person1,
    contact_person2, contact_phone2, show_person2,
    email, phone, contractor_name, print_path, print_date,
    report_without_data, working_days_per_week, position_count,
    created_at, updated_at
)
SELECT
    u.ID, u.ID_KONTRAHENTA,
    (SELECT IDO FROM rao.umowa_oddzial WHERE IDU = u.ID LIMIT 1),
    u.id_handlowca,
    u.NUMER, u.AUTONUMER,
    COALESCE(u.typ, 'S'),
    u.OPIS, u.ADRES, u.DATA_OD, u.DATA_DO,
    u.WARTOSC, u.PRZEDPLATA_KWOTA, u.PRZEDPLATA_DOKUMENT,
    u.FAKTURA_KWOTA, u.FAKTURA_DOKUMENT, u.UWAGI, u.OPLATY,
    u.OSOBA1, u.TELEFON1, COALESCE(u.pokaz_osobe1, 1) = 1,
    u.OSOBA2, u.TELEFON2, COALESCE(u.pokaz_osobe2, 1) = 1,
    u.EMAIL, u.TELEFON, u.NAZWA,
    u.SCIEZKA_WYDRUKU, u.DATA_WYDRUKU,
    COALESCE(u.PZ_BEZ, 0) = 1,
    COALESCE(u.LICZBA_DNI, 6),
    COALESCE(u.ilepoz, 0),
    COALESCE(u.DATA_WPROWADZENIA, NOW()), u.DATA_MODYFIKACJI
FROM rao.umowa2 u;

-- 12. DELIVERIES (dostawa → deliveries)
INSERT INTO rao_new.deliveries (id, contract_id, address_id, latitude, longitude)
SELECT ID, ID_UMOWY, ID_ADRES, LTT, LNG
FROM rao.dostawa;

-- 13. DELIVERY ADDRESSES (adres_dostawy → delivery_addresses)
INSERT INTO rao_new.delivery_addresses (
    id, contract_id, name, street, number, postal_code,
    hamlet, city, town, village, county, municipality,
    province, district, neighbourhood
)
SELECT
    ID, ID_UMOWY, NAZWA, ULICA, NUMER, KOD_POCZTOWY,
    HAMLET, MIEJSCOWOSC, MIASTO, WIOSKA, POWIAT, GMINA,
    WOJEWODZTWO, DZIELNICA, OSIEDLE
FROM rao.adres_dostawy;

-- 14. CONTRACT POSITIONS (umowa_pozycja3 → contract_positions)
INSERT INTO rao_new.contract_positions (
    id, contract_id, article_id, description, rental_days,
    quantity, unit_price, costs, rate_type_id, billing_frequency,
    billing_unit, supplier_id, delivery_date, article_name
)
SELECT
    p.ID, p.ID_UMOWY, p.ID_ARTYKULU, p.TYP_WYNAJMU, p.OPIS, p.LICZBA_DNI,
    p.ILOSC, p.CENA, p.koszty, p.ID_STAWKI, p.rozliczanie,
    p.oplataza, p.id_dostawcy, p.data_dostawy, p.NAZWA
FROM rao.umowa_pozycja3 p;

-- 15. POSITION CONDITIONS (umowa_pozycja2_warunek → position_conditions)
INSERT INTO rao_new.position_conditions (
    id, position_id, rate_type_id, description, rate1, rate2,
    billing_label, period_count, minimum
)
SELECT
    ID, ID_POZYCJI, ID_STAWKI, OPIS, OPLATA1, OPLATA2,
    ROZLICZANA, LICZBA_DNI, MINIMUM
FROM rao.umowa_pozycja2_warunek;

-- 16. COSTS (koszt → costs)
INSERT INTO rao_new.costs (id, cost_type_id, position_id, description, amount, created_at)
SELECT ID, ID_TYPU, ID_UMOWA_POZYJCA, OPIS, KWOTA, COALESCE(DATA, NOW())
FROM rao.koszt;

-- 17. SETTLEMENTS (rozliczenie → settlements)
INSERT INTO rao_new.settlements (id, position_id, date, amount)
SELECT ID, ID_POZYCJI, DATA, WARTOSC
FROM rao.rozliczenie;

-- ============================================================
-- RESET AUTO_INCREMENT na wszystkich tabelach
-- ============================================================
-- Po migracji ustawiamy auto_increment wyżej niż max(id)
-- aby nowe rekordy nie kolidowały

SET @max_id = (SELECT COALESCE(MAX(id), 0) + 1 FROM rao_new.contractors);
SET @sql = CONCAT('ALTER TABLE rao_new.contractors AUTO_INCREMENT = ', @max_id);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- (powtórz dla każdej tabeli)
```

## Tabele NIE migrowane (legacy/tymczasowe)

| Tabela | Powód |
|--------|-------|
| `a`, `u` | Historyczny cache/log — dane dostępne z relacji |
| `artykul`, `artykul2` | Legacy wersje — zastąpione przez `artykul3` |
| `umowa`, `umowa_pozycja`, `umowa_pozycja2` | Legacy wersje |
| `kontrahent` | Legacy — zastąpione przez `kontrahent2` |
| `kontakt` | Nieużywane w kodzie (brak SELECT/INSERT w .cs) |
| `imp`, `imp_*` | Tabele importowe (jednorazowe) |
| `dane` | View, nie tabela danych |
| `temp`, `lp`, `nr_umowy`, `oddo` | Tabele pomocnicze/tymczasowe |

## Post-migracja: hashowanie haseł

```python
# Skrypt jednorazowy po migracji
import bcrypt
from sqlalchemy import create_engine, text

engine = create_engine("mariadb+mariadbconnector://user:pass@localhost/rao_new")

with engine.begin() as conn:
    users = conn.execute(text("SELECT id, password FROM users")).fetchall()
    for user_id, password in users:
        if password.startswith("$PLAINTEXT$"):
            # Zamiast kopiować plaintext, generuj losowe hasło tymczasowe + force_password_reset
            temp_password = generate_random_temp_password()  # losowe hasło bcrypt
            conn.execute(
                text("UPDATE users SET password = :pwd, force_password_reset = 1 WHERE id = :id"),
                {"pwd": temp_password, "id": user_id}
            )
    print(f"Zaktualizowano {len(users)} użytkowników (force_password_reset=1 dla migrowanych haseł)")
```

## Weryfikacja migracji

```sql
-- Porównaj liczbę rekordów stare vs nowe
SELECT 'contractors' AS tbl, (SELECT COUNT(*) FROM rao.kontrahent2) AS old_count,
       (SELECT COUNT(*) FROM rao_new.contractors) AS new_count
UNION ALL
SELECT 'addresses', (SELECT COUNT(*) FROM rao.adres),
       (SELECT COUNT(*) FROM rao_new.contractor_addresses)
UNION ALL
SELECT 'articles', (SELECT COUNT(*) FROM rao.artykul3),
       (SELECT COUNT(*) FROM rao_new.articles)
UNION ALL
SELECT 'contracts', (SELECT COUNT(*) FROM rao.umowa2),
       (SELECT COUNT(*) FROM rao_new.contracts)
UNION ALL
SELECT 'positions', (SELECT COUNT(*) FROM rao.umowa_pozycja3),
       (SELECT COUNT(*) FROM rao_new.contract_positions)
UNION ALL
SELECT 'conditions', (SELECT COUNT(*) FROM rao.umowa_pozycja2_warunek),
       (SELECT COUNT(*) FROM rao_new.position_conditions);
-- Wszystkie old_count == new_count → migracja OK
```

---

## P1-114: Reset bazy od zera (DROP + CREATE + seed) — 2026-07-12

> **Skrypt:** `scripts/reset_db.py`
> **Zgoda:** User potwierdził destrukcję (sesja FULL-AUTO, hard stop DROP/TRUNCATE = raport)

### Procedura

```bash
cd backend && python reset_db.py              # DROP + CREATE + schema + seed + FA invoices
cd backend && python reset_db.py --skip-seed  # tylko DROP + CREATE + schema
cd backend && python reset_db.py --skip-fa    # bez FA invoices
```

### Co robi skrypt

1. **DROP DATABASE IF EXISTS rao_new** (bezpośrednio przez aiomysql)
2. **CREATE DATABASE rao_new** (utf8mb4_polish_ci)
3. **Base.metadata.create_all** — schema z modeli SQLAlchemy (mirror main.py startup)
4. **seed_demo_data.py** — pełny seed:
   - 16 kategorii, 5 maszyn (4 diesel + 1 elektryk), 7 usług dodatkowych
   - 8 kontrahentów, 2 handlowców, 2 oddziały, 4 użytkowników (admin/admin123)
   - 6 rate types, konfiguracja firmy, FA settings (bootstrap z env)
   - 5 cenników kaskadowych per maszyna, 4 presety opłat (Diesel/Elektryk)
   - 64 umowy (24 historia 2025 + 10 aktywnych FA-pending + 14 historia 2026 + 16 FA-pending zakończone)
   - 86 pozycji, 258 warunków, 191 usług dodatkowych, 156 rozliczeń, 8 rezerwacji
5. **seed_fa_invoices.py** — faktury FA dla rozliczonych umów (source=fakturownia)

### Weryfikacja po resecie (2026-07-12)

```sql
SELECT (SELECT COUNT(*) FROM contracts) as contracts,        -- 64
       (SELECT COUNT(*) FROM contract_positions) as positions, -- 86
       (SELECT COUNT(*) FROM machines) as machines,           -- 5
       (SELECT COUNT(*) FROM additional_services) as add_srv, -- 7
       (SELECT COUNT(*) FROM contractors) as contractors,     -- 8
       (SELECT COUNT(*) FROM users) as users;                 -- 4

SELECT COUNT(*) FROM contracts WHERE date_to >= CURDATE() AND is_settled = 0; -- 10 aktywnych
SELECT id, name, power_type FROM machines; -- 4 diesel + 1 elektryk
SELECT id, enabled, domain_subdomain FROM fakturownia_settings; -- enabled=1, domain=matsnd
```

### Fakturownia — status integracji

| Element | Status |
|---|---|
| `FAKTUROWNIA_API_TOKEN` w `.env` | ✅ poprawny |
| Domain `matsnd.fakturownia.pl` | ✅ DNS działa (54.76.110.157) |
| API endpointy | ✅ `/clients.json`, `/products.json`, `/invoices.json` (BEZ `/api/` prefiksu) |
| DB `fakturownia_settings` | ✅ enabled=True, domain=matsnd, token encrypted |
| DB `machines.fakturownia_product_id` | ✅ 5 maszyn zmapowanych |
| FA clients (8 kontrahentów) | ✅ zmapowani po NIP |
| FA products (5 maszyn) | ✅ zmapowane po ID |

### Uwagi

- **P1-115 (backlog):** Umowy typu U (usługi) w seedzie mają pozycje z `machine_id` zamiast `service_id` — do naprawy osobno. Services table jest pusta (0 rekordów).
- **Migracje `ALTER TABLE ... IF NOT EXISTS`** w main.py startup mogą logować ostrzeżenia (np. "Unknown column 'article_id'") — niekrytyczne, schema tworzona od zera przez create_all.
