---
trigger: always_on
description: Core kontekst projektu RAO — stack, porty, login, design system, smoke regression
---

# Kontekst projektu RAO

Aplikacja do wynajmu maszyn budowlanych. Migracja z legacy WinForms (C#) → FastAPI + Vue 3.

## Stack & porty (zapamiętaj na pamięć)

| Warstwa | Technologia | Lokalizacja | Komenda | Port |
|---------|-------------|-------------|---------|------|
| DB | MariaDB (utf8mb4_polish_ci) | schema `rao_new` | systemowy | 3306 |
| Backend | FastAPI + SQLAlchemy async + asyncmy | `backend/` | `uvicorn main:app --reload --port 8000` | 8000 |
| Frontend | Vue 3 + Vite + TS + Pinia + Axios | `frontend/` | `npm run dev` | 5173 |
| E2E | Playwright | `e2e/tests/*.spec.ts` | `npx playwright test` | – |
| SMTP dev | Mailpit | – | `mailpit` | 1025 / UI 8025 |

**Krytyczne ustawienia:**
- FastAPI `root_path="/rao/api"` → wszystkie endpointy są pod tym prefiksem (np. `http://localhost:8000/rao/api/health`)
- E2E credentials: `admin` / `admin123` (w `e2e/tests/helpers.ts`)
- DB user: `rao_user` / hasło `<<DB_PASSWORD_PLACEHOLDER>>` (z `.env`)

## Reguła portów (wzmacnia user global rule)

- ❌ NIGDY `kill-port`, `pkill -f`, `taskkill /IM`. Cudze procesy nietykalne.
- ✅ Port zajęty → start na kolejnym wolnym (8001, 5174…)
- ✅ Po zmianie portu backendu → zaktualizuj `VITE_API_URL` w `frontend/.env`
- ✅ W finalnym raporcie ZAWSZE podaj na jakim porcie działają serwery

## Design system Toolsmart (NIENARUSZALNY)

Zmienne CSS są w `frontend/src/style.css`. Używaj **wyłącznie** ich, nigdy hardcoded.

```css
--color-primary: #1D2B53;     /* Navy — sidebar, nagłówki, buttons, table headers */
--color-bg-white: #FFFFFF;
--color-bg-light: #F8F9FA;
--font-family: 'Montserrat', sans-serif;
--border-radius: 12px;        /* karty, modale, inputy */
--shadow-card: 0 1px 3px rgba(0,0,0,0.08);
```

Antywzorce frontendu:
- Inline styles z hardcoded colors
- `any` w TS bez komentarza wyjaśniającego
- Mutowanie props
- `v-html` z user inputem (XSS)
- Brak loading/error/empty state

## Mapa kluczowych plików

```
spec/                  ← single source of truth (czytaj PRZED kodowaniem)
backend/main.py        ← rejestracja routerów + startup migrations
backend/<feature>/     ← models.py, schemas.py, service.py, router.py
backend/tests/unit/    ← pytest unit tests
frontend/src/views/    ← routowalne widoki (DashboardView, ContractFormView)
frontend/src/components/ ← reuzywalne (DataGrid, ArticlePicker)
frontend/src/stores/   ← Pinia
e2e/tests/             ← Playwright e2e (01-login.spec.ts to smoke regression)
e2e/tests/helpers.ts   ← waitForBackend, login, navigateTo
```

## Reguły operacyjne dla każdego zadania

1. **Czytaj `spec/` PRZED kodowaniem** — odpowiedzi na 90% pytań są tam
2. **Po każdej zmianie kodu → smoke `e2e/tests/01-login.spec.ts`** (najszybsza ochrona przed regresją)
3. **Root cause > symptomy** — minimalny upstream fix > obejście downstream
4. **Nie usuwaj/osłabiaj testów** bez wyraźnej zgody user-a
5. **Spec/ to single source of truth** — patrz reguła `rao-spec-sync`
6. **Zmiany DB tylko przez deterministyczne migracje** — patrz reguła `rao-migrations`
7. **Nie commituj automatycznie** — workflow nie tworzy gitowych commitów

## Quick tooling cheatsheet (Cascade)

| Sytuacja | Narzędzie |
|----------|-----------|
| Eksploracja "gdzie jest X?" | `code_search` (subagent — pierwszy wybór) |
| Targeted search w pliku | `grep_search` z `Includes` |
| Plan zadania (3+ kroki) | `todo_list` (jeden `in_progress` na raz) |
| Kompleks decyzyjny | `mcp6_sequentialthinking` |
| Manualny test UI | `mcp5_browser_navigate` + `_snapshot` + `_console_messages` |
| Szybki dowód działania | `mcp5_browser_take_screenshot` → `temp/verify-*.png` |
| Komenda systemowa | `run_command` z `Cwd` (NIGDY `cd` w CommandLine) |

**Złota zasada:** niezależne tool calls → wywołuj **równolegle** w jednym bloku.

## Tryb autonomiczny "do skutku"

Gdy user prosi o autonomiczne wykonanie zadania z self-healingiem i pełną weryfikacją (5-tier matrix) → użyj workflow `/loop-do-skutku-rao`.
