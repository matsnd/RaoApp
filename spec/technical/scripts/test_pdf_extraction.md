# test_pdf_extraction.py

## Opis
Skrypt testowy do weryfikacji bibliotek ekstrakcji obrazów z PDF na Windows. Używany w RAO-P1-022 do znalezienia biblioteki do wyciągania pieczątek firmowych z referencyjnych PDF.

## Użycie

```bash
cd spec/technical/scripts
python test_pdf_extraction.py
```

## Wymagania
- Biblioteki: `fitz` (PyMuPDF), opcjonalnie `pdfplumber`, `wand`
- Referencyjne PDF w `spec/archive/reference_reports/`

## Działanie
1. Testuje dostępność bibliotek: pdfplumber, fitz, wand
2. Jeśli fitz dostępny → ekstrahuje obrazy z referencyjnych PDF
3. Wyświetla listę znalezionych obrazów (strona, indeks, format, rozmiar)

## Wynik (RAO-P1-022)
```
🧪 Testing PDF extraction libraries on Windows
============================================================
✅ pdfplumber is available
   Version: 0.11.9
✅ fitz (PyMuPDF) is available
   Version: 1.27.2
❌ wand is NOT available
============================================================

📁 Extracting images from reference PDFs in: spec/archive/reference_reports
============================================================
📄 ownA.pdf: 2 images extracted
   Page 2, Image 0: jpg (12275 bytes)
   Page 2, Image 1: jpg (512 bytes)
📄 ownU.pdf: 2 images extracted
   Page 2, Image 0: jpg (12275 bytes)
   Page 2, Image 1: jpg (512 bytes)
...
============================================================
📊 Total images extracted: 10 from 6 PDFs
```

## Wnioski (RAO-P1-022)
- **pdfplumber:** ✅ dostępny (0.11.9)
- **fitz (PyMuPDF):** ✅ dostępny (1.27.2) — UŻYTY w implementacji
- **wand:** ❌ niedostępny

## Użycie w RAO
- RAO-P1-022 — znalezienie biblioteki do ekstrakcji pieczątek z PDF
- Testing — weryfikacja kompatybilności bibliotek na Windows
- Development — analiza zawartości referencyjnych PDF

## Powiązane
- Pattern: `spec/technical/patterns/pdf_extraction.md`
- Script: `convert_pdf_to_screenshots.py`
- Vision AI: rao-vision MCP
- Reference PDFs: `spec/archive/reference_reports/`

## Implementacja
RAO-P1-022 użył fitz (PyMuPDF) do ekstrakcji pieczątki firmowej:
- Pieczątka: JPEG 12275 bytes (company_stamp.jpg)
- Zapisano w: `backend/reports/assets/company_stamp.jpg`