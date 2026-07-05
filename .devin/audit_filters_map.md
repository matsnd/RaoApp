# Audyt filtrów Analytics — mapa frontend → backend

> Wstępna analiza kodu (przed cross-check z Playwright + DB).
> Autor: Tech Lead (analiza statyczna kodu).

## 1. Filtry w UI (AnalyticsFilters.vue)

| Filtr | data-testid | Typ | Wartości |
|-------|-------------|-----|----------|
| Okres (preset) | preset-{today,week,month,quarter,year,all,custom} | pills (single-select) | today/week/month/quarter/year/all/custom |
| Typ (articleType) | filter-article-type | select | all/machine/service |
| Kontrahent (contractorId) | filter-contractor | combobox (ContractorCombobox) | null lub ID>0 |
| Miasto (city) | filter-city | text input | string (case-insensitive) |
| Wyczyść | filter-clear | button | reset → month/all/null/'' |

## 2. Mapowanie preset → zakres dat (AnalyticsView.vue:37-50)

| preset | from | to |
|--------|------|----|
| today | dziś | dziś |
| week | dziś - 6 dni | dziś |
| month | 1. dzień miesiąca | dziś |
| quarter | 1. dzień kwartału (Math.floor(m/3)*3) | dziś |
| year | 1. stycznia | dziś |
| all | '' (puste) | dziś |
| custom | dateFrom (input) | dateTo (input) |

**UWAGA:** `to` = `new Date().toISOString().slice(0,10)` — UTC, może się różnić od lokalnego "dziś" o kilka godzin (timezone).

## 3. Mapa frontend → backend (PRZEKAZYWANIE FILTRÓW)

### Tab: 'period' (Wynajem w okresie) — PeriodRentalTab.vue:217-227

| Sekcja UI | Funkcja store | Endpoint backend | contractor_id | city | article_type | internal_number |
|-----------|---------------|-------------------|---------------|------|--------------|-----------------|
| KPI (góra) | fetchSummary | /stats/fleet-summary | ❌ NIE | ❌ NIE | ❌ NIE | ✅ |
| Top maszyny | fetchTopMachines | /stats/top-machines | ✅ | ✅ | ❌ NIE | ✅ |
| Pozycje dodatkowe (usługi) | fetchAdditionalFees | /stats/additional-fees | ✅ | ❌ NIE | ❌ NIE | ❌ NIE |
| Lokalizacje | fetchLocations | /stats/locations | ✅ | ❌ NIE (NIE wysyła!) | ❌ NIE | ✅ |
| Pozycje | fetchPositions('all',...) | /stats/positions | ✅ | ✅ | ❌ HARDCODED 'all' | ❌ NIE |
| Kategorie | fetchByCategory('main',...,'all') | /stats/by-category | ❌ NIE | ❌ NIE | ❌ HARDCODED 'all' | ❌ NIE |

### Tab: 'locations' (Lokalizacje) — LocationsTab.vue

| Sekcja UI | Funkcja store | Endpoint backend | contractor_id | city | article_type | internal_number |
|-----------|---------------|-------------------|---------------|------|--------------|-----------------|
| Ranking miast/PNA | fetchLocationsRanking | /explorer/locations | ❌ NIE | ❌ NIE | ❌ NIE | ❌ NIE |

**KRYTYCZNE:** LocationsTab dostaje od AnalyticsView TYLKO `:date-from` i `:date-to` (linia 197-199 w AnalyticsView.vue). Filtry contractorId/city/articleType są CAŁKOWICIE IGNOROWANE na tej tabie.

### Tab: 'explorer' (Eksplorator) — ExplorerTab.vue

| Sekcja UI | Funkcja store | Endpoint backend | contractor_id | city | article_type | internal_number |
|-----------|---------------|-------------------|---------------|------|--------------|-----------------|
| Wyszukiwarka | fetchExplorerSearch | /explorer/search | ❌ NIE | ❌ NIE | ❌ NIE | ❌ NIE |

**KRYTYCZNE:** ExplorerTab dostaje od AnalyticsView TYLKO `:date-from` i `:date-to` (linia 200-204 w AnalyticsView.vue). Filtry contractorId/city/articleType są CAŁKOWICIE IGNOROWANE.

