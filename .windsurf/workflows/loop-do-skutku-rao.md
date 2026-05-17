---
description: Autonomiczna pętla "do skutku" dla pełnego stacku RAO (FastAPI + Vue 3 + MariaDB + Playwright) — agent sam planuje, implementuje, weryfikuje, naprawia
---

# 🔁 `/loop-do-skutku-rao` — Autonomous Full-Stack Loop

> **Komenda:** `/loop-do-skutku-rao <opis zadania>`
>
> **Filozofia:** Agent jest pełnoprawnym software developerem RAO — pisze backend (FastAPI/SQLAlchemy/Pydantic),
> frontend (Vue 3 + Pinia), poprawia bazę (MariaDB), pisze i odpala testy (pytest + Playwright),
> sam się sprawdza, sam łata błędy. **NIE PYTA — RÓB.** Iteruje aż wszystkie warstwy są zielone.
>
> _Jeśli czegoś naprawdę nie wie — używa `code_search` / `read_file` / spec/, nie pyta user-a o oczywistości._
>
> **Różnica vs `/agent-loop-do-skutku-until-success`:**
> tamten skupia się tylko na froncie + Playwright. Ten obejmuje **całą piramidę testów RAO** i działa świadomie
> z architekturą warstwową aplikacji.

## 🔗 Powiązane zawsze-aktywne reguly (`.windsurf/rules/`)

To workflow **zakłada że reguly są aktywne** — nie powtarza ich treści, tylko rozszerza o tryb autonomiczny:

- **`rao-project`** (always_on) — stack, porty, login `admin/admin123`, root_path `/rao/api`, design system Toolsmart, mapa plików, tooling cheatsheet
- **`rao-migrations`** (glob na pliki DB) — 4-warstwowy proces zmiany schema, idempotentne wzorce, zakazane praktyki
- **`rao-spec-sync`** (always_on) — mapa "co zmieniłeś → który spec", 5 reguł update

**To znaczy:** jeśli czegoś nie wiesz o portach, design systemie, migracjach lub spec/ — jest to już w kontekście. Nie duplikuj, **stosuj**.

---

## 🎯 Cel końcowy (Definition of Done)

Zadanie jest skończone TYLKO gdy:

1. ✅ **Static checks pass** — `vue-tsc --noEmit` i `python -m compileall backend` bez błędów
2. ✅ **Unit tests pass** — `pytest` w `backend/tests/` zielone
3. ✅ **Backend smoke pass** — `GET /rao/api/health` zwraca 200 + `/rao/api/docs` ładuje się
4. ✅ **Frontend build pass** — `npm run build` w `frontend/` bez errorów
5. ✅ **E2E pass** — relevantne specy w `e2e/tests/*.spec.ts` zielone
6. ✅ **Manualna weryfikacja MCP** — Playwright MCP screenshot + accessibility snapshot pokazuje że feature działa
7. ✅ **Brak regresji** — `e2e/tests/01-login.spec.ts` nadal zielony (smoke)
8. ✅ **Spójność stylu** — Toolsmart navy `#1D2B53`, Montserrat, border-radius 12px
9. ✅ **Migracje deterministyczne** — każda zmiana DB jest w `backend/main.py` startup event jako idempotentny `ALTER ... IF NOT EXISTS` (lub `CREATE TABLE` z `Base.metadata.create_all`). **Zero ad-hoc** ALTER-ów wpisanych ręcznie do mariadb CLI bez równoległej zmiany w kodzie.
10. ✅ **Spec/ zsynchronizowane** — relevantne pliki w `spec/` (DDL, API, screens, business logic, navigation, integrations, reports) odzwierciedlają aktualny stan kodu. Spec to **single source of truth** dla następnego agenta.

Każdy z tych punktów ma swój **automatyczny weryfikator** (sekcja Tier 1-6 niżej).

---

##  Faza 0 — Pre-flight checks

Zanim cokolwiek zmienisz, w **jednym równoległym bloku** wywołaj:

1. `list_dir` na `c:\projects\repos\RaoApp` — potwierdź strukturę
2. `read_file` na `spec/19_BACKLOG.md` — sprawdź aktualny backlog/status
3. `read_file` na pliku spec relevantnym do zadania (mapa w regule `rao-spec-sync`)
4. `code_search` z naturalnym pytaniem typu *"Where is the contract creation logic and what files implement it?"*

