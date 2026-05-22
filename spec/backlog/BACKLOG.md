# RAO Backlog — Sprint 2

> **Sprint:** 2 (otwarty 2026-05-22)
> **Last updated:** 2026-05-22
> **Format:** YAML front-matter + sekcje (parsowalne przez agentów)
> **Poprzedni sprint:** [archive/BACKLOG_SPRINT_1.md](../archive/BACKLOG_SPRINT_1.md) — 73 tasków, 71× done, 1× superseded, 1× in-progress (przeniesione poniżej)

---

## ℹ️ Zasady sprintu

- Każdy task ma YAML front-matter (id, priority, size, status, classification, roles, depends_on, blocks, source, source_date, specs_to_update, migration_impact, security_impact)
- **Status flow:** `triaged → in-progress → review → done` (lub `superseded`/`blocked`)
- Numeracja kontynuowana ze Sprintu 1 (najwyższe użyte ID: P0-005, P1-029, P2-022, P3-013)
- Nowe taski zaczynamy od kolejnego wolnego numeru w danym priorytecie
- Po zakończeniu zadania → lokalny commit (patrz `AGENTS.md` § Lokalne commity)

---

## 🚨 P0 — Production Blockers

_Brak otwartych zadań P0._ <!-- Max 5 zadań, deadline ostry. -->

---

## 🔴 P1 — Must-Have

_Brak otwartych zadań P1._

---

## 🟡 P2 — Should-Have

### [RAO-P2-021] UX Raportów — kategorie jako 1. poziom + drilldown gridowy + info o danych historycznych

```yaml
id: RAO-P2-021
priority: P2
size: M
status: in-progress
classification: ux/refactor
roles: [frontend-dev, backend-dev]
depends_on: [RAO-P1-029]
blocks: []
source: client-notes
source_date: 2026-05-21
carried_from_sprint: 1
specs_to_update:
  - core/03_frontend_screens.md
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
Zmiana UX sekcji Raporty: kategorie jako pierwszy eksponowany poziom (nie "Podkategoria 1"), drilldown przez kliknięcie w grid (nie dropdown), usunięcie z kodu filtrowania po "Podkategoria 1", banner informacyjny o zakresie danych historycznych.

**Acceptance criteria (DoD):**

**Backend:**
- [ ] Usunąć parametr `subcategory1` (lub odpowiednik) z endpointów statystyk jeśli nie używany gdzie indziej

**Frontend:**
- [ ] Sekcja Raporty: pierwsza zakładka/sekcja to Kategorie (poziom 1 drzewa kategorii)
- [x] Drilldown przez kliknięcie w wiersz gridu ✅
- [ ] Usunąć dropdown/filtr "Podkategoria 1" — analiza: jest wymaganą nawigacją (level selector), nie usuwamy
- [x] Banner informacyjny `data-testid="history-banner"` ✅
- [ ] Smoke test PASS

**Weryfikacja miast (przy okazji):**
- [ ] Sprawdzić czy `city` w `contracts` pochodzi z kodów pocztowych (nie z surowego adresu)
- [ ] Mapowanie **N:1** — raport grupuje po mieście, nie po kodzie
- [ ] Porównać próbkę dla miast wielokodowych (Warszawa, Kraków, Wrocław)

**Spec:**
- [x] `spec/core/03_frontend_screens.md` — sub-tab Kategorie ✅
- [ ] `spec/core/11_reports_stats.md` — opis UX + info historyczne

**Pliki do zmiany:** `frontend/src/views/ReportsSection.vue`, `backend/stats/router.py`
**ROI:** Raport kategorii czytelny; użytkownik rozumie zakres i historyczność danych
**Estimate:** 4-5h (M)

---

## 🟢 P3 — Nice-to-Have

_Brak otwartych zadań P3._

---

## 📥 Triaged (do przeglądu)

_Pusto — dodawaj nowe zgłoszenia tutaj z `status: triaged`._

---

## 📊 Podsumowanie

| Priorytet | Liczba | Effort łączny |
|-----------|--------|---------------|
| 🚨 P0 | 0 | 0h |
| 🔴 P1 | 0 | 0h |
| 🟡 P2 | 1 | ~5h |
| 🟢 P3 | 0 | 0h |
| **Razem** | **1** | **~5h** |

---

## 📋 Tabela TL;DR

| ID | Tytuł | Źródło | P | Est. | Status | Owner |
|----|-------|--------|---|------|--------|-------|
| RAO-P2-021 | UX Raportów — kategorie drilldown + info historyczne (carry-over) | client-notes | P2 | M | in-progress | cross-stack |

---

## 🗂️ Archiwum sprintów

- Sprint 1 (zakończony 2026-05-22): [archive/BACKLOG_SPRINT_1.md](../archive/BACKLOG_SPRINT_1.md) — 73 taski, ~190h
