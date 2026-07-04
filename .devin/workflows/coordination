---
description: Protokół koordynacji 11 ról RAO — single source of truth, linkowany nie kopiowany
---

# 🤝 Coordination Protocol — RAO Software House

> Parent (Tech Lead) czyta to. Subagenty dostają kontekst w prompcie od parenta — nie czytają protokołu.
> Szczegóły sekcji 2-5 tylko gdy konflikt lub nietypowa sytuacja.

## TL;DR (parent czyta to, reszta opcjonalna)

1. **Parent** tworzy `.devin/_session_context.md` na starcie (zadanie, decyzja, DoD, plan z statusami)
2. **Subagenty czytają** `_session_context.md` (read-only, NIE edytują) + dostają kontekst w prompcie
3. **Subagenty zwracają** HANDOFF w outputcie → **parent dopisuje** do `_session_context.md` (single-writer = zero race)
4. **Evidence obowiązkowe** w `.devin/_evidence/<role>/` — brak = odrzucony handoff
5. **Review chain:** DB→Backend→Frontend→[UI|UX|Motion równolegle]→[Security|Performance równolegle]→QA→[TL|PO]
6. **Conflict hierarchy:** Security (veto) > Data > Correctness > UX > Performance > UI > Motion > Style
7. **Vision dedup:** frontend-dev robi 1 screenshot per widok, inne role reuse przez `rao-vision.analyze_screenshot`
8. **Spec/backlog:** subagenty aktualizują zgodnie ze swoim AGENT.md (NIE zmienia się); parent weryfikuje `git diff --stat spec/core/` przed commitem

---

## 1. Handoff format (każdy subagent zwraca w outputcie)

```
## HANDOFF
**CO ZROBIŁEM:** <konkret, pliki>
**GOTOWE DLA:** <role + co mogą użyć>
**BLOCKERY:** <lista lub "brak">
**EVIDENCE:** <ścieżki do .devin/_evidence/<role>/ lub "brak">
**SPEC UPDATE:** <pliki spec/ zaktualizowane zgodnie z AGENT.md — RAPORT; lub "brak">
```

**NIE edytuj `_session_context.md`** — parent dopisze (single-writer).

## 2. Review chain (DAG zależności)

```
Phase 0 ANALYSIS (równolegle, bg): product-owner, tech-lead, qa-engineer, security-auditor
Phase 1 DB: db-architect (po tech-lead plan)
Phase 2 BACKEND: backend-dev (po db-architect)
Phase 3 FRONTEND: frontend-dev (po backend-dev)
Phase 4 POLISH (równolegle po frontend, bg): ui-designer, ux-designer, motion-designer
Phase 5 AUDIT (równolegle po backend+frontend, bg): security-auditor, performance-eng
Phase 6 QA: qa-engineer (po wszystkich implementacjach)
Phase 7 FINAL REVIEW (równolegle po QA, bg): tech-lead, product-owner
COMMIT (Tech Lead po final review)
```

- **Foreground** (czekaj): zależne kroki (DB→Backend→Frontend)
- **Background** (równolegle): niezależne (analiza, polish, audit, final review)
- **Max 4 równolegle** (limit kontekstu)
- **Pomiń fazę** gdy nie dotyczy (DB-only → pomiń 3,4; bugfix → pomiń 0 jeśli trywialny)

## 3. Conflict resolution

Hierarchia (wyższy wygrywa):
```
1. Security (veto — blokuje produkcję, ostateczne)
2. Data integrity (DB-architect)
3. Correctness (QA — testy zielone, veto do merge)
4. UX (zrozumiałość flow)
5. Performance (p95 < target)
6. UI consistency (design system)
7. Motion (polish)
8. Code style
```

- **CO** budujemy → Product Owner
- **JAK** architektonicznie → Tech Lead
- **Security veto** jest ostateczne — escaluj do usera jeśli blokuje, NIGDY nie omijaj
- Konflikty zapisuj w `Open issues / conflicts` w `_session_context.md`, rozstrzygaj według hierarchii

## 4. Evidence (obowiązkowe)

`.devin/_evidence/<role>/` (git-ignored, artefakty sesji):
- `.txt` — curl, pytest, vue-tsc, DESCRIBE, EXPLAIN
- `.png` — screenshoty z Playwright
- `.md` — vision verdict

**Brak evidence = odrzucony handoff.** Parent weryfikuje przed commitem.

## 5. Vision deduplikacja

Frontend-dev robi **1 screenshot per widok per faza** → `.devin/_evidence/frontend-dev/screenshot_<view>.png`.
Inne role (ui-designer, ux-designer, motion-designer, product-owner) **reuse** przez `rao-vision.analyze_screenshot` z różnymi pytaniami. Nowy screenshot tylko gdy: inny widok, inny stan, inna akcja.

## 6. Spec/backlog alignment (NIE zastępuje, wzmacnia)

Subagenty aktualizują spec/ zgodnie ze swoim AGENT.md (sekcja "Po zmianie") — **to się NIE zmienia**.
W handoff "SPEC UPDATE" to **RAPORT** (co zaktualizowano), nie akcja.
Parent weryfikuje `git diff --stat spec/core/` przed commitem — pusty diff przy zmianach funkcjonalnych = niedopełniony obowiązek (reguła z AGENTS.md).

| Spec | Aktualizuje | Weryfikuje parent |
|------|-------------|-------------------|
| spec/core/01_database.md | db-architect | `git diff spec/core/01_database.md` |
| spec/core/02_backend_api.md | backend-dev | `git diff spec/core/02_backend_api.md` |
| spec/core/03_frontend_screens.md | frontend-dev | `git diff spec/core/03_frontend_screens.md` |
| spec/core/09_design_reference.md | ui-designer | `git diff spec/core/09_design_reference.md` |
| spec/core/25_security.md | security-auditor | `git diff spec/core/25_security.md` |
| spec/backlog/BACKLOG.md | rola wykonująca | `git diff spec/backlog/BACKLOG.md` |

---

**Ostatnia aktualizacja:** 2026-07-05
**Powiązane:** `AGENTS.md`, `.devin/skills/software-house/SKILL.md`, `.devin/agents/*/AGENT.md`
