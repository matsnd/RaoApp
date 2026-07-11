# PLAN: Rozdzielenie articles → machines / services / additional_services

> **Status:** APPROVED — Phase 0 complete, implementacja START
> **Data:** 2026-01-23
> **Scope:** Full refactor — backend + frontend + E2E + migracja od nowa
> **Archiwum:** BEZ ZMIAN — archive_articles zostaje jak jest
> **Fakturownia:** ZEROWANA — nie jest ograniczeniem, seed od nowa

## Phase 0 — wnioski z analiz (4 subagenty)

### Skala danych (z mariadb.query_database)
- `articles`: **25** rekordów (18 maszyn + 7 usług dodatkowych + **0 usług zwykłych**)
- `contract_positions`: **86** (wszystkie → maszyny)
- `service_fee_templates`: **22** (wszystkie → 7 usług dodatkowych)
- `article_rate_presets`: **5** (wszystkie → maszyny)
- `archive_articles`: **0** (puste — brak ryzyka)
- `reservations`: **NIE ISTNIEJE** (tabela nie utworzona)
- **Wniosek:** skala dev/demo, ~138 rekordów do remapowania, zerowe ryzyko produkcyjne

### Findings do wdrożenia (z Phase 0)

**CRITICAL (z Tech Lead):**
1. `technical_attributes` JSON column — BRAK w planie machines schema. Dodać do `machines.technical_attributes`.
2. `power_type` — `String(10)` nie `String(20)` (zgodność z obecnym modelem)
3. `article_type` dyskryminator — MUSI być użyty w migracji przed usunięciem (`article_type='usluga_dodatkowa'` → additional_services)

**MEDIUM (z Security Auditor):**
4. XOR walidacja w `update_position` (nie tylko create) — partial update może obejść invariant
5. Post-migration assertion: `SELECT COUNT(*) FROM contract_positions WHERE (machine_id IS NULL) = (service_id IS NULL)` = 0
6. CHECK constraint DB-level dla XOR (MariaDB 10.2+): `CHECK ((machine_id IS NOT NULL) <> (service_id IS NOT NULL))`

**LOW (z Security Auditor):**
7. `replacement_value` i `default_amount` z `Field(None, ge=0, decimal_places=2)`
8. `Depends(get_current_user)` na KAŻDYM endpoincie 3 nowych routerów
9. Stub `_verify_machine_access` / `_verify_service_access` / `_verify_additional_service_access` (future RBAC)

**Z QA Engineer:**
10. Seed ≥1 usługi zwykłej (obecnie 0 — ścieżka service_id nieprzetestowana danymi)
11. 14 unit test files do update + 4 nowe (patrz Faza 3.5)
12. 14 smoke gates (G1-G14) z 4 VETO gates (G3, G7, G8, G10)

**Z Product Owner:**
13. DoD 20 punktów (kontrakt dla QA)
14. Priorytet P2 — prerequisite dla P2-002 (power_type) i P2-003 (rezerwacje)

## 1. Problem

Obecnie jedna tabela `articles` z flagą `is_service: bool` miesza 3 kategorie biznesowe:
- **Maszyny** (koparka, ładowarka) — `is_service=false`
- **Usługi** (usługa koparką) — `is_service=true, article_type!='usluga_dodatkowa'`
- **Usługi dodatkowe** (transport, tankowanie) — `is_service=true, article_type='usluga_dodatkowa'`

## 2. Decyzje architektoniczne (APPROVED)

| Decyzja | Wybór |
|---------|-------|
| API endpointy | **3 osobne**: `/machines`, `/services`, `/additional-services` |
| Frontend routing | **3 osobne widoki**: `/machines`, `/services`, `/additional-services` |
| Pinia stores | **3 osobne**: `machineStore`, `serviceStore`, `additionalServiceStore` |
| Kategorie (category_id FK) | **Tylko machines** — services i additional_services bez kategorii |
| Fakturownia | **Zerowana** — seed od nowa, brak ograniczeń |
| Archiwum | **Bez zmian** — archive_articles zostaje po staremu |

## 3. Architektura — 3 niezależne tabele

### 3.1 Schema

