# _session_context.md — szablon (kopiuj na start zadania)

> Pisze WYLACZNIE orkiestrator (single-writer). Subagenty czytaja (dostaja tresc w prompcie).

```markdown
# Session: <task_id / krotki opis>
Data: <YYYY-MM-DD> · Rozmiar: S|M|L · Tryb: normal|full-auto

## Zadanie
<opis od usera>

## DoD
<z product-owner (L) lub wlasna (M/S) — weryfikowalna lista>

## Plan faz
- [ ] Phase 0 analiza (L only)
- [ ] DB (db-architect) — commit: <hash>
- [ ] Backend (backend-dev) — commit: <hash>
- [ ] Frontend (frontend-dev) — commit: <hash>
- [ ] Polish (design-reviewer, gdy wizualne)
- [ ] Audit (security + perf, rownolegle)
- [ ] QA — commit: <hash>
- [ ] Final review (L only)

## HANDOFFY (append-only, orkiestrator dopisuje)
### <rola> @ <czas>
<wklejony HANDOFF>
REVIEW: <APPROVE po N iteracjach | findings>

## Open issues / conflicts
<konflikt + rozstrzygniecie wg hierarchii>

## Proby naprawcze
<faza, proba #, root cause, strategia> (budzet: 12)
```
