# RAO — Macierz Testów (Test Matrix)

> **Cel:** Pełna macierz pokrycia testowego wszystkich funkcjonalności RAO.
> Mapuje każdą funkcjonalność z DECISION_LOG.md na testy unit, e2e, vision.
> Aktualizowane przy każdej zmianie testów.

---

## Legenda

| Symbol | Znaczenie |
|--------|-----------|
| ✅ | Test istnieje i przechodzi |
| ⚠️ | Test istnieje ale flaky / wymaga naprawy |
| ❌ | Brak testu — do dodania |
| 📸 | Wymaga vision verification (rao-vision) |
| 🔒 | Test bezpieczeństwa |
| 📄 | Test PDF (PyMuPDF / wizualny) |

---

## Statystyki pokrycia (stan 2026-07-05)

| Warstwa | Liczba testów | Pliki |
|---------|---------------|-------|
| **Backend unit** | 296 | 25 plików `test_*.py` |
| **E2E Playwright** | 108 | 13 plików `*.spec.ts` |
| **Vision (rao-vision)** | 0 | do dodania |
| **Total** | 404 | 38 plików |

---

## P0 — Production Blockers

| ID | Funkcjonalność | Unit | E2E | Vision | Status |
|----|----------------|------|-----|--------|--------|
| P0-030 | UNIQUE contract.number + FOR UPDATE | ✅ test_contracts.py | ✅ 04-contract.spec.ts | — | ✅ |
| P0-031 | XSS w PDF — autoescape | ✅ test_pdf_options.py | ✅ 07-reports.spec.ts | — | ✅ |
| P0-032 | build_contract_data mutuje sesję | ✅ test_contracts.py | — | — | ✅ |
| P0-033 | recalculate_total — kaskadowy | ✅ test_calc.py (17) | ✅ 07-reports.spec.ts | 📸 | ✅ |
| P0-034 | ContractUpdate exclude_unset | ✅ test_contracts.py | ✅ 04-contract.spec.ts | — | ✅ |
| P0-035 | N+1 queries — selectinload | ✅ test_contracts.py | ✅ 04-contract.spec.ts | — | ✅ |
| P0-036 | Stack trace disclosure | ✅ 08-auth-security.spec.ts | — | ✅ |
| P0-054 | Kategorie — normalizacja + polish_ci | ✅ test_categories.py (19) | ✅ 05-settings.spec.ts | — | ✅ |

---

## P1 — Must-Have

| ID | Funkcjonalność | Unit | E2E | Vision | Status |
|----|----------------|------|-----|--------|--------|
| P1-014 | Błędne obliczanie daty końcowej | ✅ test_contracts.py | ✅ 04-contract.spec.ts | — | ✅ |
| P1-015 | PDF — ukryć telefony | ✅ test_pdf_options.py | ✅ 11-pdf-verification.spec.ts | 📸 | ✅ |
| P1-016 | PDF Protokół ZO — adres dostawy | ✅ test_pdf_options.py | ✅ 11-pdf-verification.spec.ts | 📸 | ✅ |
| P1-017 | Nominatim — auto-fill adresu | ✅ test_fakturownia_service.py | ✅ 02-contractor.spec.ts | — | ✅ |
| P1-018 | PDF — usuń pieczątkę str.1 | ✅ test_pdf_options.py | ✅ 11-pdf-verification.spec.ts | 📸 | ✅ |
| P1-019 | PDF Umowa U — redesign | ✅ test_pdf_options.py | ✅ 11-pdf-verification.spec.ts | 📸 | ⚠️ user-verified |
| P1-020 | PDF — rozliczenie kaskadowe | ✅ test_calc.py | ✅ 07-reports.spec.ts | 📸 | ⚠️ user-verified |
| P1-021 | Pole "Wartość" → ekran rozliczenia | ✅ test_contracts.py | ✅ 04-contract.spec.ts | — | ✅ |
| P1-022 | Nazewnictwo S i G dla Gdańska | ✅ test_contracts.py | ✅ 04-contract.spec.ts | — | ⚠️ user-verified |
| P1-037 | delete_contract guard is_settled | ✅ test_contracts.py | ✅ 04-contract.spec.ts | — | ✅ |
| P1-038 | Indeksy DB (5 kolumn) | ✅ test_contracts.py | — | — | ✅ |
| P1-039 | Walidacja date_from > date_to | ✅ test_contracts.py | ✅ 06-analytics.spec.ts | — | ✅ |
| P1-040 | is_settled blokuje mutacje pozycji | ✅ test_contracts.py | ✅ 04-contract.spec.ts | — | ✅ |
| P1-041 | JWT fallback "change-me" usunięty | ✅ 08-auth-security.spec.ts | — | ✅ |
| P1-042 | Frontend logout + redirect + baseURL | — | ✅ 01-login.spec.ts | — | ✅ |
| P1-043 | Frontend memory leaks | — | ✅ 10-ux-screenshots.spec.ts | — | ✅ |
| P1-044 | localStorage 'rao_token' | — | ✅ 01-login.spec.ts | — | ✅ |
| P1-045 | _build_conditions_text dedup | ✅ test_format_conditions.py (4) | — | — | ✅ |
| P1-055 | Branch — migracja + /stats/by-branch | ✅ test_stats_branch.py (12) | ❌ | — | ✅ unit, ❌ e2e |
| P2-060 | Statystyki — gruba krecha legacy | ✅ test_p2_065_stats_fixes.py (18) | ✅ 06-analytics.spec.ts | — | ✅ |
| P2-062 | Archiwum — migracja archive_* | ✅ test_archive.py (22) | ✅ tmp_archive_drilldown.spec.ts | — | ✅ |

