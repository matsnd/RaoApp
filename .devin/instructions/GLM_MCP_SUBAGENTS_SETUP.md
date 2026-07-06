# Instrukcja konfiguracji MCP dla subagentów - GLM-5.2 High

## Cel
Skonfigurować custom subagenty RAO (backend-dev, db-architect, frontend-dev, itd.) aby miały dostęp do MCP narzędzi (codebase-memory, depwire, mariadb, rao-vision).

## Wymagania wstępne
- Devin CLI z ostatnich tygodni (sprawdź czy funkcja "subagents can now call MCP tools directly" istnieje)
- Dostęp do plików konfiguracyjnych subagentów w `.devin/agents/` lub `.agents/`
- Dostęp do `.env` z credentials

---

## Krok 0: Uzupełnij tabelę parametrów PRZED rozpoczęciem

| Parametr | Wartość do uzupełnienia |
|----------|------------------------|
| Ścieżka do AGENTS.md | `c:/projects/repos/RaoApp_new/AGENTS.md` |
| Ścieżka do profili subagentów | `c:/projects/repos/RaoApp_new/.devin/agents/` LUB `c:/projects/repos/RaoApp_new/.agents/` |
| Nazwa testowanego subagenta | `db-architect` (najprostszy test: mariadb) |
| MCP serwer do testu | `mariadb` |
| MCP narzędzie do testu | `query_database` |
| Pełna nazwa narzędzia | `mcp__mariadb__query_database` |
| Testowe zapytanie SQL | `SELECT 1` |

---

## Krok 1: Sprawdź wersję CLI

**Komenda:**
```bash
devin --version
```

**Kryterium sukcesu:**
- Jeśli CLI jest starszy niż 2-3 tygodnie → zaktualizuj przed kontynuacją
- Jeśli changelog zawiera "subagents can now call MCP tools directly" → kontynuuj

**Jeśli wersja jest stara:**
```bash
devin update
```

---

## Krok 2: Usuń dezinformację z AGENTS.md

**Problem:** W AGENTS.md znajduje się sekcja "⚠️ MCP tools — NIEDOSTĘPNE dla custom subagentów", która powoduje że subagenty zgadzają się z instrukcją zamiast testować runtime.

**Akcja:**
1. Otwórz `AGENTS.md`
2. Znajdź sekcję zaczynającą się od `⚠️ MCP tools`
3. Usuń lub zakomentuj całą sekcję
4. Zapisz plik

**Czego NIE robić:**
- Nie usuwaj innych sekcji AGENTS.md
- Nie zmieniaj innych instrukcji

---

## Krok 3: Zaktualizuj frontmatter testowanego subagenta

**Lokalizacja pliku:** Użyj ścieżki z tabeli parametrów (Krok 0)

**Obecny frontmatter (przykładowy):**
```yaml
---
name: db-architect
description: Database Architect dla RAO...
allowed-tools:
  - read
  - edit
  - exec
  - grep
  - find_file_by_name
permissions:
  allow:
    - exec
  deny:
    - mcp__*
---
```

**Nowy frontmatter (z MCP):**
```yaml
---
name: db-architect
description: Database Architect dla RAO...
allowed-tools:
  - read
  - edit
  - exec
  - grep
  - find_file_by_name
  - mcp__mariadb__query_database
permissions:
  allow:
    - exec
    - mcp__mariadb__query_database
  deny:
    - mcp__*  # Opcjonalne: blokuj inne MCP narzędzia
---
```

**Zasady:**
- Dodaj konkretne narzędzie do `allowed-tools` (nie `mcp__*`)
- Dodaj to samo narzędzie do `permissions.allow`
- Format: `mcp__serwer__narzędzie` (dokładnie tak, jak w dokumentacji)
- Nie używaj wildcardów `mcp__*` w `allowed-tools` (bezpieczeństwo)

---

## Krok 4: Uruchom test w foreground (NIE background)

**Dlaczego foreground:** Background auto-deny może zablokować MCP nawet przy poprawnej konfiguracji. Foreground pokaże czy narzędzie istnieje w runtime.

**Komenda:**
```bash
devin --agent db-architect
```

**Prompt do subagenta (wklej dosłownie):**
```
Wywołaj narzędzie mcp__mariadb__query_database z argumentem query="SELECT 1".

WYMAGANIA:
1. Nie oceniaj z góry, czy narzędzie istnieje
2. Wykonaj wywołanie
3. Wklej dosłowny, surowy wynik LUB komunikat błędu
4. Nie interpretuj błędu - tylko wklej go

Jeśli narzędzie nie jest dostępne, wklej dokładny komunikat błędu z runtime'u.
```

---

## Krok 5: Interpretuj wynik

### Wynik A: Sukces
```
Result: {"result": "1"}
```
**Diagnoza:** MCP działa poprawnie
**Akcja:** Powtórz Krok 3 dla wszystkich subagentów z ich MCP narzędziami

