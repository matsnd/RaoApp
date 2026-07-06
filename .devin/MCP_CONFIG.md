# Devin MCP Configuration — RAO

Konfiguracja serwerów MCP dla Devina, dopasowana do tego co Cascade ma w Windsurf, plus custom `rao-vision` dla analizy screenshotów przez Claude Vision API.

## ⚠️ WAŻNE: DWA RODZAJE KONFIGURACJI

### 1. Lokalna konfiguracja (Devin for Terminal) — AKTUALNIE UŻYWANA
**Pliki:** `.devin/config.json` + `.devin/config.local.json`
**Gdzie:** W repozytorium RAO
**Restart:** Wymaga restartu sesji terminala po zmianach

### 2. Cloud konfiguracja (app.devin.ai) — NIEUŻYWANA
**Gdzie:** https://app.devin.ai/settings/mcp-marketplace
**Przeznaczenie:** Dla cloud Devina, nie dla terminala

---

## LOKALNA KONFIGURACJA (Devin for Terminal)

### Pliki konfiguracyjne

**1. `.devin/config.json` — główna konfiguracja MCP**
```json
{
  "mcpServers": {
    "rao-vision": {
      "command": "node",
      "args": ["mcp-vision/index.js"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-api03-..."
      }
    },
    "sequential-thinking": {
      "command": "node",
      "args": ["C:\\Users\\mateu\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-sequential-thinking\\dist\\index.js"],
      "env": {
        "DISABLE_THOUGHT_LOGGING": "true",
        "NODE_OPTIONS": "--max-old-space-size=512"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory@latest"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github@latest"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search@latest"],
      "env": {
        "BRAVE_API_KEY": "BSA..."
      },
      "disabled": false
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--headless"],
      "disabled": false
    }
  }
}
```

**2. `.devin/config.local.json` — sekrety (NIE commitować do git)**
```json
{
  "mcpServers": {
    "brave-search": {
      "env": {
        "BRAVE_API_KEY": "BSA_TWOJ_KLUCZ"
      },
      "disabled": false
    },
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_TWOJ_TOKEN"
      }
    }
  },
  "permissions": {
    "allow": [
      "Exec(git ls-files)",
      "Exec(git status)",
      "Exec(npx)",
      "Exec(ls)",
      "Exec(dir)",
      "Exec(find)",
      "Exec(env)"
    ]
  }
}
```

**⚠️ KLUCZOWE:**
- Klucze API są w `.devin/config.local.json` (ten plik jest w `.gitignore`)
- Główna konfiguracja w `.devin/config.json` zawiera strukturę serwerów
- Po zmianie konfiguracji **ZAWSZE** restart sesji terminala
- Devin for Terminal scala obie konfiguracje automatycznie

### Status serwerów (2026-07-04)

| Serwer | Status | Scope | Dlaczego |
|--------|--------|-------|----------|
| `rao-vision` | ✅ DZIAŁA | project | Lokalny server, klucz w config.json |
| `sequential-thinking` | ✅ DZIAŁA | project | Globalny npm package, pełna ścieżka |
| `memory` | ✅ DZIAŁA | project | Globalny npm package, pełna ścieżka |
| `github` | ✅ DZIAŁA | project.local | Globalny npm package, klucz w config.local.json |
| `brave-search` | ✅ DZIAŁA | project.local | Globalny npm package, klucz w config.local.json |
| `playwright` | ✅ DZIAŁA | project | Globalny npm package, pełna ścieżka |
| `codebase-memory` | ✅ DZIAŁA | user | `npx -y codebase-memory-mcp` — graf wiedzy kodu (9548 węzłów, 27500 krawędzi) |
| `depwire` | ✅ DZIAŁA | user | `npx -y depwire-cli mcp` — analiza zależności cross-file (315 plików, 14492 symboli) |
| `mariadb` | ✅ DZIAŁA | user | `mcp-server-mariadb` — bezpośrednie zapytania do bazy `rao_new` |

**Wszystkie 9 serwerów działa.** Problem z npx został rozwiązany przez instalację globalną pakietów npm + pełne ścieżki w config.json.

### Rozwiązania problemu z npx

**Opcja 1: Zainstalować pakiety globalnie (zalecane)**
```bash
# Zainstaluj problemyczne serwery globalnie
npm install -g @modelcontextprotocol/server-memory
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-brave-search
npm install -g @playwright/mcp
```

