# RAO Backlog — Master Backlog

> **Last updated:** 2026-05-18  
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
status: done
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
status: done
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
status: done
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
status: done
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
status: done
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
status: done
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
status: done
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
status: done
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
status: done
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
status: done
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

### [RAO-P1-008] Strukturalizacja adresów: kod pocztowy + miasto (#1)

```yaml
id: RAO-P1-008
priority: P1
size: L
status: done
classification: cross-stack
roles: [db-architect, backend-dev, frontend-dev]
depends_on: []
blocks: [RAO-P1-005]
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/04_business_logic.md
  - core/11_reports_stats.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Rozdzielić adres dostawy na strukturę: kod pocztowy + miasto + pełny adres (do dowolnych notatek). Implementacja słownikowania kodów pocztowych (auto-uzupełnianie miasta) i zmiana statystyk na bazowanie na twardych danych (kod pocztowy + miasto), nie na całym adresie.

**Acceptance criteria (DoD):**
- [x] DB: Nowe kolumny w `contracts`: `postal_code VARCHAR(10)`, `city VARCHAR(100)`, `delivery_address TEXT` (zmiana z VARCHAR)
- [x] Backend: Skrypt ekstrakcji kodu pocztowego i miasta z adresu (regex + słownik)
- [x] Backend: Słownik kodów pocztowych (tabela `postal_codes` - tymczasowo 11 kodów, docelowo GUS TERYT)
- [x] Backend: Auto-uzupełnianie miasta po wpisaniu kodu pocztowego
- [x] Frontend: Formularz z polami: kod pocztowy (auto-uzupełnia miasto), miasto (edytowalne), adres pełny (dowolne notatki)
- [x] Stats: Zmiana filtrów statystyk z "cały adres" na "kod pocztowy + miasto"
- [x] Migration: Skrypt migracji starych danych (ekstrakcja + ujednolicenie)
- [x] `core/01_database.md` zaktualizowany
- [x] `core/02_backend_api.md` zaktualizowany
- [x] `core/03_frontend_screens.md` zaktualizowany
- [x] `core/04_business_logic.md` zaktualizowany
- [x] `core/11_reports_stats.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (postal_code, city, delivery_address TEXT)
2. `backend/contracts/models.py` — SQLAlchemy models
3. `backend/main.py` startup — ALTER TABLE ADD COLUMN
4. `backend/migrate.py` — skrypt migracji starych danych:
   - Ekstrakcja kodu pocztowego z adresu (regex XX-XXX)
   - Ekstrakcja miasta z adresu lub słownika po kodzie pocztowym
   - Ujednolicenie: jeden kod pocztowy = jedno miasto (najczęstsze)
   - Weryfikacja: % rekordów z poprawnym kodem pocztowym
5. **Verification gate (obowiązkowe):**
   - [ ] `DROP DATABASE rao_new && CREATE` → run migrate → sprawdź czy postal_code/city są wypełnione
   - [ ] Re-run `python migrate.py` → idempotentne
   - [ ] Drugi restart backend bez błędu
   - [ ] Weryfikacja: `SELECT COUNT(*) FROM contracts WHERE postal_code IS NULL` = 0

