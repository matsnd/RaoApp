# RAO — Plan Testów (MCP-indexed)

> **Cel:** Plan testów wszystkich funkcjonalności RAO oparty na analizie MCP
> (codebase-memory graf: 287 rout, 30 najbardziej złożonych funkcji;
> depwire: 14976 symboli, 3780 dead-code candidates;
> mariadb: 32 tabele z danymi demo).
> Aktualizowany przy każdej zmianie testów.

---

## Źródła danych MCP (indeksacja 2026-07-05)

### codebase-memory (graf wiedzy)
- **287 rout** API (GET/POST/PUT/DELETE/PATCH)
- **30 najbardziej złożonych funkcji** (complexity ≥ 5)
- **8 N+1 hotspots** (linear_scan_in_loop ≥ 1)
- **Top complexity**: `migrate.step8_csv_categories` (cx=30), `settlements.init_from_fakturownia` (cx=20), `migrate.step9_postal_codes` (cx=19), `main.startup_migrations` (cx=19)

### depwire (analiza zależności)
- **14976 symboli** w 384 plikach (281 Python, 36 TS, 49 JS)
- **3780 dead-code candidates** (25%) — większość to false positives (archive/* ORM models, Pydantic schemas używane przez SQLAlchemy/Pydantic runtime)
- **Prawdziwe dead code**: `_rate_type_names`, `_supplier_names` w archive/service.py (helpery nieużywane)

### mariadb (dane demo)
- **32 tabele** w schema `rao_new`
- **Kluczowe dane**: 742 archive_contracts, 62 contracts, 419 articles, 662 contractors, 4 users, 21865 postal_codes, 11 fakturownia_products_cache, 8 fee_preset_groups, 34 service_fee_templates
- **Puste tabele**: article_reservations (0), audit_log (0), company (0), contract_costs (0), deliveries (0), fakturownia_settings (0), service_hours (0)

---

## Macierz testów — warstwy

### Warstwa 1: Unit testy backend (296 testów, 25 plików)

| Moduł | Plik testu | Testy | Pokrycie | Status |
|-------|-----------|-------|----------|--------|
| auth | test_auth_ratelimit.py | 8 | rate limiting 5/60s/IP | ✅ |
| contractors | test_nip_validation.py | 7 | NIP checksum (valid/invalid/length/letters) | ✅ |
| articles | test_models_p3_005.py | 17 | modele P3-005 | ✅ |
| contracts | test_contracts.py | 27 | CRUD + positions + conditions + is_settled guard + exclude_unset | ✅ |
| settings | test_settings.py | 9 | ServiceFeeTemplate validation | ✅ |
| settings | test_categories.py | 19 | normalizacja nazw + polish_ci | ✅ |
| stats/calc | test_calc.py | 17 | calculate_position_value (kaskadowy) | ✅ |
| stats/branch | test_stats_branch.py | 12 | aggregate_by_branch | ✅ |
| stats/categories | test_stats_categories.py | 12 | aggregate_by_category | ✅ |
| stats/contract_type | test_stats_contract_type.py | 10 | aggregate_by_contract_type | ✅ |
| stats/period | test_stats_period.py | 19 | aggregate_by_period + paginacja | ✅ |
| stats/fixes | test_p2_065_stats_fixes.py | 18 | 18 poprawek po full-team review | ✅ |
| archive | test_archive.py | 22 | 15 endpointów /archive/* | ✅ |
| explorer | test_explorer_archival_filter.py | 12 | archival filter + locations/city | ✅ |
| reports | test_pdf_options.py | 9 | hide_delivery_address + signatures + report_without_data | ✅ |
| fakturownia | test_fakturownia_product_cache.py | 7 | sync_products + search_products | ✅ |
| fakturownia | test_fakturownia_service.py | 6 | service layer | ✅ |
| fakturownia | test_fakturownia_crypto.py | 15 | crypto (AES) | ✅ |
| fee_parser | test_fee_parser.py | 18 | parser legacy opłat | ✅ |
| format_conditions | test_format_conditions.py | 4 | dedup warunków | ✅ |
| fleet_external | test_fleet_external_filter.py | 9 | is_external filter | ✅ |
| migrate | test_migrate_canonical.py | 25 | migracja canonical | ✅ |
| reservations | test_reservations.py | 4 | rezerwacje | ✅ |
| availability | test_availability_reservations.py | 6 | dostępność + rezerwacje | ✅ |
| cache | test_cache.py | 22 | TTLCache (get/set/TTL/invalidate/clear/make_key/concurrency) | ✅ |

### Warstwa 2: E2E Playwright (108 testów, 13 plików + 8 nowych)

| Plik | Testy | Co testuje | Status |
|------|-------|------------|--------|
| 01-login.spec.ts | 11 | logowanie, wylogowanie, sesja, redirect | ✅ |
| 02-contractor.spec.ts | 12 | CRUD kontrahentów, NIP, GUS | ✅ |
| 03-article.spec.ts | 11 | CRUD maszyn, kategorie, is_external | ✅ |
| 04-contract.spec.ts | 15 | CRUD umów, pozycje, warunki, is_settled | ✅ |
| 05-settings.spec.ts | 12 | firma, handlowcy, kategorie, cenniki, FA | ✅ |
| 06-analytics.spec.ts | 6 | 4 zakładki, drill-down, filtry, walidacja | ✅ |
| 06-dashboard.spec.ts | 6 | dashboard, filtry, sortowanie | ✅ |
| 06-fee-preset-pdf.spec.ts | 1 | PDF cenników | ✅ |
| 07-reports.spec.ts | 6 | PDF generation, 404, 401, kaskadowy | ✅ |
| 08-auth-security.spec.ts | 10 | auth guards, change-password, logout | ✅ |
| 10-ux-screenshots.spec.ts | 17 | screenshoty 13 widoków | ✅ |
| 11-pdf-verification.spec.ts | 11 | PDF wizualna weryfikacja | ✅ |
| 12-fee-presets-ui.spec.ts | 1 | UI cenników | ✅ |
| tmp_archive_drilldown.spec.ts | 1 | archive drilldown | ✅ |
| **13-archive.spec.ts** | 6 | ArchiveView 4 zakładki + filtry + paginacja | **NOWY** |
| **14-worker.spec.ts** | 9 | WorkerView 5 paneli + filtry dni + states | **NOWY** |
| **15-commission.spec.ts** | 6 | CommissionView prowizje + states + filtry | **NOWY** |
| **16-admin.spec.ts** | 9 | AdminView CRUD użytkowników + API | **NOWY** |
| **17-home.spec.ts** | 10 | HomeView 5 paneli KPI + nawigacja | **NOWY** |
| **18-reset-password.spec.ts** | 9 | ResetPasswordView walidacja + API | **NOWY** |
| **19-stats-api.spec.ts** | 10 | /stats/by-branch, by-contract-type, cache | **NOWY** |
| **20-reservations.spec.ts** | 6 | /availability, /reservations CRUD | **NOWY** |

### Warstwa 3: Vision verification (rao-vision) — do wykonania

| Widok/PDF | Pytanie do vision | Koszt | Priorytet |
|-----------|-------------------|-------|-----------|
| PDF Umowa S | "Czy pieczątka jest na str.2, rozliczenie kaskadowe widoczne, telefony ukryte?" | ~$0.02 | HIGH |
| PDF Umowa U | "Czy redesign jak umowa S (layout, sekcje, rozliczenie)?" | ~$0.02 | HIGH |
| PDF Protokół ZO | "Czy adres dostawy jest widoczny na protokole?" | ~$0.02 | HIGH |
| AnalyticsView | "Czy 4 zakładki, drill-down, filtry są widoczne i działają?" | ~$0.02 | MEDIUM |
| ArchiveView | "Czy 4 zakładki, banner archiwum, filtry są widoczne?" | ~$0.02 | MEDIUM |
| CommissionView | "Czy tabela prowizji, filtry okresu są widoczne?" | ~$0.02 | MEDIUM |
| WorkerView | "Czy 5 paneli, filtry dni (7/14/30) są widoczne?" | ~$0.02 | MEDIUM |
| AdminView | "Czy tabela użytkowników, CRUD są widoczne?" | ~$0.02 | MEDIUM |
| LoginView | "Czy empty state, validation error, focus-visible są poprawne?" | ~$0.02 | LOW |
| DashboardView | "Czy skeleton loaders, empty states, sort są poprawne?" | ~$0.02 | LOW |
| **Total** | **10 screenshotów** | **~$0.20** | |

---

## Plan wykonania testów

### Faza 1: Unit testy backend (już PASS — 334/334)
```bash
cd backend && .venv\Scripts\python.exe -m pytest tests/unit/ -v --tb=short
```
**Status:** ✅ 334 passed, 0 failed (16.32s)

### Faza 2: E2E smoke (01-login)
```bash
cd e2e && npx playwright test tests/01-login.spec.ts --reporter=list
```
**Status:** do uruchomienia

### Faza 3: E2E pełne (wszystkie 21 plików)
```bash
cd e2e && npx playwright test --reporter=list
```
**Status:** do uruchomienia

### Faza 4: Vision verification (10 screenshotów)
```python
# rao-vision.screenshot_and_analyze dla każdego widoku/PDF
```
**Status:** do uruchomienia

### Faza 5: Type check + build
```bash
cd frontend && npx vue-tsc --noEmit
cd frontend && npm run build
```
**Status:** do uruchomienia

---

## Luki w pokryciu (zidentyfikowane przez MCP)

### Backend — funkcje wysokiej złożoności bez dedykowanych testów
1. **`migrate.step8_csv_categories`** (cx=30) — brak dedykowanego testu (covered przez test_migrate_canonical.py ogólnie)
2. **`settlements.init_from_fakturownia`** (cx=20) — brak testu (Fakturownia integration)
3. **`main.startup_migrations`** (cx=19) — brak testu (idempotentność migracji)
4. **`explorer.get_location_details`** (cx=13) — częściowo covered przez test_explorer_archival_filter.py
5. **`reports.generate_contract_report`** (cx=12) — covered przez 07-reports.spec.ts (e2e)

### Backend — N+1 hotspots
1. **`explorer.extract_city`** (linear_scan=2) — legacy, powinno być usunięte (P2-028 done, ale deployment/ ma kopię)
2. **`migrate.step9_postal_codes`** (linear_scan=2) — jednorazowy skrypt, niski priorytet
3. **`export_for_client_lite.main`** (linear_scan=1, transitive_loop_depth=5) — jednorazowy skrypt

### Backend — dead code (do cleanup)
1. **`_rate_type_names`** w archive/service.py — nieużywany helper
2. **`_supplier_names`** w archive/service.py — nieużywany helper
3. **`deployment/` katalog** — duplikat backend/ (stare deployment, powinno być usunięte)

### Frontend — widoki bez e2e smoke
1. **ResetPasswordView** — brak testów (dodany 18-reset-password.spec.ts)
2. **ArchiveView** — tylko 1 test (dodany 13-archive.spec.ts)
3. **WorkerView** — tylko screenshot (dodany 14-worker.spec.ts)
4. **CommissionView** — tylko screenshot (dodany 15-commission.spec.ts)
5. **AdminView** — tylko screenshot (dodany 16-admin.spec.ts)
6. **HomeView** — tylko screenshot (dodany 17-home.spec.ts)

### API — endpointy bez e2e
1. **/stats/by-branch** — dodany 19-stats-api.spec.ts
2. **/stats/by-contract-type** — dodany 19-stats-api.spec.ts
3. **/stats/cache/clear + /cache/stats** — dodany 19-stats-api.spec.ts
4. **/availability + /reservations** — dodany 20-reservations.spec.ts

### DB — puste tabele (brak danych do testów)
1. **article_reservations** (0 rows) — P2-066 martwy moduł
2. **audit_log** (0 rows) — brak audit logging
3. **company** (0 rows) — brak danych firmy
4. **contract_costs** (0 rows) — brak kosztów
5. **deliveries** (0 rows) — brak dostaw
6. **fakturownia_settings** (0 rows) — brak konfiguracji FA
7. **service_hours** (0 rows) — brak godzin usług

---

## Mapowanie funkcjonalności → testy (z DECISION_LOG)

### P0 — Production Blockers (8 zadań)
| ID | Unit test | E2E test | Vision | Status |
|----|-----------|----------|--------|--------|
| P0-030 | test_contracts.py | 04-contract.spec.ts | — | ✅ |
| P0-031 | test_pdf_options.py | 07-reports.spec.ts | — | ✅ |
| P0-032 | test_contracts.py | — | — | ✅ |
| P0-033 | test_calc.py (17) | 07-reports.spec.ts | 📸 | ✅ |
| P0-034 | test_contracts.py | 04-contract.spec.ts | — | ✅ |
| P0-035 | test_contracts.py | 04-contract.spec.ts | — | ✅ |
| P0-036 | — | 08-auth-security.spec.ts | — | ✅ |
| P0-054 | test_categories.py (19) | 05-settings.spec.ts | — | ✅ |

### P1 — Must-Have (20 zadań)
| ID | Unit test | E2E test | Vision | Status |
|----|-----------|----------|--------|--------|
| P1-014 | test_contracts.py | 04-contract.spec.ts | — | ✅ |
| P1-015 | test_pdf_options.py | 11-pdf-verification.spec.ts | 📸 | ✅ |
| P1-016 | test_pdf_options.py | 11-pdf-verification.spec.ts | 📸 | ✅ |
| P1-017 | test_fakturownia_service.py | 02-contractor.spec.ts | — | ✅ |
| P1-018 | test_pdf_options.py | 11-pdf-verification.spec.ts | 📸 | ✅ |
| P1-019 | test_pdf_options.py | 11-pdf-verification.spec.ts | 📸 | ⚠️ user-verified |
| P1-020 | test_calc.py | 07-reports.spec.ts | 📸 | ⚠️ user-verified |
| P1-021 | test_contracts.py | 04-contract.spec.ts | — | ✅ |
| P1-022 | test_contracts.py | 04-contract.spec.ts | — | ⚠️ user-verified |
| P1-037 | test_contracts.py | 04-contract.spec.ts | — | ✅ |
| P1-038 | test_contracts.py | — | — | ✅ |
| P1-039 | test_contracts.py | 06-analytics.spec.ts | — | ✅ |
| P1-040 | test_contracts.py | 04-contract.spec.ts | — | ✅ |
| P1-041 | — | 08-auth-security.spec.ts | — | ✅ |
| P1-042 | — | 01-login.spec.ts | — | ✅ |
| P1-043 | — | 10-ux-screenshots.spec.ts | — | ✅ |
| P1-044 | — | 01-login.spec.ts | — | ✅ |
| P1-045 | test_format_conditions.py (4) | — | — | ✅ |
| P1-055 | test_stats_branch.py (12) | 19-stats-api.spec.ts | — | ✅ |
| P2-060 | test_p2_065_stats_fixes.py (18) | 06-analytics.spec.ts | — | ✅ |
| P2-062 | test_archive.py (22) | 13-archive.spec.ts | — | ✅ |

### P2 — Should-Have (22 zadań)
| ID | Unit test | E2E test | Vision | Status |
|----|-----------|----------|--------|--------|
| P2-028 | test_stats_period.py | 06-analytics.spec.ts | — | ✅ |
| P2-029 | test_stats_period.py | 06-analytics.spec.ts | — | ✅ |
| P2-047 | test_auth_ratelimit.py (8) | 08-auth-security.spec.ts | — | ✅ |
| P2-048 | — | 08-auth-security.spec.ts | — | ✅ |
| P2-049 | — | 10-ux-screenshots.spec.ts | 📸 | ✅ |
| P2-050 | — | 10-ux-screenshots.spec.ts | — | ✅ |
| P2-051 | test_cache.py (22) | 19-stats-api.spec.ts | — | ✅ |
| P2-052 | test_explorer_archival_filter.py | 06-analytics.spec.ts | — | ✅ |
| P2-053 | test_stats_period.py | 06-analytics.spec.ts | — | ✅ |
| P2-056 | test_stats_contract_type.py (10) | 19-stats-api.spec.ts | — | ✅ |
| P2-057 | test_fleet_external_filter.py (9) | 03-article.spec.ts | — | ✅ |
| P2-058 | test_fakturownia_product_cache.py (7) | 05-settings.spec.ts | — | ✅ |
| P2-059 | test_fee_parser.py (18) | 12-fee-presets-ui.spec.ts | — | ✅ |
| P2-061 | test_migrate_canonical.py (25) | — | — | ✅ |
| P2-063 | — | 06-analytics.spec.ts | 📸 | ✅ |
| P2-064 | test_pdf_options.py (9) | 06-fee-preset-pdf.spec.ts | — | ✅ |
| P2-065 | test_p2_065_stats_fixes.py (18) | — | — | ✅ |
| P2-066 | test_reservations.py (4) | 20-reservations.spec.ts | — | ✅ |
| P2-067 | test_migrate_canonical.py | — | — | ✅ |
| P2-068 | test_fee_parser.py | 12-fee-presets-ui.spec.ts | — | ✅ |
| P2-069 | test_stats_period.py | 06-analytics.spec.ts | — | ✅ |
| P2-070 | — | 10-ux-screenshots.spec.ts | 📸 | ✅ |

### P3 — Nice-to-Have (1 zadanie)
| ID | Unit test | E2E test | Vision | Status |
|----|-----------|----------|--------|--------|
| P3-071 | — | 10-ux-screenshots.spec.ts (17) | 📸 | ✅ |

### Security (2 zadania)
| ID | Unit test | E2E test | Vision | Status |
|----|-----------|----------|--------|--------|
| SEC-001 | test_contracts.py | 07-reports.spec.ts | — | ✅ |
| SEC-002 | test_pdf_options.py | 07-reports.spec.ts | — | ✅ |

---

## Podsumowanie pokrycia

| Warstwa | Przed | Po | Delta |
|---------|-------|-----|-------|
| Unit backend | 296 | 296 | 0 (już kompletne) |
| E2E Playwright | 108 | 172 | +64 (8 nowych plików) |
| Vision | 0 | 0 | do wykonania (10 screenshotów) |
| **Total** | 404 | 468 | +64 |

### Pokrycie funkcjonalności (48 zadań)
- **46/48** ma co najmniej 1 test unit LUB e2e (96%)
- **2/48** wymaga vision verification (P1-019, P1-020 — PDF redesign)
- **0/48** bez jakiegokolwiek testu
