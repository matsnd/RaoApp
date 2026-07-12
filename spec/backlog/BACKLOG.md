# RAO Backlog — Sprint 2026-07-11 →

> **Status:** Oczyszczony 2026-07-11 (28 tasków zarchiwizowanych → `archiwum/BACKLOG_SPRINT_20260705_20260711.md`)
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/BACKLOG_SPRINT_20260705_20260711.md`
> **Decision log:** `spec/backlog/DECISION_LOG.md` — pełna historia decyzji (co, dlaczego, status)
> **Cel:** Nowe zadania będą dodawane na podstawie współpracy z klientem
> **Źródło uwag:** `temp/uwagi klienta/ROA - uwagi.md` (15 uwag + 1 notatka o statystykach)

---

## ℹ️ Zasady

- Nowe taski dodawane na podstawie wymagań klienta / operatora
- Format: YAML front-matter + sekcje (jak w poprzednim backlogu)
- Status flow: `triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)`
- Po zakończeniu zadania → lokalny commit + update `DECISION_LOG.md`
- Każda decyzja architektoniczna/biznesowa → sekcja w `DECISION_LOG.md`
- Agent ustawia MAX `team-verified`; `user-verified`/`client-approved` = CZŁOWIEK, nigdy agent
- Sweep done→archiwum gdy BACKLOG > 400 linii

---

## 🚨 P0 — Production Blockers

*Brak aktywnych P0. Wszystkie P0 z poprzedniego sprintu zrealizowane (zweryfikowane 2026-07-12):*

| ID | Tytuł | Status | Rozwiązanie |
|----|-------|--------|-------------|
| P0-001 | `/stats/currently-rented` 500 | done | `id=` → `article_id=` w router.py |
| P0-002 | AnalyticsView brak scrolla | done (naprawione przez P1-110 refactor) | `flex:1; min-height:0; overflow-y:auto` — scrollHeight 1318 > clientHeight 720 |
| P0-003 | Znak `$` kojarzy się z USD | done (false alarm) | `$` = placeholdery `$1`/`$2`, nie waluta |
| P0-004 | Eksplorator: kontrahent dropdown | done (P1-110) | ContractorCombobox działa |
| P0-005 | Wszystkie umowy prefiks `S` | done (P1-022) | Zamierzony design — `generate_contract_number()` zawsze "S" |
| P0-006 | ContractFormView checkboxy nie w PDF | done (`ee216c3`) | `show_person1/2` działają, martwe pola usunięte |

---

## 🔴 P1 — Must-Have

### P1-016: Statystyki — błędne wartości (-300%, -7)

```yaml
id: P1-016
status: needs-repro
priority: P1
created: 2026-07-08
updated: 2026-07-09
source: client-request (uwagi klienta 2026-07-08, notatka na końcu dokumentu)
component: frontend/AnalyticsView + backend/stats
```

**Opis:** W statystykach pojawiają się błędne wartości: „-300%" i „-7". Klient zauważył nieprawidłowe dane w module statystyk/analytics. Wymaga analizy — prawdopodobnie błędne obliczenia delta/percentage lub brakujące dane powodujące ujemne wartości.

**Analiza (2026-07-09):** Nie udało się odtworzyć błędu na aktualnych danych:
- Fleet summary: utilization_pct=13.6%, period_revenue=1789944.00 — poprawne
- By period: wszystkie wartości dodatnie
- Machine ROI: roi_pct=null (brak replacement_value > 0 w DB)
- Drilldown maszyny: przychód 7500 zł, 7 dni, 1 umowa — poprawne
- Vision verification: brak ujemnych wartości na screenshocie
- `clamped_days = max((c_to - c_from).days + 1, 0)` — zabezpieczone przed ujemnymi
- `roi_pct = round(float(revenue) / float(art.replacement_value) * 100, 2)` — może być ujemne jeśli revenue < 0 (korekta/zwrot), ale brak replacement_value > 0 w DB

**Potencjalne przyczyny:**
1. Dane mogły się zmienić od czasu zgłoszenia (migracje, rozliczenia)
2. Wartości mogły pochodzić z konkretnego filtru/okresu niedostępnego teraz
3. "-300%" mogło być ROI z ujemnym revenue (korekta) i replacement_value > 0 (już usunięte)
4. "-7" mogło być liczbą dni z błędną datą (date_to < date_from) — `clamped_days` zabezpiecza, ale stare dane mogły mieć inny kod

**Do wyjaśnienia przez klienta:** W jakim dokładnie filtrze/okresie/zakładce pojawiły się te wartości?

---

### P1-110: Przebudowa statystyk — osobne ekrany z drill-down + audyt obliczeń

```yaml
id: P1-110
status: in_progress
priority: P1
created: 2026-07-11
updated: 2026-07-11
source: client-request (statystyki klienta)
component: frontend/AnalyticsView + backend/stats + backend/explorer (remove) + backend/reservations
plan: C:/Users/mateu/.windsurf/plans/megaplan-statystyki-klienta-10c667.md
```

> **Uwaga:** Poprzednio błędnie oznaczony jako P1-009 (kolizja ID z "Opiekun zamówienia na protokole"). Przemianowany na P1-110 przy cleanup 2026-07-11.

**Opis:** Pełna przebudowa statystyk zgodnie z wymaganiami klienta:
- Usunięcie eksploratora (nieintuicyjny, do zaorania)
- 7 tabów w Analytics: Flota teraz, Maszyny, Usługi dodatkowe (S), Usługi zwykłe (U), Lokalizacje, Wynajem w okresie, Rezerwacje
- Drill-down z wyszukiwarką na każdym tabie
- Eksport CSV (wspólny komponent ExportCsvButton)
- Pełny audyt obliczeń w całej aplikacji (nie tylko Analytics) z weryfikacją bazodanową
- Testy Playwright dla każdego ekranu i obliczeń
- Dead code analysis (depwire: 4268 martwych symboli = 24.9%)
- Regresja wszystkich 20 testów E2E + szukanie dziur → backlog (bez implementacji)

**Implementacja:** 12 faz (0-11), patrz plan `megaplan-statystyki-klienta-10c667.md`

**Status implementacji (2026-07-11):**
- ✅ Fazy 0-8: Explorer tab usunięty, 4 nowe taby (Machines, ServicesAdditional, ServicesRegular, Reservations), ExportCsvButton, backend contract_type filter + /reservations/with-articles, spec updated, committed
- ✅ Faza 9: Weryfikacja UI przez Playwright MCP — wszystkie taby renderują się poprawnie (KPI, tabele, empty states)
- ✅ Faza 10: Spec zaktualizowane (03_frontend_screens.md, 02_backend_api.md)
- ✅ Naprawiono pre-existing bug: brak importu ContractorCombobox w AnalyticsFilters.vue

**Dead code findings (codebase-memory):**
- `frontend/src/components/analytics/tabs/ExplorerTab.vue` — plik nie importowany nigdzie (martwy) — ✅ USUNIĘTY (2026-07-11)
- `searchExplorer()` w `frontend/src/stores/analytics.ts` — 0 callerów (martwy) — ✅ USUNIĘTY (2026-07-11)
- `explorerResults`, `explorerSummary`, `loadingExplorer` — state refs używane tylko przez searchExplorer (martwe) — ✅ USUNIĘTE (2026-07-11)
- Typy `ExplorerResultItem`, `ExplorerSearchResponse` — używane tylko przez martwy searchExplorer — ✅ USUNIĘTE (2026-07-11)
- Backend `/explorer/*` endpointy — **NIE usuwać** (drill-down drawer używa `fetchMachineDetails`, `fetchLocationDetails`, `fetchCityDetails`)

**Pre-existing bugs (nie naprawione — do backlogu):**
- ~~TEST-03: Drill-down ROI section (`drill-machine-roi`) nie renderuje się — `test.fail` oznaczony~~ — ✅ NAPRAWIONO (2026-07-11): `store.machineRoi` był referencjonowany w AnalyticsView.vue ale nie istniał w analytics store (regresja po refactorze). Dodano `MachineRoiResponse` interface + `machineRoi` ref + `fetchMachineRoi` action (best-effort, `/stats/machine-roi`), wywołanie równoległe z `fetchMachineDetails` w `openDrillDown`. `test.fail` usunięte.
- Depwire MCP `find_dead_code` i `get_health_score` — timeout/zawieszanie na dużym repo (315 plików)

**Pozostałe fazy (do dokończenia):**
- [ ] Faza 11: Pełny audyt obliczeń w całej aplikacji z weryfikacją bazodanową
- [x] Dead code cleanup (frontend: ExplorerTab.vue, searchExplorer, explorerResults) — 2026-07-11
- [x] Test E2E: drill-down ROI section fix — 2026-07-11 (TEST-03 `test.fail` usunięte)
- [ ] Regresja wszystkich 20 testów E2E

---

### P1-115: Seed umów usługi (type=U) — pozycje z machine_id zamiast service_id

```yaml
id: P1-115
status: dev-verified
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: backend/seed_demo_data + backend/contracts (XOR machine_id/service_id)
migration_impact: no
```

**Opis:** Umowy typu U (usługi) w seedzie mają pozycje z `machine_id` (maszyny) zamiast `service_id` (usługi). W formularzu umowy usługi wyszukiwarka pokazuje sprzęt a nie usługi — niespójność.

**Dowód DB (2026-07-12):**
- `contract_positions` dla `contract_type='U'`: 22 pozycje, wszystkie `machine_id=NULL, service_id=NULL` (article_name = nazwa maszyny)
- `contract_positions` dla `contract_type='S'`: 67 pozycji, tylko 3 z `machine_id` (reszta NULL — stare seedy)

**Root cause:** `_build_positions_and_fees` w `seed_demo_data.py` (linia 506) ZAWSZE używa `maszyny` (MASZYNY list) i ustawia `machine_id` w pozycjach — ignoruje `contract_type`. Dla umów U powinien używać `services` (tabela `services`) i ustawiać `service_id`.

**Zadania:**
1. `seed_demo_data.py` — `_build_positions_and_fees` przyjmować `contract_type`; dla U używać services (z `services` table), dla S używać machines
2. `seed_demo_data.py` — dodać seed usług zwykłych (services table) — obecnie pusta? Sprawdzić
3. `seed_umowy` — zapisywać `service_id` zamiast `machine_id` dla pozycji umów U
4. Weryfikacja DB: umowy U mają `service_id` NOT NULL, `machine_id` NULL; umowy S odwrotnie
5. E2E: formularz umowy usługi pokazuje usługi w wyszukiwarce

**Definition of Done:**
- [ ] Umowy U w DB mają pozycje z `service_id` (nie `machine_id`)
- [ ] Umowy S w DB mają pozycje z `machine_id` (nie `service_id`)
- [ ] Formularz umowy usługi — wyszukiwarka pokazuje usługi
- [ ] `pytest` zielony
- [ ] Smoke E2E zielony

---

### P1-116: Usunąć cennik z Machine Details — cennik tylko z poziomu umowy

```yaml
id: P1-116
status: dev-verified
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/MachineDetailsView (lub MachineFormView)
migration_impact: no
```

**Opis:** Widok cennika w szczegółach maszyny jest "beznadziejny" (cyt. klient). Cennik warunków rozliczenia ma być zarządzany TYLKO z poziomu formularza umowy (gdzie jest uproszczony i kontekstowy). Usunąć sekcję cennika z Machine Details.

**Zadania:**
1. Znaleźć widok cennika w Machine Details (MachineDetailsView.vue lub MachineFormView.vue)
2. Usunąć sekcję "Nowy cennik rozliczenia" / "Warunki rozliczenia" z Machine Details
3. Zachować backend endpointy (cennik nadal używany w formularzu umowy)
4. E2E: Machine Details nie pokazuje cennika

**Definition of Done:**
- [ ] Machine Details nie ma sekcji cennika
- [ ] Formularz umowy nadal pozwala na cennik (uproszczony)
- [ ] `vue-tsc` zielony
- [ ] Smoke E2E zielony

---

### P1-117: Dodawanie rozliczenia inline w formularzu umowy — auto-zapis + auto-apply

```yaml
id: P1-117
status: dev-verified
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/ContractFormView + backend/contracts (cennik kaskadowy)
migration_impact: no
```

**Opis:** Dodawanie warunków rozliczenia z poziomu tworzenia umowy ma być uproszczone:
1. Po wpisaniu pierwszego warunku → auto-zapis (nie trzeba klikać "Zapisz")
2. Auto-apply ostatniego cennika dla maszyny/usługi (prefill z ostatniego użycia)
3. Edycja w locie w gridzie (inline editing, nie modal)

**Zadania:**
1. `ContractFormView.vue` — sekcja warunków rozliczenia: inline grid (edycja w locie)
2. Auto-zapis: po wpisaniu pierwszego warunku → POST/PUT automatycznie (debounce)
3. Auto-apply: po wybraniu maszyny/usługi → pobierz ostatni cennik (GET /machines/{id}/rate-presets/last-used lub podobnie)
4. UX: grid z kolumnami (rate1, rate2, period_count, minimum, billing_label) — edycja inline
5. E2E: dodanie warunku nie wymaga kliknięcia "Zapisz"

**Definition of Done:**
- [ ] Warunki rozliczenia edytowalne inline w gridzie
- [ ] Auto-zapis po wpisaniu pierwszego warunku
- [ ] Auto-apply ostatniego cennika po wybraniu maszyny/usługi
- [ ] `vue-tsc` zielony
- [ ] Smoke E2E zielony

---

### P1-118: Panel rezerwacji — stronicowanie listy dnia

```yaml
id: P1-118
status: dev-verified
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/ReservationsView (panel dnia — P1-111)
migration_impact: no
```

**Opis:** Panel listy dnia w ReservationsView (P1-111) ma być wielkości kalendarza, a kolejne elementy stronicowane. Obecnie panel może rosnąć nieograniczenie jeśli dzień ma dużo eventów.

**Zadania:**
1. `ReservationsView.vue` — panel dnia: `max-height` = wysokość kalendarza, `overflow-y: auto`
2. Stronicowanie listy eventów (np. 10 na stronę) lub virtual scroll
3. Paginacja: prev/next lub "Pokaż więcej"
4. E2E: dzień z 20+ eventami — panel nie przepełnia kalendarza

**Definition of Done:**
- [ ] Panel dnia ma max-height = wysokość kalendarza
- [ ] Lista eventów stronicowana (lub scroll z paginacją)
- [ ] `vue-tsc` zielony
- [ ] Smoke E2E zielony

---

### P1-119: Rezerwacja maszyn — opcjonalny handlowiec (salesperson_id)

```yaml
id: P1-119
status: dev-verified
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: backend/reservations (model + schema + service) + frontend/ReservationsView (modal)
migration_impact: yes (ALTER TABLE machine_reservations ADD COLUMN salesperson_id)
```

**Opis:** Rezerwacja maszyn ma mieć do wyboru opcjonalnego handlowca (salesperson_id). Obecnie rezerwacja nie ma powiązania z handlowcem.

**Zadania:**
1. DB: `ALTER TABLE machine_reservations ADD COLUMN salesperson_id INT NULL` (FK → salespeople)
2. `backend/reservations/models.py` — dodać `salesperson_id` column + relationship
3. `backend/reservations/schemas.py` — `ReservationCreate/Update/Response` + `salesperson_id`
4. `backend/reservations/service.py` — zapis/aktualizacja `salesperson_id`
5. `frontend/src/stores/reservations.ts` — typy + payload
6. `frontend/src/views/ReservationsView.vue` — modal: select handlowca (opcjonalny)
7. E2E: rezerwacja z handlowcem

**Definition of Done:**
- [ ] `machine_reservations.salesperson_id` w DB (nullable, FK → salespeople)
- [ ] Modal rezerwacji ma select handlowca (opcjonalny)
- [ ] API zapisuje/zwraca `salesperson_id`
- [ ] `pytest` zielony, `vue-tsc` zielony
- [ ] Smoke E2E zielony

---

### P1-120: Opłaty dodatkowe — combobox mapowany do additional_services

```yaml
id: P1-120
status: dev-verified
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: backend/contracts + backend/additional_services + frontend/ContractFormView
migration_impact: yes (ALTER TABLE additional_services ADD display_name + contract_service_fees ADD additional_service_id)
```

**Opis:** Opłaty dodatkowe na umowie (`contract_service_fees`) mają być mapowane do katalogu `additional_services` przez FK `additional_service_id`. Z punktu widzenia usera jedyna zmiana to combobox z listy zamiast wolnego tekstu — reszta bez zmian. Cel: statystyki rozliczeń per usługa + integracja z Fakturownią (`additional_services.fakturownia_product_id`).

**Zadania:**
1. DB: `ALTER TABLE additional_services ADD COLUMN display_name VARCHAR(400) NULL` (długa nazwa do umowy/PDF, fallback do name)
2. DB: `ALTER TABLE contract_service_fees ADD COLUMN additional_service_id INT NULL` (FK → additional_services, ON DELETE SET NULL)
3. `backend/additional_services/models.py` + `schemas.py` — `display_name`
4. `backend/contracts/models.py` + `schemas.py` — `additional_service_id` (Create/Update/Response)
5. `backend/contracts/service.py` — propagacja `additional_service_id` z template do fee
6. `backend/seed_demo_data.py` — `display_name` w USLUGI + `additional_service_id` w fee
7. `frontend/src/views/ContractFormView.vue` — combobox (select) z `additional_services` w nowym wierszu i edycji inline; opcja "✎ własna nazwa…"
8. Backfill istniejących opłat: match po `display_name` → `additional_service_id`

**Definition of Done:**
- [x] `additional_services.display_name` w DB
- [x] `contract_service_fees.additional_service_id` w DB (FK → additional_services)
- [x] Combobox z listy `additional_services` w formularzu opłat
- [x] Po wyborze: `name` = `display_name`, `amount_from` = `default_amount`
- [x] Opcja "✎ własna nazwa…" dla ręcznego wpisu
- [x] Backfill: 195/195 opłat ma `additional_service_id`
- [x] `vue-tsc` zielony
- [x] Spec sync (01_database, 02_backend_api, 03_frontend_screens)

---

## 🟡 P2 — Should-Have

### P2-002: `articles.power_type` — sugestia zestawu diesel/elektryk

```yaml
id: P2-002
status: team-verified
priority: P2
created: 2026-07-08
source: tech-lead (follow-up po P1-100)
component: backend/articles + frontend/ArticleFormView + frontend/ContractFormView
migration_impact: yes
```

**Opis:** Dodać `articles.power_type` ENUM('diesel','electric','other') + dropdown w formularzu artykułu. W formularzu umowy: pre-selekcja sugerowanego zestawu usług dodatkowych na podstawie typu pierwszej pozycji sprzętu (nigdy silent auto-apply — klient wymaga wyboru przez operatora). Migracja legacy: heurystyka po nazwie (`%spalinowy%` → diesel, `%elektryczny%` → electric).

---

### P2-003: Rezerwacje tylko na maszyny wewnętrzne

```yaml
id: P2-003
status: triaged
priority: P2
created: 2026-07-11
source: client-request (wywiad FULL-AUTO 2026-07-11)
component: backend/reservations + frontend/ReservationsView
migration_impact: no
```

**Opis:** Rezerwacje maszyn mają dotyczyć **tylko maszyn wewnętrznych** (`is_external = false`). Maszyny zewnętrzne (wynajmowane od innych firm) nie powinny być dostępne do rezerwacji.

**Stan obecny:**
- `Article.is_external` istnieje (Boolean, default False, index `idx_articles_external`)
- Backend `reservations/service.py` — brak walidacji `is_external` (można zarezerwować dowolną maszynę)
- Frontend `ReservationsView.vue:175` — pobiera maszyny z `is_service: false` ale bez filtra `is_external` (w dropdownie są też zewnętrzne)

**Zadania:**
1. **Frontend** `ReservationsView.vue:176` — dodać `.filter((a) => !a.is_service && !a.is_external)` do `articleOptions`
2. **Backend** `reservations/service.py:create()` — walidacja: jeśli `article.is_external` → 400 "Nie można rezerwować maszyn zewnętrznych"
3. **Backend** `reservations/service.py:update()` — to samo gdy zmieniają `article_id`
4. **Testy** — unit test: rezerwacja maszyny zewnętrznej → 400. E2E: dropdown pokazuje tylko wewnętrzne

**Definition of Done:**
- [ ] Dropdown rezerwacji pokazuje tylko maszyny wewnętrzne (`is_external=false`)
- [ ] Backend odrzuca rezerwację maszyny zewnętrznej (400)
- [ ] Update rezerwacji na maszynę zewnętrzną → 400
- [ ] Unit test: create reservation on external article → 400
- [ ] E2E: dropdown nie zawiera maszyn zewnętrznych
- [ ] Spec sync: `03_frontend_screens.md`, `02_backend_api.md`

---

### P2-004: Auto-zapis PDF do folderów klienta (File System Access API)

```yaml
id: P2-004
status: triaged
priority: P2
created: 2026-07-11
source: client-request (wywiad FULL-AUTO 2026-07-11)
component: frontend (composable + SettingsView + ContractFormView)
migration_impact: no
browser: Chrome/Edge only (Firefox/Safari fallback do zwykłego download)
```

**Opis:** Klient chce auto-zapis PDF do folderów na swoim komputerze (nie na serwerze). Różne komputery = różne foldery. Multi-folder: umowa Gdańsk → zapis do głównego + Gdańsk jednocześnie.

**Wymagania:**
1. Umowy → folder główny (wszystkie umowy)
2. Protokoły → folder główny (wszystkie protokoły)
3. Umowy Gdańsk → główny + dodatkowy folder Gdańsk
4. Protokoły Gdańsk → główny + dodatkowy folder Gdańsk
5. Konfiguracja per-komputer (IndexedDB, nie w bazie — różne komputery mają różne foldery)
6. Zostawić zapis na serwerze (report_folder/protocol_folder w Company) jako backup

**Rozwiązanie: File System Access API (Chrome/Edge)**
- `window.showDirectoryPicker()` — klient raz wybiera folder
- `directoryHandle` zapisany w IndexedDB (persistencja między sesjami)
- Przy pobraniu PDF: frontend zapisuje do wszystkich skonfigurowanych folderów automatycznie
- Re-permission: jeden klik "Zezwól" przy pierwszym zapisie w nowej sesji
- Fallback (Firefox/Safari): zwykły download (jak obecnie)

**Zadania:**
1. **Frontend** `composables/usePdfFolders.ts` (nowy) — directoryHandle management, IndexedDB persistencja, `savePdf(bytes, branch_id, type)`
2. **Frontend** `views/SettingsView.vue` — UI: 4 przyciski "Wybierz folder" (główny umowy, główny protokoły, Gdańsk umowy, Gdańsk protokoły) + status (zapisany/nie)
3. **Frontend** `views/ContractFormView.vue` — przy pobraniu PDF: użyj `usePdfFolders().savePdf()` zamiast zwykłego download
4. **Backend** — bez zmian (zapis na serwerze zostaje jako backup)
5. **Fallback** — detekcja `window.showDirectoryPicker` → jeśli brak, zwykły download
6. **Testy** — E2E: smoke (File System Access API nie działa w Playwright headless → testować fallback path)

**Architektura:**
```
Backend (bez zmian)          Frontend (nowe)
─────────────────            ──────────────────
generate_pdf() → bytes  →    usePdfFolders() composable
                             ├─ główny umowy: directoryHandle (IndexedDB)
                             ├─ główny protokoły: directoryHandle (IndexedDB)
                             ├─ Gdańsk umowy: directoryHandle (IndexedDB)
                             └─ Gdańsk protokoły: directoryHandle (IndexedDB)

                             savePdf(bytes, branch_id, type):
                               folders = getFolders(branch_id, type)
                               for folder in folders:
                                 if hasPermission(folder):
                                   writeFile(folder, filename, bytes)
                                 else:
                                   requestPermission(folder)  ← 1 klik
                                   writeFile(folder, filename, bytes)
```

**Definition of Done:**
- [ ] `usePdfFolders.ts` composable — directoryHandle + IndexedDB + savePdf()
- [ ] SettingsView — 4 przyciski wyboru folderu (główny umowy/protokoły, Gdańsk umowy/protokoły)
- [ ] ContractFormView — auto-zapis do folderów przy pobraniu PDF
- [ ] Umowa Warszawa → 1 folder (główny)
- [ ] Umowa Gdańsk → 2 foldery (główny + Gdańsk) automatycznie
- [ ] Protokół Gdańsk → 2 foldery (główny + Gdańsk) automatycznie
- [ ] Re-permission przy nowej sesji (jeden klik)
- [ ] Fallback Firefox/Safari → zwykły download
- [ ] Zapis na serwerze zostaje (backup)
- [ ] Spec sync: `03_frontend_screens.md`

### P2-005: Usunąć Filie i Kategorie z additional-services (form + lista)

```yaml
id: P2-005
status: triaged
priority: P2
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/AdditionalServiceFormView + frontend/AdditionalServicesListView
migration_impact: no
```

**Opis:** Formularz edycji/tworzenia usługi dodatkowej (`/rao/additional-services/*/edit`) zawiera pola Kategoria (kaskada 3-level) i Filia, które NIE istnieją w backend model/schema (`additional_services` tabela nie ma `category_id` ani `branch_id`). Pola wysyłają wartości które backend ignoruje. Lista usług dodatkowych ma kolumnę "Kategoria" która zawsze pokazuje "—".

**Zadania:**
1. `AdditionalServiceFormView.vue` — usunąć blok Kategoria (kaskada 3 selecty) + Filia select + related script (catSelectedMain/Sub1/Sub2, catMainOptions, catSub1Options, catSub2Options, findCatPath, setCategoryFromId, watch category, settingsStore import, fetchCategoriesTree/fetchBranches)
2. `AdditionalServicesListView.vue` — usunąć kolumnę "Nr wew." i "Kategoria" (th + td), colspan 3→1 w state rows (SkeletonRow, StateMessage error/empty)
3. Form `form` ref — usunąć `category_id` i `branch_id` pola

**Definition of Done:**
- [ ] Formularz additional-service nie ma pól Kategoria i Filia
- [ ] Lista additional-services NIE ma kolumn "Nr wew." i "Kategoria" (tylko Nazwa)
- [ ] `vue-tsc --noEmit` zielony
- [ ] Smoke E2E `01-login.spec.ts` zielony
- [ ] Spec sync: `03_frontend_screens.md`

**Uwaga:** Zmiany częściowo rozpoczęte (edycje w obu plikach już zastosowane w sesji 2026-07-12, wymaga weryfikacji stanu i dokończenia).

---

### P2-006: Usunąć Filie i Kategorie z services (form + lista)

```yaml
id: P2-006
status: triaged
priority: P2
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/ServiceFormView + frontend/ServicesListView
migration_impact: no
```

**Opis:** Formularz edycji/tworzenia usługi zwykłej (`/rao/services/*/edit`) zawiera pola Kategoria i Filia, które NIE istnieją w backend model/schema (`services` tabela nie ma `category_id` ani `branch_id`). Same problem jak P2-005 ale dla modułu services.

**Zadania:**
1. `ServiceFormView.vue` — usunąć blok Kategoria + Filia + related script code (analogicznie do P2-005)
2. `ServicesListView.vue` — usunąć kolumnę "Nr wew." i "Kategoria" (th + td), colspan adjust
3. Form `form` ref — usunąć `category_id` i `branch_id` pola

**Definition of Done:**
- [ ] Formularz service nie ma pól Kategoria i Filia
- [ ] Lista services NIE ma kolumn "Nr wew." i "Kategoria"
- [ ] `vue-tsc --noEmit` zielony
- [ ] Smoke E2E `01-login.spec.ts` zielony
- [ ] Spec sync: `03_frontend_screens.md`

**Uwaga (2026-07-12):** Klient jawnie potwierdził — z gridu usług skasować "Nr wew" i "Kategoria".

---

### P1-111: Kalendarz rezerwacji — panel boczny z listą dnia + context menu

```yaml
id: P1-111
status: triaged
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/ReservationsView + backend/reservations (może wymagać endpoint)
migration_impact: no
```

**Opis:** Przebudowa widoku kalendarza rezerwacji. Obecnie kalendarz i lista to toggle (albo/albo). Klient chce:
1. **Kalendarz po lewej + panel listy po prawej** (side-by-side, nie toggle)
2. **Klik na dzień kalendarza** → prawy panel pokazuje listę umów + rezerwacji na ten dzień
3. **Prawy klik na dzień** → context menu: "Dodaj rezerwację" / "Dodaj umowę" na ten dzień
4. **Checkboxes w panelu listy** (nie toggle): "Blokady rezerwacjami" + "Blokady umowami" — filtruje co pokazywać

**Stan obecny (`ReservationsView.vue`):**
- Toggle kalendarz/lista (albo/albo)
- Kalendarz: month grid, kropki eventów (rezerwacje + umowy), hover=tooltip, klik=dodaj rezerwację, klik kropki=edycja
- Lista: tabela wszystkich rezerwacji z filtrami (maszyna, kontrahent, status, zakres dat)
- Backend: `GET /reservations/calendar?date_from&date_to&machine_id` → `CalendarEvent[]` (source: reservation|contract)
- Backend: `GET /reservations/with-machines` → `ReservationWithMachine[]`

**Wymagania szczegółowe:**

**Layout:**
```
┌─────────────────────────┬──────────────────────────┐
│  Kalendarz (month grid) │  Panel listy dnia        │
│  - nawigacja miesiąc    │  ┌────────────────────┐  │
│  - kropki eventów       │  │ Wybrany dzień:     │  │
│  - hover = tooltip      │  │ 2026-07-12 (sob)   │  │
│                         │  ├────────────────────┤  │
│                         │  │ ☑ Blokady rezerw.  │  │
│                         │  │ ☑ Blokady umowami  │  │
│                         │  ├────────────────────┤  │
│                         │  │ • Koparka X        │  │
│                         │  │   Rezerwacja potw. │  │
│                         │  │   08:00-18:00      │  │
│                         │  │ • Ładowarka Y      │  │
│                         │  │   Umowa #123       │  │
│                         │  │   07-12 → 07-15    │  │
│                         │  └────────────────────┘  │
└─────────────────────────┴──────────────────────────┘
```

**Interakcje:**
- Lewy klik na dzień → wybierz dzień, pokaż listę w prawym panelu
- Prawy klik na dzień → context menu: "Dodaj rezerwację" / "Dodaj umowę" (z pre-set datą)
- Klik na event w prawym panelu → edycja (rezerwacja) / podgląd (umowa)
- Checkboxes: "Blokady rezerwacjami" + "Blokady umowami" — filtruje listę w panelu
  - Oba zaznaczone (default) → pokaż wszystko
  - Tylko rezerwacje → tylko events source=reservation
  - Tylko umowy → tylko events source=contract

**Zadania:**
1. **Frontend** `ReservationsView.vue` — przebudowa layout: kalendarz (flex: 1) + panel listy (flex: 0, min-width: 320px)
2. **Frontend** — `selectedDay` ref, klik na dzień → `selectedDay = cell.date`, panel pokazuje `calendarEvents.filter(e => selectedDay >= e.date_from && selectedDay <= e.date_to)`
3. **Frontend** — context menu (prawy klik): `@contextmenu.prevent` na cell → menu z 2 opcjami
4. **Frontend** — checkboxes `showReservations` + `showContracts` (default oba true), filtruje listę dnia
5. **Frontend** — "Dodaj umowę" → `router.push({ name: 'ContractNew', query: { date: selectedDay } })`
6. **Frontend** — usunąć toggle kalendarz/lista (lista staje się panelem dnia, nie osobnym widokiem)
7. **Backend** — prawdopodobnie bez zmian (`/reservations/calendar` już zwraca umowy + rezerwacje)

**Definition of Done:**
- [ ] Kalendarz i panel listy widoczne side-by-side (nie toggle)
- [ ] Klik na dzień → panel pokazuje umowy + rezerwacje na ten dzień
- [ ] Prawy klik → context menu "Dodaj rezerwację" / "Dodaj umowę"
- [ ] Checkboxes "Blokady rezerwacjami" + "Blokady umowami" filtrują listę
- [ ] "Dodaj rezerwację" otwiera modal z pre-set datą
- [ ] "Dodaj umowę" → nawigacja do formularza umowy z datą
- [ ] Klik na event w panelu → edycja/podgląd
- [ ] `vue-tsc --noEmit` zielony
- [ ] Smoke E2E `01-login.spec.ts` zielony
- [ ] E2E: klik na dzień → panel listy widoczny z eventami
- [ ] E2E: checkboxes filtrują listę
- [ ] Spec sync: `03_frontend_screens.md`

---

### P1-112: Statystyki — zmiana kolejności tabów + rename "Wynajem w okresie" + audyt filtrów

```yaml
id: P1-112
status: triaged
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/AnalyticsView + frontend/AnalyticsFilters + frontend/analytics/tabs/*
migration_impact: no
```

**Opis:** Przebudowa kolejności tabów w statystykach, zmiana nazwy taba "Wynajem w okresie" na rankingowy, oraz pełny audyt wszystkich filtrów na każdym tabie.

**Obecna kolejność tabów (`AnalyticsView.vue:20-27`):**
1. Flota teraz (live)
2. Maszyny (machines)
3. Usługi dodatkowe (services-s)
4. Usługi zwykłe (services-u)
5. Wynajem w okresie (period)
6. Lokalizacje (locations)

**Nowa kolejność (wg klienta):**
1. Flota teraz (live) — bez zmian
2. Maszyny (machines) — bez zmian
3. Usługi zwykłe (services-u) — przesunięte wyżej
4. Usługi dodatkowe (services-s) — przesunięte niżej
5. Lokalizacje (locations) — przesunięte wyżej
6. ~~Wynajem w okresie~~ → **Rankingi wynajmu** (period) — rename + ew. przebudowa

**Propozycje nazwy dla "Wynajem w okresie" → ranking:**
- **Rankingi wynajmu** — najprostsze, jasne (ranking maszyn/lokalizacji/kontrahentów wg przychodu/dni)
- **Top wynajmy** — krótkie, biznesowe
- **Ranking maszyn** — jeśli ma być focus na maszynach
- **Liderzy wynajmu** — bardziej marketingowe
- **Wynajm — rankingi** — z dywizem

**Rekomendacja:** **Rankingi wynajmu** — najjaskrawiej oddaje że to zestawienie/ranking, a nie kalendarz/okres.

**Filtry obecne (`AnalyticsFilters.vue`):**
- Okres: preset pills (Dziś / Tydzień / Miesiąc / Kwartał / Rok / Wszystko / Własny)
- Custom date range (od/do) — gdy preset=custom
- Typ: select (Wszystkie / Maszyny / Usługi) — `articleType: all|machine|service`
- Kontrahent: combobox z filtrowaniem
- Miasto: text input
- Wyczyść (reset)

**Audyt filtrów — sprawdzić na KAŻDYM tabie:**
1. Czy filtr `articleType` ma sens na tabach Maszyny / Usługi dodatkowe / Usługi zwykłe? (te taby są już dedykowane — filtr Typ może być redundant lub mylący)
2. Czy filtr `contractorId` jest przekazywany do backendu na każdym tabie?
3. Czy filtr `city` działa na tabach Maszyny / Usługi / Rankingi?
4. Czy filtr `dateFrom/dateTo` jest ignorowany na tabie "Flota teraz" (live)? — tak, filtry ukryte na live
5. Czy zmiana filtrów odświeża dane bez przeładowania strony?
6. Czy filtr `articleType` powinien zniknąć na tabach Maszyny/Usługi (skoro tab już determinuje typ)?
7. Czy filtr `city` ma sens na tabie Usługi dodatkowe / Usługi zwykłe? (usługi nie mają lokalizacji)

**Zadania:**
1. `AnalyticsView.vue:20-27` — zmiana kolejności tabów (nowa kolejność wyżej)
2. `AnalyticsView.vue` — rename label taba `period` z "Wynajem w okresie" na "Rankingi wynajmu" (ikona 📊 zamiast 📅)
3. `AnalyticsView.vue:29` — default `activeTab` zmienić z `'period'` na `'live'` (lub zostawić 'period' → 'period' z nową nazwą)
4. Audyt filtrów — dla każdego tabu sprawdź:
   - [ ] `articleType` — czy ma sens? czy powinien być ukryty na dedykowanych tabach?
   - [ ] `contractorId` — czy backend odbiera i filtruje?
   - [ ] `city` — czy backend odbiera? czy ma sens na usługach?
   - [ ] `dateFrom/dateTo` — czy przekazywane do API?
5. `AnalyticsFilters.vue` — ew. warunkowe ukrywanie filtrów zależnie od activeTab (np. `articleType` ukryte na Maszyny/Usługi)
6. E2E — update testów jeśli zmieniły się nazwy/seq tabów

**Definition of Done:**
- [ ] Kolejność tabów: Flota teraz → Maszyny → Usługi zwykłe → Usługi dodatkowe → Lokalizacje → Rankingi wynajmu
- [ ] Tab "Wynajem w okresie" przemianowany na "Rankingi wynajmu"
- [ ] Audyt filtrów wykonany — każdy filtr sprawdzony na każdym tabie
- [ ] Filtry nieistotne na danym tabie ukryte (jeśli audyt to wykaże)
- [ ] `vue-tsc --noEmit` zielony
- [ ] Smoke E2E `01-login.spec.ts` zielony
- [ ] E2E statystyki update (nazwy tabów, kolejność)
- [ ] Spec sync: `03_frontend_screens.md`

---

### P1-113: Opłaty dodatkowe — $1/$2 placeholdery w tekście umowy zamiast ręcznych kwot

```yaml
id: P1-113
status: triaged
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/ContractFormView + backend/contracts + backend/additional_services
migration_impact: no
```

**Opis:** W opłatach dodatkowych są pola "Kwota od" (amount_from) i "Kwota do" (amount_to). Tekst opisu na umowie powinien używać placeholderów `$1` i `$2` które są podmieniane na sformatowane kwoty, np.:
- Opis w bazie: `"$1 zł dostawa / $2 zł odbiór"`
- Na umowie: `"150,00 zł dostawa / 200,00 zł odbiór"` (gdzie $1=amount_from, $2=amount_to)

Obecnie tekst jest ręcznym stringiem z wpisanymi kwotami — placeholdery `$1` `$2` nie są wykorzystywane. Klient chce żeby placeholdery były używane tak żeby zmiana kwoty w gridzie automatycznie podmieniała wartości w tekście.

**Kontekst (z poprzedniej sesji):**
- `ContractFormView.vue` — już miało fix na $1/$2 → sformatowane kwoty (commit `15eb900`)
- `seed_demo_data.py` — zaktualizowane placeholdery + elektryk 90→35 zł (commit `15eb900`)
- `main.py` migracja — obsługuje bare `$1` (bez ' zł' suffix) (commit `15eb900`)
- `migrate.py` — `_fix_fee_placeholders` obsługuje bare `$1` (commit `15eb900`)
- **ALE:** klient zgłasza że nadal nie działa poprawnie — sprawdzić czy na nowej bazie/seedzie teksty używają placeholderów

**Zadania:**
1. Zweryfikować obecny stan — czy `$1`/`$2` są podmieniane w tekście umowy (ContractFormView + PDF)
2. Sprawdzić czy seedy (`seed_demo_data.py`) używają `$1`/`$2` w opisach (nie hardcoded kwoty)
3. Sprawdzić czy grid opłat dodatkowych pozwala edytować kwoty i czy tekst się aktualizuje
4. Jeśli nie działa — naprawić podmianę `$1`→amount_from, `$2`→amount_to w opisie na umowie i PDF
5. Test E2E — dodaj opłatę z `$1`/`$2` w opisie, sprawdź czy umowa pokazuje sformatowane kwoty

**Definition of Done:**
- [ ] Opis opłaty z `$1`/`$2` w bazie → na umowie pokazuje sformatowane kwoty
- [ ] Zmiana kwoty w gridzie → tekst na umowie się aktualizuje
- [ ] PDF umowy pokazuje podmienione kwoty
- [ ] Seedy używają `$1`/`$2` (nie hardcoded kwot)
- [ ] `vue-tsc --noEmit` zielony
- [ ] Smoke E2E zielony
- [ ] Spec sync: `03_frontend_screens.md`, `04_business_logic.md`

---

### P2-007: Szybkie przyciski Diesel/Elektryk dla opłat dodatkowych + usunięcie "Wspólne opłaty dodatkowe"

```yaml
id: P2-007
status: triaged
priority: P2
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/ContractFormView + backend/seed_demo_data + backend/additional_services
migration_impact: no
depends_on: P1-113
```

**Opis:** Usunąć przycisk "Wspólne opłaty dodatkowe". Zamiast tego zrobić szybkie przyciski dla predefiniowanych zestawów opłat: **Diesel** i **Elektryk**. Reszta opłat z dropdownu. Ważne: seedy muszą mieć placeholdery `$1` `$2` w opisach żeby szybko podmieniać kwoty w gridzie.

**Wymagania:**
1. **Usunąć** przycisk "Wspólne opłaty dodatkowe" z formularza umowy
2. **NIE seedować** "Wspólne" — usunąć z seed_demo_data.py
3. **Seedować 2 domyślne zestawy**: Diesel i Elektryk (z `$1`/`$2` placeholderami w opisach)
4. **Dodać** szybkie przyciski: `[Diesel]` `[Elektryk]` — klik dodaje predefiniowany zestaw opłat dodatkowych do umowy
5. **Reszta** opłat dodatkowych z dropdownu (jak obecnie)
6. **Seedy** — predefiniowane zestawy Diesel i Elektryk muszą mieć opisy z `$1`/`$2` placeholderami:
   - Diesel: np. transport `$1 zł dostawa / $2 zł odbiór`, tankowanie `$1 zł za litr`
   - Elektryk: np. transport `$1 zł dostawa / $2 zł odbiór`, podłączenie `$1 zł`
7. **Grid** — po dodaniu zestawu, kwoty są edytowalne i tekst się aktualizuje (zależne z P1-113)

**Zadania:**
1. `ContractFormView.vue` — usunąć przycisk "Wspólne opłaty dodatkowe"
2. `ContractFormView.vue` — dodać szybkie przyciski `[Diesel]` `[Elektryk]` które dodają zestaw opłat
3. Backend — endpoint lub logika frontendowa: pobierz predefiniowany zestaw opłat dla Diesel/Elektryk
4. `seed_demo_data.py` — **NIE seedować "Wspólne"**, seedować tylko 2 zestawy: Diesel i Elektryk (z `$1`/`$2` w opisach)
5. E2E — test: klik Diesel → opłaty dodane z placeholderami, edycja kwoty aktualizuje tekst

**Definition of Done:**
- [ ] Przycisk "Wspólne opłaty dodatkowe" usunięty
- [ ] "Wspólne" NIE jest seedowane
- [ ] Seedowane 2 domyślne zestawy: Diesel i Elektryk (z `$1`/`$2` w opisach)
- [ ] Szybkie przyciski Diesel i Elektryk działają
- [ ] Klik Diesel → dodaje zestaw opłat diesel do umowy
- [ ] Klik Elektryk → dodaje zestaw opłat elektryk do umowy
- [ ] Reszta opłat z dropdownu
- [ ] `vue-tsc --noEmit` zielony
- [ ] Smoke E2E zielony
- [ ] Spec sync: `03_frontend_screens.md`

---

### P1-114: Czysty seed + odtworzenie bazy + Fakturownia + 10 umów aktywnych

```yaml
id: P1-114
status: dev-verified
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: backend/seed_demo_data + backend/migrate + backend/integrations/fakturownia + DB
migration_impact: yes
```

**Opis:** Przygotować procedurę odtworzenia bazy od zera (czysty seed) z integracją Fakturownia i 10 aktywnymi umowami skonfigurowanymi w Fakturowni, żeby przetestować czy integracja działa end-to-end.

**Wymagania:**
1. **Odtworzenie bazy** — skrypt/procedura: DROP + CREATE + schema z modeli + seed
2. **Czysty seed** — `seed_demo_data.py` przebudowany:
   - Maszyny (z power_type: diesel/elektryk/other)
   - Usługi dodatkowe z `$1`/`$2` placeholderami (zależne z P1-113)
   - Zestawy Diesel i Elektryk (zależne z P2-007)
   - Kontrahenci
   - Handlowcy
   - Filie
   - Kategorie
3. **Fakturownia** — integracja skonfigurowana:
   - `FAKTUROWNIA_API_TOKEN` w `.env`
   - Maszyny/usługi/additional_services z `fakturownia_product_id` (mapping)
   - Firma z danymi do Fakturowni
4. **10 umów aktywnych** — z konfiguracją w Fakturowni:
   - Różne typy: S (najem maszyn) i U (usługi)
   - Różne maszyny (diesel + elektryk)
   - Różne kontrahenci
   - Pozycje z `machine_id` lub `service_id` (XOR)
   - Opłaty dodatkowe z `$1`/`$2` placeholderami
   - Warunki rozliczeniowe
   - Status: aktywne (nie archiwalne)
5. **Test integracji** — po seedzie:
   - GET /fakturownia/products → sprawdź mapping
   - Generuj PDF umowy → sprawdź czy Fakturownia product info jest poprawne
   - Ewentualnie: wystaw fakturę testową (jeśli API Fakturowni dostępne)

**Zadania:**
1. Skrypt `reset_db.py` (lub `seed_demo_data.py --reset`) — DROP schema + CREATE + create_all + seed
2. `seed_demo_data.py` — pełny seed z 10 umowami + Fakturownia mapping
3. `seed_fa_invoices.py` — mapping 3 tabel (machines, services, additional_services) → Fakturownia
4. Weryfikacja: 10 umów w DB, każda z pozycjami, opłatami, warunkami
5. Weryfikacja: Fakturownia products zmapowane
6. E2E — smoke: lista umów pokazuje 10 aktywnych, PDF generuje się

**Definition of Done:**
- [ ] Skrypt reset_db działa (DROP + CREATE + schema + seed w jednym)
- [ ] 10 umów aktywnych w DB po seedzie
- [ ] Umowy mają pozycje (machine_id XOR service_id)
- [ ] Umowy mają opłaty dodatkowe z `$1`/`$2` placeholderami
- [ ] Fakturownia products zmapowane (machines, services, additional_services)
- [ ] PDF umowy generuje się poprawnie dla seedywanych umów
- [ ] E2E smoke zielony po seedzie
- [ ] Spec sync: `08_migration_plan.md`, `07_integrations.md`

---

### P1-121: Statystyki Kategorie — drill-down bez powrotu + puste szczegóły "(bez kategorii)"

```yaml
id: P1-121
status: triaged
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/CategoriesTab.vue + backend/stats/calc.py
migration_impact: no
```

**Opis:** W zakładce "Kategorie" (`/rao/analytics` → Kategorie) drill-down hierarchiczny (main → sub1 → sub2) ma dwa poważne bugi UX:

1. **Brak powrotu do wyższego poziomu** — gdy użytkownik wklika się w kategorię "(bez kategorii)" i ta nie ma podkategorii, tabela zwraca 0 wierszy. Wtedy `data.length === 0` → renderuje się `<div v-else class="ct-empty">` **bez breadcrumb**. Użytkownik utyka na pustym ekranie bez możliwości powrotu do "Wszystkie".

2. **Puste szczegóły kategorii** — dla kategorii "(bez kategorii)" (maszyny z `category_main IS NULL`) backend zwraca:
   - `articles_count = 0` (powinno być > 0)
   - `rented_days = 0` (powinno być > 0)
   - `contracts_count = 58` (poprawne)
   - `revenue = 109 040,00 zł` (poprawne)
   
   Czyli JOIN z `machines` gubi wiersze gdzie `category_main IS NULL`, ale agregacja kontraktów/przychodu działa. Niespójność metryk.

**Stan obecny (`CategoriesTab.vue`):**
- Breadcrumb (linie 270-276) jest wewnątrz `<template v-else-if="data.length">` (linia 265)
- Gdy `data.length === 0` → fallback do `<div v-else class="ct-empty">` (linia 324) — **bez breadcrumb**
- Drill-down: `onDrillDown()` (linia 183) → `load()` → jeśli backend zwraca `[]`, breadcrumb znika z UI
- Backend `stats/calc.py` — agregacja po `category_main` / `category_sub1` / `category_sub2`, JOIN z machines może gubić NULL-e

**Zadania:**
1. **Frontend** `CategoriesTab.vue` — przenieść breadcrumb **poza** blok `v-else-if="data.length"`, żeby był widoczny nawet gdy `data.length === 0`. Breadcrumb musi być zawsze renderowany gdy `breadcrumb.length > 0`.
2. **Frontend** — dodać przycisk "← Wstecz" lub zapewnić że breadcrumb z "Wszystkie" jest zawsze dostępny podczas drill-down, niezależnie od wyników.
3. **Frontend** — empty state drill-down: zamiast "Brak danych o kategoriach" pokazać "Brak podkategorii dla »{breadcrumb[-1].name}«" + breadcrumb do powrotu.
4. **Backend** `stats/calc.py` — audyt agregacji kategorii: dlaczego `articles_count=0` i `rented_days=0` dla "(bez kategorii)" gdy `contracts_count=58` i `revenue>0`. Prawdopodobnie LEFT JOIN z machines na `category_main IS NULL` gubi pozycje. Sprawdzić czy maszyny bez kategorii są poprawnie liczone.
5. **Backend** — rozważyć czy "(bez kategorii)" powinno być kategorią wirtualną (agregacja `COALESCE(category_main, '(bez kategorii)')`) czy wymuszać przypisanie kategorii do maszyny.
6. **E2E** — test: drill-down do kategorii bez podkategorii → breadcrumb widoczny → klik "Wszystkie" → powrót do main.

**Definition of Done:**
- [ ] Breadcrumb widoczny nawet gdy `data.length === 0` (przeniesiony poza `v-else-if`)
- [ ] Empty state drill-down pokazuje nazwę kategorii + breadcrumb
- [ ] Klik "Wszystkie" w breadcrumb zawsze wraca do poziomu głównego
- [ ] Backend: `articles_count` i `rented_days` poprawne dla "(bez kategorii)" (spójne z `contracts_count` i `revenue`)
- [ ] E2E: drill-down do pustej kategorii + powrót działa
- [ ] Spec sync: `03_frontend_screens.md`, `04_business_logic.md`
- [ ] Smoke `01-login.spec.ts` zielony

---

### P1-122: Cennik w tekście umowy — sztywne kwoty zamiast placeholderów $1/$2

```yaml
id: P1-122
status: triaged
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: backend/contracts/service.py + backend/reports/service.py + frontend/ConditionPanel.vue
migration_impact: no
```

**Opis:** Gdy użytkownik dodaje nową umowę i wybiera maszynę z cennikiem (MachineRatePreset), warunki rozliczenia (PositionCondition) są kopiowane z `rate1`/`rate2` jako **sztywne kwoty** (np. "1200,00 zł / doba"). W tekście umowy na PDF nie ma placeholderów `$1`/`$2` — są od razu rozwinięte wartości.

Skutek: **szybka edycja "od kwota / do kwota" nie działa na podgląd PDF**. Gdy użytkownik zmieni `amount_from`/`amount_to` w opłatach dodatkowych (service_fees), tekst na umowie się nie aktualizuje, bo warunki cennika (PositionCondition) nie używają placeholderów — mają hardcoded `rate1`/`rate2`.

**Stan obecny:**

1. **Opłaty dodatkowe (service_fees)** — działają poprawnie z placeholderami:
   - `reports/service.py:_resolve_fee_description()` (linia 17) — rozwija `$1`/`$2` → formatted amount + zł
   - `frontend/ConditionPanel.vue:formatPreview()` (linia 414) — rozwija `$1`/`$2` w podglądzie na żywo
   - Gdy zmienisz `amount_from`/`amount_to`, podgląd PDF aktualizuje się natychmiast ✓

2. **Warunki cennika (PositionCondition)** — BRAK placeholderów:
   - `contracts/service.py:format_position_conditions_cascading()` (linia 404) — formatuje sztywno: `f"{range_text} - {_format_rate(n['rate'])}zł / {rate_unit}"` (linia 459)
   - `contracts/service.py:apply_preset_to_position()` (linia 795) — kopiuje `rate1`/`rate2` z MachineRatePresetItem jako liczby, nie jako placeholdery
   - `ConditionPanel.vue:formatPreview()` (linia 420) — fallback gdy brak `description`: `${rateStr}zł / ${labels.rate}` (sztywna kwota)
   - Gdy zmienisz `rate1`/`rate2` w warunku, podgląd PDF **nie aktualizuje się** bo tekst ma hardcoded wartość ✗

**Root cause:** `PositionCondition` nie ma pola `description` z placeholderami (jak `ContractServiceFee.description`). Warunki są zawsze formatowane z `rate1`/`rate2` jako liczby. Nie ma mechanizmu "tekst na umowie" z placeholderami dla warunków cennika.

**Zadania:**
1. **Decyzja architektoniczna** — czy warunki cennika (PositionCondition) powinny mieć pole `description` z placeholderami `$1`/`$2` (jak ContractServiceFee), czy wystarczy że `format_position_conditions_cascading` dynamicznie formatuje z `rate1`/`rate2` (już to robi, ale PDF jest generowany raz — nie "na żywo")?
2. **Frontend** `ConditionPanel.vue` — podgląd PDF (`pdfPreviewLines`) już działa na żywo z `rate1`/`rate2` (linia 442). Sprawdzić czy po zmianie `rate1` w inline edit, podgląd się odświeża.
3. **Backend** `reports/service.py` — `build_contract_data` generuje PDF z aktualnych `rate1`/`rate2` (linia 114 `format_position_conditions_cascading`). Jeśli użytkownik zmieni `rate1` i zapisze umowę, nowy PDF będzie poprawny. Problem jest tylko z **podglądem na żywo** bez zapisu.
4. **Frontend** `ContractFormView.vue` — sprawdzić czy podgląd PDF warunków (przycisk ⎙) używa zapisanych danych czy formularza na żywo. Jeśli zapisanych — trzeba zapisać przed podglądem, albo generować podgląd z formularza.
5. **Spójność z P1-113** — P1-113 dotyczy `$1`/`$2` w opłatach dodatkowych (service_fees). P1-122 rozszerza to na warunki cennika (PositionCondition). Rozważyć czy to ten sam pattern czy osobny.

**Definition of Done:**
- [ ] Podgląd PDF warunków cennika aktualizuje się na żywo po zmianie `rate1`/`rate2` w inline edit
- [ ] Tekst na umowie (PDF) pokazuje aktualne kwoty po zmianie i zapisie
- [ ] Decyzja: czy PositionCondition.description z $1/$2 jest potrzebne, czy wystarcza dynamiczne formatowanie
- [ ] E2E: zmiana rate1 w warunku → podgląd PDF pokazuje nową kwotę
- [ ] Spec sync: `04_business_logic.md`, `03_frontend_screens.md`
- [ ] Smoke `01-login.spec.ts` zielony

---

### P1-123: Prowizje handlowców — drill-down do umów z kwotą prowizji per umowa

```yaml
id: P1-123
status: triaged
priority: P1
created: 2026-07-12
source: client-request (współpraca 2026-07-12)
component: frontend/CommissionView.vue + backend/stats (nowy endpoint drill-down)
migration_impact: no
```

**Opis:** W widoku Prowizje handlowców (`/commissions` → `CommissionView.vue`) tabela podsumowania per handlowiec jest **tylko do odczytu** — wiersze nie są klikalne. Klient chce móc **wklikać się w handlowca** i zobaczyć listę umów, za które ten handlowiec otrzymał prowizję w wybranym okresie (podlegających filtrowi dat), wraz z **kwotą prowizji dla każdej umowy**.

Formuła prowizji (RAO-P1-018, już zaimplementowana): `commission = margin × commission_rate / 100`, gdzie `margin = cost_client − cost_company` (z `contract_settlements`). Gdy brak danych settlement → backward compatibility: `commission = revenue × commission_rate / 100`. Klient potwierdza: prowizja od (przychód − koszty), procentowo.

**Stan obecny:**
- `frontend/src/views/CommissionView.vue` — tabela `<tr v-for="item in report.items">` (linia 48) z `cursor: default` (linia 159 w `<style>`), brak `@click`, brak drill-down
- `backend/stats/router.py` — `GET /stats/commissions` (linia 1233) zwraca `CommissionReportResponse` z `items: list[SalespersonCommissionItem]` (agregat per handlowiec: `contracts_count`, `total_revenue`, `commission_amount`) — **brak endpointu zwracającego umowy per handlowiec z prowizją per umowa**
- `backend/stats/schemas.py` — `SalespersonCommissionItem` (linia 122): `salesperson_id`, `salesperson_name`, `commission_rate`, `contracts_count`, `total_revenue`, `commission_amount` — brak listy umów
- `spec/core/04_business_logic.md` §14 (linia 1196) — `calculate_salesperson_commission` oblicza prowizję zagregowaną, nie per-umowa
- `spec/core/03_frontend_screens.md` (linia 1577) — CommissionView opisany jako "Tabela per handlowiec" bez drill-down

**Zadania:**
1. **Backend** `stats/router.py` — nowy endpoint `GET /stats/commissions/{salesperson_id}/contracts?date_from&date_to` zwracający listę umów handlowca w zakresie dat z prowizją per umowa. Każdy element: `contract_id`, `contract_number`, `contractor_name`, `date_from`, `date_to`, `revenue` (z pozycji), `cost_client`, `cost_company`, `margin`, `commission_rate`, `commission_amount`. Użyć tej samej formuły co `/stats/commissions` (margin z `contract_settlements`, fallback revenue). `Depends(get_current_user)`.
2. **Backend** `stats/schemas.py` — nowy `SalespersonContractCommissionItem` + `SalespersonContractCommissionResponse` (z `salesperson_id`, `salesperson_name`, `commission_rate`, `items: list[...]`, `total_revenue`, `total_margin`, `total_commission`).
3. **Backend** — test jednostkowy: 2 umowy z settlement (margin), 1 umowa bez settlement (revenue fallback), weryfikacja sum = zagregowane `commission_amount` z `/stats/commissions`.
4. **Frontend** `CommissionView.vue` — wiersze handlowca klikalne (`@click="openDrillDown(item)"`, `cursor: pointer`), otwierają panel/drawer/tabelę z listą umów. Kolumny: Numer, Kontrahent, Data od, Data do, Przychód, Koszty, Marża, Prowizja. Suma wierszy = prowizja handlowca z tabeli nadrzędnej.
5. **Frontend** — breadcrumb / przycisk "← Wstecz" do powrotu do tabeli podsumowania (wzór z `CategoriesTab.vue` P1-121). Loading / error / empty state.
6. **Frontend** — `data-testid` dla wierszy handlowca (`commission-row-{salesperson_id}`), wierszy umów (`commission-contract-row-{contract_id}`), przycisku wstecz.
7. **E2E** — test: otwarcie `/commissions` → klik na handlowca → lista umów → suma prowizji = wartość z wiersza handlowca → powrót.
8. **Spec sync** — `02_backend_api.md` (nowy endpoint), `03_frontend_screens.md` (drill-down w CommissionView), `04_business_logic.md` (prowizja per umowa), `11_reports_stats.md`.

**Definition of Done:**
- [ ] `GET /stats/commissions/{salesperson_id}/contracts` zwraca umowy z prowizją per umowa (margin + fallback revenue)
- [ ] Suma `commission_amount` per umowa = `commission_amount` z `/stats/commissions` dla tego handlowca
- [ ] Klik na wiersz handlowca w `CommissionView.vue` otwiera listę umów
- [ ] Lista umów pokazuje: Numer, Kontrahent, Data od, Data do, Przychód, Koszty, Marża, Prowizja
- [ ] Breadcrumb / "← Wstecz" wraca do tabeli podsumowania
- [ ] Loading / error / empty state działają
- [ ] Test jednostkowy backend: margin + fallback revenue + spójność sum
- [ ] E2E: drill-down handlowiec → umowy → powrót
- [ ] Spec sync: `02_backend_api.md`, `03_frontend_screens.md`, `04_business_logic.md`, `11_reports_stats.md`
- [ ] Smoke `01-login.spec.ts` zielony

---

## 🟢 P3 — Nice-to-Have

*Brak*

---

## ✅ Done — Ukończone zadania

### REFACTOR-001: Articles split — rozdzielenie `articles` na `machines`/`services`/`additional_services`

```yaml
id: REFACTOR-001
status: done
priority: P1
created: 2026-07-11
completed: 2026-07-11
source: tech-lead (architektura)
component: backend (models, schemas, service, routers) + frontend (stores, views, router) + DB schema + e2e tests
commits: 39f2958 → 862b66b (10 commitów)
phases: 1-6 (DB schema + modele + schemas/service + routers + frontend + e2e + migracja)
```

**Opis:** Pełny refaktor architektury danych — rozdzielenie pojedynczej tabeli `articles` (z flagą `is_service`) na trzy dedykowane tabele:
- `machines` — maszyny budowlane (najem, contract_type='S')
- `services` — usługi zwykłe (contract_type='U')
- `additional_services` — usługi dodatkowe (katalog opłat: transport, czyszczenie, tankowanie)

**Kluczowe zmiany:**
- `contract_positions.article_id` → `machine_id XOR service_id` (CHECK constraint `chk_pos_machine_xor_service`)
- `service_fee_templates.article_id` → `additional_service_id` (FK → additional_services)
- `article_rate_presets` → `machine_rate_presets` (article_id → machine_id)
- `machine_reservations.article_id` → `machine_id`
- Backend: 3 nowe moduły (`machines/`, `services/`, `additional_services/`) z CRUD
- Frontend: 6 nowych widoków (MachinesListView, MachineFormView, ServicesListView, ServiceFormView, AdditionalServicesListView, AdditionalServiceFormView) + 3 nowe store'y + routing
- E2E: testy zaktualizowane dla nowych endpointów
- `shared/revenue.py`: JOIN Machine + Service zamiast JOIN Article
- Fakturownia mapping: 3 tabele (machines, services, additional_services) zamiast articles

**Commits (10):**
1. `39f2958` — Faza 1: DB schema + 3 modele SQLAlchemy + FK update
2. `362d6ff` — update revenue.py for articles split
3. `0c4cec3` — Faza 2: schemas + service layer dla 3 nowych modułów
4. `903b1ec` — Faza 3: update routers stats/reports/explorer/settlements
5. `acb34fb` — Faza 3.5: unit tests update + 4 nowe testy CRUD
6. `2a71128` — Faza 4a: stores + router + views dla machines/services/additional_services
7. `31ab62e` — Faza 4b: articles→machines split w widokach i storeach
8. `69ffce6` — Faza 4c: articles→machines w 12 komponentach
9. `2723ff7` — Faza 5: update e2e tests for split
10. `862b66b` — Faza 6: skrypty migracji + seed update

**Spec sync:** `01_database.md`, `02_backend_api.md`, `03_frontend_screens.md`, `04_business_logic.md`, `06_navigation_flow.md`, `07_integrations.md`, `11_reports_stats.md`, `25_security.md` — wszystkie zaktualizowane.