```sql
-- Maszyny (sprzęt budowlany) — pełne dane techniczne
CREATE TABLE machines (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(200) NOT NULL,
    internal_number VARCHAR(50),
    registration_no VARCHAR(40),
    serial_no       VARCHAR(40),
    brand           VARCHAR(100),
    model           VARCHAR(100),
    replacement_value DECIMAL(18,2),
    category_id     INT,  -- FK → categories.id (jedyna tabela z kategoriami)
    owner_id        INT,  -- FK → contractors.id
    branch_id       INT,  -- FK → branches.id
    description     VARCHAR(400),
    notes           VARCHAR(200),
    rental_days     INT,
    category_main   VARCHAR(100),
    category_sub1   VARCHAR(100),
    category_sub2   VARCHAR(100),
    category_sub3   VARCHAR(100),
    is_archival     BOOLEAN DEFAULT FALSE,
    is_external     BOOLEAN DEFAULT FALSE,
    reach_m         DECIMAL(8,2),   -- zasięg w metrach (was: zasieg_m)
    capacity_t      DECIMAL(8,2),   -- udźwig w tonach (was: udzwig_t)
    accessories     TEXT,           -- dodatkowe akcesoria (was: dodatki)
    power_type      VARCHAR(10) DEFAULT 'other',  -- zgodność z obecnym modelem
    technical_attributes JSON,              -- przeniesione z articles (Phase 0 finding #1)
    fakturownia_product_id BIGINT,          -- nullable, seed od nowa
    fakturownia_tax_rate   VARCHAR(10),
    fakturownia_gtu_code   VARCHAR(20),
    fakturownia_pkwiu      VARCHAR(50),
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME
);

-- Usługi (usługa wykonana maszyną — pozycja umowy typu U)
CREATE TABLE services (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(200) NOT NULL,
    description     VARCHAR(400),
    notes           VARCHAR(200),
    replacement_value DECIMAL(18,2),  -- opcjonalnie, dla ubezpieczenia maszyny użytej w usłudze
    is_archival     BOOLEAN DEFAULT FALSE,
    fakturownia_product_id BIGINT,
    fakturownia_tax_rate   VARCHAR(10),
    fakturownia_gtu_code   VARCHAR(20),
    fakturownia_pkwiu      VARCHAR(50),
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME
);

-- Usługi dodatkowe (transport, tankowanie, czyszczenie — kwoty stałe)
CREATE TABLE additional_services (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(200) NOT NULL,
    default_amount  DECIMAL(18,2),  -- domyślna kwota (np. transport 500zł)
    description     VARCHAR(400),
    notes           VARCHAR(200),
    is_archival     BOOLEAN DEFAULT FALSE,
    fakturownia_product_id BIGINT,
    fakturownia_tax_rate   VARCHAR(10),
    fakturownia_gtu_code   VARCHAR(20),
    fakturownia_pkwiu      VARCHAR(50),
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME
);
```

### 3.2 Rozwiązanie problemu FK (5 obecnych FK do articles.id)

| Tabela | Obecne FK | Nowe FK | Strategia |
|--------|-----------|---------|-----------|
| `contract_positions` | `article_id → articles.id` (NOT NULL) | `machine_id → machines.id` (nullable) + `service_id → services.id` (nullable) | Dwa nullable FK, app-level walidacja: dokładnie jeden non-NULL |
| `service_fee_templates` | `article_id → articles.id` (nullable) | `additional_service_id → additional_services.id` (nullable) | Proste rename FK |
| `article_rate_presets` → `machine_rate_presets` | `article_id → articles.id` (NOT NULL) | `machine_id → machines.id` (NOT NULL) | Rename tabeli + rename FK |
| `reservations` | `article_id → articles.id` (NOT NULL) | `machine_id → machines.id` (NOT NULL) | Proste rename FK — tylko maszyny można rezerwować |
| `archive_contract_positions` | `article_id → archive_articles.id` | **BEZ ZMIAN** | Archiwum nie ruszamy |

### 3.3 contract_positions — kluczowa zmiana

```sql
-- Obecnie: article_id NOT NULL → articles.id
-- Nowe: machine_id NULL + service_id NULL (app-level: dokładnie jeden non-NULL)
ALTER TABLE contract_positions DROP COLUMN article_id;
ALTER TABLE contract_positions ADD COLUMN machine_id INT NULL;
ALTER TABLE contract_positions ADD COLUMN service_id INT NULL;
ALTER TABLE contract_positions ADD CONSTRAINT fk_cp_machine FOREIGN KEY (machine_id) REFERENCES machines(id);
ALTER TABLE contract_positions ADD CONSTRAINT fk_cp_service FOREIGN KEY (service_id) REFERENCES services(id);
```

