---
description: Kanoniczny protokol implement→review — jedyna kopia. Wykonalny przez stateless subagenty (zadnego fikcyjnego "pair programmingu w locie").
---

# Implement → Review Protocol

> Dlaczego nie "pair programming"? Subagenty sa stateless i one-shot — dwa agenty w tle
> NIE rozmawiaja ze soba. Rownolegly spawn "pary" = 2 niezalezne monologi za 2x tokeny.
> Sekwencja implement→review daje realna druga pare oczu za ulamek kosztu:
> reviewer czyta DIFF (tanio), nie pisze od zera.

## Cykl (per faza)

```
IMPLEMENTER                     ORKIESTRATOR                REVIEWER
subagent_general                (Ty)                        subagent_general
+ rola X                                                    + rola X + checklist
     │                               │                            │
     │ 1. implementuje               │                            │
     │ 2. testy + evidence           │                            │
     │ 3. HANDOFF (diff summary) ───▶│                            │
     │                               │ 4. scope check             │
     │                               │    evidence check          │
     │                               │ 5. spawn z diffem ────────▶│
     │                               │                            │ 6. czyta diff
     │                               │◀─── APPROVE / CHANGES ─────│    + checklist
     │◀── respawn z lista poprawek ──│ (gdy CHANGES, max 2 iter)  │
     │                               │ 7. APPROVE → commit fazy   │
```

## Krok po kroku

1. **Spawn IMPLEMENTER** (foreground): rola + kontekst + zadanie. Output: HANDOFF.
2. **Weryfikacja orkiestratora** (SKILL.md Krok 5): scope, evidence, spec.
3. **Spawn REVIEWER** (foreground): TA SAMA rola + sekcja "Review checklist" z pliku roli
   + wklejony `git diff` fazy + kontekst zadania. Reviewer NIE pisze kodu.
   Output — dokladnie jeden z:
   - `REVIEW: APPROVE` + 1-2 zdania uzasadnienia
   - `REVIEW: CHANGES` + numerowana lista konkretnych poprawek (plik:linia, co, dlaczego)
4. **CHANGES** → respawn implementera z lista (pelny kontekst + diff + lista). **Max 2 iteracje** — po 2. iteracji orkiestrator rozstrzyga sam wg hierarchii konfliktow.
5. **APPROVE** → commit fazy (targeted add + secret scan).

## Kiedy review, kiedy nie

| Rozmiar | Review? |
|---------|---------|
| S | NIE — orkiestrator sam weryfikuje smoke testem |
| M | TAK — 1 cykl na jedyna faze implementacyjna |
| L | TAK — na kazda faze DB/Backend/Frontend; Audit i QA to osobne fazy, nie review |

## Wariant ping-pong (opcjonalny, dla logiki biznesowej wysokiego ryzyka)

1. Spawn A: "napisz TYLKO testy (pytest) pod DoD, bez implementacji" → testy czerwone
2. Spawn B: "zaimplementuj tak, by testy przeszly; testow nie zmieniaj"
3. Review normalnie na diffie implementacji

Uzywaj gdy: rozliczenia, uprawnienia, obliczenia finansowe. Nie uzywaj do CRUD.

## Zasady twarde

- Reviewer dostaje diff w prompcie — NIE kaz mu szukac zmian po repo.
- Review checklist pochodzi z pliku roli (sekcja "Review checklist") — nie improwizuj.
- Reviewer nie edytuje plikow. Znalazl problem → opisuje, implementer naprawia.
- Iteracja 3+ nie istnieje. Deadlock → orkiestrator decyduje, loguje konflikt.
