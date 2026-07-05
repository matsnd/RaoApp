# RAPORT: Audyt filtrów Analytics — UI vs Backend vs DB

> Tech Lead audit. Cross-check 3 źródeł: Playwright (UI), kod backendu, SQL truth (DB).
> Data: 2026-07-05. Baseline: preset=month (2026-07-01..2026-07-05).

## 1. Podsumowanie wykonawcze

**Zbadano:** 14 scenariuszy filtrów × 4 taby (live/period/locations/explorer) × 6 sekcji UI (KPI, top maszyny, usługi, lokalizacje, pozycje, kategorie).

**Znaleziono 8 bugów** (2 P0, 6 P1). **Wrażenie usera "przychód się zmienia a dni nie" = BUG-1** (KPI ignoruje filtry, tabele reagują częściowo).

## 2. Cross-check UI vs DB (baseline month 2026-07-01..07-05)

| Scenariusz | UI KPI (przychód/umowy) | DB truth (przychód/dni/umowy) | Match? | Uwagi |
|------------|------------------------|-------------------------------|--------|-------|
| A-baseline (month, all) | 196 400 / 14 | 196 400 / 196 / 14 | ✅ | Spójne |
| B-today | 188 000 / 13 | 188 000 / 42 / 13 | ✅ | Spójne |
| B-week | 196 400 / 14 | 196 400 / 231 / 14 | ✅ | Ten sam zbiór umów (wszystkie ≥ 07-01) |
| B-quarter | 196 400 / 14 | 396 180 / 576 / 30 | ⚠️ | **UI poprawne** — Q3 zaczyna się w lipcu (floor(6/3)*3=6), DB-agent liczył od kwietnia (błąd agenta, nie aplikacji) |
| B-year | 539 890 / 42 | 539 890 / 822 / 42 | ✅ | Spójne |
| B-all | 196 400 / 14 | 1 006 440 / 2 133 / 76 | 🔴 | **BUG-6**: preset=all nie pokazuje wszystkiego — backend defaultuje None→początek miesiąca |
| C-machine | 196 400 / 14 | 191 280 / 82 / 14 | 🔴 | **BUG-1**: KPI ignoruje type |
| C-service | 196 400 / 14 | 5 120 / 114 / 12 | 🔴 | **BUG-1**: KPI ignoruje type |
| D-contractor (14403) | 196 400 / 14 | 37 990 / 37 / 3 (dla 14441) | 🔴 | **BUG-1**: KPI ignoruje contractor |
| E-city (Warszawa) | 196 400 / 14 | 38 690 / 14 / 2 | 🔴 | **BUG-1**: KPI ignoruje city |
| F-combo (year+machine+contractor) | 539 890 / 42 | 77 920 / 60 / 6 (dla 14441) | 🔴 | **BUG-1**: KPI pokazuje globalne year, ignoruje machine+contractor |
| G-custom (2025-01-01..2025-12-31) | 344 470 / 26 | — (inny zakres) | — | DB-agent nie liczył tego scenariusza |
| H-clear | 196 400 / 14 | 196 400 / 196 / 14 | ✅ | Wraca do baseline |

## 3. Bugi znalezione (uszeregowane wg priorytetu)

### 🔴 BUG-1 (P0): KPI (fleet-summary) ignoruje contractorId/city/articleType

**Dowód UI:** KPI "Przychód w okresie" = 196 400 zł we WSZYSTKICH scenariuszach z preset=month (baseline, machine, service, contractor, city). Tabele puste dla contractor=14403, ale KPI pokazuje globalne 196 400.

**Dowód API:** `/stats/fleet-summary` NIGDY nie dostaje `contractor_id`/`city`/`article_type` w params (przechwycone requesty).

**Root cause (frontend):** `frontend/src/stores/analytics.ts:298-310` — `fetchSummary(dateFrom, dateTo, internalNumber?)` nie przyjmuje contractorId/city/articleType.

**Root cause (backend):** `backend/stats/router.py:78-185` — endpoint `/stats/fleet-summary` ma tylko `internal_number` jako filtr.

**Wpływ UX:** User zmienia filtr → tabele się zmieniają (top machines, positions) → KPI zostaje te same → wrażenie "przychód się zmienia a dni nie" (bo KPI pokazuje dni/umowy globalnie).

**Fix:** Rozszerzyć `fetchSummary` o przekazywanie `contractorId`/`city`/`articleType` + rozszerzyć endpoint `/stats/fleet-summary` o te parametry + dodać `_apply_position_filters` w logice.

### 🔴 BUG-6 (P0): preset=all nie pokazuje wszystkich danych

**Dowód UI:** B-all → KPI = 196 400 / 14 (identyczne jak month).

