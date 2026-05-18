# Vision AI Analysis Pattern

## Opis
Wzorzec do analizy layout dokumentów (PDF, screenshots) używając Vision AI (rao-vision MCP).

## MCP Server: rao-vision

### Dostępne narzędzia
- `analyze_screenshot` — Analiza istniejącego screenshotu
- `screenshot_and_analyze` — Zrobienie screenshotu i analiza

### Użycie MCP
```python
import asyncio
from mcp_call_tool import mcp_call_tool

async def analyze_screenshot_with_vision_ai(image_path):
    """Analiza screenshotu używając rao-vision MCP"""
    result = await mcp_call_tool(
        server_name="rao-vision",
        tool_name="analyze_screenshot",
        arguments={"image_path": image_path}
    )
    return result
```

## Przepływ pracy (RAO-P1-022)

### 1. Konwersja PDF do PNG
```bash
cd spec/technical/scripts
python convert_pdf_to_screenshots.py
```

Wynik: PNG pliki w `spec/archive/reference_screenshots/`

### 2. Analiza Vision AI
```python
# Analiza ownA_p2.png
result = await mcp_call_tool(
    server_name="rao-vision",
    tool_name="analyze_screenshot",
    arguments={"image_path": "spec/archive/reference_screenshots/ownA_p2.png"}
)
```

### 3. Wynik analizy
```json
{
  "stamp_position": {
    "x": "~45-50px",
    "y": "~1650-1700px",
    "width": "~220-240px",
    "height": "~80-90px"
  },
  "stamp_content": "Toolsmart Sp. z o.o., ul. Kłobucka 6B/103, 02-699 Warszawa, NIP 9512598092, Regon 528847142, KRS 0001109942",
  "position_relative": "ABOVE signature line 'Czytelny podpis Wynajmującego'",
  "font": "Times New Roman",
  "style": "Serif"
}
```

## Użycie w RAO

### RAO-P1-022 (Pieczątki firmowe)
- **Cel:** Analiza pozycji pieczątek w referencyjnych PDF
- **Implementacja:** Vision AI + MCP rao-vision
- **Wynik:** Dokładne wymiary i pozycja pieczątki
- **Zastosowanie:** Integracja pieczątek w HTML templates

### Inne zastosowania
- Analiza layout formularzy
- Weryfikacja wyglądu generowanych dokumentów
- Ekstrakcja danych z skanów
- OCR i rozpoznawanie tekstu

## Zalety Vision AI
- ✅ Automatyczna analiza layout
- ✅ Dokładne pomiary pozycji i wymiarów
- ✅ Rozpoznawanie fontów i stylów
- ✅ Szybka implementacja bez ręcznego pomiaru

## Wymagania
- MCP server: rao-vision
- PNG screenshots dokumentów
- Dostęp do narzędzi MCP przez `mcp_call_tool`

## Powiązane
- Pattern: `spec/technical/patterns/pdf_extraction.md`
- Pattern: `spec/technical/patterns/weasyprint_images.md`
- Script: `spec/technical/scripts/convert_pdf_to_screenshots.py`
- MCP: rao-vision (analyze_screenshot, screenshot_and_analyze)
- Reference: `spec/archive/reference_screenshots/`