### Tab: 'live' (Flota teraz) — LiveFleetTab.vue

Filtry są UKRYTE (v-if="activeTab !== 'live'" w AnalyticsView.vue:174). LiveFleetTab nie używa filtrów.

## 4. PODEJRZANE BUGI (z analizy statycznej)

### BUG-1: KPI (fleet-summary) ignoruje contractorId/city/articleType
- **Plik:** frontend/src/stores/analytics.ts:298-310 (fetchSummary)
- **Plik:** backend/stats/router.py:78-185 (endpoint /stats/fleet-summary — tylko internal_number)
- **Symptom:** Zmiana Typu/Kontrahenta/Miasta NIE zmienia KPI (przychód, dni, utilization)
- **Wpływ:** User widzi że "przychód się nie zmienia" przy zmianie filtra — bo KPI nie reaguje

### BUG-2: fetchPositions hardcoded type='all'
- **Plik:** frontend/src/components/analytics/tabs/PeriodRentalTab.vue:225
- **Symptom:** Filtr Typ (machine/service) NIE działa na sekcję "Pozycje"
- **Fix:** Przekazać props.filters.articleType zamiast 'all'

### BUG-3: fetchByCategory hardcoded articleType='all' + brak contractorId/city
- **Plik:** frontend/src/components/analytics/tabs/PeriodRentalTab.vue:227
- **Plik:** frontend/src/stores/analytics.ts:380-396 (fetchByCategory nie ma parametrów contractorId/city)
- **Symptom:** Filtr Typ/Kontrahent/Miasto NIE działa na sekcję "Kategorie"

### BUG-4: fetchLocations NIE wysyła city
- **Plik:** frontend/src/stores/analytics.ts:343-356 (brak `if (filters?.city) params.city = filters.city`)
- **Plik:** backend/stats/router.py:411-438 (endpoint /stats/locations nie ma parametru city)
- **Symptom:** Filtr Miasto NIE działa na sekcję "Lokalizacje" w PeriodRentalTab

### BUG-5: LocationsTab i ExplorerTab ignorują wszystkie filtry oprócz dat
- **Plik:** frontend/src/views/AnalyticsView.vue:195-204 (tylko :date-from, :date-to)
- **Symptom:** Na tab "Lokalizacje" i "Eksplorator" filtry Typ/Kontrahent/Miasto NIE działają w ogóle

### BUG-6: fetchTopMachines ignoruje articleType
- **Plik:** frontend/src/stores/analytics.ts:312-327 (brak articleType w params)
- **Plik:** backend/stats/router.py:187-238 (endpoint /stats/top-machines nie ma article_type)
- **Symptom:** Filtr Typ NIE działa na sekcję "Top maszyny"

### BUG-7: fetchAdditionalFees ignoruje city + articleType
- **Plik:** frontend/src/stores/analytics.ts:329-341 (tylko contractorId)
- **Symptom:** Filtr Miasto/Typ NIE działa na sekcję "Pozycje dodatkowe (usługi)"

## 5. Wyjaśnienie wrażenia usera: "przychód się zmienia a dni się nie zmienialy"

User zmienia filtr (np. Kontrahent):
- **KPI (fleet-summary):** NIE reaguje (BUG-1) → dni wynajmu, utilization, contracts_in_ppozostają te same
- **Top maszyny:** REAGUJE na contractorId → przychód w tabeli się zmienia
- **Pozycje:** REAGUJE na contractorId → przychód w tabeli się zmienia
- **Kategorie:** NIE reaguje (BUG-3) → przychód w kategoriach zostaje ten sam

Więc user widzi: tabele się zmieniają (przychód w Top maszynach / Pozycjach), ale KPI (dni) zostaje te same. To pasuje do wrażenia "przychód się zmienia a dni nie".

## 6. Czeka na cross-check

- Playwright (qa-engineer): zbierze faktyczne wartości UI dla każdej kombinacji filtrów
- Backend (backend-dev): potwierdzi mapę parametrów endpointów
- DB (db-architect): da SQL truth dla porównania

Po scaleniu → finalny raport z tabelą UI vs DB vs expected.
