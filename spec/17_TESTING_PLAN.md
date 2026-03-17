# Plan testowania aplikacji RAO

## Podejście ogólne

Trzy warstwy testów, od najszybszych do najwolniejszych:

```
┌─────────────────────────────────────────┐
│  E2E (Playwright)  — 20–30 scenariuszy  │  ~5 min
│  Integracyjne (pytest + TestClient)      │  ~2 min
│  Jednostkowe (pytest)    — logika bizn. │  <30 s
└─────────────────────────────────────────┘
```

---

## 1. Testy jednostkowe (backend / pytest)

### Lokalizacja: `backend/tests/unit/`

### Co testować:

| Moduł | Funkcja | Co sprawdzić |
|-------|---------|--------------|
| `stats/calc.py` | `calculate_position_value()` | poprawność kwot dla różnych billing_frequency |
| `migrate.py` | `_parse_fee_line()` | wszystkie 9 wzorców z OPLATY (patrz spec/08) |
| `migrate.py` | `_parse_text_to_fees()` | multi-line blok → lista pozycji |
| `reports/service.py` | `_html_to_pdf_sync()` | zwraca bytes > 0 |
| `auth/` | bcrypt rehash | nie rehashuje już zahashowanych haseł |

### Priorytet uruchomienia:
```bash
pytest backend/tests/unit/ -v
```

---

## 2. Testy integracyjne API (pytest + httpx)

### Lokalizacja: `backend/tests/integration/`

### Konfiguracja: testowa baza SQLite in-memory

```python
# conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def client():
    # override get_db with test session
    ...
```

### Scenariusze wg modułu:

#### Auth
- [ ] POST `/auth/login` — poprawne dane → token
- [ ] POST `/auth/login` — złe hasło → 401
- [ ] GET `/auth/profile` — bez tokenu → 401
- [ ] PUT `/auth/change-password` — stare hasło niepoprawne → 400

#### Contractors
- [ ] GET `/contractors` — lista z paginacją
- [ ] POST `/contractors` — walidacja NIP (9 cyfr)
- [ ] GET `/contractors/{id}` — 404 dla nieistniejącego
- [ ] GET `/contractors/gus/{nip}` — mock GUS, parsowanie odpowiedzi

#### Contracts
- [ ] POST `/contracts` — tworzy umowę + kopiuje fee templates
- [ ] GET `/contracts/{id}` — zwraca pozycje, warunki, usługi
- [ ] PATCH `/contracts/{id}` — aktualizacja pól
- [ ] DELETE `/contracts/{id}` — kaskadowe usunięcie pozycji

#### Stats / Worker reports
- [ ] GET `/stats/expiring-contracts?days=14` — tylko umowy kończące się w oknie
- [ ] GET `/stats/overdue-contracts` — tylko umowy z date_to < today
- [ ] GET `/stats/deliveries-today?lookahead=2` — filtruję po delivery_date
- [ ] GET `/stats/unprinted-contracts` — print_date IS NULL + date_to >= today
- [ ] GET `/stats/fleet-summary` — sumaryczne KPI

#### Reports PDF
- [ ] GET `/reports/contract/{id}` — zwraca PDF (Content-Type: application/pdf)
- [ ] GET `/reports/protocol-zo/{id}` — jak wyżej

#### Settings
- [ ] POST/GET/DELETE `/settings/categories`
- [ ] POST `/settings/fee-preset-groups` + przypisanie do umowy

### Uruchomienie:
```bash
pytest backend/tests/integration/ -v --asyncio-mode=auto
```

---

## 3. Testy E2E (Playwright)

### Lokalizacja: `e2e/`

### Stack: `@playwright/test` (TypeScript)

```bash
npx playwright test --reporter=html
```

### Scenariusze krytyczne (P0):

#### SC-01: Logowanie
```
1. Otwórz /login
2. Wpisz admin / Admin123!
3. Sprawdź redirect → /dashboard/contracts
4. Sprawdź nagłówek "Toolsmart"
```

#### SC-02: Tworzenie umowy najmu end-to-end
```
1. Kliknij "Nowa umowa"
2. Wybierz kontrahenta (search)
3. Wypełnij daty od/do
4. Dodaj pozycję (artykuł z bazy)
5. Kliknij "Zapisz"
6. Sprawdź pojawienie się umowy na liście
```

