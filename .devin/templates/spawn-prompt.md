# Szablon promptu spawnu (subagent_general)

> Orkiestrator wypelnia i spawnuje. Subagent jest STATELESS — sekcje 1-2 wklejaj W CALOSCI, bez skrotow.

```
=== ROLA ===
<CALA tresc .devin/roles/<rola>.md>

=== KONTEKST STACKU ===
<CALA tresc .devin/context/rao-stack.md>

=== ZADANIE ===
<konkret: co ma powstac / co zweryfikowac>

=== TRYB ===
IMPLEMENTER | REVIEWER (gdy REVIEWER: ponizej diff; uzyj sekcji "Review checklist" z roli;
NIE edytuj plikow; output: REVIEW: APPROVE|CHANGES + lista)

=== DIFF DO REVIEW === (tylko tryb REVIEWER)
<git diff fazy>

=== CO JUZ WIEM ===
<wnioski z poprzednich faz / HANDOFFy poprzednich rol / findings z analizy>

=== PLIKI DO PRZECZYTANIA NAJPIERW ===
<konkretne sciezki — spec + kod>

=== DOZWOLONE SCIEZKI (scope; git diff bedzie zweryfikowany) ===
<globy z sekcji Scope roli>

=== POPRAWKI DO WPROWADZENIA === (tylko iteracja 2+ po CHANGES)
<numerowana lista od reviewera>

=== OUTPUT ===
HANDOFF wg formatu z kontekstu stacku. Evidence do .devin/_evidence/<rola>/.
```
