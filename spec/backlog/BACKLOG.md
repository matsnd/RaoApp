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
- `frontend/src/components/analytics/tabs/ExplorerTab.vue` — plik nie importowany nigdzie (martwy)
- `searchExplorer()` w `frontend/src/stores/analytics.ts` — 0 callerów (martwy)
- `explorerResults`, `explorerSummary`, `loadingExplorer` — state refs używane tylko przez searchExplorer (martwe)
- Backend `/explorer/*` endpointy — **NIE usuwać** (drill-down drawer używa `fetchMachineDetails`, `fetchLocationDetails`, `fetchCityDetails`)

**Pre-existing bugs (nie naprawione — do backlogu):**
- TEST-03: Drill-down ROI section (`drill-machine-roi`) nie renderuje się — `test.fail` oznaczony
- Depwire MCP `find_dead_code` i `get_health_score` — timeout/zawieszanie na dużym repo (315 plików)

**Pozostałe fazy (do dokończenia):**
- [ ] Faza 11: Pełny audyt obliczeń w całej aplikacji z weryfikacją bazodanową
- [ ] Dead code cleanup (frontend: ExplorerTab.vue, searchExplorer, explorerResults)
- [ ] Test E2E: drill-down ROI section fix
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

## 🟢 P3 — Nice-to-Have

*Brak*
