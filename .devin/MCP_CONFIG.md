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

### Status serwerów (2026-05-17)

| Serwer | Status | Dlaczego |
|--------|--------|----------|
| `rao-vision` | ✅ DZIAŁA | Lokalny server, klucz w config.json |
| `sequential-thinking` | ✅ DZIAŁA | Globalny npm package, pełna ścieżka |
| `memory` | ❌ NIE DZIAŁA | Problem z npx przez MCP framework |
| `github` | ❌ NIE DZIAŁA | Problem z npx przez MCP framework (mimo klucza) |
| `brave-search` | ❌ NIE DZIAŁA | Problem z npx przez MCP framework (mimo klucza) |
| `playwright` | ❌ NIE DZIAŁA | Problem z npx przez MCP framework |

**Diagnoza:** Serwery uruchamiane przez `npx` nie startują przez MCP framework, mimo że działają ręcznie. Może być problem z:
- Przekazywaniem env variables przez MCP
- Ścieżkami do npm/node w Windows MINGW64
- Uprawnieniami do uruchamiania procesów

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

## Priorytet dla RAO

| Priorytet | MCP | Po co |
|-----------|-----|-------|
| 🔴 KRYTYCZNY | `rao-vision` | Devin "widzi" wynik swojej pracy → autonomiczne UI verification |
| 🔴 KRYTYCZNY | `playwright` | E2E tests, navigation, manual UI testing |
| 🟡 ZALECANE | `github` | PR/issue management automatycznie |
| 🟢 OPCJONALNE | `brave-search` | Research |
| 🟢 OPCJONALNE | `sequential-thinking` | Złożone planowanie |
| 🟢 OPCJONALNE | `memory` | Wiedza między sesjami |

**Minimalna konfiguracja:** `rao-vision` + `playwright` = pełna autonomia UI verification.

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

### Aktualny status (2026-05-17)
- ✅ **Działające:** `rao-vision`, `sequential-thinking`
- ❌ **Niedziałające:** `memory`, `github`, `brave-search`, `playwright` (problem z npx)

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