---

## P2 — Should-Have

| ID | Funkcjonalność | Unit | E2E | Vision | Status |
|----|----------------|------|-----|--------|--------|
| P2-028 | Statystyki miast via PNA | ✅ test_stats_period.py | ✅ 06-analytics.spec.ts | — | ✅ |
| P2-029 | Statystyki — audyt determinizmu | ✅ test_stats_period.py | ✅ 06-analytics.spec.ts | — | ✅ |
| P2-047 | Rate limiting /auth/login | ✅ test_auth_ratelimit.py (8) | ✅ 08-auth-security.spec.ts | — | ✅ |
| P2-048 | Swagger docs_url=None prod | — | ✅ 08-auth-security.spec.ts | — | ✅ |
| P2-049 | Frontend error/loading/empty states | — | ✅ 10-ux-screenshots.spec.ts | 📸 | ✅ |
| P2-050 | Frontend form validation | — | ✅ 10-ux-screenshots.spec.ts | — | ✅ |
| P2-051 | Cache statystyk TTL 5 min | ✅ test_cache.py (22) | ❌ | — | ✅ unit, ❌ e2e |
| P2-052 | /explorer/locations/{city} SQL | ✅ test_explorer_archival_filter.py | ✅ 06-analytics.spec.ts | — | ✅ |
| P2-053 | /stats/positions paginacja | ✅ test_stats_period.py | ✅ 06-analytics.spec.ts | — | ✅ |
| P2-056 | contract_type (S/U) grupowanie | ✅ test_stats_contract_type.py (10) | ❌ | — | ✅ unit, ❌ e2e |
| P2-057 | is_external nie blokuje | ✅ test_fleet_external_filter.py (9) | ✅ 03-article.spec.ts | — | ✅ |
| P2-058 | Fakturownia OID + product cache | ✅ test_fakturownia_product_cache.py (7) | ✅ 05-settings.spec.ts | — | ✅ |
| P2-059 | Usługi dodatkowe per-artikel | ✅ test_fee_parser.py (18) | ✅ 12-fee-presets-ui.spec.ts | — | ✅ |
| P2-061 | Demo data seeding | ✅ test_migrate_canonical.py (25) | — | — | ✅ |
| P2-063 | Merge Stats+Raporty → AnalyticsView | — | ✅ 06-analytics.spec.ts | 📸 | ✅ |
| P2-064 | Opcje wydruku PDF | ✅ test_pdf_options.py (9) | ✅ 06-fee-preset-pdf.spec.ts | — | ✅ |
| P2-065 | Stats poprawki po review | ✅ test_p2_065_stats_fixes.py (18) | — | — | ✅ |
| P2-066 | Rezerwacje maszyn UI | ✅ test_reservations.py (4) | ❌ | — | ✅ unit, ❌ e2e |
| P2-067 | Demo data refactor | ✅ test_migrate_canonical.py | — | — | ✅ |
| P2-068 | Demo data cenniki kaskadowe | ✅ test_fee_parser.py | ✅ 12-fee-presets-ui.spec.ts | — | ✅ |
| P2-069 | Analytics agregacja po mieście | ✅ test_stats_period.py | ✅ 06-analytics.spec.ts | — | ✅ |
| P2-070 | Audyt interaktywności | — | ✅ 10-ux-screenshots.spec.ts | 📸 | ✅ |