#### SC-03: Generowanie PDF
```
1. Otwórz umowę
2. Kliknij "Drukuj PDF"
3. Sprawdź że plik się pobrał (network request 200 + Content-Type: application/pdf)
```

#### SC-04: Panel pracownika
```
1. Nawiguj do /worker
2. Sprawdź ładowanie 4 sekcji (expiring, overdue, deliveries, unprinted)
3. Zmień filtr "Kończące się" z 14 na 30 dni
4. Sprawdź ponowne załadowanie listy
```

#### SC-05: Wyszukiwanie kontrahenta (GUS)
```
1. Nowy kontrahent → wpisz NIP "9512598092"
2. Kliknij "Pobierz z GUS"
3. Sprawdź autouzupełnienie nazwy i adresu
```

### Scenariusze regresji (P1):
- [ ] SC-06: Logowanie → wylogowanie → ponowne logowanie
- [ ] SC-07: Zmiana hasła przy `must_change_password=true`
- [ ] SC-08: Edycja kontrahenta → zapis → reload → dane zachowane
- [ ] SC-09: Statystyki — KPI się ładują (fleet-summary, top-machines)
- [ ] SC-10: Ustawienia — dodaj kategorię → pojawia się na liście

---

## 4. Testy migracji (standalone)

### Lokalizacja: `backend/tests/migration/`

Po każdorazowym uruchomieniu `python migrate.py` automatycznie weryfikuj:

```python
# test_migration_counts.py
EXPECTED_MIN = {
    "company": 1,
    "contractors": 500,
    "articles": 300,
    "contracts": 500,
    "contract_positions": 600,
    "position_conditions": 800,
    "contract_service_fees": 2000,
}

def test_row_counts(db_connection):
    for table, min_count in EXPECTED_MIN.items():
        count = db_connection.execute(f"SELECT COUNT(*) FROM {table}").scalar()
        assert count >= min_count, f"{table}: expected >= {min_count}, got {count}"
```

### Testy parsowania OPLATY:
```python
@pytest.mark.parametrize("input,expected_name,expected_amount", [
    ("- Transport: 400.00 zł dostawa / 400.00 zł odbiór", "Transport", 400.0),
    ("- Czyszcz.: 150.00 zł - 400.00 zł", "Czyszcz.", 150.0),
    ("- Ponadnorm.: 200.00 zł / h - 300.00 zł / h", "Ponadnorm.", 200.0),
    ("- Ładowarka - wynajem 900,00 zł / doba", "Ładowarka - wynajem", 900.0),
    ("- Transport: odbiór własny", "Transport", None),
])
def test_parse_fee_line(input, expected_name, expected_amount):
    result = _parse_fee_line(input)
    assert result['name'] == expected_name
    assert float(result['amount_from'] or 0) == expected_amount or result['amount_from'] is None
```

---

## 5. CI/CD (GitHub Actions — propozycja)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: rao_test
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --asyncio-mode=auto

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
        working-directory: frontend
      - run: npx playwright install --with-deps chromium
      - run: npx playwright test
        working-directory: e2e
```

---

## 6. Priorytety implementacji testów

| Sprint | Co implementować |
|--------|-----------------|
| **S1** | Unit: `calculate_position_value`, `_parse_fee_line` |
| **S1** | Integration: auth login/logout, contract CRUD |
| **S2** | Integration: stats endpoints (worker reports) |
| **S2** | E2E: SC-01, SC-02, SC-03 (krytyczne ścieżki) |
| **S3** | E2E: SC-04..SC-10 (regresja) |
| **S3** | Migration tests + CI/CD |

---

## 7. Narzędzia i komendy

```bash
# Backend — jednostkowe + integracyjne
cd backend
pip install pytest pytest-asyncio httpx aiosqlite
pytest tests/ -v --asyncio-mode=auto --cov=. --cov-report=html

# Frontend — unit (Vitest)
cd frontend
npm run test:unit

# E2E
cd e2e
npx playwright install chromium
npx playwright test --headed   # z przeglądarką
npx playwright test            # headless (CI)
npx playwright show-report     # HTML raport
```