Następnie sprawdź czy serwery działają:

```pwsh
# Backend health (root_path = /rao/api z reguly rao-project)
curl http://localhost:8000/rao/api/health

# Frontend
curl http://localhost:5173
```

Jeśli któryś nie działa → uruchom **non-blocking** (`run_command` z `Cwd` + `Blocking: false`):

```pwsh
# Backend (Cwd: backend)
uvicorn main:app --reload --port 8000

# Frontend (Cwd: frontend) — sam dobierze wolny port jak 5173 zajęte
npm run dev
```

⚠️ Reguly portów — patrz `rao-project`: zero `kill-port`/`pkill`/`taskkill`, zajęty port → kolejny wolny + update `VITE_API_URL`.

---

## 📝 Faza 1 — Plan & Discovery

### 1.1 Klasyfikacja zadania

Zanim zaczniesz, sklasyfikuj zadanie do jednej z kategorii:

| Kategoria | Symptomy | Warstwy do ruszenia |
|-----------|----------|---------------------|
| **DB-only** | Nowa kolumna, indeks, migracja, FK | DB + (czasem) backend models |
| **Backend-only** | Nowy endpoint, fix walidacji, logika serwisu | models → schemas → service → router → unit test |
| **Frontend-only** | Nowy widok, fix UX, zmiana stylu, store | components/views/stores + e2e (jeśli flow) |
| **Cross-stack** | End-to-end feature (np. nowy moduł "Dostawy") | DB → backend → frontend → e2e |
| **Bugfix** | Coś nie działa, regresja | Najpierw repro, potem fix najmniejszą zmianą |
| **Refactor** | Bez zmian funkcjonalnych | Zachować zielone testy 100% |

### 1.2 Plan w `todo_list`

Utwórz `todo_list` z **3-8 krokami** (więcej = za dużo). Tylko **jeden** krok ma `in_progress` w danym momencie.

Wzór dobrego planu:
```
1. [in_progress] Zlokalizuj X w kodzie (code_search)
2. [pending] Dodaj kolumnę Y do modelu Article + migracja inline
3. [pending] Zaktualizuj schema Pydantic ArticleOut
4. [pending] Dodaj unit test dla serializacji
5. [pending] Frontend: pokaż Y w ArticlePicker.vue
6. [pending] Verification Tier 1-5
```

### 1.3 Sequential thinking (tylko gdy złożone)

Jeśli zadanie ma ≥3 niezależne decyzje architektoniczne lub niejasne wymagania → wywołaj `mcp6_sequentialthinking` z 5-10 myślami. Inaczej **pomiń**, marnuje tokeny.

---

## ⚙️ Faza 2 — Implementacja warstwowa

### 2.A Database (jeśli dotyczy)

🔗 **Pełny proces 4-warstwowy w regule `rao-migrations`** (aktywuje się automatycznie przy edycji `backend/main.py`, `models.py`, `spec/01_DATABASE_DDL.md`).

W skrócie: `spec/01_DATABASE_DDL.md` → `backend/<feature>/models.py` → `backend/main.py` startup `ALTER ... IF NOT EXISTS` → weryfikacja `DESCRIBE` + drugi restart.

W trybie loop dodatkowo:
- Po dodaniu migracji **restart backendu na nowym porcie** (np. 8001) i sprawdź logi uvicorn pod kątem błędów startup
- Idempotentność testowana w Tier 4.5

### 2.B Backend (FastAPI module)

Każdy moduł trzyma się struktury `backend/<feature>/`:
```
<feature>/
├── __init__.py
├── models.py     # SQLAlchemy
├── schemas.py    # Pydantic (Out/Create/Update)
├── service.py    # Logika biznesowa
└── router.py     # Endpointy
```

**Kolejność:**
1. **`models.py`** — dokładnie 1:1 z DDL (kolumny, FK, relationships)
2. **`schemas.py`** — `Field(...)` z constraints; pomyśl o `model_config = {"from_attributes": True}`
3. **`service.py`** — async funkcje przyjmujące `db: AsyncSession`; **zero logiki w routerze**
4. **`router.py`** — `APIRouter`, `Depends(get_current_user)`, sensowne HTTP codes (201, 204, 404, 409)
5. **Rejestracja** w `backend/main.py` (`app.include_router(...)`)
6. **Unit test** w `backend/tests/unit/test_<feature>.py` — minimum happy path + 1 edge case

