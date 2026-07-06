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

## Deterministyczna migracja i seed danych demo

Baza składa się z dwóch światów:
- **Archiwum** (`archive_*`) — 740 umów legacy ze starej bazy WinForms (gruba krecha, tylko do odczytu)
- **Demo** (`contracts`, `contract_positions`, etc.) — 64 umowy demo z seeda (do prezentacji)

Orkiestrator `migrate_all.py` wykonuje 6 kroków:

| Krok | Nazwa | Opis |
|------|-------|------|
| 1 | `legacy` | Migracja legacy dump → `rao_new` (DROP bazy! wymaga `--confirm-drop`) |
| 2 | `archive` | Archive split: legacy → `archive_*` (gruba krecha) |
| 2b | `clean` | Czyszczenie tabel demo (bez archiwizacji — dla `--reseed`) |
| 3 | `demo` | Seed danych demo (umowy + lokalizacje + zestawy usług + FA-pending) |
| 4 | `fa` | Faktury w Fakturowni (backfill + FA-pending) |
| 5 | `verify` | Weryfikacja środowiska demo |

### Pełny reset od zera (DROP bazy + wszystko od nowa)

```bash
cd backend
python migrate_all.py --steps 1-5 --confirm-drop
```

Co robi:
1. DROP bazy `rao_new` + recreate
2. Import dumpa starej bazy WinForms (`temp/toolsmart_roa_*.sql`) → 740 umów legacy
3. Archiwizacja legacy → `archive_*` (tabele oryginalne wyczyszczone)
4. Seed 64 umów demo (10 aktywnych FA-pending + 18 zakończonych + 36 rozliczonych)
5. Faktury w Fakturowni dla rozliczonych + FA-pending czekające (demo "Pobierz z FA")
6. Weryfikacja: liczby, lokalizacje, FA

**Wymagania:**
- Dump starej bazy w `temp/toolsmart_roa_*.sql`
- `.env` z `RAO_DATABASE_URL`, `RAO_FAKTUROWNIA_ENC_KEY`, `RAO_FAKTUROWNIA_API_TOKEN`, `RAO_FAKTUROWNIA_DOMAIN_SUBDOMAIN`
- MariaDB dostępna na `localhost:3306`

### Re-seed demo (bez DROP, archiwum nietknięte)

```bash
cd backend
python migrate_all.py --reseed
```

Co robi (kroki 2b-5):
1. Czyści tabele demo (`contracts`, `contract_positions`, `position_conditions`, `contract_service_fees`, `contract_settlements`) — **bez archiwizacji** (demo dane nie idą do archiwum)
2. Seed 64 umów demo od nowa
3. Faktury FA
4. Weryfikacja

Archiwum (740 umów legacy) pozostaje nietknięte.

### Tylko seed (bez czyszczenia, idempotentny)

```bash
cd backend
python migrate_all.py --steps 3-5
```

Seed jest idempotentny (`get_or_create` po numerze umowy) — bezpieczny do uruchomienia bez czyszczenia.

### Tylko faktury FA

```bash
cd backend
python migrate_all.py --steps 4
```

Wymaga tokenu FA w `.env` (`FAKTUROWNIA_API_TOKEN` lub `RAO_FAKTUROWNIA_API_TOKEN`).

### Lista kroków

```bash
cd backend
python migrate_all.py --list
```

### Dane demo (po seedzie)

| Metryka | Wartość |
|---------|---------|
| Umowy demo | 64 (10 aktywnych FA-pending + 18 zakończonych + 36 rozliczonych) |
| Archiwum legacy | 740 umów (ID 6134-15492, z starej bazy WinForms) |
| Rozliczenia | 156 (134 source=fakturownia + 22 source=manual) |
| FA-pending (demo "Pobierz z FA") | 28 (10 aktywnych + 18 zakończonych, faktury czekają w Fakturowni) |
| Lokalizacje | 12 miast (Warszawa, Kraków, Poznań, Wrocław, Łódź, Gdynia, Gdańsk, Katowice, Bydgoszcz, Lublin, Szczecin, Radom) — wszystkie z PNA |
| Integracja FA | włączona (bootstrap z env) |

### 10 aktywnych umów FA-pending (do demo rozliczeń)

| Numer | Miasto | Date from | Date to | Days left |
|-------|--------|-----------|---------|-----------|
| S010/2026G | Lublin | 06-18 | 07-09 | 3 |
| S007/2026 | Gdańsk | 06-24 | 07-15 | 9 |
| S008/2026G | Katowice | 06-22 | 07-20 | 14 |
| S004/2026G | Wrocław | 06-30 | 07-21 | 15 |
| S009/2026 | Bydgoszcz | 06-20 | 07-25 | 19 |
| S005/2026 | Łódź | 06-28 | 07-26 | 20 |
| S001/2026 | Warszawa | 07-06 | 07-27 | 21 |
| S006/2026G | Gdynia | 06-26 | 07-31 | 25 |
| S002/2026G | Kraków | 07-04 | 08-01 | 26 |
| S003/2026 | Poznań | 07-02 | 08-06 | 31 |

**Demo flow rozliczeń:** otwórz aktywną umowę → "Pobierz z Fakturowni" → rozliczenia tworzą się na żywo → zapisz → następna umowa (10 sztuk do przejścia).

### Backup bazy (przed re-seed)

```bash
# Backup do _backups/ (gitignored)
mkdir -p _backups
mariadb-dump --user=rao_user --password='<<DB_PASSWORD>>' --host=localhost --port=3306 \
  --single-transaction --routines --triggers rao_new > _backups/rao_new_backup_$(date +%Y%m%d).sql

# Przywrócenie z backupu
mariadb --user=rao_user --password='<<DB_PASSWORD>>' --host=localhost --port=3306 rao_new < _backups/rao_new_backup_YYYYMMDD.sql
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
