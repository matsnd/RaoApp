# Strategia testowania RAO

> Single source of truth dla testów. Aktualizuj po każdej zmianie pokrycia.

## Test pyramid

```
        /\
       /  \  E2E (Playwright Chromium) — flow + smoke regression
      /----\
     /      \  Integration (pytest + httpx + AsyncSession) — endpoint + DB
    /--------\
   /          \  Unit (pytest) — service logic, validators, schemas
  /____________\
```

## Komendy

```bash
# Backend unit
cd backend && python -m pytest -x --tb=short
cd backend && python -m pytest --cov=. --cov-report=html

# Frontend type/build
cd frontend && npx vue-tsc --noEmit
cd frontend && npm run build

# E2E (oba serwery muszą działać: backend 8001, frontend 5174)
cd e2e && npx playwright test --reporter=list

# Smoke regression (PO KAŻDEJ ZMIANIE!)
cd e2e && npx playwright test tests/01-login.spec.ts --reporter=list

# Pojedynczy plik
cd e2e && npx playwright test tests/04-contract.spec.ts

# Debug (otwarta przeglądarka)
cd e2e && npx playwright test --debug
```

## Lokalizacja testów

| Warstwa | Lokalizacja | Konwencja |
|---------|-------------|-----------|
| Unit (backend) | `backend/tests/unit/` | `test_<feature>.py` |
| E2E | `e2e/tests/` | `NN-<feature>.spec.ts` |
| Helpers | `e2e/tests/helpers.ts` | `apiLogin`, `authHeaders`, `safeDelete`, `newApiContext`, `login`, `navigateTo`, `waitForBackend` |

## Konwencje E2E

1. **Cleanup:** Każdy spec file ma `test.afterAll` który usuwa utworzone zasoby przez API. Track ID-ki w tablicy modułowej.
2. **API gdy się da:** Operacje setup/teardown przez `request.post/put/delete` (szybsze, mniej flaky niż klikanie UI).
3. **`test.fixme` zamiast `skip`:** Gdy feature nie jest jeszcze zaimplementowany — z komentarzem `Owner: <agent>`.
4. **Dane unikalne:** `Date.now()` w nazwach (np. `EditMe ${ts}`) — brak kolizji z poprzednimi runami.
5. **Timeouts:** explicit w każdym `expect` / `goto` (8s default, 15s navigation, 30s PDF).
6. **NIP-y testowe:** prefiks 2-cyfrowy (66, 77, 78...) + suffix `String(ts).slice(-8)` — 10 cyfr.

## Macierz pokrycia E2E (po RAO-P2-013)

### TEST-01: Logowanie (`01-login.spec.ts`) — smoke

| # | Use case | Status |
|---|----------|--------|
| 1.1 | Brak sesji → /login | ✅ |
| 1.2 | Form widoczny | ✅ |
| 1.3 | Złe dane → błąd | ✅ |
| 1.4 | Poprawne dane → /home | ✅ |
| 1.5 | Wylogowanie czyści sesję | ✅ |
| 1.6 | Submit disabled w trakcie loadingu | ✅ |
| 1.7 | Enter w polu hasła submit | ✅ |
| 1.8 | JWT w localStorage po login | ✅ |
| 1.9 | Reload zachowuje sesję | ✅ |
| 1.10 | /rao/ zalogowany → /home | ✅ |
| 1.11 | /rao/login zalogowany → redirect | ✅ |

### TEST-02: Kontrahenci (`02-contractor.spec.ts`)

| # | Use case | Status |
|---|----------|--------|
| 2.1 | Lista ładuje się | ✅ |
| 2.2 | Form nowego kontrahenta | ✅ |
| 2.3 | Tworzenie + redirect /edit | ✅ |
| 2.4 | Walidacja: brak nazwy | ✅ |
| 2.5 | Wyszukiwanie | ✅ |
| 2.6 | Edycja istniejącego | ✅ |
| 2.7 | Delete → 204; ponowne → 404 | ✅ |
| 2.8 | CRUD adresów dostawy (API) | ✅ |
| 2.9 | GUS lookup button visible | ✅ |
| 2.10 | NIP edge cases (znaki niedozw.) | ✅ |
| 2.11 | XSS w nazwie — escape w UI | ✅ |
| 2.12 | Paginacja (warunkowa) | ✅ |
| 2.13 | Pole "reprezentowany przez" | 🟡 fixme (brak w UI) |

### TEST-03: Artykuły (`03-article.spec.ts`)