**Wzorzec endpointu:**
```python
@router.post("/", response_model=ArticleOut, status_code=201)
async def create_article(
    payload: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await service.create_article(db, payload, user)
```

### 2.C Frontend (Vue 3 + Pinia)

Struktura `frontend/src/`:
```
src/
├── components/   # reuzywalne (DataGrid, ArticlePicker)
├── views/        # routowalne (DashboardView, ContractFormView)
├── stores/       # Pinia
├── composables/  # use*()
├── router/
└── style.css     # zmienne CSS Toolsmart
```

**Kolejność:**
1. **Store** (jeśli nowy stan) — `defineStore('feature', ...)` z `state/getters/actions` (async)
2. **Komponent** — `<script setup lang="ts">`, Composition API, `ref()`/`computed()`
3. **CSS** — TYLKO zmienne z `style.css`:
   ```css
   --color-primary: #1D2B53;
   --color-bg-light: #F8F9FA;
   --font-family: 'Montserrat', sans-serif;
   --border-radius: 12px;
   --shadow-card: 0 1px 3px rgba(0,0,0,0.08);
   ```
4. **Routing** w `frontend/src/router/`
5. **Type check** po edycji: `npx vue-tsc --noEmit` (Cwd: frontend)

⚠️ **Antywzorce frontendu:**
- ❌ Inline styles z hardcoded colors
- ❌ `any` w TypeScript bez komentarza dlaczego
- ❌ Mutowanie props
- ❌ `v-html` z user inputem (XSS)
- ❌ Zapomnienie o loading state / error state / empty state

### 2.D Spec sync

🔗 **Mapa "co zmieniłeś → który spec" + 5 reguł w regule `rao-spec-sync`** (always_on).

W trybie loop dodatkowo:
- Spec update jest **częścią zadania**, nie pominiesz tego pod prysznicem deadline-u
- W Tier 4.5 wykonujesz `git diff --stat spec/` — pusty diff przy zmianach funkcjonalnych = fail
- W Final Report enumerujesz **które pliki spec/ zaktualizowałeś**

### 2.E E2E test (gdy dotyczy flow użytkownika)

**Lokalizacja:** `e2e/tests/<NN>-<feature>.spec.ts`

**Wzór:**
```typescript
import { test, expect } from '@playwright/test'
import { waitForBackend, login, navigateTo } from './helpers'

test.describe('TEST-XX: <Feature>', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('user może <akcja>', async ({ page }) => {
    await navigateTo(page, 'contracts')
    // Arrange / Act / Assert
  })
})
```

**Reguły:**
- Używaj `getByRole`/`getByPlaceholder`/`getByLabel` — **nie** XPath/CSS selektorów
- `expect(...).toHaveURL(/\/dashboard/)` — regexy dla URL
- Timeouty: nawigacja 15s, akcja 8s, expect 8s (zgodnie z `playwright.config.ts`)
- Zero `page.waitForTimeout(N)` w finalnej wersji (tylko do debugowania!)

---

## ✅ Faza 3 — Verification Matrix (5 tierów)

Po implementacji odpalasz **wszystkie tiery od najtańszego do najdroższego**. Pierwszy fail → wracasz do Fazy 2 (self-heal).

### Tier 1 — Static checks (sekundy)

W **jednym równoległym bloku**:

```pwsh
# Backend syntax check (Cwd: backend)
python -m compileall -q .

# Frontend type check (Cwd: frontend)
npx vue-tsc --noEmit
```

**Pass kryteria:** zero errorów, ostrzeżenia OK.

### Tier 2 — Unit tests (do 30s)

```pwsh
# Cwd: backend
python -m pytest -x --tb=short
```

Flagi: `-x` (stop on first fail), `--tb=short` (zwięzły traceback). Jeśli dodałeś nowy moduł — minimum **1 happy path test**.

### Tier 3 — Smoke tests (do 10s)

Backend musi być uruchomiony.

```pwsh
# Health
curl -sf http://localhost:8000/rao/api/health

# OpenAPI dostępne
curl -sf http://localhost:8000/rao/api/openapi.json | findstr "openapi"

# Login działa (zwraca JWT)
curl -sf -X POST http://localhost:8000/rao/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"login\":\"admin\",\"password\":\"admin123\"}'
```