---

## P3 — Nice-to-Have

| ID | Funkcjonalność | Unit | E2E | Vision | Status |
|----|----------------|------|-----|--------|--------|
| P3-071 | Audyt UX (5 faz) | — | ✅ 10-ux-screenshots.spec.ts (17) | 📸 | ✅ |

---

## Security

| ID | Funkcjonalność | Unit | E2E | Vision | Status |
|----|----------------|------|-----|--------|--------|
| SEC-001 | IDOR /reports/contract/{id} | ✅ test_contracts.py | ✅ 07-reports.spec.ts | — | ✅ |
| SEC-002 | Jinja2 autoescape | ✅ test_pdf_options.py | ✅ 07-reports.spec.ts | — | ✅ |

---

## Widoki Vue — pokrycie e2e

| Widok | E2E smoke | E2E screenshot | Vision | Status |
|-------|-----------|----------------|--------|--------|
| LoginView | ✅ 01-login (11) | ✅ 10-ux (2) | 📸 | ✅ |
| DashboardView | ✅ 06-dashboard (6) | ✅ 10-ux (1) | 📸 | ✅ |
| HomeView | — | ✅ 10-ux (1) | 📸 | ⚠️ brak smoke |
| AnalyticsView | ✅ 06-analytics (6) | — | 📸 | ✅ |
| ArchiveView | ✅ tmp_archive (1) | — | 📸 | ⚠️ tylko 1 test |
| SettingsView | ✅ 05-settings (12) | ✅ 10-ux (5) | — | ✅ |
| AdminView | — | ✅ 10-ux (1) | 📸 | ⚠️ brak smoke |
| WorkerView | — | ✅ 10-ux (1) | 📸 | ⚠️ brak smoke |
| CommissionView | — | ✅ 10-ux (1) | 📸 | ⚠️ brak smoke |
| ContractFormView | ✅ 04-contract (15) | ✅ 10-ux (1) | — | ✅ |
| ArticleFormView | ✅ 03-article (11) | ✅ 10-ux (1) | — | ✅ |
| ContractorFormView | ✅ 02-contractor (12) | ✅ 10-ux (2) | — | ✅ |
| ChangePasswordView | ✅ 08-auth (3) | ✅ 10-ux (1) | — | ✅ |
| ResetPasswordView | ❌ | ❌ | — | ❌ brak testów |

---

## Backend endpoints — pokrycie unit

