# Instrukcja: MCP w subagentach RAO — zweryfikowana konfiguracja (v2)

## Kontekst — dlaczego wcześniej nie działało

Poprzednia konfiguracja miała cztery błędy, które łącznie dawały objaw "subagenty nie widzą MCP":

1. **`config.json` był niepoprawnym JSON-em** (nadmiarowe `}` na końcu) — parser mógł pomijać `mcpServers`/`permissions`.
2. **`allowed-tools` zawierało `mcp_call_tool`** — takie narzędzie nie istnieje. Narzędzia MCP są eksponowane jako `mcp__<serwer>__<narzędzie>`. Whitelist bez tych nazw = zero MCP w runtime subagenta.
3. **`permissions.allow` używało `MCP(nazwa)`** — wymyślona składnia. Poprawne matchery: `mcp__serwer__narzędzie`, `mcp__serwer__*`, `mcp__*`.
4. **AGENTS.md i README deklarowały "MCP NIEDOSTĘPNE"** — subagenty cytowały tę tezę zamiast testować runtime (samospełniająca się przepowiednia).

Wszystkie cztery są naprawione w tej paczce `.devin/`. Ta instrukcja służy już tylko do WERYFIKACJI i diagnostyki.

## Poprawny wzorzec frontmatteru (referencja)

```yaml
---
name: db-architect
description: ...
allowed-tools:          # co subagent WIDZI (ekspozycja)
  - read
  - grep
  - glob
  - edit
  - write
  - exec
  - mcp__codebase-memory__*
  - mcp__depwire__*
  - mcp__mariadb__*
permissions:
  allow:                # co przechodzi BEZ pytania (konieczne dla background)
    - Exec(mariadb*)
    - mcp__codebase-memory__*
    - mcp__depwire__*
    - mcp__mariadb__*
  deny:
    - Write(frontend/**/*)
model: GLM-5.2 High
---
```

Zasada: matcher MCP musi być w OBU miejscach — `allowed-tools` (żeby narzędzie istniało w runtime) i `permissions.allow` (żeby background nie dostał auto-deny).

## Procedura weryfikacji (wykonaj kroki w kolejności)

### Krok 1 — wersja CLI
```bash
devin --version
```
Funkcja "subagents can call MCP tools directly" jest świeża. Jeśli CLI starszy niż z ostatnich tygodni: `devin update`, potem kontynuuj.

### Krok 2 — świeża sesja + status serwerów
Uruchom NOWĄ sesję `devin` w root repo (konfiguracja ładuje się przy starcie). Wpisz `/mcp`.
Kryterium: serwery `rao-vision`, `mariadb`, `codebase-memory`, `depwire`, `playwright` mają status connected. Jeśli któregoś nie ma na liście — nie jest zdefiniowany w żadnym configu (sprawdź też user-level `%APPDATA%\devin\config.json`); dopisz go zanim przejdziesz dalej.

### Krok 3 — test runtime na subagencie
Prompt do głównego agenta:
```
Uruchom subagenta db-architect w foreground z zadaniem:
"Wywołaj narzędzie mcp__mariadb__query_database z zapytaniem SELECT 1.
Nie oceniaj z góry, czy narzędzie istnieje — wykonaj wywołanie
i wklej DOSŁOWNY surowy wynik lub pełny komunikat błędu.
Dodatkowo wypisz pełną listę narzędzi, które masz w runtime."
```

### Krok 4 — interpretacja wyniku
| Wynik | Diagnoza | Akcja |
|---|---|---|
| `SELECT 1` zwraca wynik | MCP działa | koniec, zaktualizuj status w README |
| "unknown tool" / brak na liście | ekspozycja ucięta mimo poprawnego `allowed-tools` | to jest bug CLI — zgłoś do Cognition z wersją CLI i frontmatterem |
| "permission denied" / prompt o zgodę | warstwa approvals | sprawdź, czy matcher jest w `permissions.allow` frontmatteru ORAZ czy `config.json` parsuje się (`python -m json.tool .devin/config.json`) |
| subagent odmawia "bo instrukcja mówi że nie ma MCP" | gdzieś został stary tekst | `grep -rn "NIEDOST" AGENTS.md .devin/` i usuń |

### Krok 5 — test background
Powtórz Krok 3 z jawnym uruchomieniem w tle. Auto-deny w tle = brakujący wpis w `permissions.allow`.

## Reguły stałe

- Sekrety TYLKO w `.devin/config.local.json` (gitignored). Nigdy w `config.json`, nigdy w raportach subagentów (nazwy zmiennych zamiast wartości).
- Po każdej zmianie configu / frontmatteru: nowa sesja.
- Raport z każdego testu MCP musi zawierać surowy komunikat runtime, nie parafrazę.
