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

*Brak aktywnych P0. Wszystkie P0 z poprzedniego sprintu zrealizowane (P0-001 team-verified) lub odłożone (P0-002 do P0-006 — patrz DECISION_LOG).*

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

## 🟡 P2 — Should-Have

### P2-002: `articles.power_type` — sugestia zestawu diesel/elektryk

```yaml
id: P2-002
status: triaged
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

---

## 🟢 P3 — Nice-to-Have

*Brak*
