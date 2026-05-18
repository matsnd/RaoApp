# PDF Extraction Pattern

## Opis
Wzorzec do ekstrakcji obrazów i danych z plików PDF używając fitz (PyMuPDF).

## Biblioteki

| Biblioteka | Status na Windows | Wersja | Użycie w RAO |
|-----------|------------------|--------|--------------|
| fitz (PyMuPDF) | ✅ Dostępny | 1.27.2 | RAO-P1-022 (pieczątki) |
| pdfplumber | ✅ Dostępny | 0.11.9 | Opcjonalny |
| wand | ❌ Niedostępny | - | Nie działa na Windows |

## Implementacja z fitz

### Ekstrakcja obrazów
```python
import fitz

def extract_images_from_pdf(pdf_path):
    """Ekstrakcja obrazów z PDF"""
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            images.append({
                "page": page_num + 1,
                "index": img_index,
                "ext": image_ext,
                "size": len(image_bytes),
                "xref": xref,
                "bytes": image_bytes
            })

    doc.close()
    return images
```

### Konwersja stron do PNG
```python
import fitz

def convert_pdf_to_pngs(pdf_path, output_dir, zoom=2):
    """Konwersja stron PDF do PNG"""
    doc = fitz.open(pdf_path)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    png_files = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))

        png_path = os.path.join(output_dir, f"{pdf_name}_p{page_num + 1}.png")
        pix.save(png_path)
        png_files.append(png_path)

    doc.close()
    return png_files
```

## Użycie w RAO

### RAO-P1-022 (Pieczątki firmowe)
- **Cel:** Ekstrakcja pieczątki firmowej z referencyjnych PDF
- **Implementacja:** `spec/technical/scripts/test_pdf_extraction.py`
- **Wynik:** 10 obrazów z 6 PDF, pieczątka JPEG 12275 bytes
- **Zapis:** `backend/reports/assets/company_stamp.jpg`

### RAO-P1-022 (Vision AI Analysis)
- **Cel:** Konwersja PDF do PNG dla analizy Vision AI
- **Implementacja:** `spec/technical/scripts/convert_pdf_to_screenshots.py`
- **Wynik:** 12 PNG z 6 PDF (2x zoom)
- **Output:** `spec/archive/reference_screenshots/`

## Zalety fitz (PyMuPDF)
- ✅ Działa na Windows
- ✅ Szybki i wydajny
- ✅ Obsługuje wiele formatów obrazów (JPEG, PNG, etc.)
- ✅ Łatwy w użyciu
- ✅ Aktywnie rozwijany

## Alternatywy
- **pdfplumber:** Dostępny, ale mniej wszechstronny niż fitz
- **wand:** Niedostępny na Windows (wymaga ImageMagick)
- **pdf2image:** Wymaga poppler (dodatkowa zależność)

## Powiązane
- Pattern: `spec/technical/patterns/vision_ai_analysis.md`
- Pattern: `spec/technical/patterns/weasyprint_images.md`
- Script: `spec/technical/scripts/test_pdf_extraction.py`
- Script: `spec/technical/scripts/convert_pdf_to_screenshots.py`