| Moduł | Endpointy | Unit tests | Status |
|-------|-----------|------------|--------|
| auth | /auth/login, /auth/forgot-password, /auth/change-password | ✅ test_auth_ratelimit.py (8) | ✅ |
| contractors | /contractors CRUD | ✅ test_nip_validation.py (7) | ✅ |
| articles | /articles CRUD | ✅ test_models_p3_005.py (17) | ✅ |
| contracts | /contracts CRUD + positions + conditions + service-fees | ✅ test_contracts.py (27) | ✅ |
| settings | /settings CRUD + categories + salespeople + fee-presets | ✅ test_settings.py (9), test_categories.py (19) | ✅ |
| reports | /reports/contract/{id} PDF | ✅ test_pdf_options.py (9) | ✅ |
| stats | /stats/* (11 endpointów) | ✅ test_stats_*.py (53) | ✅ |
| explorer | /explorer/* | ✅ test_explorer_archival_filter.py (12) | ✅ |
| archive | /archive/* (15 endpointów) | ✅ test_archive.py (22) | ✅ |
| integrations/fakturownia | /fakturownia/* | ✅ test_fakturownia_*.py (28) | ✅ |
| shared/cache | TTLCache | ✅ test_cache.py (22) | ✅ |
| shared/revenue | compute_position_revenues | ✅ test_calc.py (17) | ✅ |

---

## Luki w pokryciu (do dodania)

### E2E — brakujące testy
1. **ResetPasswordView** — brak jakichkolwiek testów e2e
2. **ArchiveView** — tylko 1 test (drilldown), brak smoke (4 zakładki, filtry, paginacja)
3. **WorkerView** — tylko screenshot, brak smoke (5 paneli: expiring, deliveries, unprinted, stale, overdue)
4. **CommissionView** — tylko screenshot, brak smoke (prowizje handlowców)
5. **AdminView** — tylko screenshot, brak smoke (CRUD użytkowników)
6. **HomeView** — tylko screenshot, brak smoke (5 paneli KPI)
7. **/stats/by-branch** — brak e2e (P1-055)
8. **/stats/by-contract-type** — brak e2e (P2-056)
9. **Cache /cache/clear + /cache/stats** — brak e2e (P2-051)
10. **Rezerwacje maszyn** — brak e2e (P2-066)

### Vision — brakujące weryfikacje
1. **PDF Umowa S** — layout, pieczątka, rozliczenie kaskadowe (P1-019, P1-020)
2. **PDF Umowa U** — redesign jak S (P1-019)
3. **PDF Protokół ZO** — adres dostawy (P1-016)
4. **AnalyticsView** — 4 zakładki, drill-down, filtry (P2-063)
5. **ArchiveView** — 4 zakładki, banner archiwum (P2-062)
6. **CommissionView** — prowizje, tabela (P2-070)
7. **WorkerView** — 5 paneli, filtry dni (P2-070)
8. **AdminView** — panel admina, CRUD użytkowników
9. **LoginView** — empty state, validation error (P2-049)
10. **DashboardView** — empty state, skeleton loaders (P3-071)

---

## Plan uzupełnienia luk

### Faza 1: E2E smoke dla niepokrytych widoków (priorytet HIGH)
- `13-archive.spec.ts` — ArchiveView 4 zakładki + filtry + paginacja
- `14-worker.spec.ts` — WorkerView 5 paneli + filtry dni
- `15-commission.spec.ts` — CommissionView prowizje
- `16-admin.spec.ts` — AdminView CRUD użytkowników
- `17-home.spec.ts` — HomeView 5 paneli KPI
- `18-reset-password.spec.ts` — ResetPasswordView full flow

### Faza 2: E2E dla endpointów API (priorytet MEDIUM)
- `19-stats-api.spec.ts` — /stats/by-branch, /stats/by-contract-type, /cache/clear, /cache/stats
- `20-reservations.spec.ts` — Rezerwacje maszyn UI

### Faza 3: Vision verification (priorytek MEDIUM)
- PDF: Umowa S, Umowa U, Protokół ZO (3 screenshoty)
- UI: AnalyticsView, ArchiveView, CommissionView, WorkerView, AdminView (5 screenshotów)
- Total: 8 screenshotów (~$0.08-0.24 koszt)

---

## Uruchamianie testów

```bash
# Wszystkie unit testy backend
cd backend && .venv\Scripts\python.exe -m pytest tests/unit/ -v --tb=short

# Wszystkie e2e (oba serwery muszą działać)
cd e2e && npx playwright test --reporter=list

# Smoke regression (zawsze po zmianach)
cd e2e && npx playwright test tests/01-login.spec.ts

# Konkretne testy
cd e2e && npx playwright test tests/06-analytics.spec.ts
cd backend && .venv\Scripts\python.exe -m pytest tests/unit/test_cache.py -v

# Type check (frontend)
cd frontend && npx vue-tsc --noEmit

# Build check (frontend)
cd frontend && npm run build
```