### Wynik B: "unknown tool" / "tool not found"
```
Error: Unknown tool: mcp__mariadb__query_database
```
**Diagnoza:** Ekspozycja ucięta przez restrict - allowed-tools nie wystawia MCP
**Akcja:** Sprawdź czy narzędzie jest dokładnie w allowed-tools (literówki?) oraz czy CLI jest aktualny

### Wynik C: "permission denied"
```
Error: Permission denied: mcp__mariadb__query_database
```
**Diagnoza:** Narzędzie jest widoczne, ale permissions.allow blokuje
**Akcja:** Dodaj do permissions.allow w frontmatterze

### Wynik D: Auto-deny (background)
```
Error: Tool call auto-denied
```
**Diagnoza:** Background mode bez pre-approval
**Akcja:** Testuj w foreground, dodaj do permissions.allow dla background

---

## Krok 6: Jeśli sukces - zaktualizuj wszystkie subagenty

**Mapa MCP narzędzi dla ról RAO:**

| Rola | MCP narzędzia do dodania |
|------|--------------------------|
| `backend-dev` | `mcp__codebase-memory__search_graph`, `mcp__codebase-memory__trace_path` |
| `db-architect` | `mcp__mariadb__query_database` |
| `frontend-dev` | `mcp__rao-vision__screenshot_and_analyze` (opcjonalnie) |
| `qa-engineer` | `mcp__depwire__get_architecture_summary`, `mcp__depwire__impact_analysis` |
| `security-auditor` | `mcp__codebase-memory__trace_path`, `mcp__depwire__security_scan` |
| `performance-eng` | `mcp__depwire__find_dead_code`, `mcp__codebase-memory__query_graph` |

**Dla każdego subagenta:**
1. Otwórz plik profilu
2. Dodaj odpowiednie MCP narzędzia do `allowed-tools`
3. Dodaj te same narzędzia do `permissions.allow`
4. Zapisz plik

---

## Krok 7: Przywróć AGENTS.md (opcjonalnie)

**Jeśli test się powiódł:**
- Przywróć sekcję "⚠️ MCP tools" w AGENTS.md
- Zmień treść na: "MCP narzędzia są dostępne dla subagentów po skonfigurowaniu w frontmatterze"

**Jeśli test się nie powiódł:**
- Przywróć sekcję "⚠️ MCP tools" w AGENTS.md
- Zostaw informację o niedostępności
- Używaj workflow "Tech Lead jako MCP proxy"

---

## Tabela obsługi błędów

| Błąd | Przyczyna | Rozwiązanie |
|------|-----------|-------------|
| `unknown tool` | Literówka w nazwie narzędzia | Sprawdź format: `mcp__serwer__narzędzie` |
| `unknown tool` | CLI stary, brak funkcji MCP | `devin update` |
| `permission denied` | Brak w `permissions.allow` | Dodaj do permissions.allow |
| `permission denied` | Background auto-deny | Testuj w foreground |
| `mcp__* blocked` | Wildcard w `deny` | Usuń `deny: mcp__*` lub dodaj wyjątki |
| Subagent cytuje instrukcję | Priming z AGENTS.md | Usuń sekcję o niedostępności MCP |
| Narzędzie nie pojawia się | Zła ścieżka profilu | Sprawdź czy edytujesz właściwy plik |

---

## Kryteria sukcesu end-to-end

1. ✅ CLI jest aktualny
2. ✅ AGENTS.md nie zawiera dezinformacji o MCP
3. ✅ Testowany subagent ma MCP w allowed-tools
4. ✅ Testowany subagent ma MCP w permissions.allow
5. ✅ Foreground test zwraca sukces LUB jasny komunikat błędu
6. ✅ Wszystkie subagenty mają swoje MCP narzędzia skonfigurowane
7. ✅ Smoke test: subagent wykonuje rzeczywiste MCP wywołanie

---

## Zasady dla GLM-5.2 High

1. **Nie improwizuj** - postępuj dokładnie według kroków
2. **Nie pomijaj kroków** - nawet jeśli wydaje się że są zbędne
3. **Uzupełnij tabelę parametrów** przed rozpoczęciem
4. **Wklejaj dosłowne błędy** - nie interpretuj ich
5. **Jeśli coś nie działa** - sprawdź tabelę obsługi błędów
6. **Sekrety tylko do .env** - nie wklejaj haseł w raportach
7. **Scalaj zamiast nadpisywać** - dodawaj MCP do istniejących list, nie wymieniaj całych frontmatterów

---

## Notatki dla implementacji

- Krok 5 (izolacja MCP tylko dla jednego subagenta) jest opcjonalny - GLM może go pominąć
- Jeśli test się nie powiedzie, workflow "Tech Lead jako MCP proxy" jest bezpiecznym fallback
- Zgłoś do Cognition jeśli CLI aktualny, a MCP nadal nie działa (rozbieżność z changelogiem)