Walidacja w service.py:
```python
# Pozycja umowy: machine_id XOR service_id (dokładnie jeden non-NULL)
if (data.machine_id is None) == (data.service_id is None):
    raise bad_request("Pozycja musi mieć dokładnie jedno: machine_id lub service_id")
# additional_service_id NIGDY nie jest pozycją umowy — tylko service fees
```

## 4. Fazy refaktora

### Faza 1: DB schema + modele SQLAlchemy
**Pliki (10):**
- `backend/machines/__init__.py`, `backend/machines/models.py` (NOWE)
- `backend/services/__init__.py`, `backend/services/models.py` (NOWE)
- `backend/additional_services/__init__.py`, `backend/additional_services/models.py` (NOWE)
- `backend/contracts/models.py` — ContractPosition: `article_id` → `machine_id` + `service_id`
- `backend/settings/models.py` — ServiceFeeTemplate: `article_id` → `additional_service_id`; ArticleRatePreset → MachineRatePreset
- `backend/reservations/models.py` — `article_id` → `machine_id`
- `backend/main.py` — startup migrations (CREATE TABLE + ALTER + seed update)

**Kolumny po angielsku:**
- `zasieg_m` → `reach_m`
- `udzwig_t` → `capacity_t`
- `dodatki` → `accessories`

### Faza 2: Backend schemas + service layer
**Pliki (16):**
- `backend/machines/schemas.py`, `backend/machines/service.py` (NOWE)
- `backend/services/schemas.py`, `backend/services/service.py` (NOWE)
- `backend/additional_services/schemas.py`, `backend/additional_services/service.py` (NOWE)
- `backend/contracts/service.py` — `create_position` walidacja XOR, `list_positions` JOIN machines OR services, `get_last_conditions_for_article` → `get_last_conditions_for_machine`
- `backend/contracts/schemas.py` — PositionCreate/Response: `article_id` → `machine_id` + `service_id`
- `backend/settings/service.py` — rate presets tylko machines, `_resolve_article_name` → `_resolve_machine_name`
- `backend/settings/schemas.py` — rename ArticleRatePreset* → MachineRatePreset*
- `backend/reservations/service.py` — `article_id` → `machine_id`, `list_for_article` → `list_for_machine`, `get_active_for_article` → `get_active_for_machine`
- `backend/reservations/schemas.py` — `article_id` → `machine_id`
- `backend/integrations/fakturownia/schemas.py` — `RaoArticleRef` → `RaoMachineRef` / `RaoServiceRef` / `RaoAdditionalServiceRef`
- `backend/migrate_service_fees.py` — `_find_or_create_service_article` → `_find_or_create_additional_service`
- **DELETE** `backend/articles/` (cały moduł: models.py, schemas.py, service.py, router.py, __init__.py)

### Faza 3: Backend API (routers) + wszystkie zależne moduły
**Pliki (18+):**
- `backend/machines/router.py` (NOWE) — GET/POST/PUT/DELETE /machines + availability + last-conditions + duplicate
- `backend/services/router.py` (NOWE) — GET/POST/PUT/DELETE /services
- `backend/additional_services/router.py` (NOWE) — GET/POST/PUT/DELETE /additional-services
- `backend/main.py` — rejestracja 3 nowych routerów, wyrejestrowanie articles, update seed (KISS presets → additional_services)
- `backend/stats/router.py` — `article_type` → `kind`, JOIN machines/services zamiast articles
- `backend/stats/calc.py` — `is_service` filter → JOIN z odpowiednią tabelą
- `backend/reports/service.py` — PDF generation z JOIN machines/services (patrz sekcja 7)
- `backend/explorer/router.py` — przeszukiwanie 3 tabel (UNION)
- `backend/settlements/router.py` — fakturownia mapping z 3 tabel
- `backend/settlements/service.py` — update zapytań
- `backend/export_to_unify.py` — export z 3 tabel
- `backend/shared/revenue.py` — jeśli używa articles
- `backend/integrations/fakturownia/service.py` — mapping z 3 tabel
- `backend/reservations/router.py` — `list_for_article` → `list_for_machine`, ścieżka `/article/{article_id}` → `/machine/{machine_id}`
- `backend/settings/router.py` — `article_rate_preset` endpointy → `machine_rate_preset`, ścieżki `/articles/{id}/rate-presets` → `/machines/{id}/rate-presets`
- `backend/seed_fa_invoices.py` — `get_article_fa_product_map` → mapping z 3 tabel

