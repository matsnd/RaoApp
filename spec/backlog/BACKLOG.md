# RAO Backlog — Master Backlog

> **Last updated:** 2026-05-17  
> **Format:** YAML front-matter + sekcje (parsowalne przez agentów)  
> **Source:** Unified backlog (merge of 19_BACKLOG.md + 21_BACKLOG_CLIENT.md)

---

## 🚨 P0 — Production Blockers

Max 5 zadań, każdy z deadline ostry.

### [RAO-P0-001] Usuń sekrety produkcyjne ze specyfikacji

```yaml
id: RAO-P0-001
priority: P0
size: XS
status: triaged
classification: security
roles: [tech-lead]
depends_on: []
blocks: [RAO-P0-002, RAO-P0-003]
source: security
source_date: 2026-05-17
specs_to_update:
  - core/25_security.md
migration_impact: no
security_impact: critical
```

**Job-to-be-done:**
Usunąć hasła produkcyjne z plików specyfikacji które zostały przypadkowo zakomitowane.

**Acceptance criteria (DoD):**
- [ ] Hasła usunięte z `core/08_migration_plan.md` (zastąpione `<<PLACEHOLDER>>`)
- [ ] Hasła usunięte z `AGENTS.md`
- [ ] Hasła usunięte z `.windsurf/rules/rao-project.md`
- [ ] `git diff | grep -iE "password|secret" spec/` zwraca 0 trafień
- [ ] `RaoPass2026!` zrotowane jeśli repo było udostępnione

**Security DoD:**
- [ ] Brak sekretów w repo (weryfikacja: `gitleaks detect`)
- [ ] Nowe hasło DB zapisane tylko w `.env` (chmod 600)
- [ ] Wszystkie pliki spec używają `<<PLACEHOLDER>>` zamiast sekretów

**Pliki do zmiany:** `core/08_migration_plan.md`, `AGENTS.md`, `.windsurf/rules/rao-project.md`
**ROI:** Security critical — hasła w repo to potencjalny breach
**Estimate:** 30 min (XS)
**Deadline:** 2026-05-17 (natychmiast)

---

### [RAO-P0-002] Utwórz core/25_SECURITY.md

```yaml
id: RAO-P0-002
priority: P0
size: M
status: todo
classification: security
roles: [security-auditor, tech-lead]
depends_on: [RAO-P0-001]
blocks: [RAO-P0-003]
source: security
source_date: 2026-05-17
specs_to_update:
  - core/25_security.md
migration_impact: no
security_impact: critical
```

**Job-to-be-done:**
Utworzyć kompletny plik security spec z threat model, RBAC matrix, polityką haseł, JWT, sekretów, RODO.

**Acceptance criteria (DoD):**
- [ ] `core/25_security.md` utworzony z 12 sekcjami (zgodnie z planem reorganizacji)
- [ ] Threat model zdefiniowany (aktorzy, zasoby, wektory)
- [ ] RBAC matrix kompletna (admin/user × zasób × akcja)
- [ ] Polityka haseł zdefiniowana (bcrypt, min length, blacklist)
- [ ] Polityka JWT zdefiniowana (TTL, refresh, rotacja)
- [ ] Polityka sekretów zdefiniowana (rotacja, manager)
- [ ] RODO procedury zdefiniowane (retencja, prawo do bycia zapomnianym)

**Security DoD:**
- [ ] Każdy nowy endpoint ma zdefiniowane RBAC w matrix
- [ ] Polityka migracji haseł: force_password_reset zamiast plaintext
- [ ] Polityka eksportu PII: szyfrowanie ZIP + hasło osobnym kanałem

**Pliki do zmiany:** `core/25_security.md` (nowy plik)
**ROI:** Security critical — brak security spec = agent nie ma gdzie sprawdzić
**Estimate:** 2h (M)
**Deadline:** 2026-05-17

---

### [RAO-P0-003] Napraw migrację haseł — force_password_reset zamiast plaintext

```yaml
id: RAO-P0-003
priority: P0
size: M
status: todo
classification: backend
roles: [backend-dev, db-architect]
depends_on: [RAO-P0-001, RAO-P0-002]
blocks: []
source: security
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - process/migrations.md
migration_impact: yes
security_impact: critical
```

**Job-to-be-done:**
Zmienić migrację haseł z kopiowania plaintext na force_password_reset + losowe hasło tymczasowe.