Następnie zaktualizuj `.devin/config.json` z pełnymi ścieżkami:
```json
"memory": {
  "command": "node",
  "args": ["C:\\Users\\mateu\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-memory\\dist\\index.js"]
},
"github": {
  "command": "node",
  "args": ["C:\\Users\\mateu\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-github\\dist\\index.js"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
  }
},
"brave-search": {
  "command": "node",
  "args": ["C:\\Users\\mateu\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-brave-search\\dist\\index.js"],
  "env": {
    "BRAVE_API_KEY": "BSA..."
  }
},
"playwright": {
  "command": "node",
  "args": ["C:\\Users\\mateu\\AppData\\Roaming\\npm\\node_modules\\@playwright\\mcp\\dist\\index.js", "--headless"]
}
```

**Opcja 2: Użyć lokalnych instalacji w repozytorium**
```bash
# Zainstaluj w .devin/node_modules
cd .devin
npm install @modelcontextprotocol/server-memory
npm install @modelcontextprotocol/server-github
npm install @modelcontextprotocol/server-brave-search
npm install @playwright/mcp
cd ..
```

Następnie użyj względnych ścieżek:
```json
"memory": {
  "command": "node",
  "args": [".devin/node_modules/@modelcontextprotocol/server-memory/dist/index.js"]
}
```

**Opcja 3: Zostawić jak jest (2 działające serwery wystarczą)**
- `rao-vision` + `sequential-thinking` = wystarczające dla większości zadań
- Reszta serwerów może być dodana później gdy problem zostanie rozwiązany

### Jak przetestować działanie MCP

W sesji Devina:
```bash
# Lista wszystkich serwerów
mcp_list_servers

# Lista tools dla konkretnego serwera
mcp_list_tools --server_name rao-vision
mcp_list_tools --server_name sequential-thinking
```

### Jak dodać/zmienić klucz API

1. Otwórz `.devin/config.local.json`
2. Dodaj/zmień klucz w odpowiednim sekcji `env`
3. Zapisz plik
4. **RESTART SESJI TERMINALA** (to jest krytyczne!)
5. Sprawdź status: `mcp_list_tools --server_name <nazwa>`

### Jak dodać nowy serwer MCP

1. Otwórz `.devin/config.json`
2. Dodaj nową sekcję w `mcpServers`:
```json
"<nazwa-serwera>": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-nazwa@latest"],
  "env": {
    "API_KEY": "wartość-klucza"
  },
  "disabled": false
}
```
3. Jeśli wymaga klucza API, dodaj go do `.devin/config.local.json`
4. **RESTART SESJI TERMINALA**
5. Test: `mcp_list_tools --server_name <nazwa-serwera>`

---

## CLOUD KONFIGURACJA (app.devin.ai) — NIEUŻYWANA

## Jak dodać MCP do Devina (cloud)