### Faza 3.5: Unit tests (backend) — pełny refaktor
**Pliki (7):**
- `backend/tests/unit/test_contracts.py` — `test_position_create_requires_article_id` → `test_position_create_requires_machine_or_service_id`, `test_get_last_conditions_for_article_no_history` → `..._for_machine...`
- `backend/tests/unit/test_availability_reservations.py` — `_mk_article` → `_mk_machine`
- `backend/tests/unit/test_fleet_external_filter.py` — 6 testów `article_*` → `machine_*` (is_external)
- `backend/tests/unit/test_settings.py` — wszystkie `article_rate_preset` testy → `machine_rate_preset` (12+ testów)
- `backend/tests/unit/test_stats_categories.py` — `test_aggregate_deduplicates_articles_within_category` → `..._machines...`
- `backend/tests/unit/test_archive.py` — archive tests zostają (archive_articles bez zmian), ale weryfikacja że nie importują articles
- `backend/tests/unit/test_fakturownia_service.py` — update jeśli używa Article

### Faza 4: Frontend — pełny refaktor
**Pliki (25+):**
- `frontend/src/views/MachineListView.vue` (NOWE)
- `frontend/src/views/MachineFormView.vue` (NOWE)
- `frontend/src/views/ServiceListView.vue` (NOWE)
- `frontend/src/views/ServiceFormView.vue` (NOWE)
- `frontend/src/views/AdditionalServiceListView.vue` (NOWE)
- `frontend/src/views/AdditionalServiceFormView.vue` (NOWE)
- `frontend/src/stores/machines.ts` (NOWE)
- `frontend/src/stores/services.ts` (NOWE)
- `frontend/src/stores/additionalServices.ts` (NOWE)
- `frontend/src/router/index.ts` — nowe trasy, usunięcie /articles
- `frontend/src/views/ContractFormView.vue` — picker: N→machines, U→machines+services, fees→additional_services
- `frontend/src/views/SettingsView.vue` — rate presets→machines, fee templates→additional_services
- `frontend/src/views/ReservationsView.vue` — `article_id` → `machine_id`, machineStore
- `frontend/src/views/ExplorerView.vue` — przeszukiwanie 3 tabel
- `frontend/src/views/DashboardView.vue` — jeśli używa articles
- `frontend/src/views/AnalyticsView.vue` — jeśli używa articles
- `frontend/src/components/contracts/ConditionPanel.vue` — jeśli używa article_id
- `frontend/src/components/contracts/ArticlePicker.vue` — jeśli istnieje, rename → MachinePicker / ServicePicker
- `frontend/src/components/articles/RatePresetSection.vue` — rename → `components/machines/RatePresetSection.vue`, `articleId` → `machineId`
- `frontend/src/stores/reservations.ts` — `ArticleReservation` → `MachineReservation`, `fetchForArticle` → `fetchForMachine`
- `frontend/src/stores/contracts.js` (or .ts) — `fetchLastConditionsForArticle` → `fetchLastConditionsForMachine`
- `frontend/src/stores/fakturownia.ts` — `RaoArticleRef` → `RaoMachineRef` / `RaoServiceRef`
- `frontend/src/stores/archive.ts` — `ArchiveArticle` zostaje (archive bez zmian), ale weryfikacja importów
- **DELETE** `frontend/src/views/ArticleFormView.vue`, `ArticleListView.vue`
- **DELETE** `frontend/src/stores/articles.ts` (or .js)