**Dowód API:** `/stats/fleet-summary?date_to=2026-07-05` — brak `date_from` (frontend nie wysyła pustego stringa).

**Dowód DB:** DB truth all = 1 006 440 / 2 133 / 76.

**Root cause:** `frontend/src/views/AnalyticsView.vue:48` — preset='all' ustawia `from=''`. Frontend nie wysyła pustego `date_from` (`if (dateFrom) params.date_from = dateFrom`). Backend `_default_dates(None, ...)` defaultuje `date_from` do początku miesiąca (zamiast zostawić None = brak filtra).

**Fix:** Backend: gdy `date_from=None` i `date_to` jest podane, NIE defaultuj `date_from`. Lub frontend: dla preset='all' wysyłaj specjalny flag `all=true`. Najprościej: backend `_default_dates` — gdy date_from=None, zostaw None (nie defaultuj).

### 🟡 BUG-2 (P1): fetchPositions hardcoded type='all'

**Dowód:** API zawsze dostaje `type='all'` niezależnie od filtra Typ. Tabela "Pozycje" identyczna dla machine/service.

**Root cause:** `frontend/src/components/analytics/tabs/PeriodRentalTab.vue:225` — `store.fetchPositions('all', ...)` zamiast `props.filters.articleType`.

**Fix:** Zamień `'all'` na `props.filters.articleType`. Mapowanie: `all→'all'`, `machine→'machines'`, `service→'services'` (backend używa liczby mnogiej).

### 🟡 BUG-3 (P1): fetchByCategory hardcoded + ignoruje contractorId/city

**Dowód:** API zawsze dostaje `level=main` + daty, nigdy `article_type`/`contractor_id`/`city`. Tabela "Kategorie" identyczna we wszystkich scenariuszach.

**Root cause (frontend):** `PeriodRentalTab.vue:227` — `store.fetchByCategory('main', ..., [], 'all')` hardcoded.

**Root cause (backend):** `backend/stats/router.py:447-538` — endpoint `/stats/by-category` nie ma `contractor_id`/`city` w sygnaturze.

**Fix:** Frontend: przekazać `props.filters.articleType` + `props.filters.contractorId`. Backend: dodać `contractor_id`/`city` do sygnatury + `_apply_position_filters`.

### 🟡 BUG-4 (P1): LocationsTab i ExplorerTab ignorują contractorId/city/articleType

**Dowód:** Cross-tab test (filtry: machine+Warszawa+contractor) → `/explorer/locations params={}` (brak filtrów). Locations KPI identyczne jak baseline.

**Root cause:** `frontend/src/views/AnalyticsView.vue:195-204` — przekazuje tylko `:date-from`/`:date-to` do LocationsTab/ExplorerTab.

**Decyzja produktowa wymagana:** (a) filtry wspólne dla wszystkich tabów (przekazać pełny `filters`), lub (b) ukryć filtry kontrahenta/miasta/typu na tabach locations/explorer (jak już ukryte na 'live').

### 🟡 BUG-5 (P1): fetchLocations/fetchAdditionalFees ignorują city

**Dowód:** `/stats/locations` i `/stats/additional-fees` dostają `contractor_id` ale NIE `city`. Tabele identyczne dla city=Warszawa vs baseline.

**Root cause (frontend):** `analytics.ts:343-356` (fetchLocations) i `:329-341` (fetchAdditionalFees) — brak `if (filters?.city) params.city = filters.city`.

**Root cause (backend):** `/stats/locations` (L411-438) i `/stats/additional-fees` (L366-394) — brak `city` w sygnaturze.

**Fix:** Frontend: dodać wysyłanie `city`. Backend: dodać `city` param + `_apply_position_filters`.

### 🟡 BUG-7 (P1): aggregate_by_category/aggregate_by_period liczą rented_days dla usług

**Dowód (backend audit):** `stats/calc.py:161,225` sumują `clamped_days` dla WSZYSTKICH pozycji (łącznie z usługami). Inne agregatory (contract_type, branch, positions) liczą TYLKO maszyny (`if not is_service`).

**Wpływ:** Niespójność dni między endpointami — "Kategorie" pokaże więcej dni niż "Pozycje" dla tego samego zakresu.

**Fix:** Dodać `if not is_service` w `aggregate_by_category`/`aggregate_by_period` (albo świadomie liczyć wszystkie — ale spójnie wszędzie).

### 🟡 BUG-8 (P1): "Pozycje dodatkowe (usługi)" — źródło danych niejasne

**Dowód (DB audit):** Backend `/stats/additional-fees` agreguje `contract_service_fees` (530 zł), NIE pozycje-usługi z `contract_positions` (5 120 zł).

