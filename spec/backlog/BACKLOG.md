# RAO Backlog — Nowy sprint

> **Status:** Czysty arkusz (2026-07-05)
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/BACKLOG_SPRINT_20260525_20260705.md`
> **Decision log:** `spec/backlog/DECISION_LOG.md` — pełna historia decyzji (co, dlaczego, status)
> **Cel:** Nowe zadania będą dodawane na podstawie współpracy z klientem

---

## ℹ️ Zasady

- Nowe taski dodawane na podstawie wymagań klienta / operatora
- Format: YAML front-matter + sekcje (jak w poprzednim backlogu)
- Status flow: `triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)`
- Po zakończeniu zadania → lokalny commit + update `DECISION_LOG.md`
- Każda decyzja architektoniczna/biznesowa → sekcja w `DECISION_LOG.md`

---

## 🚨 P0 — Production Blockers

### P0-001: `/stats/currently-rented` zwraca 500 — Pydantic ValidationError

```yaml
id: P0-001
status: done
priority: P0
created: 2026-07-05
reporter: Devin (session 2026-07-05)
component: backend/stats
severity: blocker
```

**Symptom:** `GET /rao/api/stats/currently-rented` → 500 Internal Server Error.
Blokada: AnalyticsView → LiveFleet tab (`/rao/analytics`) nie renderuje tabeli.
E2E test `06-analytics.spec.ts:26` (TEST-01: LiveFleet) failuje (1/205 e2e).

**Root cause:** `stats/router.py:311-315` tworzy `CurrentlyRentedItem(id=r[0], ...)`,
ale schema `stats/schemas.py:30` wymaga pola `article_id: int` (brak aliasu `id`).
Pydantic v2 rzuca `ValidationError: article_id Field required`.

**Fix:** zmienić `id=r[0]` → `article_id=r[0]` w `stats/router.py:312`.

**Weryfikacja:**
- `curl /rao/api/stats/currently-rented` → 200 + JSON z `items[]`
- E2E `06-analytics.spec.ts:26` → PASS
- AnalyticsView `/rao/analytics` → LiveFleet tab pokazuje tabelę maszyn

---

### P0-002: AnalyticsView — brak scrolla w dół (treść ucięta)

```yaml
id: P0-002
status: triaged
priority: P0
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/views/AnalyticsView
severity: blocker
```

**Symptom:** `http://localhost:5173/rao/analytics` — nie da się przewijać w dół.
Treść pod tabelą / sekcjami jest niedostępna (ucięta).

**Podejrzany plik:** `frontend/src/views/AnalyticsView.vue` (style: `overflow: hidden`
lub brak `overflow-y: auto` na kontenerze, ew. `height: 100vh` bez scrolla).

**Fix (propozycja):** sprawdzić `.analytics-view` i parent layout — usunąć
`overflow: hidden`, dodać `overflow-y: auto` na scrollowalnym kontenerze.

---

### P0-003: Znak `$` (jedna kreska) kojarzy się z USD — niedopuszczalne

```yaml
id: P0-003
status: triaged
priority: P0
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend (globalne)
severity: blocker
```

**Symptom:** W UI używany jest znak `$` z jedną kreską pionową, który silnie
kojarzy się z dolarem amerykańskim (USD). W polskiej aplikacji wynajmu maszyn
jest to niedopuszczalne — należy używać `zł` lub `PLN`.

**Zakres:** wszystkie miejsca w UI gdzie pojawia się `$` (placeholder, PDF,
raporty, formularze, tabele). Wymaga audytu globalnego.

**Fix (propozycja):**
- Zamienić wszystkie `$` na `zł` w frontend (formatowanie waluty)
- Sprawdzić `frontend/src/utils/format.ts` lub podobne (formatter waluty)
- Sprawdzić szablony PDF (`backend/reports/templates/*.html`)
- Sprawdzić czy `$` nie jest używane jako symbol zmiennej w treściach (np. `$1`, `$2` w opisach opłat — tam zamienić na `{{ }}` lub `zł`)

---

### P0-004: Eksplorator — kontrahent jako dropdown (select) zamiast wyszukiwarki

```yaml
id: P0-004
status: triaged
priority: P0
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/components/analytics/ExplorerTab + AnalyticsFilters
severity: blocker
```

**Symptom:** W Eksploratorze (`/rao/analytics` → tab Eksplorator) kontrahent
jest zwykłym dropdownem (`<select>`). Przy dużej liczbie kontrahentów (698 w DB)
zwykły select jest nieużywalny — nie da się wyszukać po nazwie.

**Wymaganie:** Kontrahent musi być comboboxem (dropdown wpisywalny) —
pole tekstowe z autouzupełnianiem, filtrujące listę w miarę wpisywania.

**Podejrzany plik:** `frontend/src/components/analytics/AnalyticsFilters.vue`
(`data-testid="filter-contractor"` — obecnie `<select>`).

**Fix (propozycja):**
- Zamienić `<select>` na combobox (input + dropdown z filtrowaniem)
- Lub użyć istniejący komponent `ContractorPicker` jeśli istnieje
- Filtr po nazwie (case-insensitive, substring match)
- Backend już wspiera `?contractor_id=` — frontend musi wysłać ID wybranego
- Sprawdzić czy ten sam filtr jest używany w innych tabach (PeriodRental, Locations) —
  jeśli tak, naprawa w jednym miejscu (`AnalyticsFilters.vue`) pokryje wszystkie

---

## 🔴 P1 — Must-Have
*(brak)*

---

## 🟡 P2 — Should-Have
*(brak)*

---

## 🟢 P3 — Nice-to-Have
*(brak)*

---

## 📋 Decyzje operatora

*(nowe decyzje dodawane tutaj + w `DECISION_LOG.md`)*

---

## 📊 Summary

**Razem:** 4 zadania (P0: 4, done: 1)

### Pipeline weryfikacji (status flow)

```
triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)
           │              │               │               │               │
           Devin koduje   Devin testuje   Software-house  Ty wzrokowo    Klient zatwierdza
           zmianę         programatycz.   subagenty       w UI/PDF        → zadanie zamknięte
                          (Playwright,    (QA, Security,
                           PyMuPDF,       UX, PO, Tech
                           pytest,        Lead review)
                           vue-tsc)
```
