# Technical Solutions — RAO

> Indeks odkrytych technicznych rozwiązań podczas pracy nad RAO.
> Służy do szybkiego odzyskania wiedzy po restarcie AI agenta.

## Struktura

```
spec/technical/
├── TECHNICAL_SOLUTIONS.md    # Ten plik - główny indeks
├── scripts/                  # Pythonowe skrypty testowe/utility + *.md opisy
└── patterns/                 # Wzorce architektoniczne (PDF extraction, JWT, etc.)
```

## Wzorce (Patterns)

### PDF Extraction & Vision AI (RAO-P1-022)
- **Pattern:** `spec/technical/patterns/pdf_extraction.md` — Ekstrakcja obrazów z PDF używając fitz (PyMuPDF)
- **Pattern:** `spec/technical/patterns/vision_ai_analysis.md` — Analiza layout referencyjnych PDF z Vision AI (rao-vision MCP)
- **Pattern:** `spec/technical/patterns/weasyprint_images.md` — Obsługa obrazów w WeasyPrint (file:// URI)

### JWT Auth & E2E Testing
- **Pattern:** `spec/technical/patterns/jwt_auth_e2e.md` — Reset hasła admina, JWT token, smoke test

### Port Management (Windows)
- **Pattern:** `spec/technical/patterns/port_management.md` — Obsługa zajętych portów (8001, 5174)

### Migracje DB (MariaDB)
- **Pattern:** `spec/technical/patterns/migrations_mariadb.md` — Idempotentne ALTER TABLE, bez Alembic

## Skrypty (Scripts)

### PDF & Vision AI (RAO-P1-022)
- **Script:** `spec/technical/scripts/test_pdf_extraction.py` — Test bibliotek PDF extraction (pdfplumber, fitz)
- **Script:** `spec/technical/scripts/convert_pdf_to_screenshots.py` — Konwersja PDF do PNG dla Vision AI
- **Doc:** `spec/technical/scripts/test_pdf_extraction.md` — Opis bibliotek i wyników testów
- **Doc:** `spec/technical/scripts/convert_pdf_to_screenshots.md` — Opis konwersji PDF do PNG

### Auth & Testing
- **Script:** `spec/technical/scripts/reset_admin_password.py` — Reset hasła admina do admin123
- **Doc:** `spec/technical/scripts/reset_admin_password.md` — Opis użycia

## Szybki dostęp

- **AGENTS.md:** Sekcja "Technical Solutions Storage" z linkiem do tego pliku
- **Software-house skill:** Procedura "Post-task cleanup" (commit + zapisz rozwiązanie)

## Dodawanie nowych rozwiązań

Po każdym zadaniu:
1. **Skrypt:** Dodaj do `spec/technical/scripts/` z opisem `*.md`
2. **Wzorzec:** Jeśli to powtarzalny pattern → dodaj do `spec/technical/patterns/`
3. **Indeks:** Zaktualizuj ten plik (TECHNICAL_SOLUTIONS.md)
4. **AGENTS.md:** Dodaj krótki wpis do sekcji "Technical Solutions Discovered"

## Historia

- **2026-05-18:** Utworzenie struktury spec/technical/, migracja rozwiązań z AGENTS.md
- **2026-05-18:** RAO-P1-022 — PDF extraction, Vision AI, WeasyPrint images