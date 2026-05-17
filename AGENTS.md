# AGENTS.md — RAO

> Instrukcje dla AI agentów (Devin, Codex, Cursor, Cascade, Aider) pracujących w tym repo.
> Czytaj ten plik PRZED jakimkolwiek działaniem.

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

**Kluczowe ustawienia:**
- FastAPI `root_path="/rao/api"` — wszystkie endpointy pod tym prefiksem (np. `http://localhost:8000/rao/api/health`)
- Login do aplikacji: `admin` / `admin123`
- DB user: `rao_user` / hasło `RaoPass2026!` (z `.env`)

## Setup (od zera)

```bash
# 1. MariaDB
sudo service mariadb start
sudo mariadb -e "CREATE DATABASE IF NOT EXISTS rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"
sudo mariadb -e "CREATE USER IF NOT EXISTS 'rao_user'@'localhost' IDENTIFIED BY 'RaoPass2026!';"
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
4. DDL w `spec/01_DATABASE_DDL.md` jako single source of truth

**Każda zmiana DB = 4 pliki** (kolejność):
1. `spec/01_DATABASE_DDL.md` — finalny DDL (mirror, nie inkrementalne ALTER-y)
2. `backend/<feature>/models.py` — SQLAlchemy
3. `backend/main.py` startup — `ALTER ... IF NOT EXISTS` (lub try/except dla MariaDB <10.6)
4. Weryfikacja: restart backendu + `DESCRIBE` + drugi restart bez błędu

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

Folder `spec/` opisuje aktualny stan aplikacji. Po **każdej zmianie funkcjonalnej** zaktualizuj odpowiedni plik:

| Co zmieniłeś | Spec do update |
|--------------|----------------|
| Schema DB | `spec/01_DATABASE_DDL.md` |
| Endpoint REST / Pydantic | `spec/02_BACKEND_API.md` |
| Widok Vue / komponent | `spec/03_FRONTEND_SCREENS.md` |
| Algorytm biznesowy | `spec/04_BUSINESS_LOGIC.md` |
| Routing / nawigacja | `spec/06_NAVIGATION_FLOW.md` |
| GUS/Nominatim/PDF/SMTP | `spec/07_INTEGRATIONS.md` |
| Design system / CSS | `spec/09_DESIGN_REFERENCE.md` |
| Backlog (oznacz ✅ done) | `spec/19_BACKLOG.md` |

**Czytaj odpowiedni spec PRZED kodowaniem** — odpowiedzi na 90% pytań są tam.

Po zakończeniu zadania sprawdź `git diff --stat spec/` — pusty diff przy zmianach funkcjonalnych = niedopełniony obowiązek.

## Reguły operacyjne

1. **Root cause > symptomy** — minimalna upstream fix > obejście downstream
2. **Nie usuwaj/osłabiaj testów** bez wyraźnej zgody użytkownika (nawet "tymczasowo")
3. **Lokalne commity po każdym zadaniu** — po zakończeniu każdego zadania/feature wykonaj lokalny commit z opisem zmian. To pozwala na śledzenie postępów i łatwe przywracanie wcześniejszych stanów przez `git revert` lub `git reset`. Commit message powinien być krótki i opisywać "co i dlaczego" (nie "jak").
4. **Po każdej zmianie kodu → smoke `e2e/tests/01-login.spec.ts`** (najszybsza ochrona przed regresją)
5. **Port zajęty?** Użyj kolejnego wolnego (8001, 5174). NIGDY `kill-port`/`pkill`/`taskkill` cudzych procesów. Po zmianie portu backendu zaktualizuj `VITE_API_URL` w `frontend/.env`.
6. **Sekrety w `.env`**, nigdy w kodzie. `.env` jest w `.gitignore`. Szablon: `.env.example`.

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
├── 01_DATABASE_DDL.md   # SSoT dla schema
├── 02_BACKEND_API.md    # SSoT dla endpointów
├── 03_FRONTEND_SCREENS.md
├── 04_BUSINESS_LOGIC.md
├── ... (05-25)
└── 19_BACKLOG.md        # aktualny backlog (P0/P1/P2)
```

## Tryb autonomiczny "do skutku"

Gdy zadanie wymaga pełnej autonomii z self-healingiem i pełną weryfikacją:

1. Klasyfikuj: DB-only / Backend / Frontend / Cross-stack / Bugfix / Refactor
2. Plan w todo (3-8 kroków, jeden in_progress na raz)
3. Implementacja warstwowa (DB → backend → frontend → e2e → spec sync)
4. **6-tier verification matrix:**
   - Tier 1: static (`vue-tsc --noEmit` + `python -m compileall`)
   - Tier 2: unit (`pytest -x --tb=short`)
   - Tier 3: smoke (curl `/health`, `/openapi.json`, `/auth/login`)
   - Tier 4: e2e (`npx playwright test`)
   - Tier 4.5: migration & spec consistency (drugi restart + `git diff spec/`)
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

- Pełny plan budowy od zera: `.windsurf/workflows/build-rao-app.md`
- Cross-role audit: `.windsurf/workflows/cross-role-audit.md`
- Loop autonomiczny (5-tier): `.windsurf/workflows/loop-do-skutku-rao.md`
- Deploy produkcyjny: `DEPLOY.md`
- Stack reguły szczegółowe (Cascade): `.windsurf/rules/rao-project.md`
- Migracje DB szczegółowe (Cascade): `.windsurf/rules/rao-migrations.md`
- Spec sync szczegółowe (Cascade): `.windsurf/rules/rao-spec-sync.md`
