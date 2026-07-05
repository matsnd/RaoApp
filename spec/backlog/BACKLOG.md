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
status: triaged
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

**Razem:** 1 zadanie (P0: 1)

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