### Tier 4 — E2E (1-3 min)

```pwsh
# Cwd: e2e — całość
npx playwright test --reporter=list

# Lub konkretny spec po zmianie pojedynczego flow
npx playwright test tests/04-contract.spec.ts --reporter=list
```

**Smoke regression:** ZAWSZE odpal `tests/01-login.spec.ts` po **każdej** zmianie, nawet czysto frontowej.

### Tier 4.5 — Migration & spec consistency check

Po Tier 4 (E2E) ale przed Tier 5 (manualna MCP) — szybki audyt deterministyczności:

```pwsh
# 1. Restart backendu by sprawdzić idempotentność migracji (Cwd: backend)
#    (uvicorn --reload sam podchwyci, ale startup events działają tylko przy fresh start —
#     jeśli zmieniałeś main.py startup → zabij i wystartuj ponownie na innym porcie)
uvicorn main:app --port 8001
# Sprawdź logi — żadnego "Duplicate column", "Table already exists" itp.

# 2. DESCRIBE wszystkie tabele które zmieniałeś — porównaj ze spec/01_DATABASE_DDL.md
mariadb -u rao_user -pRaoPass2026! rao_new -e "DESCRIBE <table>;"

# 3. git diff spec/ — czy aktualizowałeś dokumentację?
git diff --stat spec/
```

**Pass kryteria:**
- Drugi (i kolejny) restart backendu działa bez błędów (idempotentność potwierdzona)
- DESCRIBE zgadza się z DDL ze spec/01_DATABASE_DDL.md
- `git diff spec/` pokazuje aktualizacje proporcjonalne do zmian funkcjonalnych
  - 0 zmian jeśli zadanie czysto kosmetyczne
  - DDL + API jeśli backend feature
  - Screens + Navigation jeśli frontend feature

### Tier 5 — Manualna weryfikacja Playwright MCP

Najpotężniejszy tier — sprawdza **doświadczenie użytkownika**.

W **jednej sekwencji**:

```
1. mcp5_browser_navigate → http://localhost:5173
2. mcp5_browser_snapshot (accessibility tree — lepsze niż screenshot do akcji)
3. mcp5_browser_click → wykonaj scenariusz user-a
4. mcp5_browser_console_messages (level: "error") — sprawdź czy zero errorów JS
5. mcp5_browser_network_requests (filter: "/rao/api/") — czy zapytania zwracają 2xx
6. mcp5_browser_take_screenshot → zapisz do `temp/verify-<timestamp>.png` jako dowód
```

**Pass kryteria:**
- Zero error w console (warningi OK jeśli niekrytyczne)
- Zero 4xx/5xx w network (poza oczekiwanymi 401 na nieautoryzowanych endpointach)
- Snapshot pokazuje oczekiwany element (np. `[role="button"][name="Zapisz"]`)
- Screenshot wizualnie pasuje do `spec/03_FRONTEND_SCREENS.md`

---

## 🔁 Faza 4 — Self-Healing Loop

```
LOOP (max 15 iteracji LUB 25 minut wall-clock):

  ┌─ Run Tier 1-5 sekwencyjnie ─────────────────────────────┐
  │                                                          │
  │  PASS wszystkie?                                         │
  │   └─ YES → break (przejdź do Fazy 5)                     │
  │   └─ NO  → root cause analysis:                          │
  │      a) Przeczytaj traceback / error message uważnie     │
  │      b) Klasyfikuj:                                      │
  │         - syntax/type → fix w kodzie                     │
  │         - logiczny (zła wartość) → fix w service         │
  │         - integracja (404, CORS) → fix w main.py/router  │
  │         - flaky test → zwiększ timeout / use waitFor     │
  │         - timing → page.waitForLoadState('networkidle')  │
  │      c) Zaproponuj NAJMNIEJSZY fix (1-5 linii idealnie)  │
  │      d) Jeśli fix wymaga restartu uvicorn:               │
  │         • --reload sam podchwyci backend                 │
  │         • frontend Vite HMR — też auto                   │
  │         • migracje DB — restart backend                  │
  │      e) Wróć do top loopa                                │
  │                                                          │
  │  Po każdej iteracji: log "Próba X/15 — fix: <opis>"      │
  └──────────────────────────────────────────────────────────┘

  Po 15 próbach BEZ sukcesu:
   - NIE udawaj że działa
   - Zapisz w temp/loop-failure-<timestamp>.md:
     • Opis zadania
     • Co zostało zrobione (lista plików zmienionych)
     • Ostatni error
     • 3 hipotezy dlaczego nie działa
     • Sugestia dla user-a co zrobić ręcznie
   - Zaktualizuj todo_list z ostatnim krokiem jako "blocked"
   - Wyświetl USER-owi finalny raport (Faza 5 z escape valve)
```

