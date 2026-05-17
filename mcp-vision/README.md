# RAO MCP Vision Server

Lokalny MCP server który daje Cascade (Windsurf) narzędzia do analizy screenshotów UI przez Claude Vision API.

## Setup (jednorazowy)

```powershell
# 1. Zainstaluj zależności
cd mcp-vision
npm install

# 2. Dodaj klucz do .env (w root projektu)
# ANTHROPIC_API_KEY=sk-ant-...
# Uzyskaj na: https://console.anthropic.com/settings/keys
```

## Konfiguracja Windsurf

Plik `.windsurf/mcp.json` jest już skonfigurowany. Windsurf załaduje serwer automatycznie.

**Uwaga:** Windsurf czyta `ANTHROPIC_API_KEY` ze zmiennych środowiskowych systemowych LUB z `${VAR}` w mcp.json.
Ustaw zmienną systemową:

```powershell
# PowerShell (trwałe)
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-twoj-klucz", "User")
# Restart Windsurf po ustawieniu
```

## Narzędzia MCP

### `analyze_screenshot`
Analizuje istniejący plik PNG/JPG.

```
Użycie w Cascade:
"Przeanalizuj screenshot w temp/screen.png"
→ Cascade wywołuje analyze_screenshot({image_path: "...", question: "..."})
→ Zwraca ocenę UI + zapisuje raport obok pliku
```

### `screenshot_and_analyze`
Robi screenshot podanego URL i od razu analizuje. Wymaga działającego frontendu.

```
Użycie w Cascade:
"Zrób screenshot http://localhost:5173/contracts i oceń UI"
→ Cascade wywołuje screenshot_and_analyze({url: "...", question: "..."})
→ Zapisuje screenshot do temp/ + raport
```

## Jak Devin może to używać

Devin nie ma dostępu do MCP Cascade — ale może:
1. Zapisać screenshot do `temp/vision-request.png`
2. Zapisać pytanie do `temp/vision-request.md`
3. Cascade (Windsurf) wywołuje `analyze_screenshot` na żądanie

Protokół pliku requestu (`temp/vision-request.md`):
```markdown
# Vision Request
screenshot: temp/vision-request.png
question: Czy formularz umowy wygląda poprawnie po dodaniu pola delivery_address?
```

## Koszty

- Claude claude-opus-4-5 vision: ~$0.01-0.03 za jeden screenshot (zależnie od rozmiaru)
- Wywoływany TYLKO gdy Cascade explicite użyje toola — zero pollingu, zero idle costs
