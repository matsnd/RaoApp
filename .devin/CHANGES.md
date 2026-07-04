# CHANGES — audyt i naprawa .devin (2026-07-05)

## Weryfikacja runtime MCP w subagentach (2026-07-05, CLI 2026.8.18)

Test empiryczny (3 profile, foreground, to samo zadanie):

| Profil | MCP w runtime? | Narzędzia |
|---|---|---|
| `subagent_general` (wbudowany) | ✅ TAK | pełny zestaw + 11 serwerów MCP (`mariadb`, `codebase-memory`, `depwire`, `rao-vision`, `playwright`, …) |
| `subagent_explore` (wbudowany) | ❌ NIE | filesystem + `web_search` (6 narzędzi) |
| custom `AGENT.md` (`db-architect`) | ❌ NIE | 5 narzędzi (`read`, `grep`, `edit`, `exec`, `find_file_by_name`) — nawet po usunięciu `allowed-tools` |

**Dowód:** `subagent_general` wywołał `mcp__mariadb__query_database({"query":"SHOW TABLES"})` → 33 tabele; `mcp__codebase-memory__search_graph(...)` → 199 wyników. `db-architect` (custom) przy tym samym zadaniu: "narzędzie nie istnieje w moim runtime" (tylko 5 narzędzi filesystem).

**Wniosek:** to **bug CLI 2026.8.18**, nie błąd konfiguracji. Configi parsują się OK (`python -m json.tool` przechodzi na 3 plikach), `mcp__serwer__*` matchery są poprawne w `allowed-tools` i `permissions.allow`. Custom subagenty po prostu nie dostają MCP wstrzykniętego do runtime.

**Workaround (testowany, działa):** używaj `subagent_general` z instrukcją roli z `AGENT.md` wklejoną do promptu. Tech Lead (główny agent) spawnuje `subagent_general` z treścią roli. `subagent_general` ma pełny dostęp do MCP.

**Zaktualizowano:**
- `.devin/agents/README.md` — sekcja "Agents z dostępem do vision" przepisana z weryfikowanym statusem + tabelą profil/MCP + workaround
- `.devin/agents/db-architect/AGENT.md` — banner runtime w sekcji MCP + naprawione nazwy narzędzi mariadb (`execute_sql`/`list_tables`/`get_table_schema` → `query_database` z odpowiednim SQL)

**Pozostało do naprawy (follow-up):**
- ~~Nazwy narzędzi mariadb w 7 pozostałych `AGENT.md`~~ — **ZROBIONE 2026-07-05** (commit poniżej): `backend-dev`, `frontend-dev`, `tech-lead`, `qa-engineer`, `performance-eng`, `security-auditor`, `product-owner` — wszystkie 45 błędnych odniesień zamienione na `query_database` z mapowaniami.
- ~~Banner runtime w 10 pozostałych `AGENT.md`~~ — **ZROBIONE 2026-07-05**: wszystkie 11 `AGENT.md` ma banner "RUNTIME 2026-07-05" w sekcji MCP/Vision.
- Zgłoszenie buga do Cognition: custom `AGENT.md` subagenty nie dostają MCP tools mimo poprawnych `mcp__serwer__*` w `allowed-tools` (CLI 2026.8.18)

## Krytyczne (to blokowało MCP w subagentach) — poprzednia tura

1. **config.json był niepoprawnym JSON-em** — nadmiarowe `} }` + `}` na końcu pliku.
   Naprawione i zwalidowane (`python -m json.tool` przechodzi na wszystkich trzech configach).
2. **`allowed-tools: mcp_call_tool` we wszystkich 11 profilach** — takie narzędzie nie istnieje;
   MCP jest eksponowane jako `mcp__<serwer>__<narzędzie>`. Zastąpione matcherami `mcp__serwer__*`
   dobranymi per rola.
3. **`permissions.allow: MCP(nazwa)`** — wymyślona składnia, zastąpiona `mcp__serwer__*`.
   Każdy matcher jest w OBU miejscach (allowed-tools = ekspozycja, permissions.allow = auto-approval
   dla background).
4. **`permissions.deny: write/edit/exec`** — niepoprawne matchery; zastąpione `Write(**)`/`Edit(**)`
   dla ról read-only (exec egzekwowany przez brak w allowed-tools). Deny na Write dostały parę Edit
   (wcześniej dało się edytować pliki zabronione do zapisu, np. backend/main.py).
5. **Samospełniająca się przepowiednia** — sekcja "MCP NIEDOSTĘPNE dla custom subagentów"
   w agents/README.md zastąpiona neutralną instrukcją "testuj runtime, raportuj surowy błąd".
   ⚠️ UWAGA: analogiczna sekcja jest podobno w AGENTS.md w root repo — TEGO PLIKU NIE MA W TEJ
   PACZCE, usuń ją ręcznie.
6. **Pseudo-API `mcp_call_tool(server_name=..., ...)`** w treściach 4 profili + MCP_CONFIG.md —
   zastąpione notacją bezpośrednią `mcp__serwer__narzędzie({...})`.

## Bezpieczeństwo

7. **Żywe sekrety w config.json** (OPENROUTER_API_KEY, ANTHROPIC_API_KEY) — z komentarzem fałszywie
   twierdzącym, że to placeholdery. Przeniesione do config.local.json (gitignored).
   config.json jest teraz commitowalny i bez kluczy.
   ⚠️ ZALECANA ROTACJA WSZYSTKICH 4 KLUCZY (OpenRouter, Anthropic, Brave, GitHub PAT) — patrz wiadomość.
8. Dodany `.devin/.gitignore` (config.local.json, *.log, _evidence/, plans/).
9. config.example.json przerobiony na szablon config.local.json z placeholderami.

## Porządek

10. Usunięte 23 pliki-śmieci: _commit_msg* (11 wariantów), fragmenty workflows (coord,
    coordination-, ...), logi, _fix_readme.*, pliki "_" i "work".
11. instructions/GLM_MCP_SUBAGENTS_SETUP.md przepisany na v2: diagnoza 4 błędów + procedura
    weryfikacji z tabelą interpretacji błędów runtime.
12. MCP_CONFIG.md: banner aktualizacyjny z nowym podziałem configów i poprawną składnią.

## Znane otwarte tematy

- Serwery `codebase-memory`, `depwire`, `mariadb` używane w profilach NIE są zdefiniowane w tym
  katalogu — jeśli działają, są w user-level `%APPDATA%\devin\config.json`. Jeśli mają być
  per-projekt (zalecane dla spójności zespołu), dopisz definicje do config.json.
- `model: GLM-5.2 High` — zweryfikuj, że to dokładny identyfikator modelu w Twojej wersji CLI
  (spacja w nazwie bywa problematyczna); jeśli subagenty spawnują się na innym modelu, podmień
  na id z pickera.
- Po podmianie: NOWA sesja devin → `/mcp` → test z instructions/GLM_MCP_SUBAGENTS_SETUP.md (Krok 3).