### Faza 5: E2E tests — pełny refaktor
**Pliki (12):**
- `e2e/tests/03-machines.spec.ts` (NOWE) — CRUD maszyn, kategorie, dane techniczne, availability
- `e2e/tests/03b-services.spec.ts` (NOWE) — CRUD usług
- `e2e/tests/03c-additional-services.spec.ts` (NOWE) — CRUD usług dodatkowych
- `e2e/tests/helpers.ts` — `createArticle` → `createMachine`/`createService`/`createAdditionalService`, `quickAddArticle` → `quickAddMachine`, `API` paths
- `e2e/tests/04-contract.spec.ts` — pozycje z machine_id/service_id
- `e2e/tests/04-contract-P1-005.spec.ts` — pozycje z machine_id/service_id (27 referencji)
- `e2e/tests/05-p1100.spec.ts` — service articles → additional_services
- `e2e/tests/06-analytics.spec.ts` — jeśli używa articles
- `e2e/tests/06-reservations.spec.ts` — `article_id` → `machine_id`
- `e2e/tests/07-reports.spec.ts` — PDF z machines/services
- `e2e/tests/10-ux-screenshots.spec.ts` — nowe widoki
- `e2e/tests/21-legacy-patterns.spec.ts` — fixtures z machine_id/service_id
- `e2e/tests/20-reservations.spec.ts` — `article_id` → `machine_id`
- `e2e/tests/08-auth-security.spec.ts` — jeśli używa articles
- **DELETE** `e2e/tests/03-article.spec.ts`

### Faza 6: Migracja od nowa + seed data
**Pliki (5):**
- `backend/migrate.py` — pełna przebudowa:
  - `artykul3` → 3 INSERT-y (machines, services, additional_services)
  - `umowa_pozycja3.id_artykulu` → `contract_positions.machine_id` OR `service_id`
  - CSV kategoryzacja → tylko machines
  - `firma.oplata_*` → `additional_services`
  - Rate presets → `machine_rate_presets`
  - `step5d_link_articles_to_templates` → `step5d_link_additional_services_to_templates`
  - Kolumny po angielsku (reach_m, capacity_t, accessories)
- `backend/seed_demo_data.py` — pełna przebudowa:
  - Maszyny (11 szt.) → `INSERT INTO machines`
  - Usługi dodatkowe (4 szt.) → `INSERT INTO additional_services`
  - Usługi (jeśli jakieś) → `INSERT INTO services`
  - `seed_article_rate_presets` → `seed_machine_rate_presets`
  - Fakturownia mapping — od nowa (zerowana)
- `backend/seed_fa_invoices.py` — `get_article_fa_product_map` → mapping z 3 tabel
- `backend/migrate_service_fees.py` — `_find_or_create_service_article` → `_find_or_create_additional_service`
- `backend/archive_legacy_data.py` — update jeśli używa articles (archive zostaje, ale skrypt może referencjonować articles dla source)

### Faza 7: Spec sync — pełny przepis
**Pliki spec/core (15 z referencjami do articles):**
- `spec/core/01_database.md` (57 referencji) — pełny DDL: 3 tabele + zmienione FK + kolumny EN
- `spec/core/02_backend_api.md` (89 referencji) — nowe endpointy /machines, /services, /additional-services
- `spec/core/03_frontend_screens.md` (76 referencji) — nowe widoki, picker, stores
- `spec/core/04_business_logic.md` (46 referencji) — walidacja XOR, rozliczenia
- `spec/core/05_cross_check.md` (2 referencje)
- `spec/core/06_navigation_flow.md` (8 referencji) — nowe trasy
- `spec/core/07_integrations.md` (2 referencje) — Fakturownia mapping
- `spec/core/08_migration_plan.md` (17 referencji) — migracja 3 tabel
- `spec/core/11_reports_stats.md` (15 referencji) — stats z machines/services
- `spec/core/12_logic_audit.md` (2 referencje)
- `spec/core/13_audit_all_processes.md` (6 referencji)
- `spec/core/14_audit_contract_process.md` (2 referencje)
- `spec/core/17_testing_plan.md` (1 referencja)
- `spec/core/23_explorer_design.md` — explorer 3 tabele
- `spec/core/24_export_ujednolicenie.md` (6 referencji) — export
- `spec/core/25_security.md` (2 referencje) — RBAC

**Pliki spec/process (1):**
- `spec/process/testing.md` — update jeśli referencjonuje articles

**Pliki spec/backlog (2):**
- `spec/backlog/BACKLOG.md` — P1-005 (Fakturownia /articles/14145/edit) → update ścieżki
- `spec/archive/BACKLOG_SPRINT_1.md` — `03-article.spec.ts` referencja → update