| # | Use case | Status |
|---|----------|--------|
| 3.1 | Lista | ✅ |
| 3.2 | Form nowego | ✅ |
| 3.3 | Tworzenie + redirect | ✅ |
| 3.4 | Duplikacja | ✅ |
| 3.5 | Walidacja: brak nazwy | ✅ |
| 3.6 | Edycja | ✅ |
| 3.7 | Delete → 204; ponowne → 404 | ✅ |
| 3.8 | Wyszukiwanie po nazwie | ✅ |
| 3.9 | Pusta nazwa → 422 | ✅ |
| 3.10 | Długa nazwa (1000) — nie 500 | ✅ |
| 3.11 | Polskie znaki round-trip | ✅ |
| 3.12 | Pole `fakturownia_product_id` w UI | 🟡 fixme (frontend-dev) |

### TEST-04: Umowy (`04-contract.spec.ts`)

| # | Use case | Status |
|---|----------|--------|
| 4.1 | Lista | ✅ |
| 4.2 | Form nowy | ✅ |
| 4.3 | Walidacja brak kontrahenta | ✅ |
| 4.4 | Tworzenie po wyborze kontrahenta | ✅ |
| 4.5 | Sekcja pozycji widoczna | ✅ |
| 4.6 | PDF protocol_zo (S/U/nodata) | ✅ |
| 4.7 | Edycja date_to | ✅ |
| 4.8 | Walidacja brak date_from | ✅ |
| 4.9 | Walidacja zły contractor_id | ✅ |
| 4.10 | Typ U + PDF protocol_zo_u | ✅ |
| 4.11 | PDF type=contract — magic header %PDF | ✅ |
| 4.12 | PDF nieistniejącej → 404 | ✅ |
| 4.13 | CRUD pozycji (API) | ✅ |
| 4.14 | CRUD service-fee (API) | ✅ |
| 4.15 | Filtr contract_type=S | ✅ |
| 4.16 | PDF wielostronicowy — podpisy na ostatniej | 🟡 fixme |

### TEST-05: Ustawienia (`05-settings.spec.ts`)

| # | Use case | Status |
|---|----------|--------|
| 5.1 | Otwiera widok | ✅ |
| 5.2 | Zakładka Dane firmy | ✅ |
| 5.3 | Przełączanie zakładek | ✅ |
| 5.4 | Zapis dane firmy | ✅ |
| 5.5 | CRUD handlowca | ✅ |
| 5.6 | CRUD kategorii | ✅ |
| 5.7 | Dodanie typu stawki | ✅ |
| 5.8 | CRUD szablonu usługi | ✅ |
| 5.9 | Zakładka Fakturownia | ✅ |
| 5.10 | Token Fakturownia maskowany | ✅ |

### TEST-06: Dashboard (`06-dashboard.spec.ts`) — NOWY

| # | Use case | Status |
|---|----------|--------|
| 6.1 | KPI strip widoczny | ✅ |
| 6.2 | Karta "Maszyny w terenie" | ✅ |
| 6.3 | Tabela kontraktów lub empty | ✅ |
| 6.4 | Filtr typu S/U | ✅ |
| 6.5 | Filtr dat date_from/to | ✅ |
| 6.6 | Dwuklik wiersza → /edit | ✅ |
| 6.7 | Statystyki per maszyna | 🟡 fixme (UI brak osobnego widoku) |

### TEST-07: Reports API (`07-reports.spec.ts`) — NOWY

| # | Use case | Status |
|---|----------|--------|
| 7.1 | type=contract → 200 PDF | ✅ |
| 7.2 | type=protocol_zo_s → 200 PDF | ✅ |
| 7.3 | type=protocol_zo_u → 200 PDF | ✅ |
| 7.4 | type=protocol_zo_nodata_s → 200 PDF | ✅ |
| 7.5 | Nieistniejące ID → 404 | ✅ |
| 7.6 | Brak tokenu → 401 | ✅ |
| 7.7 | Zły type query → 4xx | ✅ |
| 7.8 | ID jako string → 422 | ✅ |

### TEST-08: Auth & Security (`08-auth-security.spec.ts`) — NOWY

| # | Use case | Status |
|---|----------|--------|
| 8.1 | Route guards (8 ścieżek) bez tokenu → /login | ✅ |
| 8.2 | API GET bez tokenu → 401 (5 endpointów) | ✅ |
| 8.3 | POST /contractors bez tokenu → 401 | ✅ |
| 8.4 | POST /contracts bez tokenu → 401 | ✅ |
| 8.5 | Zmodyfikowany token → 401 | ✅ |
| 8.6 | Pusty Bearer → 401 | ✅ |
| 8.7 | Zmiana hasła: błędne stare → 4xx | ✅ |
| 8.8 | Zmiana hasła: confirm != new → 4xx | ✅ |
| 8.9 | Zmiana hasła happy path + revert | ✅ |
| 8.10 | Wylogowanie czyści localStorage | ✅ |