### Anti-pattern: gaszenie symptomów zamiast root cause

❌ **Złe:** test fails na timeout → `expect(...).toHaveTimeout(60_000)`
✅ **Dobre:** test fails na timeout → sprawdź czy backend nie zwraca 500, czy nie ma N+1 w SQLAlchemy

❌ **Złe:** Pydantic validation error → dodać `Optional[X]` żeby przeszło
✅ **Dobre:** sprawdzić dlaczego frontend wysyła `null` zamiast wartości — fix po stronie tego co generuje błędne dane

❌ **Złe:** TypeError w Vue → `// @ts-ignore`
✅ **Dobre:** dodać proper typ do response API (`ArticleOut` interface) i użyć go

❌ **Złe:** `playwright test --update-snapshots` żeby zielone
✅ **Dobre:** zrozumieć dlaczego snapshot się zmienił, jeśli intencjonalne — update z opisem w komicie

---

## 📦 Faza 5 — Final Report

Po sukcesie wszystkich tierów, wyświetl USER-owi **zwięzły raport**:

```markdown
## ✅ `/loop-do-skutku-rao` — Sukces

**Zadanie:** <oryginalny opis user-a>
**Iteracji self-heal:** N
**Czas łączny:** ~M minut

### Co zmieniłem
**Kod:**
- `backend/articles/router.py` — nowy endpoint POST /articles/duplicate
- `backend/articles/service.py` — funkcja duplicate_article()
- `frontend/src/components/ArticlePicker.vue` — przycisk "Duplikuj"
- `e2e/tests/03-article.spec.ts` — TEST-03b duplikacja

**Migracje DB (jeśli dotyczy):**
- `backend/main.py` startup — `ALTER TABLE articles ADD COLUMN IF NOT EXISTS duplicated_from INT NULL`
- Idempotentność potwierdzona (drugi restart OK)

**Spec sync:**
- `spec/01_DATABASE_DDL.md` — kolumna `duplicated_from` w tabeli `articles`
- `spec/02_BACKEND_API.md` — sekcja "Articles" → endpoint duplicate
- `spec/19_BACKLOG.md` — pozycja B5 oznaczona ✅

### Verification — wszystko zielone
- ✅ Tier 1: vue-tsc + python compile
- ✅ Tier 2: 47 unit tests (3 nowe)
- ✅ Tier 3: smoke /health /docs /auth/login
- ✅ Tier 4: Playwright `tests/03-article.spec.ts` (5 testów)
- ✅ Tier 4.5: migracja idempotentna + spec/ zsynchronizowane
- ✅ Tier 5: MCP snapshot + screenshot → temp/verify-1234.png

### Serwery działające
- Backend: http://localhost:8000/rao/api (uvicorn --reload)
- Frontend: http://localhost:5173 (Vite dev)

### Co warto sprawdzić ręcznie
- (jeśli coś niepewne) np. wydruk PDF — wymaga ręcznej weryfikacji layoutu

### Następne kroki sugerowane
- (opcjonalnie) — kolejne pozycje z spec/19_BACKLOG.md powiązane z tym tematem
```

W przypadku **escape valve** (15 prób bez sukcesu):

```markdown
## ⚠️ `/loop-do-skutku-rao` — Wymaga interwencji

**Po 15 iteracjach nie udało się ukończyć.**

### Co zostało zrobione
<lista>

### Ostatni błąd
```
<traceback>
```

### Hipotezy
1. <hipoteza A>
2. <hipoteza B>
3. <hipoteza C>

### Co user może zrobić
- Sprawdź X
- Otwórz logi Y
- Rozważ Z

Pełny log: `temp/loop-failure-<timestamp>.md`
```

---

## 🚫 Reguły specyficzne dla trybu loop

Reguly globalne projektu są w `.windsurf/rules/` (zawsze aktywne). Ten workflow dodaje:

