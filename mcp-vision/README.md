# RAO MCP Vision Server

Lokalny MCP server który daje agentom narzędzia do analizy screenshotów UI.

**Strategia kosztów:** Najpierw darmowy Nemotron Nano 12B v2 VL (OpenRouter), fallback Claude Vision gdy free model nie poradzi. Większość analiz = $0.

## Setup (jednorazowy)

```powershell
# 1. Zainstaluj zależności
cd mcp-vision
npm install

# 2. Klucze API — w .devin/config.json (env rao-vision):
#    OPENROUTER_API_KEY — darmowy, uzyskaj na https://openrouter.ai/keys
#    ANTHROPIC_API_KEY — fallback (płatny), uzyskaj na https://console.anthropic.com/settings/keys
```

## Konfiguracja MCP

W `.devin/config.json` (sekcja `mcpServers.rao-vision.env`):
```json
{
  "OPENROUTER_API_KEY": "sk-or-v1-...",
  "ANTHROPIC_API_KEY": "sk-ant-..."
}
```

## Narzędzia MCP

### `analyze_screenshot`
Analizuje istniejący plik PNG/JPG.

```
→ analyze_screenshot({image_path: "...", question: "..."})
→ Zwraca ocenę UI + zapisuje raport obok pliku
```

### `screenshot_and_analyze`
Robi screenshot podanego URL i od razu analizuje. Wymaga działającego frontendu.

```
→ screenshot_and_analyze({url: "http://localhost:5173/contracts", question: "..."})
→ Zapisuje screenshot do temp/ + raport
```

## Fallback chain

```
1. Nemotron Nano 12B v2 VL (free, OpenRouter) — first choice, $0
   └─ jeśli brak klucza / HTTP error / pusta odpowiedź
2. Claude Vision (Anthropic, płatny) — fallback, ~$0.01-0.03/screenshot
   └─ jeśli oba niedostępne
3. Error report
```

Raport zawiera pole `Model:` wskazujący który provider odpowiedział.

## Koszty

- **Nemotron (free):** $0 — większość analiz UI
- **Claude fallback:** ~$0.01-0.03 za screenshot (tylko gdy Nemotron nie poradzi)
- Wywoływany TYLKO gdy agent explicite użyje toola — zero pollingu, zero idle costs
