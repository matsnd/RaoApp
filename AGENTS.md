# AGENTS.md — RAO

> Instrukcje dla AI agentów (Devin, Codex, Cursor, Cascade, Aider) pracujących w tym repo.
> Czytaj ten plik PRZED jakimkolwiek działaniem.

> **🚀 QUICK START:**
> 1. Czytaj `spec/AGENT_PLAYBOOK.md` — znajdź swoją rolę i "Primary read"
> 2. Czytaj swój "Primary read" z AGENT_PLAYBOOK.md
> 3. Sprawdź `spec/backlog/BACKLOG.md` — co jest priorytetem (P0/P1/P2)
> 4. Zacznij od P0 — production blockers first

## Czym jest RAO

Aplikacja do wynajmu maszyn budowlanych. Migracja z legacy WinForms (C# .NET) → FastAPI + Vue 3.
Funkcje: kontrahenci, artykuły (maszyny), umowy, pozycje, warunki rozliczeniowe, raporty PDF, GUS/Nominatim, statystyki.

## Stack

| Warstwa | Technologia | Lokalizacja | Port |
|---------|-------------|-------------|------|
| DB | MariaDB (utf8mb4_polish_ci), schema `rao_new` | system | 3306 |
| Backend | FastAPI + SQLAlchemy async + asyncmy + Pydantic v2 | `backend/` | 8000 |
| Frontend | Vue 3 + Vite + TypeScript + Pinia + Axios | `frontend/` | 5173 |
| E2E | Playwright (Chromium) | `e2e/tests/` | – |
| SMTP dev | Mailpit | system | 1025 / UI 8025 |
| MCP: code analysis | codebase-memory (graf wiedzy: 9548 węzłów, 27500 krawędzi) | user config | – |
| MCP: dependency analysis | depwire (315 plików, 14492 symboli, 11259 krawędzi) | user config | – |
| MCP: database | mariadb (bezpośrednie zapytania do `rao_new`) | user config | – |
| MCP: UI vision | rao-vision (Claude Vision API) | project config | – |
| MCP: browser | playwright (headless) | project config | – |
| MCP: GitHub | github (issues, PRs) | project.local config | – |
| MCP: web search | brave-search | project.local config | – |
| MCP: reasoning | sequential-thinking | project config | – |
| MCP: persistence | memory (knowledge graph między sesjami) | project config | – |

**Kluczowe ustawienia:**
- FastAPI `root_path="/rao/api"` — wszystkie endpointy pod tym prefiksem (np. `http://localhost:8000/rao/api/health`)
- Login do aplikacji: `admin` / `admin123`
- DB user: `rao_user` / hasło `<<DB_PASSWORD_PLACEHOLDER>>` (z `.env`)

## Setup (od zera)

```bash
# 1. MariaDB
sudo service mariadb start
sudo mariadb -e "CREATE DATABASE IF NOT EXISTS rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"
sudo mariadb -e "CREATE USER IF NOT EXISTS 'rao_user'@'localhost' IDENTIFIED BY '<<DB_PASSWORD_PLACEHOLDER>>';"
sudo mariadb -e "GRANT ALL PRIVILEGES ON rao_new.* TO 'rao_user'@'localhost'; FLUSH PRIVILEGES;"

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. Frontend
cd frontend && npm ci && cd ..

# 4. E2E
cd e2e && npm ci && npx playwright install --with-deps chromium && cd ..

# 5. .env
[ -f .env ] || cp .env.example .env

# 6. Pierwszy start backendu (utworzy schemat z modeli SQLAlchemy)
cd backend && source .venv/bin/activate && timeout 10 uvicorn main:app --port 8000 || true
```

**Skrót:** `bash .devin/setup.sh` (Ubuntu/Linux)

## Uruchomienie

```bash
# Backend (terminal 1)
cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend && npm run dev

# Sprawdź:
curl http://localhost:8000/rao/api/health   # → {"status":"ok"}
curl http://localhost:5173                  # → HTML Vite
```

**Skrót:** `bash .devin/run.sh`

## Testy

```bash
# Unit (backend)
cd backend && source .venv/bin/activate && python -m pytest -x --tb=short

# Type check (frontend)
cd frontend && npx vue-tsc --noEmit

# Build check (frontend)
cd frontend && npm run build

# E2E (oba serwery muszą działać)
cd e2e && npx playwright test --reporter=list

# Smoke regression (zawsze odpalaj po zmianie!)
cd e2e && npx playwright test tests/01-login.spec.ts
```

## Konwencje kodu

### Backend (FastAPI)

Każdy moduł `backend/<feature>/`:
```
__init__.py
models.py     # SQLAlchemy (Column, ForeignKey, relationship)
schemas.py    # Pydantic v2 (Out/Create/Update, Field constraints)
service.py    # Logika biznesowa (async, AsyncSession)
router.py     # APIRouter, Depends(get_current_user), HTTP codes
```

Logika biznesowa **w service**, nie w router. Router rejestrowany w `backend/main.py`.

### Frontend (Vue 3)

`<script setup lang="ts">`, Composition API, `ref()`/`computed()`. Pinia stores w `frontend/src/stores/`.

Style **wyłącznie** przez zmienne CSS z `frontend/src/style.css`:
```css
--color-primary: #1D2B53;     /* Toolsmart navy */
--font-family: 'Montserrat', sans-serif;
--border-radius: 12px;
--shadow-card: 0 1px 3px rgba(0,0,0,0.08);
```

**Antywzorce:** inline hardcoded colors, `any` bez komentarza, mutowanie props, `v-html` z user input, brak loading/error/empty state.

## Migracje DB — DETERMINISTYCZNE

RAO **nie używa Alembic**. Schema zarządzane przez:
1. Modele SQLAlchemy w `backend/<feature>/models.py`
2. `Base.metadata.create_all` przy starcie (tworzy nowe tabele)
3. **Idempotentne `ALTER TABLE ... IF NOT EXISTS`** w `@app.on_event("startup")` w `backend/main.py`
4. DDL w `spec/core/01_database.md` jako single source of truth

**Każda zmiana DB = 4 pliki** (kolejność):
1. `spec/core/01_database.md` — finalny DDL (mirror, nie inkrementalne ALTER-y)
2. `backend/<feature>/models.py` — SQLAlchemy
3. `backend/main.py` startup — `ALTER ... IF NOT EXISTS` (lub try/except dla MariaDB <10.6)
4. Weryfikacja: restart backendu + `DESCRIBE` + drugi restart bez błędu

**Szczegółowa polityka migracji:** `spec/process/migrations.md`

**Przykład poprawnej migracji w `backend/main.py`:**
```python
@app.on_event("startup")
async def startup_migrations():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "delivery_address VARCHAR(255) NULL"
        ))
```

**ZAKAZANE:**
- Ad-hoc `ALTER TABLE` w mariadb CLI bez równoległej zmiany w `main.py` (następna sesja na czystym środowisku dostanie schema mismatch)
- ALTER bez `IF NOT EXISTS` (drugi restart rzuci "Duplicate column")
- `DROP COLUMN` / `DROP TABLE` bez wyraźnej zgody użytkownika i backupu (`mariadb-dump`)
- Modyfikacja typu kolumny przez naked `MODIFY COLUMN` na produkcyjnych danych
- Migracje są **forward-only** — brak rollbacku

## spec/ to single source of truth

Folder `spec/` opisuje aktualny stan aplikacji. Nowa struktura (reorganizacja 2026-05-17):

```
spec/
├── core/           # Single source of truth (database, API, screens, business logic, security)
├── process/        # Procedures (migrations, testing, workflow)
├── backlog/        # Planning with YAML front-matter format
├── archive/        # Historical specs
├── AGENT_PLAYBOOK.md  # Role mapping for agents
└── 00_INDEX.md     # Mapa całej specyfikacji
```

Po **każdej zmianie funkcjonalnej** zaktualizuj odpowiedni plik:

| Co zmieniłeś | Spec do update |
|--------------|----------------|
| Schema DB | `spec/core/01_database.md` |
| Endpoint REST / Pydantic | `spec/core/02_backend_api.md` |
| Widok Vue / komponent | `spec/core/03_frontend_screens.md` |
| Algorytm biznesowy | `spec/core/04_business_logic.md` |
| Routing / nawigacja | `spec/core/06_navigation_flow.md` |
| GUS/Nominatim/PDF/SMTP | `spec/core/07_integrations.md` |
| Design system / CSS | `spec/core/09_design_reference.md` |
| Security / RBAC | `spec/core/25_security.md` |
| Backlog (status: done) | `spec/backlog/BACKLOG.md` |

**Czytaj odpowiedni spec PRZED kodowaniem** — odpowiedzi na 90% pytań są tam.

**AGENT_PLAYBOOK.md** zawiera szczegółowe role mapping:
- DB Agent → `spec/core/01_database.md` + `spec/process/migrations.md`
- Backend Agent → `spec/core/02_backend_api.md` + `spec/core/04_business_logic.md`
- Frontend Agent → `spec/core/03_frontend_screens.md` + `spec/core/09_design_reference.md`
- QA Agent → `spec/process/testing.md` + `spec/backlog/BACKLOG.md`
- Tech Lead → wszystkie spec + priorytetyzacja backlog

Po zakończeniu zadania sprawdź `git diff --stat spec/core/` — pusty diff przy zmianach funkcjonalnych = niedopełniony obowiązek.

## Reguły operacyjne

1. **Root cause > symptomy** — minimalna upstream fix > obejście downstream
2. **Nie usuwaj/osłabiaj testów** bez wyraźnej zgody użytkownika (nawet "tymczasowo")
3. **Lokalne commity po każdym zadaniu** — po zakończeniu każdego zadania/feature wykonaj lokalny commit z opisem zmian. To pozwala na śledzenie postępów i łatwe przywracanie wcześniejszych stanów przez `git revert` lub `git reset`. Commit message powinien być krótki i opisywać "co i dlaczego" (nie "jak").
4. **Czytaj AGENT_PLAYBOOK.md** — znajdź swoją rolę i "Primary read" przed kodowaniem
5. **Sprawdź backlog/BACKLOG.md** — zacznij od P0 (production blockers)
6. **Po każdej zmianie kodu → smoke `e2e/tests/01-login.spec.ts`** (najszybsza ochrona przed regresją)
7. **Port zajęty?** Użyj kolejnego wolnego (8001, 5174). NIGDY `kill-port`/`pkill`/`taskkill` cudzych procesów. Po zmianie portu backendu zaktualizuj `VITE_API_URL` w `frontend/.env`.
8. **Sekrety w `.env`**, nigdy w kodzie. `.env` jest w `.gitignore`. Szablon: `.env.example`.

## Lokalne commity — śledzenie postępów

Po każdym zakończonym zadaniu wykonaj lokalny commit. To tworzy historię zmian i pozwala na:

- **Śledzenie postępów** — widoczne co zostało zrobione w danym czasie
- **Easy rollback** — `git revert HEAD` cofa ostatnie zmiany
- **Debugging** — można porównać stany przed/po przez `git diff`
- **Eksperymenty** — gałęzie do testowania bez ryzyka

### Format commit message

```
feat(category): krótki opis co i dlaczego

Szczegóły jeśli potrzebne (opcjonalne).
```

Przykłady:
```
feat(contracts): add delivery_address field to contracts
fix(auth): resolve JWT token expiration edge case
refactor(frontend): extract ArticlePicker to reusable component
```

### Procedura commitowania

1. **Sprawdź zmiany:** `git status` i `git diff`
2. **Dodaj pliki:** `git add <pliki>` lub `git add .`
3. **Commit:** `git commit -m "opis zmiany"`
4. **Weryfikacja:** `git log --oneline -3`

### Przywracanie stanów

- **Cofnij ostatni commit:** `git revert HEAD`
- **Reset do konkretnego commita:** `git reset --hard <commit-hash>`
- **Porównaj stany:** `git diff HEAD~1 HEAD`

<Note>
Lokalne commity NIE są automatycznie pushowane do origin. Pushuj tylko gdy zmiany są stabilne i przetestowane.
</Note>

## Mapa plików

```
backend/
├── main.py              # rejestracja routerów + startup migrations
├── config.py            # Pydantic Settings (czyta .env)
├── database.py          # async engine + AsyncSessionLocal
├── auth/                # JWT, użytkownicy, role
├── contractors/         # CRUD kontrahentów
├── articles/            # CRUD maszyn
├── contracts/           # umowy + pozycje + warunki
├── settings/            # firma, handlowcy, szablony usług
├── reports/             # PDF (WeasyPrint, Jinja2)
├── stats/               # statystyki + KPI
├── explorer/            # eksplorator kontrahent/umowa/maszyna
├── integrations/        # GUS SOAP, Nominatim
├── shared/              # utils
├── tests/unit/          # pytest
├── migrate.py           # ↪ jednorazowy skrypt migracji STARYCH DANYCH (NIE schema!)
└── requirements.txt

frontend/src/
├── views/               # routowalne (DashboardView, ContractFormView, ...)
├── components/          # reuzywalne (DataGrid, ArticlePicker, ...)
├── stores/              # Pinia
├── composables/         # use*()
├── router/              # vue-router + auth guard
├── style.css            # CSS variables Toolsmart
└── main.ts

e2e/tests/
├── 01-login.spec.ts     # ← smoke regression
├── 02-contractor.spec.ts
├── 03-article.spec.ts
├── 04-contract.spec.ts
├── 05-settings.spec.ts
└── helpers.ts           # waitForBackend, login, navigateTo

spec/                    # ← czytaj PRZED kodowaniem
├── 00_INDEX.md          # przegląd całości
├── AGENT_PLAYBOOK.md    # role mapping dla agentów (czytaj to jako pierwsze!)
├── core/                # SSoT dla aktualnego stanu
│   ├── 01_database.md       # schema DB
│   ├── 02_backend_api.md    # endpointy REST
│   ├── 03_frontend_screens.md # ekrany Vue
│   ├── 04_business_logic.md  # algorytmy
│   ├── 06_navigation_flow.md # routing
│   ├── 09_design_reference.md # design system
│   └── 25_security.md        # RBAC, auth
├── process/             # procedury
│   ├── migrations.md        # polityka migracji DB
│   └── testing.md           # strategia testowania
├── backlog/             # backlog z YAML front-matter
│   └── BACKLOG.md           # P0/P1/P2 tasks
└── archive/             # historyczne specy
```

## Tryb autonomiczny "do skutku"

Gdy zadanie wymaga pełnej autonomii z self-healingiem i pełną weryfikacją:

1. Klasyfikuj: DB-only / Backend / Frontend / Cross-stack / Bugfix / Refactor
2. Plan w todo (3-8 kroków, jeden in_progress na raz)
3. Implementacja warstwowa (DB → backend → frontend → e2e → spec sync)
4. **6-tier verification matrix:**
   - Tier 1: static (`vue-tsc --noEmit` + `python -m compileall` + MCP graph analysis: `depwire.get_health_score`, `codebase-memory.query_graph` dla complexity hotspots)
   - Tier 2: unit (`pytest -x --tb=short`)
   - Tier 3: smoke (curl `/health`, `/openapi.json`, `/auth/login`)
   - Tier 4: e2e (`npx playwright test`)
   - Tier 4.5: migration & spec consistency (drugi restart + `git diff spec/core/`)
   - Tier 5: manual (browser navigate + snapshot + screenshot)
   - Tier 6: local commit (opis zmian, historia do rollbacku)
5. Self-healing loop: max 15 iteracji, root-cause analysis, escape valve z uczciwym raportem
6. Final report: lista plików zmienionych + spec/ updated + screenshot dowodu + hash lokalnego commita

## Reguły agentów (mapa konfiguracji)

| Agent | Konfiguracja |
|-------|--------------|
| **Cascade** (Windsurf) | `.windsurf/rules/` (3 pliki) + `.windsurf/workflows/loop-do-skutku-rao.md` |
| **Cursor agent** | `.cursor/rules/` (TODO — sklonuj z `.windsurf/rules/`) |
| **Devin** | ten plik (`AGENTS.md`) + `.devin/setup.sh` + `.devin/run.sh` + Knowledge w panelu |
| **Codex / Aider / inni** | ten plik (`AGENTS.md`) — uniwersalny standard |

## Dokumentacja rozszerzona

- **Specyfikacja:** `spec/AGENT_PLAYBOOK.md` (role mapping), `spec/00_INDEX.md` (mapa)
- **Backlog:** `spec/backlog/BACKLOG.md` (P0/P1/P2 tasks z YAML front-matter)
- **Procesy:** `spec/process/migrations.md`, `spec/process/testing.md`
- Pełny plan budowy od zera: `.windsurf/workflows/build-rao-app.md`
- Cross-role audit: `.windsurf/workflows/cross-role-audit.md`
- Loop autonomiczny (6-tier): `.windsurf/workflows/loop-do-skutku-rao.md`
- Deploy produkcyjny: `DEPLOY.md`
- Stack reguły szczegółowe (Cascade): `.windsurf/rules/rao-project.md`
- Migracje DB szczegółowe (Cascade): `.windsurf/rules/rao-migrations.md`
- Spec sync szczegółowe (Cascade): `.windsurf/rules/rao-spec-sync.md`

## Technical Solutions Storage

Wszystkie odkryte techniczne rozwiązania są zapisywane w `spec/technical/`. Służy to do szybkiego odzyskania wiedzy po restarcie AI agenta.

### Struktura
```
scripts/                     # WSZYSTKIE helper Python scripts (root-level, discoverable) + *.md opisy
spec/technical/
├── TECHNICAL_SOLUTIONS.md    # Główny indeks
└── patterns/                 # Wzorce architektoniczne (PDF extraction, JWT, etc.)
```

> **Kanoniczna lokalizacja helper scripts:** `scripts/` (root-level) — tu żyją WSZYSTKIE pomocnicze skrypty Python (reset_db, seed_demo_data, migrate_*, check_*, audit_db, export_*, itd.). `backend/` root zawiera TYLKO pliki aplikacji (config.py, database.py, main.py, migrate.py, passenger_wsgi.py, wsgi.py). Skrypty w `scripts/` mają `sys.path.append('../backend')` — uruchamiaj z repo root jako `python scripts/<name>.py`.

### Szybki dostęp
- **Indeks:** `spec/technical/TECHNICAL_SOLUTIONS.md`
- **Skrypty:** `scripts/*.py` + `scripts/*.md`
- **Wzorce:** `spec/technical/patterns/*.md`

### Dodawanie nowych rozwiązań
Po każdym zadaniu:
1. **Skrypt:** Dodaj do `scripts/` z opisem `*.md`
2. **Wzorzec:** Jeśli to powtarzalny pattern → dodaj do `spec/technical/patterns/`
3. **Indeks:** Zaktualizuj `spec/technical/TECHNICAL_SOLUTIONS.md`

### Przykłady rozwiązań
- **PDF Extraction:** fitz (PyMuPDF) na Windows → `spec/technical/patterns/pdf_extraction.md`
- **Vision AI:** rao-vision MCP do analizy layout → `spec/technical/patterns/vision_ai_analysis.md`
- **WeasyPrint Images:** file:// URI z absolute path → `spec/technical/patterns/weasyprint_images.md`
- **JWT Auth:** reset hasła admina, token → `spec/technical/patterns/jwt_auth_e2e.md`
- **Port Management:** alternatywne porty (8001, 5174) → `spec/technical/patterns/port_management.md`
- **Migracje DB:** idempotentne ALTER TABLE → `spec/technical/patterns/migrations_mariadb.md`
- **Contract Pricing Grids:** KISS split dla umów S/U i uproszczone usługi dodatkowe → `spec/technical/patterns/contract_pricing_grids.md`