1. Wejdź na **[app.devin.ai/settings/mcp-marketplace](https://app.devin.ai/settings/mcp-marketplace)**
2. Dla **marketplace** MCP — kliknij ten z listy i autoryzuj
3. Dla **custom** MCP — kliknij **"Add Your Own"** i wklej JSON poniżej
4. Po dodaniu kliknij **"Test listing tools"** — Devin sprawdzi czy serwer odpowiada

---

## 1. `rao-vision` (CUSTOM, kluczowy) — Claude Vision dla UI

**Cel:** Analiza screenshotów UI przez Claude Vision API. Devin wywołuje gdy potrzebuje "obejrzeć" wynik swojej pracy wizualnie.

**Tools:**
- `analyze_screenshot(image_path, question?)` — analiza istniejącego pliku PNG/JPG
- `screenshot_and_analyze(url, question?)` — screenshot URL przez Playwright + analiza w jednym wywołaniu

**Konfiguracja (Add Your Own → STDIO):**

```json
{
  "transport": "STDIO",
  "command": "node",
  "args": ["mcp-vision/index.js"],
  "env_variables": {
    "ANTHROPIC_API_KEY": "sk-ant-twoj-klucz-tutaj"
  }
}
```

**Wymagania (już w `.devin/setup.sh`):**
- `npm install` w `mcp-vision/` (robi się automatycznie)
- `ANTHROPIC_API_KEY` ustawiony jako secret Devina (Settings → Secrets) lub w `env_variables` powyżej

**Uzyskaj klucz:** https://console.anthropic.com/settings/keys

**Koszty:** ~$0.01-0.03 za jeden screenshot (claude-opus-4-5).

---

## 2. `playwright` (MARKETPLACE) — testy E2E + przeglądarka

**Cel:** Przeglądarka headless dla Devina — nawigacja, klikanie, accessibility snapshot.

**Konfiguracja:** wybierz **Playwright** z marketplace (oficjalny `mcp/playwright` z Docker Hub).

**Tools (przykładowe):** `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_take_screenshot`, `browser_evaluate`.

> 💡 **Synergia z `rao-vision`:** Devin może użyć `playwright.browser_take_screenshot` → zapisuje plik → `rao-vision.analyze_screenshot` na ten plik. Lub szybciej: bezpośrednio `rao-vision.screenshot_and_analyze` (wszystko w jednym).

---

## 3. `github` (MARKETPLACE) — operacje na repo

**Cel:** Dostęp do issues, PRs, branchy, komentarzy.

**Konfiguracja:** wybierz **GitHub** z marketplace, zaloguj się przez OAuth.

**Tools:** `create_pull_request`, `list_issues`, `add_issue_comment`, `get_file_contents`, etc.

---

## 4. `brave-search` (MARKETPLACE, opcjonalne) — wyszukiwanie w sieci

**Cel:** Web search dla Devina (research bibliotek, API docs).

**Konfiguracja:** wybierz **Brave Search** z marketplace, podaj `BRAVE_API_KEY`.

**Klucz:** https://brave.com/search/api/ (free tier 2000 zapytań/mies)

---

## 5. `sequential-thinking` (CUSTOM, opcjonalne) — strukturyzowane myślenie

**Cel:** Tool do złożonego rozumowania krok po kroku (Devin używa wewnętrznie zwykle, MCP to bonus).

**Konfiguracja (Add Your Own → STDIO):**

```json
{
  "transport": "STDIO",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
  "env_variables": {}
}
```

---

## 6. `memory` (CUSTOM, opcjonalne) — knowledge graph między sesjami

**Cel:** Persystentna pamięć Devina między sesjami (knowledge graph).

**Konfiguracja (Add Your Own → STDIO):**

```json
{
  "transport": "STDIO",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"],
  "env_variables": {
    "MEMORY_FILE_PATH": "/home/ubuntu/.devin-memory/rao.json"
  }
}
```

---

## 7. `codebase-memory` (CUSTOM, kluczowy) — graf wiedzy kodu

**Cel:** Semantyczna analiza kodu przez graf wiedzy. Zindeksowane: **9548 węzłów, 27500 krawędzi** (tryb `full` z semantic edges). Wszyscy agenci (poza motion-designer) mają dostęp.

**Instalacja:**
```bash
npm install -g codebase-memory-mcp
codebase-memory-mcp install  # auto-detekcja agentów (Claude-Code, Gemini-CLI, VS Code)
```

**Konfiguracja (user scope — `~/.config/devin/config.json`):**
```json
{
  "mcpServers": {
    "codebase-memory": {
      "command": "npx",
      "args": ["-y", "codebase-memory-mcp"]
    }
  }
}
```

**Tools (kluczowe):**
- `index_repository` — zindeksuj repo (mode: `full`/`moderate`/`fast`/`cross-repo-intelligence`)
- `search_graph` — BM25 + semantic search po funkcjach/klasach/routach (ZAMIAST grep)
- `query_graph` — zapytania Cypher: complexity hotspots, N+1 candidates, circular deps
- `trace_path` — call chain (inbound/outbound/both), data_flow, cross_service
- `get_code_snippet` — czytaj kod funkcji po `qualified_name`

**Complexity metrics (wbudowane w każdy Function node):**
- `complexity` (cyclomatic), `cognitive`, `loop_count`, `loop_depth`
- `transitive_loop_depth` (worst-case nested-loop degree propagated along CALLS)
- `linear_scan_in_loop` (hidden O(n²) that loop_depth misses)
- `alloc_in_loop`, `recursion_in_loop`, `unguarded_recursion`

**Projekt zindeksowany jako:** `C-projects-repos-RaoApp_new`

**Reindeksacja (po dużych zmianach):**
```python
mcp_call_tool(
    server_name="codebase-memory",
    tool_name="index_repository",
    arguments={"mode": "fast", "repo_path": "C:/projects/repos/RaoApp_new"}
)
```

---

## 8. `depwire` (CUSTOM, kluczowy) — analiza zależności cross-file

**Cel:** Analiza zależności między plikami i symbolami. Zindeksowane: **315 plików, 14492 symboli, 11259 krawędzi**. Wszyscy agenci (poza motion-designer) mają dostęp.

**Konfiguracja (user scope):**
```json
{
  "mcpServers": {
    "depwire": {
      "command": "npx",
      "args": ["-y", "depwire-cli", "mcp"]
    }
  }
}
```

**Tools (kluczowe):**
- `connect_repo` — połącz z repo (auto-detekcja z cwd)
- `get_architecture_summary` — overview: file count, hotspots, orphan files, languages
- `impact_analysis` — blast radius zmiany symbolu (direct + transitive dependents + affected files)
- `simulate_change` — symuluj move/delete/rename/split/merge przed dotknięciem kodu
- `verify_change` — safety report przed apply (broken imports, circular deps, health delta)
- `get_health_score` — 0-100 score architektury (coupling, cohesion, circular deps, god files)
- `get_file_context` — pełny kontekst pliku: symbole, importy, eksporty, kto importuje
- `find_dead_code` — nieużywane symbole (high/medium/low confidence)
- `security_scan` — skanuj pod kątem vulnerabilities z graph-aware severity

**Projekt:** `C:/projects/repos/RaoApp_new` (auto-detected)

---

## 9. `mariadb` (CUSTOM, kluczowy) — bezpośrednie zapytania do bazy `rao_new`

**Cel:** Bezpośrednie zapytania SQL do bazy RAO przez MCP. Agenci mogą czytać schema, EXPLAIN, dane — oraz grzebać w danych (INSERT/UPDATE/DELETE). **Migracje schema (ALTER TABLE) zostają deterministyczne w `backend/main.py`** — uruchamiane poza agentami przy starcie backendu.

**Instalacja:**
```bash
pip install mcp-server-mariadb
```

**Konfiguracja (user scope — hasło w args, bezpieczne bo user scope nie commitowane):**
```json
{
  "mcpServers": {
    "mariadb": {
      "command": "mcp-server-mariadb",
      "args": ["--host", "localhost", "--port", "3306", "--user", "rao_user", "--password", "RaoPass2026!", "--database", "rao_new"]
    }
  }
}
```

**Tools:**
- `list_databases` — wszystkie bazy dostępne dla usera
- `list_tables` — wszystkie tabele w `rao_new`
- `get_table_schema` — schema tabeli (kolumny, typy, klucze)
- `get_table_schema_with_relations` — schema z FK relacjami
- `execute_sql` — zapytania SQL (SELECT, SHOW, DESCRIBE, EXPLAIN, INSERT, UPDATE, DELETE, ALTER)

**Zasady użycia:**
- ✅ **Czytać:** schema, EXPLAIN, SHOW INDEX, SELECT — każdy agent
- ✅ **Grzebać w danych:** INSERT, UPDATE, DELETE — agenci z write permissions (db-architect, backend-dev, qa-engineer)
- ⚠️ **ALTER TABLE:** tylko db-architect, i to z równoległą zmianą w `backend/main.py` (migracja deterministyczna)
- ❌ **DROP TABLE/COLUMN:** bez wyraźnej zgody usera (bezpieczeństwo danych)

---

## Priorytet dla RAO

| Priorytet | MCP | Po co |
|-----------|-----|-------|
| 🔴 KRYTYCZNY | `rao-vision` | Devin "widzi" wynik swojej pracy → autonomiczne UI verification |
| 🔴 KRYTYCZNY | `playwright` | E2E tests, navigation, manual UI testing |
| � KRYTYCZNY | `codebase-memory` | Graf wiedzy kodu — search, trace, complexity metrics (ZAMIAST grep) |
| 🔴 KRYTYCZNY | `depwire` | Impact analysis, dead code, health score, security scan |
| 🔴 KRYTYCZNY | `mariadb` | Bezpośrednie zapytania do bazy `rao_new` (schema, EXPLAIN, dane) |
| �🟡 ZALECANE | `github` | PR/issue management automatycznie |
| 🟢 OPCJONALNE | `brave-search` | Research |
| 🟢 OPCJONALNE | `sequential-thinking` | Złożone planowanie |
| 🟢 OPCJONALNE | `memory` | Wiedza między sesjami |

**Minimalna konfiguracja:** `rao-vision` + `playwright` + `codebase-memory` + `depwire` + `mariadb` = pełna autonomia (UI verification + code analysis + DB access).

---

## Test po konfiguracji

W sesji Devina spróbuj:

```
Zrób screenshot http://localhost:5173 i powiedz czy formularz logowania wygląda zgodnie z design systemem RAO.
```

Devin powinien:
1. Wywołać `rao-vision.screenshot_and_analyze({url: "http://localhost:5173", question: "..."})`
2. Otrzymać raport JSON: verdict + issues + design_system_compliance
3. Zwrócić Ci podsumowanie + zapisany plik raportu w `temp/vision/`

---

## Troubleshooting

**"Test listing tools" zwraca błąd dla rao-vision:**
- Sprawdź czy `bash .devin/setup.sh` zostało wykonane (instaluje deps mcp-vision)
- Sprawdź czy `ANTHROPIC_API_KEY` jest ustawiony w `env_variables` MCP konfiguracji LUB w Devin Secrets

**Devin nie wywołuje `rao-vision` automatycznie:**
- Update SKILL `software-house` ma sekcję "Vision Verification" — Tech Lead role wymusza wywołanie tooli vision po implementacji UI
- Lub poproś explicite: "Użyj rao-vision żeby sprawdzić X"

**Koszty Claude Vision rosną:**
- W trybie `--full-auto` ogranicz wywołania do 1-2 per zadanie (start + finish)
- Używaj `analyze_screenshot` (tańsze) zamiast `screenshot_and_analyze` jeśli już masz screenshot

---

## 🚀 SZYBKI CHEATSHEET — GDZIE JEST CO

### Pliki konfiguracyjne
| Plik | Zawartość | Commitowanie |
|------|-----------|--------------|
| `.devin/config.json` | Główna konfiguracja MCP, struktura serwerów | ✅ TAK |
| `.devin/config.local.json` | Sekrety API keys, permissions | ❌ NIE (w .gitignore) |
| `.devin/MCP_CONFIG.md` | Ta dokumentacja | ✅ TAK |

### Kluczowe lokacje
- **Konfiguracja MCP:** `.devin/config.json` + `.devin/config.local.json`
- **Dokumentacja:** `.devin/MCP_CONFIG.md` (ten plik)
- **Local vision server:** `mcp-vision/index.js` (wymaga `npm install`)

### Aktualny status (2026-07-04)
- ✅ **Działające (9 serwerów):** `rao-vision`, `sequential-thinking`, `memory`, `github`, `brave-search`, `playwright`, `codebase-memory`, `depwire`, `mariadb`
- ❌ **Niedziałające:** brak

### Typowe operacje
```bash
# Test MCP w sesji Devina
mcp_list_servers                    # lista serwerów
mcp_list_tools --server_name rao-vision  # tools konkretnego serwera

# Zmiana klucza API
1. Edytuj `.devin/config.local.json`
2. Restart sesji terminala
3. Test: mcp_list_tools --server_name <nazwa>

# Dodanie nowego serwera
1. Edytuj `.devin/config.json` (dodaj do mcpServers)
2. Jeśli wymaga klucza → edytuj `.devin/config.local.json`
3. Restart sesji terminala
4. Test: mcp_list_tools --server_name <nazwa>
```

### Naprawa problemu z npx
```bash
# Opcja 1: Instalacja globalna (zalecana)
npm install -g @modelcontextprotocol/server-memory
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-brave-search
npm install -g @playwright/mcp
# Następnie zaktualizuj .devin/config.json z pełnymi ścieżkami do node_modules

# Opcja 2: Instalacja lokalna
cd .devin
npm install @modelcontextprotocol/server-memory
npm install @modelcontextprotocol/server-github
npm install @modelcontextprotocol/server-brave-search
npm install @playwright/mcp
cd ..
# Następnie użyj względnych ścieżek w .devin/config.json
```

### Kontakt / Support
- Problem z MCP? Sprawdź najpierw ten plik
- Nadal nie działa? Sprawdź logi Devina przy starcie MCP serwerów
- Windows MINGW64 specyficzne? Użyj pełnych ścieżek Windows z `\\`