1. **NIE PYTAJ — RÓB.** Jeśli wymaganie niejasne, wybierz najsensowniejszą interpretację z spec/ + istniejący kod. Decyzję udokumentuj w komentarzu lub `create_memory`. User wywołał loop świadomie — chce autonomii, nie pytań.
2. **Iteruj naprawdę do skutku** — max 15 prób lub 25 minut wall-clock. Potem **escape valve** z uczciwym raportem (Faza 5 alternative).
3. **Po każdej zmianie: smoke `e2e/tests/01-login.spec.ts`** — najszybsza ochrona przed regresją. To dodatkowy obowiązek loop-a (poza 5-tier).
4. **Pełen 5-tier verification matrix obowiązkowy** — nawet jeśli wydaje się że zadanie proste. Loop = pełna pętla, bez skrótów.
5. **Final Report obowiązkowy** — user musi widzieć dowód sukcesu (lista plików + screenshot + tier'y).
6. **Migracje destruktywne (DROP/MODIFY) wymagają zgody user-a** — również w trybie autonomicznym przerywasz i pytasz przed `DROP COLUMN` / `DROP TABLE` / zmianą typu na produkcyjnych danych.

Wszystko inne (zero kill-port, root cause, design system, nie commituj automatycznie, czytaj spec, deterministyczne migracje, sync spec) — jest w regulach `rao-project`, `rao-migrations`, `rao-spec-sync` i obowiązuje **automatycznie**, też poza tym workflow.

---

## 🧪 Bonus — szybkie repro patterns

**„Backend zwraca 500"**
```pwsh
# Sprawdź ostatnie logi uvicorn (terminal gdzie odpalony)
# Albo użyj curl z verbose:
curl -v http://localhost:8000/rao/api/<endpoint>
# I porównaj request body z Pydantic schema w backend/<feature>/schemas.py
```

**„E2E test fails — nie wiadomo czemu"**
```pwsh
# Cwd: e2e
npx playwright test tests/<spec>.spec.ts --headed --debug
# Trace zostanie w test-results/ — można otworzyć:
npx playwright show-trace test-results/.../trace.zip
```

**„Frontend nie rebuilduje po zmianie"**
- Sprawdź czy Vite HMR widzi plik (powinno być w terminalu)
- Hard refresh w MCP: `mcp5_browser_evaluate` z `() => location.reload()`
- W ostateczności: nowa instancja `npm run dev` na innym porcie (3001/5174)

**„Migracja DB nie aplikuje się"**
- Sprawdź czy `@app.on_event("startup")` w `backend/main.py` ma odpowiedni ALTER
- Restart backend (Ctrl+C w terminalu uvicorn, `--reload` nie łapie zmian na startup events czasami)
- Manualnie: `mariadb -u rao_user -pRaoPass2026! rao_new -e "ALTER TABLE ..."`

**„CORS blocked"**
- Sprawdź `RAO_CORS_ORIGINS` w `.env` — port frontu musi być na liście
- Restart backend po zmianie .env

---

## 🎬 Przykład użycia

**User:** `/loop-do-skutku-rao Dodaj kolumnę "adres dostawy" w liście umów na dashboardzie. Dane są w contract.delivery_address`

**Agent (skrót działań):**

1. **Faza 0:** `list_dir`, `read_file spec/19_BACKLOG.md`, `code_search "Where is contract list table on dashboard?"` (równolegle)
2. **Faza 1:** Klasyfikacja → **Frontend-only** (kolumna już w DB i schema). Plan w `todo_list` (4 kroki).
3. **Faza 2.C:** Edycja `frontend/src/views/DashboardView.vue` — dodaję kolumnę między "Kontrahent" a "Data od".
4. **Faza 3:**
   - Tier 1: `vue-tsc --noEmit` ✅
   - Tier 4: `npx playwright test tests/04-contract.spec.ts` — fail bo nowa kolumna brak w asercji
5. **Faza 4 (próba 1):** Aktualizuję test żeby asertował nową kolumnę. ✅
6. **Faza 5:** Raport sukcesu, screenshot do `temp/verify-...png`.

---

**START komendy:** parsuj `<opis zadania>`, idź Faza 0 → 1 → 2 → 3 → (4 jeśli trzeba) → 5.

**KONIEC tylko gdy DoD zielone albo escape valve.**