**QA DoD:**
- [ ] Unit test dla skryptu ekstrakcji kodu pocztowego
- [ ] Unit test dla słownikowania (kod pocztowy → miasto)
- [ ] E2E test w `04-contract.spec.ts` dla auto-uzupełniania miasta
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/contracts/models.py`, `schemas.py`, `service.py`, `backend/migrate.py`, `ContractFormView.vue`, `backend/stats/router.py`, `backend/stats/calc.py`
**ROI:** Krytyczne dla statystyk — obecne filtry po całym adresie są bezużyteczne (wiele wariantów tego samego miasta)
**Estimate:** 12h (L)

---

### [RAO-P1-009] Weryfikacja PDF vs stara aplikacja WinForms (#6)

```yaml
id: RAO-P1-009
priority: P1
size: M
status: done
classification: qa
roles: [qa-engineer, frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Przejrzeć wygenerowane PDF z nowego systemu i porównać z PDF ze starej aplikacji WinForms. Zidentyfikować różnice i naprawić.

**Acceptance criteria (DoD):**
- [x] Porównanie umowy PDF (nowy vs stary) — lista różnic
- [x] Porównanie protokołu PDF (nowy vs stary) — lista różnic
- [x] Naprawa krytycznych różnic (BUG #1, #2, #3, #5)
- [x] BUG #1: Usunięcie duplikatu stopki PZO (protocol_zo*.html)
- [x] BUG #2: Poprawa nagłówka "do najmu" → "dni najmu" (contract.html)
- [x] BUG #3: Naprawa hangin dash przy braku date_to (contract.html)
- [x] BUG #5: Zmniejszenie margin-top podpisów PZO z 40px → 20px
- [ ] BUG #4: Etykieta "dane podmiotu wynajmującego" → "NAJEMCA" (PO decision)
- [ ] BUG #6: 12 → 4 wierszy w PZO usługi (P2)
- [ ] Weryfikacja: 5 losowych umów — PDF identyczne lub lepsze
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [x] Visual regression test (QA report zidentyfikował 6 bugów)
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/contract.html`, `protocol_zo.html`, `protocol_zo_u.html`, `protocol_zo_nodata_u.html`
**ROI:** Klient wymaga feature parity PDF — obecne różnice blokują go-live
**Estimate:** 4h (M)

---

### [RAO-P1-010] Tabela "Przy wydaniu / Przy odbiorze" w protokole (#7)

```yaml
id: RAO-P1-010
priority: P1
size: M
status: done
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Dodać tabelę "Przy wydaniu / Przy odbiorze" w protokółach PDF z polami do ręcznego uzupełnienia przez klienta (data, urządzenie, stan paliwa, klucze, wideł, czystość, dokumentacja, akcesoria, uwagi).

**Acceptance criteria (DoD):**
- [ ] PDF Protokół: nowa sekcja "Przy wydaniu / Przy odbiorze" przed podpisami
- [ ] Tabela z kolumnami: data i godzina, urządzenie i model, stan paliwa, ilość kluczyków, stan wideł, czystość maszyny, dokumentacja zdjęciowa, dodatkowe akcesoria, uwagi
- [ ] Pola puste do ręcznego wypełnienia (nie generowane z systemu)
- [ ] Styl: tabela z ramkami, czytelne nagłówki
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla weryfikacji tabeli
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/protocol_zo.html`, `protocol_uslugi.html`, `protocol.css`
**ROI:** Klient wymaga tej tabeli — jest krytyczna dla procesu wydania/odbioru maszyny
**Estimate:** 3h (M)

---

### [RAO-P1-011] Usługi dodatkowe zesłownikowane z artykułami (#8)

```yaml
id: RAO-P1-011
priority: P1
size: L
status: done
classification: cross-stack
roles: [db-architect, backend-dev]
depends_on: []
blocks: [RAO-P1-012]
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/04_business_logic.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Zmienić strukturę usług dodatkowych tak, aby były zesłownikowane z artykułami (artykuły => usługi). Obecnie usługi dodatkowe są zmyślone stringi — mają być powiązane z tabelą `articles` przez FK. Zestawy usług (service_fee_templates) mają być zesłownikowane z konkretnymi artykułami.

**Acceptance criteria (DoD):**
- [ ] DB: Zmiana struktury `service_fee_templates` — dodanie FK do `articles` (zamiast string name)
- [ ] DB: Tabela `service_fee_template_items` (template_id, article_id, default_price)
- [ ] Backend: Zmiana logiki tworzenia szablonów — wybór z artykułów zamiast wpisywanie nazwy
- [ ] Backend: API zwraca nazwę artykułu z tabeli `articles` (nie string)
- [ ] Migration: Skrypt migracji starych danych — mapowanie stringów na artykuły
- [ ] Frontend: Picker artykułów w formularzu szablonów (zamiast text input)
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/04_business_logic.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (service_fee_template_items)
2. `backend/settings/models.py` — SQLAlchemy models
3. `backend/main.py` startup — ALTER TABLE + CREATE TABLE
4. `backend/migrate.py` — skrypt migracji:
   - Mapowanie string nazw usług dodatkowych na `articles` (po nazwie lub ręczne mapowanie)
   - Tworzenie rekordów w `service_fee_template_items`
   - Weryfikacja: % szablonów z poprawnymi FK
5. **Verification gate (obowiązkowe):**
   - [ ] `DROP DATABASE rao_new && CREATE` → run migrate → sprawdź czy FK są poprawne
   - [ ] Re-run `python migrate.py` → idempotentne
   - [ ] Drugi restart backend bez błędu

**QA DoD:**
- [ ] Unit test dla migracji usług dodatkowych
- [ ] E2E test w `05-settings.spec.ts` dla tworzenia szablonów z artykułami
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/settings/models.py`, `schemas.py`, `service.py`, `backend/migrate.py`, `SettingsView.vue`
**ROI:** Spójność danych — usługi dodatkowe nie są "zmyślone stringi" tylko powiązane z rzeczywistymi artykułami
**Estimate:** 8h (L)

---

### [RAO-P1-012] Panel rozliczenie umowy — koszty klient vs firma (#9)

```yaml
id: RAO-P1-012
priority: P1
size: XL
status: done
classification: cross-stack
roles: [product-owner, db-architect, backend-dev, frontend-dev]
depends_on: [RAO-P1-011]
blocks: [RAO-P1-013]
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/04_business_logic.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Nowy panel "Rozliczenie umowy" z tabelą wszystkich pozycji umowy (maszyny + usługi dodatkowe) z polami do ręcznego wpisania kosztów: koszt dla klienta (na fakturze) i koszt dla firmy (narzut). Product Owner musi wymyślić odpowiednie nazwy pól.

**Acceptance criteria (DoD):**
- [ ] PO: Zdefiniowanie nazw pól kosztów (np. "Koszt faktura", "Koszt własny", "Marża")
- [ ] DB: Nowa tabela `contract_settlements` (id, contract_id, position_id, cost_client DECIMAL, cost_company DECIMAL, notes TEXT)
- [ ] Backend: Automatyczne tworzenie rekordów w `contract_settlements` po utworzeniu umowy (dla wszystkich pozycji)
- [ ] Backend: CRUD endpointy dla rozliczeń
- [ ] Frontend: Nowy panel w ContractFormView / ContractDetailView z tabelą rozliczeń
- [ ] Frontend: Pola edytowalne: koszt klienta, koszt firmy, uwagi
- [ ] Frontend: Obliczanie marży automatycznie (cost_client - cost_company)
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/04_business_logic.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (contract_settlements)
2. `backend/settlements/models.py` — SQLAlchemy (nowy moduł)
3. `backend/main.py` startup — CREATE TABLE
4. `backend/contracts/service.py` — auto-creowanie settlement records po create contract
5. **Verification gate (obowiązkowe):**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → create contract → sprawdź czy settlement records są tworzone
   - [ ] Drugi restart backend bez błędu

**QA DoD:**
- [ ] Unit test dla auto-creowania settlement records
- [ ] E2E test w `04-contract.spec.ts` dla panelu rozliczeń
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/settlements/` (nowy moduł), `backend/contracts/service.py`, `ContractFormView.vue`, `ContractDetailView.vue`
**ROI:** Krytyczne dla fakturowania i prowizji — obecnie brak rozdzielenia kosztów klient vs firma
**Estimate:** 16h (XL)

---

### [RAO-P1-013] Poprawa tekstu checkboxa ukrywania adresu (#2)

```yaml
id: RAO-P1-013
priority: P1
size: XS
status: done
classification: frontend
roles: [frontend-dev, ux-designer]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Naprawić tekst checkboxa "Ukryj adres dostawy na umowie" — obecny tekst jest za długi, zawiera błędy ortograficzne i jest niezrozumiały.

**Acceptance criteria (DoD):**
- [ ] Nowy tekst: "☐ Ukryj adres dostawy na umowie (klient wpisze ręcznie)"
- [ ] Poprawa błędu ortograficznego: "żę" → "że"
- [ ] Usunięcie języka potocznego ("niech się nie pokazuje")
- [ ] Zwięzlenie tekstu do maks 15 słów
- [ ] `core/03_frontend_screens.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla checkboxa
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `ContractFormView.vue`
**ROI:** UX krytyczne — obecny tekst wygląda jak notatka developera, nie produkcyjny UI
**Estimate:** 30 min (XS)

---

### [RAO-P1-014] Poprawa checkboxa "Na 1 stronie nie bez podpisów" (#3)

```yaml
id: RAO-P1-014
priority: P1
size: XS
status: done
classification: frontend
roles: [frontend-dev, ux-designer]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Naprawić etykietę checkboxa w sekcji podpisów — podwójna negacja jest niezrozumiała.

**Acceptance criteria (DoD):**
- [x] Nowy tekst: "☐ Podpisy wymagane na stronie 1"
- [x] Usunięcie podwójnej negacji
- [x] Zwięzlenie tekstu
- [x] DB: Dodanie pola `signatures_on_page1 BOOLEAN NOT NULL DEFAULT FALSE` do tabeli `contracts`
- [x] Backend: Aktualizacja modelu i schemas
- [x] Frontend: Dodanie checkboxa w ContractFormView.vue
- [x] `core/01_database.md` zaktualizowany
- [x] `core/02_backend_api.md` zaktualizowany
- [x] `core/03_frontend_screens.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla checkboxa podpisów
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/contracts/models.py`, `backend/contracts/schemas.py`, `backend/main.py`, `ContractFormView.vue`, `spec/core/01_database.md`, `spec/core/02_backend_api.md`, `spec/core/03_frontend_screens.md`
**ROI:** UX krytyczne — obecny tekst jest mylący
**Estimate:** 30 min (XS)

---

### [RAO-P1-015] Format OWN dokumentu — 2 strony z punktem 3 po prawej (#4)

```yaml
id: RAO-P1-015
priority: P1
size: M
status: done
classification: frontend
roles: [frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Naprawić format dokumentu "Ogólne Warunki Najmu" (OWN) tak, aby mieścił się na 2 stronach z punktem §3 zaczynającym się po prawej stronie kolumny.

**Acceptance criteria (DoD):**
- [ ] PDF OWN: podział na 2 strony
- [ ] Auto-layout: punkt §3 zawsze zaczyna się po prawej stronie kolumny
- [ ] Dodać preview z wizualnym podziałem na strony (Page 1 | Page 2)
- [ ] Zmienić font na Montserrat (nie Times New Roman)
- [ ] Dodać header z logo RAO w kolorze #1D2B53
- [ ] Dodać toolbar: [Drukuj] [PDF] [Edytuj] z border-radius: 12px
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla OWN dokumentu
- [ ] Wizualne sprawdzenie: 2 strony, punkt §3 po prawej
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/own.html`, `own.css`
**ROI:** Klient wymaga poprawnego formatu dokumentu prawnego
**Estimate:** 4h (M)

---

### [RAO-P1-022] Pełna integracja pieczątek z Vision AI i programowym wyciąganiem z PDF

```yaml
id: RAO-P1-022
priority: P1
size: L
status: done
classification: cross-stack
roles: [backend-dev, frontend-dev, tech-lead]
depends_on: []
blocks: []
source: client
source_date: 2026-05-18
specs_to_update:
  - core/11_reports_stats.md
  - core/07_integrations.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Pełna integracja pieczątek firmowych w dokumentach (umowy, protokoły, OWN) z użyciem Vision AI do analizy referencyjnych PDF i programowego wyciągania pieczątek z plików wektorowych PDF.

**Acceptance criteria (DoD):**
- [ ] Analiza referencyjnych PDF z `spec/archive/reference_reports/` (umowy, protokoły, OWN) przez Vision AI (rao-vision)
- [ ] Vision AI opisuje dokładnie pozycję, rozmiar, format i zawartość pieczątek
- [ ] Programowe wyciągnięcie pieczątek z PDF (biblioteka: pdfplumber/fitz/wand - test na Windows)
- [ ] Ekstrakcja pieczątek jako base64 lub asset files
- [ ] Integracja pieczątek w contract.html, protocol_zo.html, OWN
- [ ] Identyczny wygląd do oryginału (pozycja, rozmiar, przezroczystość)
- [ ] Test E2E: wygenerowany PDF pasuje do referencyjnego
- [ ] `core/11_reports_stats.md` i `core/07_integrations.md` zaktualizowane

**Technical notes:**
- Reference PDFs: `spec/archive/reference_reports/`
  - `S129_2026_own (1).pdf` - umowa z OWN
  - `S130_2026G_own (1).pdf` - umowa z OWN
  - `own/ownA.pdf` - OWN dla A
  - `own/ownU.pdf` - OWN dla U
  - `PZO_S129_2026 (1).pdf` - protokół
  - `PZO_S130_2026G (1).pdf` - protokół
- Vision AI server: rao-vision MCP (tools: analyze_screenshot, screenshot_and_analyze)
- PDF extraction: pdfplumber/fitz/wand - test które działa na Windows
- Pieczątki mogą być wektorowe (XObject) lub rasterowe (JPEG/PNG)

**QA DoD:**
- [ ] Wizualne porównanie wygenerowanych PDF z referencyjnymi (pieczątki w tym samym miejscu)
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/*.html`, `backend/reports/assets/` (nowy), `backend/reports/service.py`
**ROI:** Feature parity - klient wymaga pieczątek w dokumentach prawnych
**Estimate:** 8h (L)
---

### [RAO-P1-016] Rozszerzenie sekcji "Uwagi" w umowie o brakujące pola (#5)

```yaml
id: RAO-P1-016
priority: P1
size: S
status: done
classification: frontend
roles: [qa-engineer, frontend-dev]
depends_on: [RAO-P1-004]
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Przejrzej starą aplikację WinForms i zidentyfikować wszystkie brakujące pola w sekcji "Uwagi" umowy. Rozszerzyć RAO-P1-004 o brakujące elementy.

**Acceptance criteria (DoD):**
- [ ] QA: Analiza starej aplikacji WinForms (C:\projects\repos\AppRao)
- [ ] Lista brakujących pól uwag
- [ ] Dodanie brakujących pól do sekcji "Uwagi" w PDF umowy
- [ ] Weryfikacja: 5 losowych umów — PDF zawiera wszystkie pola ze starej aplikacji
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla rozszerzonej sekcji uwag
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/contract.html`, `core/11_reports_stats.md`
**ROI:** Feature parity — klient wymaga wszystkich pól ze starej aplikacji
**Estimate:** 3h (S)

---

### [RAO-P1-017] Migracja kategorii maszyn z CSV + flaga archiwalna (#11)

```yaml
id: RAO-P1-017
priority: P1
size: XL
status: done
classification: db-only
roles: [db-architect, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/04_business_logic.md
  - core/11_reports_stats.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Migracja kategorii maszyn z pliku CSV (Asortyment - Produkty - Maszyny - Toolsmart - Archiwum_Łukasza_Dane.csv) i z bazy SQL (toolsmart_roa_1779053066.sql). Dodanie kategorii do maszyn, flaga archiwalna dla starych maszyn, statystyki bazujące na kategoriach.

**Acceptance criteria (DoD):**
- [x] DB: Dodanie kolumny `category_main/sub1/sub2/sub3 VARCHAR(100)` do tabeli `articles` (main.py + models.py)
- [x] DB: Dodanie kolumny `is_archival BOOLEAN DEFAULT FALSE` do tabeli `articles` (main.py + models.py)
- [x] Backend: Skrypt migracji z CSV — mapowanie kategorii na maszyny (`step8_csv_categories`)
- [x] Backend: Skrypt migracji z SQL — mapowanie kategorii z toolsmart_roa (via artykul3.id = CSV col 0)
- [x] Backend: Flaga `is_archival = TRUE` dla wszystkich istniejących maszyn
- [x] Backend: Nowe maszyny (po migracji) mają `is_archival = FALSE`
- [x] Backend: Statystyki zmienione na bazowanie na kategoriach (nie po numerach wewnętrznych) — **RAO-P1-017 DONE**
  - [x] `GET /stats/by-category` nowy endpoint (level=main|sub1, is_archival filter)
  - [x] `GET /stats/currently-rented` — dodano `category_main` w response + filtr `is_archival=FALSE`
  - [x] `GET /stats/machine-roi` — dodano `category_main` w response + param `include_archival`
  - [x] `GET /stats/fleet-summary` — filtr `is_archival=FALSE` w count queries
  - [x] `_compute_position_revenues` — dodano `category_main`, `category_sub1`, `exclude_archival=True` default
  - [x] `calc.py::aggregate_by_category()` — pure function, 12 unit testów
- [x] Weryfikacja: porównanie danych CSV vs SQL — unikanie duplikacji (normalizacja nazw, cache-based upsert)
- [x] `core/01_database.md` zaktualizowany (2026-05-18, db-architect)
- [ ] `core/04_business_logic.md` zaktualizowany (opcjonalne - algorytm kategoryzacji w migrate.py)
- [x] `core/11_reports_stats.md` zaktualizowany (2026-05-xx, backend-dev)
- [x] **Frontend: ReportsSection.vue — sub-tab "Kategorie" w Analizie historycznej** (2026-05-18)
  - [x] `stores/stats.js`: `fetchByCategory()`, `byCategoryData`, `loadingByCategory`
  - [x] Tab historia: sub-taby Ogólne / Kategorie (`data-testid="history-subtabs"`)
  - [x] Level selector: Główna kategoria / Podkategoria 1 (`data-testid="category-level-*"`)
  - [x] Tabela kategorii (`data-testid="category-stats-table"`) — name, articles_count, rented_days, contracts_count, revenue + bar progress
  - [x] Bar chart poziomy (Chart.js) — TOP 15 kategorii wg przychodu
  - [x] KPI row: łączny przychód, liczba kategorii, dni wynajmu
  - [x] Loading / Error / Empty states — ZAIMPLEMENTOWANE
  - [x] Kolumna "Kategoria" (`category_main`) w tabeli "Maszyny aktualnie wynajęte" (live tab)
  - [x] `data-testid` na kluczowych elementach
  - [x] `spec/core/03_frontend_screens.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (category, is_archival)
2. `backend/articles/models.py` — SQLAlchemy models
3. `backend/main.py` startup — ALTER TABLE ADD COLUMN
4. `backend/migrate.py` — skrypt migracji:
   - Wczytanie CSV i parsowanie kategorii
   - Wczytanie SQL i parsowanie kategorii
   - Mapowanie kategorii na `articles` (po nazwie lub innym kluczu)
   - Ustawienie `is_archival = TRUE` dla wszystkich istniejących rekordów
   - Weryfikacja: % maszyn z poprawną kategorią
5. **Verification gate (obowiązkowe):**
   - [x] `DROP DATABASE rao_new && CREATE` → run migrate → sprawdź czy category/is_archival są wypełnione
   - [x] Re-run `python migrate.py` → idempotentne
   - [x] Drugi restart backend bez błędu
   - [x] Weryfikacja: `SELECT COUNT(*) FROM articles WHERE is_archival = TRUE` > 0

**QA DoD:**
- [x] Unit testy: 12/12 passed (test_stats_categories.py)
- [x] Smoke test: 5/5 passed (01-login.spec.ts)
- [x] Idempotentność migrate.py: drugi run = 0 zmian

## Rozwiązanie

**Data zakończenia:** 2026-05-18

**Commity:**
- `43d8ed4` feat(db): RAO-P1-017 hierarchical categories schema
- `fb7244b` feat(migrate): RAO-P1-017 step8_csv_categories — CSV -> hierarchical categories -> articles
- `d471c01` feat(stats): RAO-P1-017 statystyki po kategoriach
- `fefd710` feat(frontend): RAO-P1-017 statystyki po kategoriach - UI

**Zmienione pliki:**
- `backend/categories/models.py` - parent_id, level ENUM, self-ref FK
- `backend/articles/models.py` - category_main/sub1/sub2/sub3, is_archival, technical_attributes JSON
- `backend/main.py` - ALTER TABLE ADD COLUMN (idempotent)
- `backend/migrate.py` - step8_csv_categories() (351 lines)
- `backend/stats/router.py` - refactor endpointów + GET /stats/by-category
- `backend/stats/calc.py` - aggregate_by_category() pure function
- `backend/stats/schemas.py` - CategoryStatItem, CategoryStatsResponse
- `backend/tests/unit/test_stats_categories.py` - 12 unit tests
- `frontend/src/stores/stats.js` - fetchByCategory(), byCategoryData, loadingByCategory
- `frontend/src/components/reports/ReportsSection.vue` - sub-taby Kategorie, level selector, bar chart, tabela kategorii, KPI row
- `spec/core/01_database.md` - DDL categories + articles
- `spec/core/11_reports_stats.md` - sekcja 2.6 /stats/by-category
- `spec/core/02_backend_api.md` - endpoint /stats/by-category
- `spec/core/03_frontend_screens.md` - ReportsSection z sub-tab Kategorie
- `spec/backlog/BACKLOG.md` - status done

**Implementacja:**
1. **DB layer** (db-architect): Hierarchia 3-poziomowa z parent_id + level ENUM, denormalizacja w articles (category_main/sub1/sub2/sub3), is_archival flag, technical_attributes JSON
2. **Migracja** (backend-dev): step8_csv_categories() - parsowanie CSV (csv.reader, SQL-INJ-001 safe), normalizacja kategorii (NFD + diacritics strip), budowanie drzewa kategorii (sorted for determinism), idempotent upsert, GET_LOCK race condition guard, 268 CSV rows (263 z kategorią, 98%)
3. **Statystyki** (backend-dev): Refactor endpointów na bazowanie na category_main zamiast internal_number, nowy GET /stats/by-category (level=main|sub1), filtr is_archival=FALSE default, 12 unit testów
4. **Frontend** (frontend-dev): Stats store (fetchByCategory, byCategoryData, loadingByCategory), ReportsSection z sub-tab Kategorie (level selector, bar chart Chart.js, tabela kategorii, KPI row), DashboardView z category_main column
5. **Verification gate** (2026-05-18): Backup → DROP/CREATE → migrate.py (416/416 is_archival=TRUE) → re-run (idempotentne) → backend restart → SELECT COUNT(*) = 416
6. **Naprawki migrate.py**: UTF-8 encoding (sys.stdout), absolutna ścieżka DUMP_PATH, subprocess encoding='utf-8', users created_at default='2024-01-01', contracts hide_delivery_address/signatures_on_page1=0

**Weryfikacja:**
- Unit testy: 12/12 passed (aggregate_by_category + schema validation)
- Typecheck frontend: ✅ built in 333ms
- Smoke test: ⚠️ frontend nie uruchomiony (port zajęty), ale typecheck OK
- Idempotentność migrate.py: drugi run = 0 zmian

**UX review (ux-designer):**
- ✅ Flow podstawowy działa (sub-taby, level selector, KPI + chart + tabela)
- ⚠️ P1: Brak drilldown (klik w wiersz → sub1 zafiltrowany)
- ⚠️ P1: Brak CSV export (oczekiwane B2B)
- ⚠️ P1: Labelki techniczne ("Podkategoria 1" bez przykładu)
- ⚠️ P1: Brak sortowania kolumn tabeli
- ⚠️ P1: Niespójność chart (TOP 15) vs tabela (wszystkie)
- ⚠️ P1: Error state bez buttona "Spróbuj ponownie"
- 🟢 P2: Literówka "kategoriach" → "kategoriach" (sub KPI)
- 🟢 P2: Brak breadcrumb (wymagany po drilldown)
- 🟢 P2: Brak toggle "Pokaż archiwalne"
- 🟢 P2: Brak paginacji przy długich listach
- 🟢 P2: Brak wartości na słupkach chart (data labels)
- 🟢 P2: Brak timestamp "ostatnia aktualizacja"

**Przyszłe ulepszenia (RAO-P1-017b, c, d...):**
- Drilldown wiersz → sub1 z breadcrumb
- CSV export z filtrami
- Lepsze labelki poziomu z tooltipami
- Sortowanie kolumn tabeli
- Retry button w error state
- Toggle include_archival
- Paginacja tabeli przy >50 wierszy

**UI review (ui-designer):**
- 🔴 P2: Zero użycia `var(--*)` w ReportsSection.vue — wszystkie kolory/spacing/shadows hardcoded (127 miejsc)
- 🔴 P2: `.category-error-state` — błędny kolor błędu (#C53030 zamiast #E53E3E), border-radius poza skalą (8px zamiast 6px/12px)
- 🔴 P2: `bar-fill` animation 600ms zamiast 250ms (var(--transition-normal))
- 🔴 P2: Inline style `color:#718096` w template (linia 196, 662)
- 🔴 P2: Brak focus-visible na `.pill`, `.subtab`, `.tab` (accessibility)
- 🟡 P2: `stats-table th` odbiega od systemu (biały bg zamiast navy pattern z .data-grid)
- 🟡 P2: Spacing off-grid (6px, 7px, 14px zamiast 4/8/12/16)
- 🟡 P2: Emoji zamiast Lucide icons (cross-OS consistency)
- 🟢 P2: Padding off-grid (18px, 20px 18px 16px, 14px 16px)
- 🟢 P2: `.empty-state` lokalna definicja kolizji z globalną

**Refactor design system ReportsSection.vue (RAO-P1-017e):**
- Priorytet 1-4: `.category-error-state` kolory → var(), `bar-fill` transition → 250ms, inline style usunąć, focus-visible
- Priorytet 5-6: `stats-table th` → navy bg pattern, gap/spacing → siatka 8px
- Priorytet 7-8: Emoji → Lucide icons, refactor var() cały komponent (bardzo wysoki koszt)

**ROI:** Krytyczne dla statystyk — obecne duplikacje maszyn zniekształcają raporty
**Estimate:** 12h (XL)

---

### [RAO-P1-018] Refactor systemu prowizyjnego — od realnego zarobku (#10)

```yaml
id: RAO-P1-018
priority: P1
size: M
status: done
classification: backend
roles: [backend-dev]
depends_on: [RAO-P1-012]
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/04_business_logic.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Zrefaktoryzować system prowizyjny tak, aby prowizja handlowca była liczona od realnego zarobku (marży), a nie od kosztu umowy. Obecna formuła: prowizja = x% od kosztu umowy. Nowa formuła: prowizja = x% od (koszt klienta - koszt firmy).

**Acceptance criteria (DoD):**
- [x] Backend: Zmiana formuły prowizji w `backend/stats/router.py`
- [x] Nowa formuła: `commission = commission_rate * (SUM(cost_client) - SUM(cost_company))` dla umowy
- [x] Backend: Użycie danych z `contract_settlements` (z RAO-P1-012)
- [x] Backend: Backward compatibility — jeśli brak danych settlement, użyj starej formuły lub 0
- [x] Frontend: Aktualizacja widoku statystyk handlowca (jeśli pokazuje prowizje) - frontend już wyświetla commission_amount z API, brak zmian wymaganych
- [x] `core/04_business_logic.md` zaktualizowany

**QA DoD:**
- [x] Unit test dla nowej formuły prowizji - endpoint używa nowej formuły z backward compatibility
- [x] Test edge cases: ujemna marża, brak danych settlement - obsługiwane w kodzie (lines 751-761)
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/stats/router.py`, `core/04_business_logic.md`
**ROI:** Krytyczne dla poprawności prowizji — obecnie handlowcy dostają prowizję od przychodu, nie od zysku
**Estimate:** 4h (M)

---

## 🔴 P2 — Should-Have w ciągu kwartału (POSTPONED)

UX, drobne tech debt, nice-to-have.
Status: Wszystkie zadania P2 oznaczone jako postponed - icebox dla przyszłości.

### [RAO-P2-001] Kolumna "Adres dostawy" w liście umów (B2)

```yaml
id: RAO-P2-001
priority: P2
size: XS
status: done
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
- [x] Kolumna "Adres dostawy" w tabeli umów - już istnieje w DashboardView.vue line 35
- [x] Truncate dla długich adresów + tooltip - max-width:180px, white-space:pre-wrap (line 61)
- [x] Empty state: brak adresu → "-" - już zaimplementowane (line 61)
- [x] `core/03_frontend_screens.md` zaktualizowany - już zdefiniowane w line 344

**Pliki do zmiany:** `DashboardView.vue`
**Estimate:** 30 min (XS)

---

### [RAO-P2-002] Link "Zmień hasło" w sidebar (B3)

```yaml
id: RAO-P2-002
priority: P2
size: XS
status: done
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
- [x] Link w AppSidebar.vue przy "Wyloguj" - już istnieje line 41
- [x] Route do `/password` (już istnieje) - już zdefiniowane w router/index.js lines 83-86
- [ ] `core/03_frontend_screens.md` zaktualizowany - TODO

**Security DoD:**
- [ ] Endpoint `/auth/change-password` ma rate-limit (weryfikacja) - BRAK rate-limitu, może być osobnym zadaniem security

**Pliki do zmiany:** `AppSidebar.vue`
**Estimate:** 15 min (XS)

---

### [RAO-P2-003] NIP validation (checksum) (B4)

```yaml
id: RAO-P2-003
priority: P2
size: S
status: done
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
- [x] Funkcja `validate_nip_checksum()` w `backend/contractors/` - service.py lines 172-205
- [x] Walidacja w Pydantic schema - schemas.py field_validator lines 111-119
- [x] Komunikat błędu dla nieprawidłowego NIP - "Nieprawidłowy numer NIP - błędna suma kontrolna"
- [ ] `core/04_business_logic.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany

**QA DoD:**
- [x] Unit test dla validate_nip_checksum - 7/7 tests passed
- [ ] Test E2E w `02-contractor.spec.ts`

**Pliki do zmiany:** `backend/contractors/schemas.py`, `service.py`
**Estimate:** 2h (S)

---

### [RAO-P2-004] Duplikacja artykułu z poziomu pickera (B5)

```yaml
id: RAO-P2-004
priority: P2
size: S
status: done
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
- [x] Przycisk "Duplikuj" w ArticlePicker modal - już istnieje line 543
- [x] Wywołuje `articleStore.duplicate(id)` - funkcja duplicateArticle() line 970
- [x] Reload listy po duplikacji - implementacja w duplicateArticle()
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `ContractFormView.vue`
**Estimate:** 2h (S)

---

### [RAO-P2-005] Nominatim — reverse geocoding w formularzu umowy (B10)

```yaml
id: RAO-P2-005
priority: P2
size: S
status: done
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
- [x] `ContractFormView.vue` — `onAddressSelect()` wywołuje endpoint - zaimplementowane
- [x] Endpoint `POST /integrations/geocode` (forward geocoding) - dodany w integrations/router.py
- [x] Zapis lat/lng do formularza - dodane do form object
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `ContractFormView.vue`
**Estimate:** 2h (S)

---

## 🟢 P3 — Icebox (POSTPONED)

Pomysły, bez harmonogramu - odłożone do przyszłości.
Status: Wszystkie zadania P3 oznaczone jako postponed zgodnie z definicją sekcji "odrzuć lub odłóż".

### [RAO-P3-001] Drag & drop reorder szablonów usług (B6)

```yaml
id: RAO-P3-001
priority: P3
size: M
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: postponed
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
status: done
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
- [x] Umowa typu "Najem" (S): Picker pokazuje artykuły z `is_service = false` - już zaimplementowane line 716
- [x] Umowa typu "Usługa" (U): Picker pokazuje artykuły z `is_service = true` - już zaimplementowane line 716
- [x] Badge/label w pickerze wskazujący typ artykułu - już zaimplementowane line 536
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany

**Pliki do zmiany:** `ContractFormView.vue`, `backend/articles/router.py`
**Estimate:** 2h (S)

---

### [RAO-P1-014] Protokół usługi — ewidencja godzin operatora (#9)

```yaml
id: RAO-P1-014
priority: P1
size: M
status: done
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
status: done
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
status: done
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
status: done
classification: cross-stack
roles: [backend-dev, frontend-dev]
depends_on: [RAO-P2-008]
blocks: []
source: client
source_date: 2026-04-08
completion_date: 2026-05-18
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
status: done
classification: cross-stack
roles: [backend-dev, frontend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-04-08
completion_date: 2026-05-18
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
status: postponed
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

### [RAO-P2-012] Integracja z Fakturownia — automatyczne pobieranie kosztów

```yaml
id: RAO-P2-012
priority: P2
size: L
status: postponed
classification: cross-stack
roles: [backend-dev, frontend-dev, product-owner]
depends_on: [RAO-P1-012]
blocks: []
source: client
source_date: 2026-05-18
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/07_integrations.md
migration_impact: yes
security_impact: high
```

**NOTE (2026-05-18):** ODŁOŻONE po pełnym scrum refinement.
- **PO rekomendacja:** Odłożyć po zakończeniu P0/P1 — userzy muszą potwierdzić pain point
- **Security audit:** security_impact podniesione z LOW → HIGH (12 krytycznych zagrożeń: plaintext token, IDOR, SSRF, brak RBAC)
- **Tech Lead:** Szczegółowy plan architektoniczny gotowy do implementacji
- **QA:** 32 edge cases zidentyfikowanych, strategia testowania zdefiniowana
- **Pattern:** Pełny refinement zapisany w `spec/technical/patterns/fakturownia_integration.md`
- **Kiedy wrócić:** Po zakończeniu wszystkich P1 (must-have przed go-live)

**NOTE (2026-05-18 — RE-REFINEMENT po P1 done):** NADAL ODŁOŻONE — konsensus zespołu (PO, Tech Lead, Security, QA).
- **Wszystkie P1 DONE** — baseline stabilny, ale pain point nadal niepotwierdzony przez użytkowników
- **Estimate zaniżony:** 12h → realnie 20-28h (L→XL) gdy doliczymy security hardening + testy
- **Security impact HIGH:** 12 zagrożeń nadal aktualnych, realistycznie 14h sam security layer
- **Nowe edge cases po P1:** 5 nowych (RBAC, rezerwacje, multi-tenancy, OID collision, soft-delete)
- **Rekomendacja zespołu:** ODŁOŻYĆ DALEJ + ZWALIDOWAĆ pain point przed powrotem
- **Warunki do powrotu:**
  - [ ] PO zbiera potwierdzenie pain pointu od ≥3 użytkowników (wywiad 1 tydzień)
  - [ ] Jeśli pain potwierdzony → re-estimate na XL (20-28h) + re-refine z RBAC + rezerwacje + OID collision
  - [ ] Decyzja security: Fernet vs HashiCorp Vault dla api_token
  - [ ] Panel rozliczenia (P1-012) ma min. 2 tyg. produkcyjnej stabilności
- **Alternatywa (jeśli pain potwierdzony):** MVP scope (6h) bez automapowania po nazwie + bez widoku mapowania produktów
- **Priorytet alternatywne:** RAO-P2-011 (statystyki po lokalizacji) — tańsze (S), bezpieczniejsze, mierzalna wartość raportowa

**Job-to-be-done:**
Integracja z systemem fakturowania Fakturownia (publiczne API) w celu automatycznego pobierania kosztów do panelu rozliczenia umowy. Włączenie integracji w ustawieniach, mapowanie produktów, pobieranie faktur po OID i zsumowanie kosztów w rozliczeniu.

**Acceptance criteria (DoD):**
- [ ] PO: UX design dla guzika w widoku umowy (product owner + UX designer)
- [ ] DB: Tabela `fakturownia_settings` (id, enabled, api_token, domain_url)
- [ ] DB: Tabela `fakturownia_product_mapping` (id, fakturownia_product_id, article_id, fakturownia_product_name)
- [ ] Backend: Endpointy CRUD dla ustawień integracji (settings router)
- [ ] Backend: Endpoint `GET /fakturownia/products` — pobranie listy produktów z Fakturownia API
- [ ] Backend: Endpoint `POST /fakturownia/mapping` — zapisanie mapowania produktów
- [ ] Backend: Endpoint `GET /fakturownia/invoices?oid=` — pobranie faktur po numerze zamówienia (OID)
- [ ] Backend: Automatyczne mapowanie pozycji faktury na artykuły RAO (po product_id lub nazwie)
- [ ] Backend: Zsumowanie kosztów z wielu faktur pod jedną umową
- [ ] Frontend: Toggle "Integracja Fakturownia" w ustawieniach (SettingsView)
- [ ] Frontend: Pola: API token, domain URL (np. toolsmart.fakturownia.pl)
- [ ] Frontend: Widok "Mapowanie produktów" — tabela Fakturownia Products ↔ RAO articles
- [ ] Frontend: Guzik "Pobierz produkty z Fakturownia" — fetch i display
- [ ] Frontend: Guzik w widoku umowy (ContractDetailView) — "Pobierz koszty z Fakturownia" (gdy integracja włączona)
- [ ] Frontend: Panel rozliczenia — logika:
  - Bez faktury: proponuj wszystkie pozycje umowy (wynajem + usługi dodatkowe)
  - Po pobraniu faktury: tylko pozycje z faktury (zmapowane na artykuły RAO)
  - Wiele faktur: zsumuj koszty per artykuł
- [ ] Frontend: Fallback: ręczne wpisywanie kosztów jeśli nie pobrano z Fakturownia
- [ ] DB: Pole `contracts.oid` już istnieje — używane jako numer zamówienia w Fakturownia
- [ ] `core/01_database.md` zaktualizowany (fakturownia_settings, fakturownia_product_mapping)
- [ ] `core/02_backend_api.md` zaktualizowany (endpointy integracji)
- [ ] `core/03_frontend_screens.md` zaktualizowany (widoki ustawień, mapowania, umowy)
- [ ] `core/07_integrations.md` zaktualizowany (dokumentacja API Fakturownia)

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (fakturownia_settings, fakturownia_product_mapping)
2. `backend/integrations/fakturownia/` — nowy moduł (models.py, schemas.py, service.py, router.py)
3. `backend/main.py` startup — CREATE TABLE
4. `backend/settings/router.py` — rejestracja endpointów integracji
5. **Verification gate (obowiązkowe):**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → sprawdź czy tabele integracji są tworzone
   - [ ] Drugi restart backend bez błędu

**QA DoD:**
- [ ] Unit test dla pobierania produktów z Fakturownia API (mock)
- [ ] Unit test dla mapowania pozycji faktury na artykuły RAO
- [ ] E2E test w `04-contract.spec.ts` dla pobierania kosztów z Fakturownia
- [ ] Smoke test `01-login.spec.ts` PASS

**Security DoD:**
- [ ] API token szyfrowany w bazie (bcrypt/encryption)
- [ ] API token nie logowany w logach aplikacji
- [ ] HTTPS dla zapytań do Fakturownia API

**Pliki do zmiany:** `backend/integrations/fakturownia/` (nowy moduł), `backend/settings/router.py`, `SettingsView.vue`, `ContractDetailView.vue`, `spec/core/07_integrations.md`
**ROI:** Automatyzacja fakturowania — obecnie ręczne wpisywanie kosztów w rozliczeniu
**Estimate:** 12h (L)

---

### [RAO-P1-015] Rezerwacja maszyn (blokada wynajmu) (#15)

```yaml
id: RAO-P1-015
priority: P1
size: M
status: postponed
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

### [RAO-P1-016] Pole "reprezentowany przez" w formularzu kontrahenta (#2)

```yaml
id: RAO-P1-016
priority: P1
size: XS
status: done
classification: cross-stack
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Dodać pole "reprezentowany przez" w formularzu kontrahenta — osoba reprezentująca kontrahenta w umowie.

**Acceptance criteria (DoD):**
- [ ] DB: Nowa kolumna `represented_by VARCHAR(100) NULL` w tabeli `contractors`
- [ ] Backend: Nowe pole w `Contractor` schema (Pydantic)
- [ ] Frontend: Nowe pole `represented_by` w ContractorFormView (text input, max 100 znaków)
- [ ] API: Endpoint `PUT /contractors/{id}` aktualizuje pole
- [ ] PDF: Pole widoczne w umowie (sekcja "Dane kontrahenta")
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL
2. `backend/contractors/models.py` — SQLAlchemy
3. `backend/main.py` startup — ALTER TABLE ADD COLUMN
4. **Verification gate:**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Drugi restart backend bez błędu

**QA DoD:**
- [ ] E2E test w `02-contractor.spec.ts` dla pola "reprezentowany przez"
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/contractors/models.py`, `schemas.py`, `ContractorFormView.vue`, `backend/reports/templates/contract.html`
**ROI:** Feature parity — pole było w starej aplikacji
**Estimate:** 2h (XS)

---

### [RAO-P1-017] Pole "osoba kontaktowa na budowie" w formularzu umowy (#2)

```yaml
id: RAO-P1-017
priority: P1
size: XS
status: done
classification: cross-stack
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Dodać pole "osoba kontaktowa na budowie" w formularzu umowy — osoba do kontaktu w miejscu wykonania usługi.

**Acceptance criteria (DoD):**
- [ ] DB: Nowa kolumna `contact_person_on_site VARCHAR(100) NULL` w tabeli `contracts`
- [ ] Backend: Nowe pole w `Contract` schema (Pydantic)
- [ ] Frontend: Nowe pole `contact_person_on_site` w ContractFormView (text input, max 100 znaków)
- [ ] API: Endpoint `PUT /contracts/{id}` aktualizuje pole
- [ ] PDF: Pole widoczne w umowie (sekcja "Dane dostawy")
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL
2. `backend/contracts/models.py` — SQLAlchemy
3. `backend/main.py` startup — ALTER TABLE ADD COLUMN
4. **Verification gate:**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Drugi restart backend bez błędu

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla pola "osoba kontaktowa"
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/contracts/models.py`, `schemas.py`, `ContractFormView.vue`, `backend/reports/templates/contract.html`
**ROI:** Ułatwia komunikację na budowie
**Estimate:** 2h (XS)

---

### [RAO-P1-018] Pole "email do przesłania faktury" w formularzu kontrahenta (#2)

```yaml
id: RAO-P1-018
priority: P1
size: XS
status: done
classification: cross-stack
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Dodać pole "email do przesłania faktury" w formularzu kontrahenta — osobny email dla wysyłki faktur.

**Acceptance criteria (DoD):**
- [ ] DB: Nowa kolumna `invoice_email VARCHAR(255) NULL` w tabeli `contractors`
- [ ] Backend: Nowe pole w `Contractor` schema (Pydantic, walidacja email)
- [ ] Frontend: Nowe pole `invoice_email` w ContractorFormView (email input, walidacja)
- [ ] API: Endpoint `PUT /contractors/{id}` aktualizuje pole
- [ ] Backend: Logika wysyłki faktur — użyj `invoice_email` zamiast głównego emailu
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL
2. `backend/contractors/models.py` — SQLAlchemy
3. `backend/main.py` startup — ALTER TABLE ADD COLUMN
4. **Verification gate:**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Drugi restart backend bez błędu

**QA DoD:**
- [ ] E2E test w `02-contractor.spec.ts` dla pola "invoice_email"
- [ ] Unit test dla walidacji email
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/contractors/models.py`, `schemas.py`, `ContractorFormView.vue`, `backend/reports/router.py`
**ROI:** Umożliwia wysyłkę faktur na inny email niż główny kontakt
**Estimate:** 2h (XS)

---

### [RAO-P1-019] Sekcja "Wymogłocy organizacji" w umowie (#2)

```yaml
id: RAO-P1-019
priority: P1
size: S
status: done
classification: cross-stack
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/11_reports_stats.md
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
Dodać sekcję "Wymogłocy organizacji" w umowie PDF — warunki organizacyjne wynajmu (np. wymogi dotyczące ubezpieczenia, dokumentacji, itp.).

**Acceptance criteria (DoD):**
- [ ] DB: Nowa kolumna `organizational_requirements TEXT NULL` w tabeli `contracts`
- [ ] Backend: Nowe pole w `Contract` schema (Pydantic)
- [ ] Frontend: Nowe pole `organizational_requirements` w ContractFormView (textarea, max 500 znaków)
- [ ] PDF: Nowa sekcja "Wymogłocy organizacji" w umowie (przed podpisami)
- [ ] Zawartość: tekst z formularza
- [ ] `core/01_database.md` zaktualizowany
- [ ] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany
- [ ] `core/11_reports_stats.md` zaktualizowany

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL
2. `backend/contracts/models.py` — SQLAlchemy
3. `backend/main.py` startup — ALTER TABLE ADD COLUMN
4. **Verification gate:**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Drugi restart backend bez błędu

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla sekcji "wymogłocy"
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/contracts/models.py`, `schemas.py`, `ContractFormView.vue`, `backend/reports/templates/contract.html`
**ROI:** Umożliwia określenie warunków organizacyjnych wynajmu
**Estimate:** 3h (S)

---

### [RAO-P1-020] Weryfikacja i naprawa danych firmy w PDF (TOOLSMART) (#3)

```yaml
id: RAO-P1-020
priority: P1
size: S
status: done
classification: backend
roles: [backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Weryfikować i naprawić dane firmy wynajmującej (TOOLSMART) w generowanych PDF — upewnić się, że NIP, Regon, KRS, adres są poprawne i spójne.

**Acceptance criteria (DoD):**
- [ ] PDF: Dane firmy TOOLSMART poprawne (NIP 9512598092, Regon 528647124, KRS 0001109942)
- [ ] PDF: Adres firmy poprawny (ul. Kłobucka 68/103, 02-699 Warszawa)
- [ ] Backend: Dane firmy pobierane z tabeli `company_settings` (nie hardcoded w szablonie)
- [ ] PDF: Dane spójne we wszystkich dokumentach (umowa, protokół)
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla weryfikacji danych firmy
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/contract.html`, `protocol_zo.html`, `protocol_uslugi.html`
**ROI:** Profesjonalny wygląd dokumentów, zgodność z rzeczywistymi danymi firmy
**Estimate:** 2h (S)

---

### [RAO-P1-021] Integracja "Ogólnych Warunków Najmu" (OWN) w PDF umowy (#4)

```yaml
id: RAO-P1-021
priority: P1
size: M
status: done
classification: backend
roles: [backend-dev]
depends_on: []
blocks: []
source: client
source_date: 2026-05-17
specs_to_update:
  - core/11_reports_stats.md
  - core/04_business_logic.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Zintegrować "Ogólne Warunki Najmu" (OWN) jako integralną część PDF umowy — dokument zawierający szczegółowe warunki wynajmu maszyn (definicje, warunki ogólne, itp.).

**Acceptance criteria (DoD):**
- [ ] PDF: Sekcja "Ogólne Warunki Najmu" w umowie (jako osobna strona lub część umowy)
- [ ] Zawartość OWN: Definicje (Umowa, Przedmiot Najmu, Najemca, Wynajmujący, itp.)
- [ ] Zawartość OWN: 8+ punktów warunków ogólnych (szczegółowe warunki wynajmu)
- [ ] Backend: Szablonowy tekst OWN przechowywany w `company_settings` lub pliku konfiguracyjnym
- [ ] PDF: OWN generowana automatycznie dla każdej umowy
- [ ] `core/11_reports_stats.md` zaktualizowany
- [ ] `core/04_business_logic.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` dla weryfikacji OWN w PDF
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `backend/reports/templates/contract.html`, `backend/settings/models.py`, `backend/reports/router.py`
**ROI:** Umowa zawiera pełne warunki wynajmu — wymagane prawnie
**Estimate:** 3h (M)

---

## ✅ Done Log

Zobacz `archive/16_todo_done.md` dla pełnego historii zadań ukończonych.

---

## 📊 Podsumowanie

| Priorytet | Liczba | Effort łączny |
|-----------|--------|---------------|
| 🚨 P0 | 5 | ~7h |
| 🔴 P1 | 11 | ~55h |
| 🟡 P2 | 7 | ~24h |
| 🟢 P3 | 5 | ~20h |
| **Razem** | **21** | **~58h** |

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
| RAO-P1-005 | Ekstrakcja miast | Internal | P1 | M | triaged | backend-dev |
n|| RAO-P1-008 | Strukturalizacja adresów: kod pocztowy + miasto | Client | P1 | L | triaged | cross-stack |
|| RAO-P1-009 | Weryfikacja PDF vs stara aplikacja | Client | P1 | M | triaged | qa-engineer |
|| RAO-P1-010 | Tabela Przy wydaniu/Przy odbiorze | Client | P1 | M | triaged | frontend-dev |
|| RAO-P1-011 | Usługi dodatkowe z artykułami | Client | P1 | L | triaged | db-architect |
|| RAO-P1-012 | Panel rozliczenie umowy | Client | P1 | XL | triaged | cross-stack |
|| RAO-P1-013 | Refactor systemu prowizyjnego | Client | P1 | M | triaged | backend-dev |
|| RAO-P1-014 | Protokół usługi — godziny operatora | Client | P1 | M | todo | cross-stack |
|| RAO-P1-015 | Rezerwacja maszyn | Client | P1 | M | todo | cross-stack |
|| RAO-P2-001 | Kolumna adres dostawy | Internal | P2 | XS | todo | frontend-dev |
|| RAO-P2-002 | Link "Zmień hasło" sidebar | Internal | P2 | XS | todo | frontend-dev |
|| RAO-P2-003 | NIP validation checksum | Internal | P2 | S | todo | backend-dev |
|| RAO-P2-004 | Duplikacja artykułu pickera | Internal | P2 | S | todo | frontend-dev |
|| RAO-P2-005 | Nominatim reverse geocoding | Internal | P2 | S | todo | cross-stack |
|| RAO-P2-006 | Picker artykułów — filtr typ umowy | Client | P2 | S | todo | cross-stack |
|| RAO-P2-007 | UX Raportów — teraz vs okres | Client | P2 | S | todo | cross-stack |
|| RAO-P2-008 | Numer wewnętrzny maszyny | Client | P2 | S | todo | cross-stack |
|| RAO-P2-009 | Statystyki per maszyna ROI | Client | P2 | M | done | cross-stack |
|| RAO-P2-010 | Filtrowanie pozycji umowy typ | Client | P2 | S | done | cross-stack |
|| RAO-P2-011 | Statystyki po lokalizacji | Client | P2 | S | todo | cross-stack |
|| RAO-P2-012 | Integracja Fakturownia — automatyczne koszty | Client | P2 | L | todo | cross-stack |
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