**Acceptance criteria (DoD):**
- [ ] `backend/migrate.py` zmieniony: stare hasła → losowe hasło tymczasowe + force_password_reset=1
- [ ] Brak okna gdzie plaintext leży w bazie
- [ ] Email notification do usera z linkiem reset (opcjonalne, P2)
- [ ] `core/01_database.md` zaktualizowany (finalny DDL)

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (mirror)
2. `backend/migrate.py` — zmiana logiki haseł
3. **Verification gate (obowiązkowe):**
   - [ ] `DROP DATABASE rao_new && CREATE` → run migrate → sprawdź czy hasła są bcrypt
   - [ ] Re-run `python migrate.py` → idempotentne (drugie uruchomienie bez zmian)
   - [ ] Drugi restart backend bez błędu
   - [ ] Weryfikacja: `SELECT password FROM users WHERE force_password_reset=1` count > 0

**Security DoD:**
- [ ] Brak plaintext haseł w bazie po migracji
- [ ] Brak plaintext haseł w logach migracji
- [ ] Logi migracji nie zawierają sekretów

**Pliki do zmiany:** `backend/migrate.py`, `core/01_database.md`, `process/migrations.md`
**ROI:** Security critical — plaintext hasła w bazie to potencjalny breach
**Estimate:** 2h (M)
**Deadline:** 2026-05-18

---

### [RAO-P0-004] Napraw bugi PDF podpisów (#6)

```yaml
id: RAO-P0-004
priority: P0
size: S
status: triaged
classification: bugfix
roles: [frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Naprawić błąd gdzie podpisy na umowie PDF pojawiają się na pierwszej stronie zamiast na ostatniej.

**Acceptance criteria (DoD):**
- [ ] PDF wygenerowany dla umowy 5-stronicowej ma podpisy TYLKO na str. 5
- [ ] CSS `page-break-inside: avoid` na bloku podpisów
- [ ] Test wizualny: screenshot porównawczy w `e2e/visual/contract-pdf.spec.ts`
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` rozszerzony o weryfikację podpisów
- [ ] Smoke test `01-login.spec.ts` PASS
- [ ] Brak nowych TS errors: `npx vue-tsc --noEmit` PASS

**Security DoD:**
- [ ] Brak `v-html` na user-input w szablonie PDF
- [ ] Logi nie zawierają PII (weryfikacja: `grep -r logger.*password backend/reports/`)

**Pliki do zmiany:** `backend/reports/templates/contract.html`, `contract.css`
**ROI:** 100% wysyłanych umów, koszt aktualnie = zażenowanie u klienta
**Estimate:** 2h (S)
**Deadline:** 2026-05-18

---

### [RAO-P0-005] Napraw format wyświetlania kwot w usługach dodatkowych (#5)

```yaml
id: RAO-P0-005
priority: P0
size: XS
status: triaged
classification: bugfix
roles: [frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Naprawić błąd gdzie w sekcji usług dodatkowych pojawiają się symbole "$1", "$2" zamiast rzeczywistych kwot.

**Acceptance criteria (DoD):**
- [ ] Zamiast "$1 zł" → wyświetlać faktyczną kwotę np. "150,00 zł"
- [ ] Format: "{nazwa usługi}: {kwota_from} zł - {kwota_to} zł"
- [ ] Przykład: "Tankowanie: 150,00 zł (plus koszt paliwa)"
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` rozszerzony o weryfikację formatu kwot
- [ ] Smoke test `01-login.spec.ts` PASS

**Security DoD:**
- [ ] Brak XSS w formacieowaniu kwot (walidacja inputu)

**Pliki do zmiany:** `ContractFormView.vue` (funkcja formatDescription)
**ROI:** Profesjonalny wygląd dokumentów
**Estimate:** 30 min (XS)
**Deadline:** 2026-05-18

---

## 🔴 P1 — Must-Have przed go-live klienta

Feature parity + krytyczne bugi.

### [RAO-P1-001] Filtrowanie po zakresie dat w Dashboard (B1)

```yaml
id: RAO-P1-001
priority: P1
size: XS
status: triaged
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Dodać możliwość filtrowania umów po zakresie dat (date_from/date_to) w Dashboard.

**Acceptance criteria (DoD):**
- [ ] 2 inputy `type="date"` w toolbarze Dashboard (dateFrom, dateTo)
- [ ] `params.date_from / params.date_to` przy wywołaniu API
- [ ] Backend już przyjmuje te parametry (weryfikacja)
- [ ] `core/03_frontend_screens.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla filtrowania dat
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `DashboardView.vue`
**ROI:** Codzienne użycie, poprawa UX
**Estimate:** 30 min (XS)

---

### [RAO-P1-002] Adres dostawy — pole wielolinijkowe (#1)