**Pliki .devin/ audit (3):**
- `.devin/audit_filters_map.md` — `articleType` referencje (BUG-1, BUG-3, BUG-6, BUG-7)
- `.devin/audit_backend_filters.md` — `article_type` w pytaniach 1, 2
- `.devin/audit_filters_final_report.md` — `articleType` w BUG-1, BUG-4
- `.devin/audit_db_truth.json` — `article_id`, `article_name` wartości

**Pliki spec/technical (2):**
- `spec/technical/TECHNICAL_SOLUTIONS.md` — dokumentacja refaktora
- `spec/refactor_articles_split_plan.md` — ten plan (oznaczyć DONE)

**Weryfikacja 6-tier:**
- Tier 1: `python -m compileall backend/` + `vue-tsc --noEmit`
- Tier 2: `pytest -x --tb=short`
- Tier 3: `curl /health` + `curl /openapi.json`
- Tier 4: `npx playwright test`
- Tier 4.5: drugi restart + `git diff spec/core/`
- Tier 6: lokalny commit

## 5. Pełny zakres plików

| Faza | Pliki nowe | Pliki modyfikowane | Pliki usunięte |
|------|-----------|-------------------|---------------|
| 1. DB + modele | 6 | 4 | 0 |
| 2. Schemas + service | 6 | 10 | 5 (articles/) |
| 3. API routers | 3 | 16+ | 0 |
| 3.5. Unit tests | 0 | 7 | 0 |
| 4. Frontend | 9 | 16+ | 3 |
| 5. E2E tests | 3 | 12+ | 1 |
| 6. Migracja + seed | 0 | 5 | 0 |
| 7. Spec sync | 0 | 23+ | 0 |
| **Total** | **27 nowych** | **93+ modyfikowanych** | **9 usuniętych** |

## 5. Kolejność wykonania (zależności)

```
Faza 1 (DB + modele)
    ↓
Faza 2 (Schemas + service)
    ↓
Faza 3 (API routers) ←──── Faza 6 (migracja + seed) może startować równolegle
    ↓
Faza 4 (Frontend)
    ↓
Faza 5 (E2E)
    ↓
Faza 7 (Spec + weryfikacja)
```

Fazy 1→2→3 są sekwencyjne (zależności DB → models → API).
Faza 6 (migracja) może startować po Fazie 1 (potrzebuje tabel).
Faza 4 (frontend) po Fazie 3 (potrzebuje API).
Faza 5 (E2E) po Fazie 4.
Faza 7 (spec) na końcu.

## 6. Backup przed refaktorem

```bash
# Backup bazy danych przed migracją
mariadb-dump rao_new > backup_before_articles_split.sql
```

## 7. Wydruki PDF — weryfikacja merytoryczna

### 7.1 Szablony PDF (6 plików HTML)

| Szablon | Co wyświetla | Źródło danych | Po refaktorze |
|---------|-------------|---------------|---------------|
| `contract.html` (umowa N) | `p.pos.article_name` (snapshot), `p.replacement_value`, `p.serial_no`, `p.registration_no` | `contract_positions.article_name` + JOIN `articles` | `article_name` zostaje (snapshot w pozycji) + JOIN `machines` dla replacement_value/serial_no/registration_no |
| `contract_u.html` (umowa U) | `p.pos.article_name`, `p.rate_type_name`, `p.pos.quantity`, `p.conditions_text` | `contract_positions.article_name` + conditions | `article_name` zostaje + conditions bez zmian |
| `protocol_zo.html` (protokół N) | `p.pos.article_name`, `p.serial_no`, `p.pos.delivery_date`, `p.replacement_value` | `contract_positions.article_name` + JOIN `articles` | `article_name` zostaje + JOIN `machines` |
| `protocol_zo_u.html` (protokół U) | `p.pos.article_name`, `p.serial_no`, `p.pos.delivery_date` | `contract_positions.article_name` + JOIN `articles` | `article_name` zostaje + JOIN `machines` OR `services` |
| `protocol_zo_nodata.html` | `p.pos.article_name`, `p.serial_no`, `p.pos.delivery_date`, `p.replacement_value` | `contract_positions.article_name` + JOIN `articles` | `article_name` zostaje + JOIN `machines` |
| `protocol_zo_nodata_u.html` | `p.pos.article_name`, `p.serial_no`, `p.pos.delivery_date` | `contract_positions.article_name` + JOIN `articles` | `article_name` zostaje + JOIN `machines` OR `services` |

