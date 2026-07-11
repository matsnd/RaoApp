# RAO — kontekst stacku (wklejany do KAZDEGO spawnu)

Aplikacja do wynajmu maszyn budowlanych. Migracja legacy WinForms (C#) → FastAPI + Vue 3.

## Stack & porty

| Warstwa | Tech | Lokalizacja | Komenda | Port |
|---------|------|-------------|---------|------|
| DB | MariaDB `rao_new` (utf8mb4_polish_ci) | — | systemowy | 3306 |
| Backend | FastAPI + SQLAlchemy async + asyncmy + Pydantic v2 | `backend/` | `uvicorn main:app --reload --port 8000` | 8000 |
| Frontend | Vue 3 + Vite + TS + Pinia + Axios | `frontend/` | `npm run dev` | 5173 |
| E2E | Playwright | `e2e/tests/*.spec.ts` | `npx playwright test` | — |
| SMTP dev | Mailpit | — | `mailpit` | 1025 / UI 8025 |

- FastAPI `root_path="/rao/api"` → wszystkie endpointy pod tym prefiksem
- Login dev: `admin` / `admin123`; DB user `rao_user`, haslo z `.env`
- Port zajety → start na kolejnym wolnym (8001, 5174...); NIGDY kill-port/pkill/taskkill

## Design system Toolsmart (NIENARUSZALNY)

Zmienne w `frontend/src/style.css` — uzywaj WYLACZNIE ich:
`--color-primary: #1D2B53` (navy) · `--color-bg-white: #FFFFFF` · `--color-bg-light: #F8F9FA`
`--font-family: 'Montserrat'` · `--border-radius: 12px` · `--shadow-card: 0 1px 3px rgba(0,0,0,0.08)`

Antywzorce: inline hardcoded colors · `any` bez komentarza · mutowanie props · `v-html` z user inputem · brak loading/error/empty state

## MCP (masz PELNY dostep — jestes subagent_general)

- `codebase-memory.search_graph` — funkcje/klasy/routy (takze `semantic_query`); `get_code_snippet`, `trace_path`, `query_graph` (Cypher, np. N+1: `linear_scan_in_loop >= 1`)
- `depwire.get_dependencies` / `get_dependents` / `impact_analysis` / `get_file_context` — blast radius przed zmiana
- `mariadb.query_database` — read-only SQL (SELECT/SHOW/DESCRIBE/EXPLAIN). Write → `exec` z `mariadb -u rao_user ... -e`
- `rao-vision.screenshot_and_analyze` / `analyze_screenshot` — TYLKO gdy weryfikacja programatyczna niemozliwa
- Playwright MCP — E2E, screenshoty

Uzywaj graph tools ZAMIAST grep do zaleznosci; grep do string literals.

## Spec/ = single source of truth

Mapa: DB → `01_database.md` + `08_migration_plan.md` · API → `02_backend_api.md` · Logika/algorytmy → `04_business_logic.md` · Integracje (GUS/PDF/Fakturownia) → `07_integrations.md` · Wydruki/KPI → `11_reports_stats.md` · Screens → `03_frontend_screens.md` · Design → `09_design_reference.md` · Security → `25_security.md` · Testy → `17_testing_plan.md` · Backlog → `spec/backlog/BACKLOG.md` (status max `team-verified`; `user/client-verified` = czlowiek). FROZEN (nie aktualizuj): 12/13/14/18, AUDYT_*, archive/, archiwum/

## Format HANDOFF (obowiazkowy output)

```
## HANDOFF
**CO ZROBILEM:** <konkret, pliki + 1-zdaniowy opis kazdego>
**DIFF SUMMARY:** <wklej git diff --stat>
**GOTOWE DLA:** <nastepna rola + co moze uzyc>
**BLOCKERY:** <lista lub "brak">
**EVIDENCE:** <sciezki .devin/_evidence/<rola>/... — realny output, nie deklaracja>
**SPEC UPDATE:** <ktore pliki spec/ zaktualizowane, lub "brak — bo ...">
```

NIE edytuj `.devin/_session_context.md` (pisze tylko orkiestrator). Evidence zapisuj do `.devin/_evidence/<twoja-rola>/`.
