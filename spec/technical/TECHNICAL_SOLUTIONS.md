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

### Fakturownia Integration (RAO-P2-012)
- **Pattern:** `spec/technical/patterns/fakturownia_integration.md` — Pełny scrum refinement (PO, Tech Lead, QA, Security)
- **Status:** ODŁOŻONE po refinement — PO rekomenduje po P0/P1
- **Security impact:** HIGH (12 krytycznych zagrożeń zidentyfikowanych)
- **Architecture:** Full module `integrations/fakturownia/` (models, schemas, service, client, router)
- **Schema:** fakturownia_settings (singleton), fakturownia_product_mapping (FK → articles)
- **Edge cases:** 32 zidentyfikowanych (API, OID, mapping, wiele faktur, UI, security)
- **Testing strategy:** Unit (15+ testów), Integration (8 testów), E2E (10 scenariuszy), Manual (8-item checklist)

## Skrypty (Scripts)

### PDF & Vision AI (RAO-P1-022)
- **Script:** `spec/technical/scripts/test_pdf_extraction.py` — Test bibliotek PDF extraction (pdfplumber, fitz)
- **Script:** `spec/technical/scripts/convert_pdf_to_screenshots.py` — Konwersja PDF do PNG dla Vision AI
- **Doc:** `spec/technical/scripts/test_pdf_extraction.md` — Opis bibliotek i wyników testów
- **Doc:** `spec/technical/scripts/convert_pdf_to_screenshots.md` — Opis konwersji PDF do PNG

### Auth & Testing
- **Script:** `spec/technical/scripts/reset_admin_password.py` — Reset hasła admina do admin123
- **Doc:** `spec/technical/scripts/reset_admin_password.md` — Opis użycia

### TERYT Postal Codes (RAO-P2-015)
- **Script:** `spec/technical/scripts/teryt_postal_codes_generator.py` — Generator słownika kodów pocztowych (200+ z głównych miast)
- **Doc:** `spec/technical/scripts/teryt_postal_codes_generator.md` — Opis użycia, integracja z RAO, rozszerzenie do pełnej bazy

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
- **2026-05-18:** RAO-P2-012 — Pełny scrum refinement Fakturownia integration (PO, Tech Lead, QA, Security) — ODŁOŻONE
- **2026-05-19:** RAO-P2-015 — TERYT postal codes integration (200+ kodów z głównych miast, endpointy lookup + sync)