## Edge cases obowiązkowe (każdy nowy feature)

### Inputy tekstowe
- [ ] Pusty string `""`
- [ ] Tylko spacje `"   "`
- [ ] Bardzo długi (1000+ znaków)
- [ ] Polskie znaki: `ąćęłńóśźż`
- [ ] Unicode emoji
- [ ] HTML tagi: `<script>alert(1)</script>`
- [ ] SQL injection: `'; DROP TABLE users; --`

### Auth
- [ ] Brak tokenu → 401
- [ ] Wygasły token → 401
- [ ] Zmodyfikowany token → 401
- [ ] Token usera A na zasób usera B → 403 (IDOR)

### CRUD
- **CREATE:** duplikat → 409, brak FK → 422, brak required → 422
- **READ:** ID nieistniejące → 404, ID jako string → 422
- **UPDATE:** brak rekordu → 404
- **DELETE:** brak rekordu → 404, podwójne delete → 404

## Cleanup po testach

Każdy spec file MUSI mieć `test.afterAll` który:
1. Loguje się przez API (`apiLogin(ctx)`)
2. Iteruje po `createdXxxIds[]` i wywołuje `safeDelete()` (tolerant na 404)
3. Disposuje context

Helper: `newApiContext()` w `helpers.ts`.

## Smoke regression (po każdej zmianie)

```bash
cd e2e && npx playwright test tests/01-login.spec.ts --reporter=list
```

Jeśli pada — **STOP**. Repro → root cause → fix.

## Status pokrycia (RAO-P2-013, 2026-05-18)

| Plik | Testy | Status |
|------|-------|--------|
| 01-login | 11 | ✅ 11/11 PASS |
| 02-contractor | 13 (1 fixme) | ✅ 12/12 PASS |
| 03-article | 12 (1 fixme) | ✅ 11/11 PASS |
| 04-contract | 16 (3 fixme + 7 skip) | ✅ 6/6 PASS |
| 05-settings | 10 | ✅ 10/10 PASS |
| 06-dashboard | 7 (1 fixme + 1 skip) | ✅ 5/5 PASS |
| 07-reports | 8 (5 skip) | ✅ 3/3 PASS |
| 08-auth-security | 21 | ✅ 21/21 PASS |
| **TOTAL** | **97 testów (5 fixme + 14 skip = 19)** | **78/78 PASS = 100%** |

**Smoke regression (01-login):** ✅ 11/11 PASS w 13s.

## 🔴 Bugi znalezione przez QA (RAO-QA-001..007)

| ID | Plik backend | Opis | Owner |
|----|--------------|------|-------|
| RAO-QA-001 | `articles/schemas.py` | `name: str = Field(..., max_length=200)` brak `min_length=1` — backend akceptuje pustą nazwę → 201 zamiast 422 | backend-dev |
| RAO-QA-002 | `contracts/service.py:182` | `data.positions` referencja do nieistniejącego pola w `ContractCreate` → AttributeError → **500 dla każdego POST /contracts**. Cascade: blokuje 12 testów. | backend-dev (P0) |
| RAO-QA-003 | `reports/router.py` | `ValueError("Contract X not found")` propagowany jako 500 zamiast HTTPException 404 | backend-dev |
| RAO-QA-004 | `contracts/router.py` (GET) | `?contract_type=S` filter → 500 (prawdopodobnie zły handler query param) | backend-dev |
| RAO-QA-005 | `reports/router.py` | Brak walidacji query param `type` (Literal/Enum) → invalid_xyz → 500 | backend-dev |
| RAO-QA-006 | `contracts/service.py` | Nieistniejący `contractor_id` w POST → AttributeError 500 zamiast 422 (brak `await db.get()` walidacji FK) | backend-dev |
| RAO-QA-007 | UI `ArticleFormView.vue` | Klik "Zapisz" w trybie edit nie wysyła PUT (do zweryfikowania manualnie) | frontend-dev |

🟡 **Fixme (feature gaps, nie bugi):**
- Pole "Reprezentowany przez" w ContractorFormView (spec'd, brak w UI)
- Pole `fakturownia_product_id` w ArticleFormView (backend ma, UI brak)
- Statystyki per maszyna w dashboard (brak osobnego widoku)
- PDF wielostronicowy: weryfikacja podpisów na ostatniej stronie (wymaga pdf-parse)