```yaml
id: RAO-P1-002
priority: P1
size: S
status: triaged
classification: cross-stack
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Zmienić pole adresu dostawy z jednolinijkowego na wielolinijkowy (textarea) w formularzu i PDF.

**Acceptance criteria (DoD):**
- [ ] Frontend: `<input>` na `<textarea rows="3">` w ContractFormView
- [ ] Backend: schema przyjmuje multiline (powinno działać bez zmian)
- [ ] PDF: aktualizacja szablonu protokołu — adres jako blok tekstowy z zachowaniem nowych linii
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla wielolinijkowego adresu
- [ ] Smoke test `01-login.spec.ts` PASS

**Security DoD:**
- [ ] Brak XSS w textarea (walidacja inputu)

**Pliki do zmiany:** `ContractFormView.vue`, `backend/reports/templates/protocol_zo.html`
**ROI:** Feature parity — klient był do tego przyzwyczajony
**Estimate:** 2h (S)

---

### [RAO-P1-003] Adres dostawy — rozdzielenie umowa vs protokół (#4)

```yaml
id: RAO-P1-003
priority: P1
size: S
status: triaged
classification: frontend
roles: [frontend-dev]
depends_on: [RAO-P1-002]
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Ukryć adres dostawy na umowie PDF, pokazać tylko na protokole.

**Acceptance criteria (DoD):**
- [ ] PDF Umowa: ukryty adres dostawy (display:none)
- [ ] PDF Protokół: widoczny adres dostawy
- [ ] Numer telefonu widoczny tylko na protokole
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla rozdzielenia wyświetlania
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/contract.html`, `protocol_zo.html`
**ROI:** Klient wymaga rozdzielenia dokumentów
**Estimate:** 2h (S)

---

### [RAO-P1-004] Sekcja "Uwagi" w umowie (#7)

```yaml
id: RAO-P1-004
priority: P1
size: XS
status: triaged
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Dodać brakującą sekcję "Uwagi" w umowie PDF z ważnymi informacjami o warunkach wynajmu.