### 7.2 reports/service.py — kluczowa zmiana

Obecnie (<ref_snippet file="c:/projects/repos/RaoApp_new/backend/reports/service.py" lines="158-175" />):
```python
article = await db.get(ArticleModel, pos.article_id) if pos.article_id else None
# ...
"replacement_value": article.replacement_value if article else None,
"serial_no": article.serial_no if article else None,
"registration_no": article.registration_no if article else None,
```

**Po refaktorze:**
```python
# Pozycja może mieć machine_id OR service_id (XOR)
machine = await db.get(Machine, pos.machine_id) if pos.machine_id else None
service = await db.get(Service, pos.service_id) if pos.service_id else None
article = machine or service  # dla wspólnych pól (replacement_value)

# replacement_value — z machine OR service (oba mogą mieć)
# serial_no, registration_no — TYLKO z machine (usługi nie mają numerów seryjnych)
"replacement_value": (machine or service).replacement_value if (machine or service) else None,
"serial_no": machine.serial_no if machine else None,
"registration_no": machine.registration_no if machine else None,
```

### 7.3 Stats PDF — `is_service` filter

Obecnie (<ref_snippet file="c:/projects/repos/RaoApp_new/backend/reports/service.py" lines="515-522" />):
```python
total_q = await db.execute(select(func.count()).select_from(Article).where(Article.is_service == False))
# ...
.join(Article, Article.id == ContractPosition.article_id)
.where(and_(Article.is_service == False, ...))
```

**Po refaktorze:**
```python
# Maszyny = tabela machines (nie is_service filter)
total_q = await db.execute(select(func.count()).select_from(Machine))
# ...
.join(Machine, Machine.id == ContractPosition.machine_id)
# Usługi = tabela services
.join(Service, Service.id == ContractPosition.service_id)
```

### 7.4 Checklist weryfikacyjna wydruków (Faza 7)

Dla KAŻDEGO typu wydruku sprawdź:

- [ ] **Umowa N (contract.html)** — nazwa maszyny, nr seryjny, nr rejestracyjny, wartość ubezpieczenia, warunki rozliczeniowe
- [ ] **Umowa U (contract_u.html)** — nazwa usługi/maszyny, stawka, warunki rozliczeniowe
- [ ] **Protokół N (protocol_zo.html)** — nazwa maszyny, nr seryjny, data dostawy, wartość ubezpieczenia
- [ ] **Protokół U (protocol_zo_u.html)** — nazwa usługi/maszyny, nr seryjny, data dostawy
- [ ] **Protokół N bez danych (protocol_zo_nodata.html)** — nazwa maszyny, nr seryjny, data dostawy, wartość ubezpieczenia
- [ ] **Protokół U bez danych (protocol_zo_nodata_u.html)** — nazwa usługi/maszyny, nr seryjny, data dostawy
- [ ] **Stats PDF** — liczba maszyn, rentowność, top machines, services breakdown
- [ ] **Zestawienie maszyn/art** — lista z 3 tabel (machines + services + additional_services)

### 7.5 Snapshot vs JOIN — kluczowa decyzja

`contract_positions.article_name` to **snapshot** — zapisany w momencie tworzenia pozycji.
Po refaktorze zostaje jako `article_name` (bez zmian nazwy kolumny).

**Zmiana:** `contract_positions.article_id` → `machine_id` + `service_id`.
`article_name` zostaje bez zmian — to snapshot, nie JOIN.

**Ryzyko:** jeśli maszyna zostanie zrenamedowana po utworzeniu umowy, stara umowa zachowa starą nazwę (to pożądane — snapshot).

## 8. Czego nie ruszamy

- `archive_articles` — archiwum zostaje po staremu
- `archive_contract_positions` — FK do archive_articles zostaje
- `archive_legacy_data.py` — archiwizacja działa na starych tabelach
- `_sync_condition_derived_fields` — logika warunków bez zmian (działa na pozycjach)
- `PositionCondition` — model warunków bez zmian
- Rate presets items — bez zmian (tylko parent tabela rename)
