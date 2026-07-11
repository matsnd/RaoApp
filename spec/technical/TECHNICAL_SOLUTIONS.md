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
- **Status:** WDROŻONE (RAO-P2-058 Faza 1 MVP + RAO-P2-061 demo setup)
- **Security impact:** HIGH (12 krytycznych zagrożeń zidentyfikowanych)
- **Architecture:** Full module `integrations/fakturownia/` (models, schemas, service, client, router)
- **Schema:** fakturownia_settings (singleton), fakturownia_product_mapping (FK → articles)
- **Edge cases:** 32 zidentyfikowanych (API, OID, mapping, wiele faktur, UI, security)
- **Testing strategy:** Unit (15+ testów), Integration (8 testów), E2E (10 scenariuszy), Manual (8-item checklist)

### Fakturownia Demo Setup (RAO-P2-061)
- **Doc:** `spec/technical/fakturownia_demo_setup.md` — Pełna dokumentacja konta matsnd.fakturownia.pl
- **Script:** `backend/seed_demo_data.py` — Idempotentny skrypt seedujący dane demo w RAO DB
- **Script:** `backend/seed_fa_invoices.py` — Idempotentny skrypt wystawiający faktury w FA
- **API quirks:** `gtu_codes` (array nie string), `price_gross` required, `tax_no` (nie `nip`), `tax_no_kind: "other"` omija walidację NIP
- **Demo data:** 11 artykułów, 8 kontrahentów, 24 umowy, 74 rozliczenia (72% fakturownia), 12 faktur FA

### Archive Legacy Data (RAO-P2-071)
- **Script:** `backend/archive_legacy_data.py` — Idempotentny skrypt archiwizacji (cut-off): przenosi WSZYSTKIE dane z tabel live do archive_* (parents-first: categories → articles → contracts → positions → conditions → fees → settlements)
- **Strategy:** Python ORM (SQLAlchemy async), batch 500 rekordów, `_map_row` mapuje TYLKO wspólne kolumny (ignoruje drift typów między live a archive)
- **Idempotentność:** Check existing po PK (id) — nie duplikuje przy re-run
- **NIE czyści tabel live** — to osobny krok (Phase 3)
- **Fix `seed_demo_data.py`:** Usunięto `unit=fee_data["unit"]` z konstrukcji `ContractServiceFee` (nieistniejąca kolumna w modelu/DB)
- **Rezerwacje demo:** `seed_rezerwacje()` — 8 rezerwacji maszyn (aktywne + przeszłe + konflikt dat) dla pokazania kalendarza

### Contract Pricing Grids — KISS split by contract type
- **Pattern:** `spec/technical/patterns/contract_pricing_grids.md` — Projekt UX rozdzielenia cenników maszyn/usług/usług dodatkowych w `ContractFormView`
- **Scope:** Rozdzielenie UX dla `contract_type='S'` (najem, doby) i `contract_type='U'` (usługa, godziny), uproszczenie usług dodatkowych (bez artykułów)
- **Source:** Analiza 515 legacy PDF z `c:\Temp\legacy_pdfs\`
- **Status:** Projekt UX / specyfikacja do implementacji

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

### Playwright UX Screenshots (RAO-P2-016)
- **Script:** `e2e/tests/10-ux-screenshots.spec.ts` — Automatyczne screenshoty wszystkich widoków dla UX review
- **Doc:** `spec/technical/scripts/playwright_ux_screenshots.md` — Opis użycia, lista 17 screenshotów, integracja z UX review

### Legacy PDF Extraction (RAO-P2-059)
- **Script:** `spec/technical/scripts/extract_legacy_pdfs.py` — Ekstrakcja tekstu z legacy PDFów (PZO + umowy) używając PyMuPDF (fitz)
- **Doc:** `spec/technical/scripts/extract_legacy_pdfs.md` — Opis analizy 4 PDFów, wzorce usług dodatkowych
- **Samples:** `spec/technical/legacy_samples/pzo_umowy/` — source PDFs, `pzo_umowy_extracted/` — wyekstraktowany tekst
- **Wzorzec:** PyMuPDF `page.get_text("text")` ekstraktuje tekst z PDF binarnego (read tool nie działa na PDF)

### Vision AI UX Analysis (RAO-P2-016 + RAO-P2-017)
- **Tool:** MCP `rao-vision` — Automatyczna analiza UX/UI przez Claude Vision
- **Doc:** `spec/technical/scripts/vision_ux_analysis.md` — Opis użycia, wzorce pytań, optymalizacja kosztów
- **Result:** 4 analizy vision (LoginView, DashboardView, ContractFormView), 20+ zidentyfikowanych problemów UX/UI

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
- **2026-05-19:** RAO-P2-016 — Playwright UX screenshots spike (17 screenshotów dla design review, checklist UX)
- **2026-05-19:** RAO-P2-016 + RAO-P2-017 — Vision AI UX analysis (4 analizy, 20+ problemów UX/UI zidentyfikowanych, backlog item utworzony)
- **2026-07-01:** RAO-P2-061 — Demo data seeding (11 artykułów, 8 kontrahentów, 24 umowy, 74 rozliczenia, 12 faktur FA, konto matsnd.fakturownia.pl skonfigurowane)
- **2026-07-11:** RAO-P2-071 — Archive legacy data script + seed_demo_data fix (unit removal + rezerwacje demo)