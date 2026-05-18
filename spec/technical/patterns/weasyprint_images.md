# WeasyPrint Images Pattern

## Opis
Wzorzec do obsługi obrazów w WeasyPrint (generowanie PDF z HTML). Kluczowa wiedza: **HTTP/static files mount NIE działa na Windows**.

## Problem
WeasyPrint na Windows nie obsługuje:
- ❌ HTTP URLs (`http://localhost:8000/static/assets/image.jpg`)
- ❌ Static files mount w FastAPI (`/static/`)

## Rozwiązanie: file:// URI

Użyj **absolute file:// URI** z pełną ścieżką do pliku.

### Implementacja w HTML template
```html
<!-- ❌ NIE DZIAŁA na Windows -->
<img src="/static/assets/company_stamp.jpg" width="220" height="85">

<!-- ❌ NIE DZIAŁA na Windows -->
<img src="http://localhost:8000/rao/api/static/assets/company_stamp.jpg" width="220" height="85">

<!-- ✅ DZIAŁA na Windows -->
<img src="file:///C:/projects/repos/RaoApp/backend/reports/assets/company_stamp.jpg" width="220" height="85">
```

### Dynamiczne ścieżki (Python)
```python
from pathlib import Path

def get_file_uri(image_path):
    """Konwersja ścieżki do file:// URI"""
    abs_path = Path(image_path).resolve()
    return f"file:///{abs_path.as_posix()}"

# Użycie w template context
stamp_uri = get_file_uri("backend/reports/assets/company_stamp.jpg")
# Wynik: file:///C:/projects/repos/RaoApp/backend/reports/assets/company_stamp.jpg
```

## Użycie w RAO (RAO-P1-022)

### Pieczątki firmowe w HTML templates
```html
<!-- contract.html -->
<img src="file:///C:/projects/repos/RaoApp/backend/reports/assets/company_stamp.jpg"
     width="220" height="85"
     style="margin-top: 10px;">
```

### Wymiary pieczątek
- **OWN (contract.html):** 220x85px
- **Protokoły:** 180x70px

## Weryfikacja

### Sprawdzenie czy obraz jest w PDF
```python
import fitz

def check_pdf_images(pdf_path):
    """Sprawdzenie czy obrazy są w wygenerowanym PDF"""
    doc = fitz.open(pdf_path)
    total_images = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        total_images += len(image_list)

        print(f"Page {page_num + 1}: {len(image_list)} images")

    doc.close()
    return total_images
```

### Wynik RAO-P1-022
```
Page 1: 1 images (stamp)
Page 2: 1 images (stamp)
...
Page 8: 1 images (stamp)

Total: 8 images (12157 bytes vs 12275 original)
```

## Zalety file:// URI
- ✅ Działa na Windows z WeasyPrint
- ✅ Nie wymaga serwera HTTP
- ✅ Prosta implementacja
- ✅ Nie zależy od portu backendu

## Wady
- ❌ Absolute path (nie portable między maszynami)
- ❌ Trzeba aktualizować ścieżki przy zmianie lokalizacji projektu
- ❌ NIE działa w środowisku produkcyjnym (inna ścieżka)

## Rozwiązanie produkcyjne
W środowisku produkcyjnym użyj:
- Base64 encoded images w HTML
- Lub relative paths z poprawnie skonfigurowanym WeasyPrint

## Powiązane
- Pattern: `spec/technical/patterns/pdf_extraction.md`
- Pattern: `spec/technical/patterns/vision_ai_analysis.md`
- Templates: `backend/reports/templates/*.html`
- Asset: `backend/reports/assets/company_stamp.jpg`

## Implementacja RAO-P1-022
- 5 templates zaktualizowanych (contract.html, contract_u.html, protocol_zo.html, protocol_zo_u.html, protocol_zo_nodata_u.html)
- Pieczątka na wszystkich stronach podpisów
- Wymiary dostosowane do typu dokumentu