**Pytanie do PO:** UI "Pozycje dodatkowe (usługi)" powinno pokazywać fee (530) czy pozycje-usługi (5 120)? Label "usługi" sugeruje pozycje, ale backend zwraca fee.

## 4. Tabela kompletności filtrów (frontend → backend)

| Sekcja UI | Endpoint | date | preset | type | contractor | city | internal |
|-----------|----------|:----:|:------:|:----:|:----------:|:----:|:-------:|
| KPI (góra) | /stats/fleet-summary | ✅ | ✅ | ❌ BUG-1 | ❌ BUG-1 | ❌ BUG-1 | ✅ |
| Top maszyny | /stats/top-machines | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| Pozycje dodatkowe | /stats/additional-fees | ✅ | ✅ | ❌ | ✅ | ❌ BUG-5 | ❌ |
| Lokalizacje (period) | /stats/locations | ✅ | ✅ | ❌ | ✅ | ❌ BUG-5 | ✅ |
| Pozycje | /stats/positions | ✅ | ✅ | ❌ BUG-2 | ✅ | ✅ | ❌ |
| Kategorie | /stats/by-category | ✅ | ✅ | ❌ BUG-3 | ❌ BUG-3 | ❌ BUG-3 | ❌ |
| Lokalizacje (tab) | /explorer/locations | ✅ | ✅ | ❌ BUG-4 | ❌ BUG-4 | ❌ BUG-4 | ❌ |
| Eksplorator (tab) | /explorer/search | ✅ | ✅ | ❌ BUG-4 | ❌ BUG-4 | ❌ BUG-4 | ❌ |
| Flota teraz (tab) | /stats/currently-rented | — | — | — | — | — | — |

## 5. Odpowiedź na wrażenie usera: "przychód się zmienia a dni nie"

**Tłumaczenie:** User zmienia filtr (np. Kontrahent):
- **KPI (fleet-summary):** NIE reaguje (BUG-1) → "Przychód w okresie", "Umów w okresie", "Wykorzystanie" zostają te same (196 400 / 14 / 100%)
- **Top maszyny:** REAGUJE na contractorId → przychód w tabeli się zmienia
- **Pozycje:** REAGUJE na contractorId → przychód w tabeli się zmienia
- **Kategorie:** NIE reaguje (BUG-3) → przychód w kategoriach zostaje ten sam

Więc user widzi: tabele się zmieniają (przychód w Top maszynach / Pozycjach), ale KPI (dni, umowy) zostaje te same. **To pasuje do wrażenia "przychód się zmienia a dni nie".**

## 6. Pliki wygenerowane

| Plik | Autor | Zawartość |
|------|-------|-----------|
| `.devin/audit_filters_map.md` | Tech Lead | Mapa frontend→backend (analiza statyczna) |
| `.devin/audit_backend_filters.md` | backend-dev | Tabela endpointów + 7 pytań |
| `.devin/audit_db_truth.md` | db-architect | 13 scenariuszy SQL + algorytm przychodu |
| `.devin/audit_db_truth.py` | db-architect | Skrypt pymysql (read-only) |
| `.devin/audit_db_truth.json` | db-architect | Surowe wyniki SQL |
| `e2e/tests/tmp_analytics_filters_audit.spec.ts` | qa-engineer | Skrypt Playwright (541 linii) |
| `e2e/analytics_filters_audit_results.json` | qa-engineer | 14 scenariuszy UI (130 KB) |

## 7. Rekomendacje (kolejność naprawy)

1. **BUG-1 (P0)** — rozszerzyć fleet-summary o contractorId/city/articleType (frontend+backend)
2. **BUG-6 (P0)** — preset=all ma pokazywać wszystkie dane (backend _default_dates)
3. **BUG-2 (P1)** — fetchPositions: 'all' → props.filters.articleType (frontend, quick fix)
4. **BUG-3 (P1)** — fetchByCategory: przekazać articleType + contractorId (frontend+backend)
5. **BUG-5 (P1)** — fetchLocations/fetchAdditionalFees: dodać city (frontend+backend)
6. **BUG-4 (P1)** — LocationsTab/ExplorerTab: decyzja PO + implementacja
7. **BUG-7 (P1)** — aggregate_by_category/period: spójność rented_days (backend)
8. **BUG-8 (P1)** — "Pozycje dodatkowe": decyzja PO źródło danych

## 8. Smoke test status

- ✅ Skrypt audit: 14/14 passed (po fix harness)
- ✅ JSON zapisany (130 KB, 14 scenariuszy)
- ✅ Backend audit: 199 linii raportu
- ✅ DB truth: 13 scenariuszy + top listy
- ⏸️ Aplikacja NIE zmodyfikowana (tylko audyt)
