# convert_pdf_to_screenshots.py

## Opis
Skrypt do konwersji stron PDF na PNG screenshoty dla analizy Vision AI. Używany w RAO-P1-022 do analizy layout referencyjnych PDF z pieczątkami firmowymi.

## Użycie

```bash
cd spec/technical/scripts
python convert_pdf_to_screenshots.py
```

## Wymagania
- Biblioteka: `fitz` (PyMuPDF)
- Referencyjne PDF w `spec/archive/reference_reports/`
- Output directory: `spec/archive/reference_screenshots/`

## Działanie
1. Czyta wszystkie PDF z `spec/archive/reference_reports/`
2. Konwertuje każdą stronę na PNG (2x zoom dla lepszej jakości)
3. Zapisuje PNG w `spec/archive/reference_screenshots/`
4. Nazewnictwo: `{pdf_name}_p{page_num}.png`

## Wynik (RAO-P1-022)
```
🖼️ Converting PDF pages to PNG for Vision AI analysis
============================================================
📁 Found 6 PDF files in: spec/archive/reference_reports
📁 Output directory: spec/archive/reference_screenshots
============================================================

📄 Converting: ownA.pdf
✅ Page 1 → spec/archive/reference_screenshots/ownA_p1.png
✅ Page 2 → spec/archive/reference_screenshots/ownA_p2.png

📄 Converting: ownU.pdf
✅ Page 1 → spec/archive/reference_screenshots/ownU_p1.png
✅ Page 2 → spec/archive/reference_screenshots/ownU_p2.png

...
============================================================
📊 Total PNG files created: 12
📁 Saved in: spec/archive/reference_screenshots
```

## Użycie w RAO
- RAO-P1-022 — konwersja referencyjnych PDF do PNG dla Vision AI
- Vision AI — analiza layout pozycji pieczątek firmowych
- Testing — weryfikacja wyglądu PDF w różnych formatach

## Powiązane
- Pattern: `spec/technical/patterns/vision_ai_analysis.md`
- Script: `test_pdf_extraction.py`
- Vision AI: rao-vision MCP (analyze_screenshot, screenshot_and_analyze)
- Reference PDFs: `spec/archive/reference_reports/`
- Output PNGs: `spec/archive/reference_screenshots/`

## Implementacja (RAO-P1-022)
Vision AI (rao-vision MCP) przeanalizował PNG i zwrócił:
- **ownA_p2.png:** Pieczątka na pozycji X~45-50px, Y~1650-1700px, wymiary ~220-240px × 80-90px
- **Treść pieczątki:** "Toolsmart Sp. z o.o., ul. Kłobucka 6B/103, 02-699 Warszawa, NIP 9512598092, Regon 528847142, KRS 0001109942"
- **Pozycja:** NAD linią podpisu "Czytelny podpis Wynajmującego"