**Acceptance criteria (DoD):**
- [ ] PDF Umowa: sekcja "Uwagi" przed podpisami (na ostatniej stronie)
- [ ] Zawartość: doba wynajmu, zgłoszenie zwrotu, dni pracy/tydzień, dokumentacja zdająca
- [ ] Dane z formularza: `working_days_per_week`
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla sekcji uwag
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/contract.html`
**ROI:** Feature parity — sekcja była w starej aplikacji
**Estimate:** 1h (XS)

---

### [RAO-P1-005] Poprawa ekstrakcji miast z adresów dostawy (#17)

```yaml
id: RAO-P1-005
priority: P1
size: M
status: triaged
classification: backend
roles: [backend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-09
specs_to_update:
  - core/04_business_logic.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Ulepsz funkcję ekstrakcji miast z wielolinijkowych adresów dostawy dla spójnych raportów lokalizacyjnych.

**Acceptance criteria (DoD):**
- [ ] Ulepszona funkcja `extract_city()` z priorytetyzacją znanych miast
- [ ] Lepsze wykrywanie i ignorowanie instrukcji dojazdu
- [ ] Testy: 16/22 przypadków poprawnych (73% skuteczności)
- [ ] `core/04_business_logic.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/04_business_logic.md` — finalny algorytm
2. `backend/stats/calc.py` — ulepszona funkcja extract_city
3. **Verification gate (obowiązkowe):**
   - [ ] Test na próbce 516 umów: top 20 miast pokrywa 80% rekordów
   - [ ] Liczba unikalnych miast <50 (obecnie prawdopodobnie >200)

**QA DoD:**
- [ ] Unit test w `backend/tests/unit/test_extract_city.py`
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/stats/calc.py`, `core/04_business_logic.md`
**ROI:** Raporty lokalizacyjne czytelne
**Estimate:** 3h (M)

---

## 🟡 P2 — Should-Have w ciągu kwartału

UX, drobne tech debt, nice-to-have.

### [RAO-P2-001] Kolumna "Adres dostawy" w liście umów (B2)

```yaml
id: RAO-P2-001
priority: P2
size: XS
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Dodać kolumnę z adresem dostawy w tabeli umów (DashboardView).

**Acceptance criteria (DoD):**
- [ ] Kolumna "Adres dostawy" w tabeli umów
- [ ] Truncate dla długich adresów + tooltip
- [ ] Empty state: brak adresu → "-"
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `DashboardView.vue`
**Estimate:** 30 min (XS)

---

### [RAO-P2-002] Link "Zmień hasło" w sidebar (B3)

```yaml
id: RAO-P2-002
priority: P2
size: XS
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Dodać link "Zmień hasło" w sidebar/profilu.

**Acceptance criteria (DoD):**
- [ ] Link w AppSidebar.vue przy "Wyloguj"
- [ ] Route do `/password` (już istnieje)
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Security DoD:**
- [ ] Endpoint `/auth/change-password` ma rate-limit (weryfikacja)

**Pliki do zmiany:** `AppSidebar.vue`
**Estimate:** 15 min (XS)

---

### [RAO-P2-003] NIP validation (checksum) (B4)

```yaml
id: RAO-P2-003
priority: P2
size: S
status: todo
classification: backend
roles: [backend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/04_business_logic.md
  - core/02_backend_api.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Dodać walidację sumy kontrolnej NIP przy tworzeniu/edycji kontrahenta.

**Acceptance criteria (DoD):**
- [ ] Funkcja `validate_nip_checksum()` w `backend/contractors/`
- [ ] Walidacja w Pydantic schema
- [ ] Komunikat błędu dla nieprawidłowego NIP
- [ ] `core/04_business_logic.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany

**QA DoD:**
- [ ] Unit test dla validate_nip_checksum
- [ ] Test E2E w `02-contractor.spec.ts`

**Pliki do zmiany:** `backend/contractors/schemas.py`, `service.py`
**Estimate:** 2h (S)

---

### [RAO-P2-004] Duplikacja artykułu z poziomu pickera (B5)

```yaml
id: RAO-P2-004
priority: P2
size: S
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Dodać przycisk "Duplikuj" w pickerze artykułów (modal w ContractFormView).

**Acceptance criteria (DoD):**
- [ ] Przycisk "Duplikuj" w ArticlePicker modal
- [ ] Wywołuje `articleStore.duplicate(id)`
- [ ] Reload listy po duplikacji
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `ContractFormView.vue`
**Estimate:** 2h (S)

---

### [RAO-P2-005] Nominatim — reverse geocoding w formularzu umowy (B10)

```yaml
id: RAO-P2-005
priority: P2
size: S
status: todo
classification: cross-stack
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
  - core/07_integrations.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Po wyborze adresu dostawy automatycznie geokodować współrzędne przez Nominatim.

**Acceptance criteria (DoD):**
- [ ] `ContractFormView.vue` — `onAddressSelect()` wywołuje endpoint
- [ ] Endpoint `POST /integrations/reverse-geocode` (już istnieje)
- [ ] Zapis lat/lng do formularza
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `ContractFormView.vue`
**Estimate:** 2h (S)

---

## 🟢 P3 — Icebox

Pomysły, bez harmonogramu, odrzuć lub odłóż.

### [RAO-P3-001] Drag & drop reorder szablonów usług (B6)

```yaml
id: RAO-P3-001
priority: P3
size: M
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Szablony usług można dodawać ale nie zmieniać kolejności przeciąganiem.

**Acceptance criteria (DoD):**
- [ ] `SettingsView.vue` — drag & drop dla szablonów
- [ ] Biblioteka `vuedraggable` lub własna implementacja
- [ ] Backend `POST /settings/fee-preset-groups/reorder` (już istnieje)
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `SettingsView.vue`
**Estimate:** 4h (M)

---

### [RAO-P3-002] Upload logo firmy (B7)

```yaml
id: RAO-P3-002
priority: P3
size: M
status: todo
classification: cross-stack
roles: [backend-dev, frontend-dev]
depends_on: []
blocks: [RAO-P3-003]
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: yes
security_impact: medium
```

**Job-to-be-done:**
Pole `logo LONGBLOB` jest w tabeli `companies` ale brak UI do uploadu/zmiany logo.

**Acceptance criteria (DoD):**
- [ ] Backend: nowy endpoint `POST /settings/company/logo` (multipart)
- [ ] Frontend: upload UI w SettingsView
- [ ] Walidacja: whitelist MIME (image/png,jpeg), max 2MB, hash filename
- [ ] Logo pojawia się w nagłówku sidebar
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (logo już istnieje)
2. `backend/settings/router.py` — nowy endpoint
3. **Verification gate (obowiązkowe):**
   - [ ] Upload PNG 2MB → success
   - [ ] Upload SVG → rejected (XSS risk)
   - [ ] Upload 10MB → rejected

**Security DoD:**
- [ ] Whitelist MIME: image/png, image/jpeg
- [ ] Zakaz SVG (XSS risk)
- [ ] Max size 2MB
- [ ] Hash filename (path traversal prevention)
- [ ] Brak `v-html` przy wyświetlaniu logo

**Pliki do zmiany:** `backend/settings/router.py`, `SettingsView.vue`
**Estimate:** 4h (M)

---

### [RAO-P3-003] Logo firmy w nagłówku sidebar (B16)

```yaml
id: RAO-P3-003
priority: P3
size: XS
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: [RAO-P3-002]
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Sidebar ma "TOOLSMART" hard-coded. Po zaimplementowaniu B7 podmienić na `<img>`.

**Acceptance criteria (DoD):**
- [ ] `AppSidebar.vue` — podmiana "TOOLSMART" na `<img>` z logo firmy
- [ ] Fallback do "TOOLSMART" jeśli brak logo
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `AppSidebar.vue`
**Estimate:** 30 min (XS)

---

### [RAO-P3-004] Export statystyk do CSV (B8)

```yaml
id: RAO-P3-004
priority: P3
size: M
status: todo
classification: cross-stack
roles: [backend-dev, frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Panel statystyk (ReportsSection) brak eksportu danych do CSV/Excel.

**Acceptance criteria (DoD):**
- [ ] Backend endpoint lub client-side CSV generation
- [ ] Przycisk "Export CSV" w ReportsSection
- [ ] Log w audit_log (kto, kiedy, jaki zakres)
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Security DoD:**
- [ ] RBAC check przed export (tylko admin/user)
- [ ] Log w audit_log (kto, kiedy, jaki zakres)

**Pliki do zmiany:** `ReportsSection.vue` lub `backend/stats/router.py`
**Estimate:** 3h (M)

---

### [RAO-P3-005] Modele DB: deliveries, costs, cost_types, audit_log (B9)

```yaml
id: RAO-P3-005
priority: P3
size: L
status: todo
classification: db-only
roles: [db-architect, backend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
migration_impact: yes
security_impact: medium
```

**Job-to-be-done:**
4 tabele z DDL nie mają modeli ORM ani endpointów API.

**Acceptance criteria (DoD):**
- [ ] Modele SQLAlchemy dla deliveries, costs, cost_types, audit_log
- [ ] Endpointy CRUD dla każdego modułu
- [ ] `core/01_database.md` zaktualizowany (finalny DDL)
- [ ] `core/02_backend_api.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (tabele już istnieją)
2. `backend/<module>/models.py` — SQLAlchemy models
3. `backend/<module>/router.py` — CRUD endpoints
4. **Verification gate (obowiązkowe):**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Drugi restart backend bez błędu "Duplicate column"

**Security DoD:**
- [ ] audit_log: append-only constraint (REVOKE UPDATE,DELETE dla rao_user)
- [ ] audit_log: admin-only read (RBAC)
- [ ] deliveries/costs/cost_types: RBAC checks na endpointach

**Pliki do zmiany:** nowe moduły backend/
**Estimate:** 8h (L)

---

### [RAO-P3-006] Auto-generowanie opisu warunku w ConditionPanel (B11)

```yaml
id: RAO-P3-006
priority: P3
size: S
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
W starym FormW.cs opis warunku był auto-generowany ("stawka 5000 zł/tyg. do 5 tygodni"). Nowy ConditionPanel nie generuje go automatycznie.

**Acceptance criteria (DoD):**
- [ ] `ConditionPanel.vue` — computed/watcher na zmianach rate1, period_count, billing_unit
- [ ] Auto-generowanie opisu w formacie "{rate} zł/{unit} do {period_count} {unit}"
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `frontend/src/components/contracts/ConditionPanel.vue`
**Estimate:** 2h (S)

---

### [RAO-P3-007] Kalendarz 2-miesieczny zamiast date inputs w umowie (B12)

```yaml
id: RAO-P3-007
priority: P3
size: M
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
W starym FormU4 wizualny kalendarz 2-miesieczny do wyboru dat od/do. Nowy formularz ma zwykłe `<input type="date">`.

**Acceptance criteria (DoD):**
- [ ] `ContractFormView.vue` — opcjonalnie zastąpić inputy data komponentem `vue-datepicker` lub własnym
- [ ] Wizualny kalendarz 2-miesieczny
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Uwaga:** Niski priorytet — obecna implementacja jest funkcjonalna.

**Pliki do zmiany:** `ContractFormView.vue`
**Estimate:** 4h (M)

---

### [RAO-P3-008] Keyboard shortcuts (B13)

```yaml
id: RAO-P3-008
priority: P3
size: S
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Dodać keyboard shortcuts dla codziennych akcji.

**Acceptance criteria (DoD):**
- [ ] `Ctrl+N` → Nowy rekord (kontekstowo)
- [ ] `Escape` → Zamknij modal
- [ ] `Enter` na wierszu tabeli → Otwórz edycję
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `AppLayout.vue` lub komponenty
**Estimate:** 2h (S)

---

### [RAO-P3-009] Empty state z CTA na nowej instalacji (B14)

```yaml
id: RAO-P3-009
priority: P3
size: XS
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Na pustej bazie lista umów jest pusta bez wskazówki co zrobić.

**Acceptance criteria (DoD):**
- [ ] "Utwórz pierwszą umowę →" button w empty state
- [ ] Empty state w DashboardView
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `DashboardView.vue`
**Estimate:** 30 min (XS)

---

### [RAO-P3-010] Globalny pasek postępu (NProgress) (B15)

```yaml
id: RAO-P3-010
priority: P3
size: S
status: todo
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Każdy widok ma własny spinner; brak globalnego feedbacku nawigacji.

**Acceptance criteria (DoD):**
- [ ] `NProgress.js` lub CSS progress bar w `AppLayout.vue`
- [ ] Odpalany na każde zapytanie API
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `AppLayout.vue`
**Estimate:** 2h (S)

---

### [RAO-P3-011] Testy integracyjne backend (pytest) (B17)

```yaml
id: RAO-P3-011
priority: P3
size: L
status: todo
classification: qa
roles: [qa-engineer, backend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
specs_to_update:
  - core/12_testing.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
`core/17_testing_plan.md` definiuje testy które nie zostały zaimplementowane.

**Acceptance criteria (DoD):**
- [ ] Testy integracyjne API (pytest + httpx, SQLite in-memory)
- [ ] E2E scenariusze SC-01..SC-10 (Playwright) — jeśli nie istnieją
- [ ] Testy migracji (row counts)
- [ ] `core/12_testing.md` zaktualizowany

**Pliki do zmiany:** `backend/tests/integration/`, `e2e/tests/`
**Estimate:** 16h (L)

---

### [RAO-P3-012] Kwota tankowania — zmiana default na 200 zł (#3)

```yaml
id: RAO-P3-012
priority: P3
size: XS
status: todo
classification: backend
roles: [backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/04_business_logic.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Zmiana domyślnej kwoty tankowania w szablonie usług dodatkowych z aktualnej na 200,00 zł.

**Acceptance criteria (DoD):**
- [ ] Defaultowa wartość dla nowych szablonów: 200,00 zł
- [ ] Dotyczy pola "Tankowanie" w service_fee_templates
- [ ] `core/04_business_logic.md` zaktualizowany

**Pliki do zmiany:** `backend/settings/service.py` lub migracja
**Estimate:** 30 min (XS)

---

### [RAO-P2-006] Picker artykułów — filtrowanie po typie umowy (#8)

```yaml
id: RAO-P2-006
priority: P2
size: S
status: todo
classification: cross-stack
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
  - core/02_backend_api.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Podczas tworzenia umowy typu "Usługa" (U), w pickerze artykułów powinny wyświetlać się wyłącznie artykuły oznaczone jako usługi (`is_service = true`).

**Acceptance criteria (DoD):**
- [ ] Umowa typu "Najem" (S): Picker pokazuje artykuły z `is_service = false`
- [ ] Umowa typu "Usługa" (U): Picker pokazuje artykuły z `is_service = true`
- [ ] Badge/label w pickerze wskazujący typ artykułu
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany

**Pliki do zmiany:** `ContractFormView.vue`, `backend/articles/router.py`
**Estimate:** 2h (S)

---

### [RAO-P1-006] Protokół usługi — ewidencja godzin operatora (#9)

```yaml
id: RAO-P1-006
priority: P1
size: M
status: todo
classification: cross-stack
roles: [db-architect, backend-dev, frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/11_reports_stats.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Protokół usługi (inny niż protokół najmu) musi umożliwiać ewidencję godzin pracy operatora.

**Acceptance criteria (DoD):**
- [ ] DB: Nowa tabela `service_hours` (id, position_id, date, time_from, time_to, notes)
- [ ] Backend: CRUD endpointy dla godzin usługi
- [ ] Frontend: Tabela godzin w ContractFormView dla umów typu "U"
- [ ] PDF: Nowy szablon lub modyfikacja protokołu usługi z sekcją godzin
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/11_reports_stats.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL
2. `backend/service_hours/models.py` — SQLAlchemy
3. `backend/main.py` startup — ALTER TABLE
4. **Verification gate:**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Drugi restart backend bez błędu

**Pliki do zmiany:** nowe moduły backend/, ContractFormView.vue, templates PDF
**Estimate:** 6h (M)

---

### [RAO-P2-007] UX Raportów — rozdzielenie "teraz" od "okres" (#10)

```yaml
id: RAO-P2-007
priority: P2
size: S
status: todo
classification: cross-stack
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
  - core/02_backend_api.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Aktualnie w sekcji raportów pokazuje się "Wynajętych teraz" obok filtrów datowych. Użytkownik myśli że wybór przedziału czasowego wpływa na tę liczbę.

**Acceptance criteria (DoD):**
- [ ] Jasne rozdzielenie sekcji "Stan aktualny" od "Analiza historyczna"
- [ ] Sekcja "Stan aktualny" wizualnie wyodrębniona (inne tło, nagłówek)
- [ ] Daty wpływają tylko na dane historyczne
- [ ] Nowy endpoint `/stats/current-status` (niezależnie od dat)
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany

**Pliki do zmiany:** `ReportsSection.vue`, `backend/stats/router.py`
**Estimate:** 3h (S)

---

### [RAO-P2-008] Numer wewnętrzny maszyny — widoczność i wyszukiwanie (#11)

```yaml
id: RAO-P2-008
priority: P2
size: S
status: todo
classification: cross-stack
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/03_frontend_screens.md
  - core/02_backend_api.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Pole `internal_number` już istnieje w tabeli `articles`, ale nie jest widoczne w formularzach ani w raportach.

**Acceptance criteria (DoD):**
- [ ] Widoczność nr wewnętrznego w formularzu artykułu
- [ ] Wyszukiwanie po nr wewnętrznym w article pickerze
- [ ] Wyświetlanie nr wewnętrznego w raportach i statystykach
- [ ] Filtrowanie raportów per konkretna maszyna (po nr wewnętrznym)
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany

**Pliki do zmiany:** `ArticleFormView.vue`, `ArticlePicker.vue`, `ReportsSection.vue`, `backend/stats/router.py`
**Estimate:** 3h (S)

---

### [RAO-P2-009] Statystyki per maszyna (ROI, wykorzystanie) (#12)

```yaml
id: RAO-P2-009
priority: P2
size: M
status: todo
classification: cross-stack
roles: [backend-dev, frontend-dev]
depends_on: [RAO-P2-008]
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Klient potrzebuje sprawdzać rentowność (stopę zwrotu) dla konkretnych maszyn.

**Acceptance criteria (DoD):**
- [ ] Backend endpoint `/stats/machine/{id}/history?from=&to=`
- [ ] Po wyborze maszyny pokazują się statystyki:
  - Okres analizy
  - Całkowity przychód z maszyny w okresie
  - Liczba dni wynajmu
  - Średni przychód/dzień wynajmu
  - Procent wykorzystania w okresie
- [ ] Panel szczegółów maszyny w ReportsSection
- [ ] Ewentualnie wykres wykorzystania w czasie
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `backend/stats/router.py`, `ReportsSection.vue`
**Estimate:** 4h (M)

---

### [RAO-P2-010] Filtrowanie pozycji umowy po typie (#13)

```yaml
id: RAO-P2-010
priority: P2
size: S
status: todo
classification: cross-stack
roles: [backend-dev, frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
W raportach klient chce widzieć nie tylko maszyny, ale też podsumowanie pozycji dodatkowych.

**Acceptance criteria (DoD):**
- [ ] Filtr "Typ pozycji" w raportach: Maszyny | Usługi | Wszystkie
- [ ] Podsumowanie przychodu z usług dodatkowych osobno
- [ ] Lista najczęściej wykonywanych usług dodatkowych
- [ ] Backend endpoint `/stats/positions?type=&from=&to=`
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `backend/stats/router.py`, `ReportsSection.vue`
**Estimate:** 3h (S)

---

### [RAO-P2-011] Statystyki po lokalizacji/miejscowości (#14)

```yaml
id: RAO-P2-011
priority: P2
size: S
status: todo
classification: cross-stack
roles: [backend-dev, frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Klient chce analizować gdzie najczęściej wynajmują maszyny (miejscowości/obszary).

**Acceptance criteria (DoD):**
- [ ] Filtrowanie raportów po miejscowości (z adresu dostawy)
- [ ] Podsumowanie: ilość wynajmów w danej lokalizacji
- [ ] Mapa lub lista top lokalizacji
- [ ] Backend endpoint `/stats/locations/detail?city=&from=&to=`
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `backend/stats/router.py`, `ReportsSection.vue`
**Estimate:** 3h (S)

---

### [RAO-P1-007] Rezerwacja maszyn (blokada wynajmu) (#15)

```yaml
id: RAO-P1-007
priority: P1
size: M
status: todo
classification: cross-stack
roles: [db-architect, backend-dev, frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/04_business_logic.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
System musi umożliwiać rezerwację maszyn na przyszłe terminy. Maszyna zablokowana w rezerwacji nie może być wynajęta w tym okresie.

**Acceptance criteria (DoD):**
- [ ] DB: Nowa tabela `article_reservations` (lub soft reservation przez umowy)
- [ ] Backend: API rezerwacji, walidacja konfliktów dat
- [ ] Frontend: Formularz rezerwacji, badge w pickerze, walidacja dostępności
- [ ] Badge "Zarezerwowana do DD.MM.YYYY" w pickerze artykułów
- [ ] Informacja kiedy maszyna będzie dostępna przy próbie wynajmu zablokowanej
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/04_business_logic.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL
2. `backend/reservations/models.py` — SQLAlchemy
3. `backend/main.py` startup — ALTER TABLE
4. **Verification gate:**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Drugi restart backend bez błędu

**Pliki do zmiany:** nowe moduły backend/, ContractFormView.vue, ArticlePicker.vue
**Estimate:** 8h (M)

---

## ✅ Done Log

Zobacz `archive/16_todo_done.md` dla pełnego historii zadań ukończonych.

---

## 📊 Podsumowanie

| Priorytet | Liczba | Effort łączny |
|-----------|--------|---------------|
| 🚨 P0 | 5 | ~7h |
| 🔴 P1 | 5 | ~8h |
| 🟡 P2 | 5 | ~11h |
| 🟢 P3 | 5 | ~20h |
| **Razem** | **20** | **~46h** |

---

## 📋 Tabela TL;DR

| ID | Tytuł | Źródło | P | Est. | Status | Owner |
|----|-------|--------|---|------|--------|-------|
| RAO-P0-001 | Usuń sekrety ze spec | Security | P0 | XS | triaged | tech-lead |
| RAO-P0-002 | Utwórz SECURITY.md | Security | P0 | M | todo | security-auditor |
| RAO-P0-003 | Napraw migrację haseł | Security | P0 | M | todo | backend-dev |
| RAO-P0-004 | Napraw podpisy PDF | Client | P0 | S | triaged | frontend-dev |
| RAO-P0-005 | Napraw format kwot | Client | P0 | XS | triaged | frontend-dev |
| RAO-P1-001 | Filtr dat Dashboard | Internal | P1 | XS | triaged | frontend-dev |
| RAO-P1-002 | Adres dostawy multiline | Client | P1 | S | triaged | cross-stack |
| RAO-P1-003 | Adres dostawy rozdzielenie | Client | P1 | S | triaged | frontend-dev |
| RAO-P1-004 | Sekcja Uwagi w umowie | Client | P1 | XS | triaged | frontend-dev |
| RAO-P1-005 | Ekstrakcja miast | Internal | P1 | M | triaged | backend-dev ||| RAO-P1-006 | Protokół usługi — godziny operatora | Client | P1 | M | todo | cross-stack |
|| RAO-P1-007 | Rezerwacja maszyn | Client | P1 | M | todo | cross-stack |
|| RAO-P2-001 | Kolumna adres dostawy | Internal | P2 | XS | todo | frontend-dev |
|| RAO-P2-002 | Link "Zmień hasło" sidebar | Internal | P2 | XS | todo | frontend-dev |
|| RAO-P2-003 | NIP validation checksum | Internal | P2 | S | todo | backend-dev |
|| RAO-P2-004 | Duplikacja artykułu pickera | Internal | P2 | S | todo | frontend-dev |
|| RAO-P2-005 | Nominatim reverse geocoding | Internal | P2 | S | todo | cross-stack |
|| RAO-P2-006 | Picker artykułów — filtr typ umowy | Client | P2 | S | todo | cross-stack |
|| RAO-P2-007 | UX Raportów — teraz vs okres | Client | P2 | S | todo | cross-stack |
|| RAO-P2-008 | Numer wewnętrzny maszyny | Client | P2 | S | todo | cross-stack |
|| RAO-P2-009 | Statystyki per maszyna ROI | Client | P2 | M | todo | cross-stack |
|| RAO-P2-010 | Filtrowanie pozycji umowy typ | Client | P2 | S | todo | cross-stack |
|| RAO-P2-011 | Statystyki po lokalizacji | Client | P2 | S | todo | cross-stack |
|| RAO-P3-001 | Drag & drop reorder szablonów | Internal | P3 | M | todo | frontend-dev |
|| RAO-P3-002 | Upload logo firmy | Internal | P3 | M | todo | cross-stack |
|| RAO-P3-003 | Logo w nagłówku sidebar | Internal | P3 | XS | todo | frontend-dev |
|| RAO-P3-004 | Export statystyk CSV | Internal | P3 | M | todo | cross-stack |
|| RAO-P3-005 | Modele DB deliveries/costs/audit | Internal | P3 | L | todo | db-architect |
|| RAO-P3-006 | Auto-generowanie opisu warunku | Internal | P3 | S | todo | frontend-dev |
|| RAO-P3-007 | Kalendarz 2-miesieczny | Internal | P3 | M | todo | frontend-dev |
|| RAO-P3-008 | Keyboard shortcuts | Internal | P3 | S | todo | frontend-dev |
|| RAO-P3-009 | Empty state CTA | Internal | P3 | XS | todo | frontend-dev |
|| RAO-P3-010 | Globalny pasek postępu NProgress | Internal | P3 | S | todo | frontend-dev |
|| RAO-P3-011 | Testy integracyjne backend pytest | Internal | P3 | L | todo | qa-engineer |
|| RAO-P3-012 | Kwota tankowania default 200 zł | Client | P3 | XS | todo | backend-dev |
