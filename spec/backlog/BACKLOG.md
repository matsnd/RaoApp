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
*(brak)*

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

**Razem:** 0 zadań

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
