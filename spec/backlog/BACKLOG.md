# RAO Backlog — Sprint 2026-07-21 →

> **Status:** Oczyszczony 2026-07-21 (31 tasków zarchiwizowanych → `archiwum/BACKLOG_SPRINT_20260711_20260721.md`)
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/BACKLOG_SPRINT_20260711_20260721.md`
> **Decision log:** `spec/backlog/DECISION_LOG.md` — pełna historia decyzji (co, dlaczego, status)
> **Cel:** Nowe zadania będą dodawane na podstawie współpracy z klientem
> **Kontekst:** Aplikacja działa stabilnie na prod. User ma nowe uwagi — po czyszczeniu backlogu zostaną dodane.

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

*Brak aktywnych P0. Aplikacja działa stabilnie na prod (2026-07-21).*

---

## 🔴 P1 — Must-Have

### P1-201: Przedpłata w PDF — dopisek "brutto"

```yaml
id: P1-201
status: dev-verified
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/reports/templates/contract.html + contract_u.html
migration_impact: no
```

**Opis:** W szablonie PDF umowy (S i U) w górnej tabeli informacyjnej przedpłata wyświetla się jako "Przedpłata: 1 200,00 zł" — klient chce dopisek "brutto" po kwocie: "Przedpłata: 1 200,00 zł brutto".

**Zadania:**
1. `backend/reports/templates/contract.html` (linia 136) — dodać " brutto" po `{{ contract.prepayment_amount | money }}`
2. `backend/reports/templates/contract_u.html` (linia 126) — to samo

**Definition of Done:**
- [x] PDF umowy S pokazuje "Przedpłata: ... zł brutto"
- [x] PDF umowy U pokazuje "Przedpłata: ... zł brutto"
- [x] Brak zmian w innych sekcjach PDF
- [x] Smoke `01-login.spec.ts` zielony (zmiana w template HTML, nie dotyka kodu)

---

---

## 🟡 P2 — Should-Have

*Brak aktywnych P2.*

---

## 🟢 P3 — Nice-to-Have

*Brak*

---

## 📝 Nowe uwagi (do triage'u)

> **Instrukcja:** Wklej nowe uwagi poniżej. Po analizie Tech Lead zaklasyfikuje je (P0/P1/P2/P3) i utworzy taski z YAML front-matter w odpowiednich sekcjach powyżej.

<!-- Wklej uwagi tutaj -->

---

## ✅ Done — Ukończone zadania

*Brak done w bieżącym sprincie. Historia w `archiwum/`.*
