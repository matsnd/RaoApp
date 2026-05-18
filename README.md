# RAO — Wynajem Maszyn Budowlanych

Aplikacja webowa do zarządzania wynajmem maszyn budowlanych. Migracja z legacy WinForms (C# .NET) na nowoczesny stack:

- **Backend:** FastAPI + SQLAlchemy async + MariaDB
- **Frontend:** Vue 3 + Vite + TypeScript + Pinia
- **E2E:** Playwright

## Quick start (Linux / macOS)

```bash
# Setup od zera (MariaDB + Python + Node + Playwright)
bash .devin/setup.sh

# Uruchom backend + frontend razem
bash .devin/run.sh

# W przeglądarce: http://localhost:5173
# Login: admin / admin123
```

## Quick start (Windows)

```powershell
# 1. MariaDB — zainstaluj z https://mariadb.org/download/ i utwórz bazę:
mariadb -u root -p -e "CREATE DATABASE rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"
mariadb -u root -p -e "CREATE USER 'rao_user'@'localhost' IDENTIFIED BY '<<DB_PASSWORD_PLACEHOLDER>>'; GRANT ALL ON rao_new.* TO 'rao_user'@'localhost';"

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# 3. Frontend
cd frontend
npm ci
cd ..

# 4. E2E
cd e2e
npm ci
npx playwright install chromium
cd ..

# 5. .env
Copy-Item .env.example .env

# 6. Uruchom (dwa terminale)
# Terminal 1:
cd backend; .venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000

# Terminal 2:
cd frontend; npm run dev
```

## Sprawdzenie

| Endpoint | Oczekiwane |
|----------|------------|
| `http://localhost:8000/rao/api/health` | `{"status":"ok","version":"1.0.0"}` |
| `http://localhost:8000/rao/api/docs` | Swagger UI |
| `http://localhost:5173` | Login screen RAO |
| Login: `admin` / `admin123` | Dashboard z umowami |

## Testy

```bash
# Backend unit tests
cd backend && python -m pytest -x --tb=short

# Frontend type check
cd frontend && npx vue-tsc --noEmit

# E2E (oba serwery muszą działać)
cd e2e && npx playwright test --reporter=list

# Smoke regression (najszybsza ochrona przed regresją)
cd e2e && npx playwright test tests/01-login.spec.ts
```

## Struktura repo

```
backend/         FastAPI + SQLAlchemy (async, MariaDB via asyncmy)
frontend/        Vue 3 + Vite + TypeScript + Pinia
e2e/             Playwright tests
spec/            Single source of truth — DDL, API, screens, business logic
.windsurf/       Cascade (Windsurf) rules + workflows
.devin/          Devin setup & run scripts
AGENTS.md        Uniwersalna instrukcja dla agentów AI (Devin/Codex/Cursor/Cascade)
DEPLOY.md        Deploy produkcyjny (toolsmart.pl)
```

## Dla AI agentów

Pracujesz nad RAO jako agent (Devin, Cursor agent, Codex, Cascade)? **Czytaj `AGENTS.md` w root** — uniwersalna instrukcja z konwencjami, regułami migracji DB, mapą `spec/`, komendami testowymi.

Cascade (Windsurf) ma dodatkowo:
- `.windsurf/rules/rao-project.md` — stack & design (always_on)
- `.windsurf/rules/rao-migrations.md` — deterministyczne migracje (glob na pliki DB)
- `.windsurf/rules/rao-spec-sync.md` — sync `spec/` po zmianach (always_on)
- `.windsurf/workflows/loop-do-skutku-rao.md` — autonomiczny tryb 5-tier verification

## Deploy produkcyjny

Patrz `DEPLOY.md` — instrukcja deploy na shared hosting toolsmart.pl (CloudLinux + cPanel + Passenger).

## Licencja

Projekt prywatny / komercyjny. Nie publiczny.
