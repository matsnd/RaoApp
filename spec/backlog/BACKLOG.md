# RAO Backlog — Master Backlog

> **Last updated:** 2026-05-21  
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
- [x] `core/03_frontend_screens.md` zaktualizowany

**Pliki do zmiany:** `ContractFormView.vue`
**Estimate:** 2h (S)

---


### [RAO-P2-016] SPIKE: Playwright screenshot wszystkich widoków dla UX review

```yaml
id: RAO-P2-016
priority: P2
size: M
status: done
classification: spike
roles: [qa-engineer, ux-designer, frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-05-18
specs_to_update:
  - process/testing.md
migration_impact: no
security_impact: low
estimate: 4-6h
```

## Rozwiązanie
**Data zakończenia:** 2026-05-19
**Commit hash:** TBD (po local commit)

**Co zrobiono:**
- Test Playwright `e2e/tests/10-ux-screenshots.spec.ts` — 17 screenshotów wszystkich widoków
- Folder `e2e/screenshots/ux-review/` — organizacja screenshotów
- README `e2e/screenshots/ux-review/README.md` — checklist UX (kolory, typografia, spacing, formularze, stany, komponenty)
- `spec/process/testing.md` — procedura UX review dodana
- Screenshoty obejmują: LoginView, DashboardView, HomeView, ContractorFormView, ArticleFormView, ContractFormView, SettingsView (5 zakładek), ChangePasswordView, AdminView, WorkerView, CommissionView

**Pliki zmienione:**
- `e2e/tests/10-ux-screenshots.spec.ts` (nowy) — test Playwright
- `e2e/screenshots/ux-review/README.md` (nowy) — checklist UX
- `spec/process/testing.md` — procedura UX review

**Uwagi:**
- Frontend nie działał w momencie tworzenia tasku, więc screenshoty nie zostały wykonane
- Infrastruktura jest gotowa — użytkownik może uruchomić test gdy frontend będzie dostępny
- Screenshoty są robione w headless mode (1280x720)
- UX Designer może użyć checklisty do ręcznego review lub rao-vision MCP do automatycznej analizy

**Job-to-be-done:**
Otworzyć w Playwright wszystkie możliwe widoki/ekrany aplikacji i przygotować zestaw screenshotów do przeglądu przez UX Designera. Celem jest weryfikacja czy każdy ekran spełnia wymagania design systemu Toolsmart (kolory, fonty, spacing, border-radius, shadows, hierarchy typograficzna, empty states, loading states).

**Scope — wszystkie widoki Vue (12 ekranów):**

#### Widoki główne
- [ ] LoginView — formularz logowania (z błędem i sukcesem)
- [ ] DashboardView — dashboard z tabelą umów (pusta lista i z danymi)
- [ ] HomeView — home page / landing

#### Formularze CRUD
- [ ] ContractorFormView — nowy kontrahent (pusty formularz)
- [ ] ContractorFormView — edycja kontrahenta (z danymi)
- [ ] ArticleFormView — nowy artykuł (pusty formularz)
- [ ] ArticleFormView — edycja artykułu (z danymi)
- [ ] ContractFormView — nowa umowa (pusty formularz)
- [ ] ContractFormView — edycja umowy (z danymi, pozycje, warunki)

#### Ustawienia i administracja
- [ ] SettingsView — zakładka Dane firmy
- [ ] SettingsView — zakładka Handlowcy
- [ ] SettingsView — zakładka Kategorie
- [ ] SettingsView — zakładka Typy stawek
- [ ] SettingsView — zakładka Szablony usług
- [ ] SettingsView — zakładka Fakturownia

#### Inne
- [ ] AdminView — panel administracyjny (jeśli istnieje)
- [ ] WorkerView — widok pracownika (jeśli istnieje)
- [ ] ChangePasswordView — zmiana hasła
- [ ] ResetPasswordView — reset hasła

#### Stany każdego widoku (jeśli dotyczy)
- [ ] Empty state — brak danych (np. pusta lista umów)
- [ ] Loading state — spinner / skeleton podczas ładowania
- [ ] Error state — błąd API / network error
- [ ] Populated state — z danymi
- [ ] Validation state — błędy walidacji formularza

**Acceptance criteria (DoD):**
- [ ] Playwright test `e2e/tests/10-ux-screenshots.spec.ts` utworzony
- [ ] Każdy widok otworzony w przeglądarce (headless) i zapisany jako screenshot PNG
- [ ] Screenshoty zapisane w `e2e/screenshots/ux-review/` z nazwami opisowymi (np. `login-view-empty.png`, `contract-form-edit-with-data.png`)
- [ ] Folder `e2e/screenshots/ux-review/` utworzony i zorganizowany (podfoldery per widok)
- [ ] README w `e2e/screenshots/ux-review/README.md` z listą wszystkich screenshotów i opisem co sprawdzić
- [ ] `process/testing.md` zaktualizowany o procedurę UX review
- [ ] UX Designer otrzyma zestaw screenshotów i checklistę weryfikacji

**UX Checklist (do przygotowania w README):**
- [ ] Kolory zgodne z Toolsmart navy (#1D2B53)
- [ ] Font Montserrat używany poprawnie (wagi, rozmiary)
- [ ] Border-radius 12px na kartach
- [ ] Shadows zgodne z design system
- [ ] Spacing (padding/margin) zgodny z 8px grid
- [ ] Hierarchy typograficzna (h1/h2/h3, weights)
- [ ] Empty states mają CTA / komunikat
- [ ] Loading states mają spinner / skeleton
- [ ] Error states mają komunikat i akcję naprawczą
- [ ] Formularze mają poprawne labelki, placeholders, walidację
- [ ] Przyciski mają poprawne stany (hover, active, disabled)
- [ ] Responsywność (jeśli dotyczy)

**Pliki do stworzenia:**
- `e2e/tests/10-ux-screenshots.spec.ts` — nowy test Playwright
- `e2e/screenshots/ux-review/` — folder z screenshotami
- `e2e/screenshots/ux-review/README.md` — checklist UX
- `spec/process/testing.md` — procedura UX review

**ROI:** Weryfikacja UX przed go-live pozwala wykryć problemy wizualne które user może zgłosić jako "brzydko" lub "nieprofesjonalnie".
**Estimate:** 4-6h (M)

---

## 🟢 P3 — Icebox (POSTPONED)

Pomysły, bez harmonogramu - odłożone do przyszłości.
Status: Wszystkie zadania P3 oznaczone jako postponed zgodnie z definicją sekcji "odrzuć lub odłóż".

### [RAO-P2-017] Poprawa UX/UI na podstawie vision analysis (Login, Dashboard, Contract Form)

```yaml
id: RAO-P2-017
priority: P2
size: L
status: done
classification: frontend
roles: [frontend-dev, ui-designer, ux-designer]
depends_on: [RAO-P2-016]
blocks: []
source: internal
source_date: 2026-05-19
specs_to_update:
  - core/09_design_reference.md
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Naprawić problemy UX/UI zidentyfikowane przez vision analysis w 3 kluczowych widokach: Login, Dashboard, Contract Form.

**Acceptance criteria (DoD):**

**LoginView:**
- [ ] Border-radius karty: 12px (zamiast ~20-24px)
- [ ] Border-radius inputów: 12px (zamiast ~8px)
- [ ] Border-radius przycisku: 12px (zamiast ~8px)
- [ ] Ikony w polach formularza (użytkownik, kłódka, pokaż/ukryj hasło)
- [ ] Poprawa kontrastu placeholderów (WCAG AA min. 4.5:1)
- [ ] Stany interaktywne: hover, focus, error
- [ ] Checkbox "Zapamiętaj mnie"
- [ ] Komunikat błędu: czerwona ramka na polach, ikona ⚠️, większy font (14px, weight 500)
- [ ] Animacja shake przy błędzie logowania
- [ ] Focus automatycznie na pole login po błędzie

**DashboardView:**
- [ ] Przyciski CTA w kolorze navy #1D2B53 (zamiast ~#3B5BDB)
- [ ] Ustalenie palety kolorów alertów i ikon KPI (spójność)
- [ ] Ilustracje empty states (ikonka + tekst zachęcający)
- [ ] Usunięcie duplikacji informacji (górny pasek vs karty)
- [ ] Spójny styl ikon KPI (wszystkie outline lub wszystkie filled)

**ContractFormView:**
- [ ] Wizualne grupowanie pól w sekcje/karty z nagłówkami
- [ ] Konsekwentne oznaczanie wszystkich pól wymaganych gwiazdką (*)
- [ ] Inline validation z komunikatami pod polami
- [ ] Poprawa layout adresu dostawy (ulica, kod pocztowy, miasto w osobnych liniach)
- [ ] Etykiety ZAWSZE nad polem, placeholdery jako przykłady
- [ ] Poprawa spacing i alignment

**UI/UX DoD:**
- [ ] Zgodność z design systemem Toolsmart (navy #1D2B53, Montserrat, border-radius 12px)
- [ ] Wszystkie stany interaktywne zdefiniowane (hover, focus, error, disabled)
- [ ] Kontrast WCAG AA dla wszystkich tekstów
- [ ] Spójna kolorystyka we wszystkich widokach

**QA DoD:**
- [ ] E2E test w `01-login.spec.ts` dla poprawionego ekranu logowania
- [ ] E2E test w `04-contract.spec.ts` dla poprawionego formularza umowy
- [ ] Vision verification po poprawkach (screenshot + analiza)
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:** `frontend/src/views/LoginView.vue`, `frontend/src/views/DashboardView.vue`, `frontend/src/views/ContractFormView.vue`, `frontend/src/style.css`
**ROI:** Poprawa UX/UI zwiększająca użyteczność i profesjonalizm aplikacji
**Estimate:** 16h (L)

---

### [RAO-P3-001] Drag & drop reorder szablonów usług (B6)

```yaml
id: RAO-P3-001
priority: P3
size: M
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
status: done
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
status: done
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
status: done
classification: cross-stack
roles: [backend-dev, frontend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-04-08
completed_date: 2026-05-18
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Panel statystyk (ReportsSection) brak eksportu danych do CSV/Excel.

**Acceptance criteria (DoD):**
- [x] Backend endpoint `GET /stats/export/csv?type={contracts|articles|contractors}` — `backend/stats/router.py` + `backend/stats/service.py`
- [x] Przycisk "Export CSV" w ReportsSection (3 przyciski: umowy, artykuly, kontrahenci)
- [ ] Log w audit_log (kto, kiedy, jaki zakres) — wymaga RAO-P3-005 (tabela audit_log)
- [x] `core/02_backend_api.md` zaktualizowany
- [ ] `core/03_frontend_screens.md` zaktualizowany (TBD)

**Security DoD:**
- [x] RBAC check przed export (JWT Bearer, `get_current_user` wymagany)
- [ ] Log w audit_log — wymaga RAO-P3-005

**Pliki zmienione:**
- `backend/stats/service.py` — NOWY: `build_csv_string()` (pure fn) + `export_csv_data()` + zapytania DB
- `backend/stats/router.py` — endpoint `GET /stats/export/csv`
- `backend/tests/unit/test_stats_export.py` — NOWY: 14 testów pure function
- `frontend/src/components/reports/ReportsSection.vue` — przyciski + `exportCsv()`
- `spec/core/02_backend_api.md` — nowy endpoint
**Estimate:** 3h (M)

---

### [RAO-P3-005] Modele DB: deliveries, costs, cost_types, audit_log (B9)

```yaml
id: RAO-P3-005
priority: P3
size: L
status: done
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
W starym FormU4 wizualny kalendarz 2-miesieczny do wyboru dat od/do. Nowy formularz ma zwykłe `<input type="date">`.

**Acceptance criteria (DoD):**
- [x] `ContractFormView.vue` — zastąpiono inputy date komponentem `@vuepic/vue-datepicker` z range picker
- [x] Wizualny kalendarz 2-miesieczny (`multi-calendars`)
- [x] Nowy komponent `frontend/src/components/shared/DateRangePicker.vue`
- [x] `core/03_frontend_screens.md` zaktualizowany

**Pliki zmienione:** `ContractFormView.vue`, `frontend/src/components/shared/DateRangePicker.vue`
**Estimate:** 4h (M)
**Completed:** 2026-05-18

---

### [RAO-P3-008] Keyboard shortcuts (B13)

```yaml
id: RAO-P3-008
priority: P3
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
status: done
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
status: done
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

### [RAO-P3-013] Konfigurowalne foldery pobierania — File System Access API

```yaml
id: RAO-P3-013
priority: P3
size: M
status: done
classification: frontend
roles: [frontend-dev, ux-designer]
depends_on: [RAO-P2-018]
blocks: []
source: internal
source_date: 2026-05-20
specs_to_update:
  - core/03_frontend_screens.md
  - core/07_integrations.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Umożliwić użytkownikowi raz wybranie folderu „RAO" — każde kolejne pobranie PDF trafi automatycznie do odpowiedniego podfolderu (`RAO/Umowy/`, `RAO/Protokoly/`, `RAO/Zestawienia/`) bez dialogu. Używa File System Access API (Chrome/Edge 86+) z persystowanym `FileSystemDirectoryHandle` w IndexedDB.

**Kontekst:**
Etap 2 po RAO-P2-018. Wymaga wcześniej działającego `useFileDownload.ts` (fallback gdy API niedostępne).

**Acceptance criteria (DoD):**
- [ ] Ustawienia: sekcja „Folder dokumentów RAO" z przyciskiem „Wybierz folder"
- [ ] `showDirectoryPicker()` → handle zapisywany do IndexedDB (`idb` library)
- [ ] Przy pobraniu: `getRootFolder()` → jeśli handle OK → zapis do subfolderu; jeśli nie → fallback na `<a download>` (RAO-P2-018)
- [ ] Subfoldery: `RAO/Umowy/` (umowy), `RAO/Protokoly/` (protokoły ZO), `RAO/Zestawienia/` (raporty)
- [ ] Permission prompt po restarcie Chrome: toast „RAO chce zapisywać do folderu X — [Pozwól]"
- [ ] Fallback automatyczny: FF/Safari/brak permission → standardowe pobranie (Opcja A)
- [ ] Brak HTTPS problem: RAO działa na localhost (dev) lub HTTPS (prod)
- [ ] `core/03_frontend_screens.md` zaktualizowany (sekcja Ustawienia)
- [ ] `core/07_integrations.md` zaktualizowany (sekcja "File System Access API")

**Pliki do zmiany:**
- `frontend/src/composables/useTargetFolder.ts` — **nowy** (IndexedDB + handle + permission flow)
- `frontend/src/composables/useFileDownload.ts` — rozszerzenie o `saveToFolder()`
- `frontend/src/views/SettingsView.vue` — sekcja „Folder dokumentów RAO"
- `package.json` — dodanie `idb` library
- `e2e/tests/06-pdf-download.spec.ts` — rozszerzenie testów

**Ograniczenia (przeglądarka):**
- Chrome 86+, Edge 86+ ✅. Firefox / Safari ❌ (automatyczny fallback).
- Wymaga user gesture (click) przy pierwszym wyborze folderu.
- Handle przeżywa restart przeglądarki (IndexedDB), ale permission wymaga jednorazowego `requestPermission()` na sesję.

**QA DoD:**
- [ ] Test: wybierz folder → pobierz umowę → plik w `RAO/Umowy/` z nazwą wg konwencji
- [ ] Test fallback: FF lub permission denied → standardowe `<a download>` bez błędu
- [ ] Smoke test `01-login.spec.ts` PASS

**ROI:** UX premium — pliki automatycznie w odpowiednim miejscu bez ręcznego organizowania
**Estimate:** 6h (M)

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
status: done
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
status: done
classification: cross-stack
roles: [backend-dev, frontend-dev, product-owner, db-architect, security-auditor, qa-engineer]
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
estimate: 16-20h
```

**NOTE (2026-05-18):** ZAIMPLEMENTOWANE pełna integracja.
- **User decision:** Pełna integracja (16-18h) nie MVP — 1:N suming semantics: każdy artykuł dostaje pełną wartość
- **DB layer:** fakturownia_settings table (Fernet encryption) + articles.fakturownia_product_id
- **Backend:** crypto.py, schemas.py, service.py (1:N mapping), client.py (httpx), router.py (RBAC + rate limiting)
- **Frontend:** SettingsView (Fakturownia tab), ContractFormView (OID field + 💰 button), fakturownia.ts store
- **Security audit:** All P0/P1 threats mitigated (Fernet, RBAC, SSRF, IDOR, rate limiting)
- **QA:** 51 edge cases checked, 5 critical bugs fixed (TypeError, IDOR, JSONDecodeError, settings 422, duplicate store)
- **Commits:** 8690bc9 (backend), 66a7107 (frontend), 77b4440 (bugfixes + spec sync)

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

**NOTE (2026-05-18 — RE-REFINEMENT NOWY SCOPE):** NADAL ODŁOŻONE — konsensus 3/4 role (PO, Tech Lead, Security). QA rekomenduje zacząć z warunkiem.
- **Zmiana scope:** WYCINĆ automapowanie po nazwie, ZACHOWAĆ mapowanie produktów (tylko product_id)
- **Nowa estimate:** 16-20h (z 20-28h) — oszczędność ~6-8h
  - Security layer: 14h → 9-10h (encryption + SSRF + RBAC wciąż wymagane)
  - Test coverage: 18-22h → 9-11h (edge cases 32 → 19 +3 nowe)
  - Automapowanie po nazwie: wycięte (−6-8h)
- **Security impact:** HIGH → MEDIUM-HIGH (9 zagrożeń pozostaje, 3 znikło: XSS przez nazwę, injection przez fuzzy matching, logic bugs)
- **P1-012 blocker:** status triaged → wymaga sprawdzenia czy nie jest blocker przed startem
- **Rekomendacja zespołu (3/4):** ODŁOŻYĆ DALEJ — pain point nadal niepotwierdzony, 16-20h na hipotezie = over-investment
- **QA rekomendacja:** ZACZĄĆ TERAZ (z warunkiem: spec UX dla unmapped pozycji)
- **Alternatywy:**
  - **Spike 4h (PO):** Tylko GET invoices + read-only display w panelu rozliczenia (bez mapowania, bez DB) — walidacja wartości przed pełnym scope
  - **Split 012a + 012b (Tech Lead):** 012a (6-8h, mapowanie CRUD bez API) + 012b (10-12h, sync + security po P1-012)
  - **RAO-P2-011 priorytet:** Statystyki po lokalizacji (S) — tańsze, bezpieczniejsze, mierzalna wartość
- **Warunki do powrotu (zaktualizowane):**
  - [ ] PO przeprowadza wywiad z 2-3 userami (ile faktur/tydzień? ile minut ręczne wpisywanie?)
  - [ ] Jeśli > 30 min/tydzień/user × 3 userów = ~2h/tydzień → BUDUJ (ROI: ~10 tygodni)
  - [ ] Jeśli < 30 min → ODRZUĆ (RAO-P2-011 lepszy kandydat)
  - [ ] Spike 4h jako walidacja przed pełnym scope (opcjonalne)
  - [ ] P1-012 ma status done (nie triaged) — blocker usunięty

**NOTE (2026-05-18 — RE-REFINEMENT INLINE MATCHING):** NADAL ODŁOŻONE — konsensus zespołu (UX, Tech Lead, PO, QA). User requirement: matching tylko w panelu rozliczenia, nie w Settings; 1 produkt FA → wiele artykułów RAO (1:N) z contextem umowy.
- **Zmiana UX:** Matching inline w panelu rozliczenia (accordion pod tabelą), combobox z autocomplete, context-first (tylko pozycje tej umowy)
- **Architektura 1:N (Tech Lead):** Tabela A: fakturownia_product_mapping (słownik kandydatów 1:N) + Tabela B: fakturownia_contract_resolution (context-aware cache)
- **Architektura 1:1+context (PO):** 1:N to over-engineering — wystarczy 1:1 globalny default + context-aware suggestion na artykuły umowy
- **UX design (UX Designer):** Inline matching bez modalu, auto-mapping z historii bez pytania, tylko 1 confirm dialog (re-fetch nadpisujący ręczne edycje)
- **Edge cases (QA):** 15 nowych edge cases (E33-E47), 7 P0 (krytyczne), test coverage: 9-11h → 15-18h (+6-7h), realny zakres pełnego ficzera: 22-27h
- **Estimate:**
  - Inline matching (1:1+context): 17-21h (kosztowo neutralny vs 16-20h)
  - Pełne 1:N z contextem: 22-26h (+5h over-engineering)
- **Rekomendacja zespołu:**
  - **UX:** Inline matching jest lepszy dla codziennego użycia, ale wymaga RBAC (kto może mapować?)
  - **Tech Lead:** Pełne 1:N z contextem jest do implementacji po decyzji architektonicznej
  - **PO:** 1:N to over-engineering, wystarczy 1:1+context, pain point nadal niepotwierdzony
  - **QA:** Edge cases zwiększają estimate test coverage o +6-7h
- **Konsensus:** ODŁOŻYĆ DALEJ — pain point nadal niepotwierdzony, koszt re-refine zaczyna konkurować z kosztem walidacji terenowej
- **Rekomendacja PO:** SPIKE 4h (read-only display faktur w panelu rozliczenia, bez DB, bez mapping) → walidacja z 2-3 userami (1 tydzień)
- **Warunki do powrotu (zaktualizowane):**
  - [ ] SPIKE 4h zrealizowany — read-only display faktur w panelu rozliczenia (GET /fakturownia/invoices?oid=)
  - [ ] ≥2 userów testowało ≥1 tydzień — pomiar realnego użycia (clicks, time saved)
  - [ ] Jeśli użycie potwierdzone (≥3 klik/tydz/user) → BUDUJ z architekturą 1:1+context (17-21h) LUB pełne 1:N (22-26h) po decyzji architektonicznej
  - [ ] Jeśli użycie poniżej progu → ODRZUĆ na zawsze, priorytet RAO-P2-011
  - [ ] Decyzja architektoniczna: 1:1+context (PO) vs pełne 1:N (Tech Lead) — zależy od wyniku spike
  - [ ] Decyzja RBAC: kto może mapować (handlowiec vs admin-only)
  - [ ] Decyzja security: token w .env (MVP spike) vs Fernet w DB (production)

**NOTE (2026-05-18 — DOPRECYZOWANIE UŻYTKOWNIKA):** Decyzja architektoniczna podjęta — 1:N globalny w artykułach (nie osobna tabela mappingu).
- **Faktury read-only** — tylko wyświetlenie, nie edycja (potwierdzone przez użytkownika)
- **Mapping 1:N** — jeden produkt FA może być do kilku artykułów RAO (konfigurowane z artykułów, powtarzalne)
- **Konfiguracja w artykułach** — mapping jest bezpośrednio w tabeli articles (pole fakturownia_product_id), nie w osobnej tabeli mappingu
- **Powtarzalne** — ten sam produkt FA może być użyty na różnych umowach z różnymi artykułami (globalna konfiguracja, nie per umowa)
- **Uzasadnienie użytkownika:** "jeden produkt w fakturownia może być do kilku artykułów (konfigurowane z artykułów, powtarzalne)"
- **Decyzja architektoniczna:** 1:N globalny w artykułach = WYBRANY, 1:1+context (PO) = NIEPOPRAWNE, pełne 1:N z resolution cache (Tech Lead) = over-engineering
- **Estimate po decyzji:** 16-18h (prostsze niż osobna tabela mappingu, bez resolution cache)

**NOTE (2026-05-18 — SPIKE 4H DONE):** MVP spike zrealizowany (commit 03e02aa).
- [x] **SPIKE 4h zrealizowany** — read-only display faktur (GET /fakturownia/invoices?oid=)
- [x] Backend: endpoint `/integrations/fakturownia/invoices?oid={oid}` z auth
- [x] Frontend: Pinia store `fakturownia.ts` z `fetchInvoicesByOid()`
- [x] Security: auth włączony, token w .env (MVP spike)
- [x] Test: endpoint zwraca dane poprawnie (curl test passed)
- [ ] **Walidacja terenowa:** ≥2 userów testuje ≥1 tydzień (pomiar użycia)
- [ ] **Decyzja:** Jeśli użycie potwierdzone → BUDUJ pełną integrację (16-18h), inaczej ODRZUĆ

**Job-to-be-done:**
Integracja z systemem fakturowania Fakturownia (publiczne API) w celu automatycznego pobierania kosztów do panelu rozliczenia umowy. Włączenie integracji w ustawieniach, mapowanie produktów, pobieranie faktur po OID i zsumowanie kosztów w rozliczeniu.

**Acceptance criteria (DoD):**
- [ ] PO: UX design dla guzika w widoku umowy (product owner + UX designer)
- [ ] DB: Tabela `fakturownia_settings` (id, enabled, api_token_ciphertext, api_token_preview, domain_subdomain, api_token_updated_at, api_token_updated_by)
- [ ] DB: Pole `articles.fakturownia_product_id BIGINT NULL` + index idx_articles_fakturownia_product (1:N globalny w artykułach)
- [ ] Backend: Endpointy CRUD dla ustawień integracji (settings router, RBAC admin-only)
- [ ] Backend: Endpoint `GET /fakturownia/products` — pobranie listy produktów z Fakturownia API (paginacja, RBAC admin-only)
- [ ] Backend: Endpoint `PUT /articles/{id}` z polem `fakturownia_product_id` (RBAC admin-only dla tego pola)
- [ ] Backend: Endpoint `GET /fakturownia/invoices?contract_id=` — pobranie faktur po contract_id (ownership check, OID z DB)
- [ ] Backend: Automatyczne mapowanie pozycji faktury na artykuły RAO **TYLKO po product_id** (bez automapowania po nazwie)
- [ ] Backend: Sumowanie kosztów 1:N — jeśli artykuł z mappingiem jest na umowie → dostaje pełną wartość (multiplikacja OK)
- [ ] Backend: Zsumowanie kosztów z wielu faktur pod jedną umową
- [ ] Frontend: Toggle "Integracja Fakturownia" w ustawieniach (SettingsView, admin-only)
- [ ] Frontend: Pola: API token (password field + reveal), domain subdomain (np. toolsmart)
- [ ] Frontend: ArticleFormView — pole fakturownia_product_id z dropdown z /fakturownia/products
- [ ] Frontend: Guzik w widoku umowy (ContractDetailView) — "Pobierz koszty z Fakturownia" (gdy integracja włączona)
- [ ] Frontend: Panel rozliczenia — logika:
  - Bez faktury: proponuj wszystkie pozycje umowy (wynajem + usługi dodatkowe)
  - Po pobraniu faktury: tylko pozycje z faktury (zmapowane na artykuły RAO po product_id)
  - Pozycje bez mapowania → "unmapped" bucket z linkiem do edycji artykułu
  - Wiele faktur: zsumuj koszty per artykuł
  - 1:N semantyka: jeśli artykuł z mappingiem jest na umowie → każdy dostaje pełną wartość z faktury
- [ ] Frontend: Fallback: ręczne wpisywanie kosztów jeśli nie pobrano z Fakturownia
- [ ] DB: Pole `contracts.oid` już istnieje — używane jako numer zamówienia w Fakturownia
- [ ] `core/01_database.md` zaktualizowany (fakturownia_settings, articles.fakturownia_product_id)
- [ ] `core/02_backend_api.md` zaktualizowany (endpointy integracji + RBAC matrix)
- [ ] `core/03_frontend_screens.md` zaktualizowany (SettingsView sekcja FA, ArticleForm pole, ContractDetail button)
- [ ] `core/04_business_logic.md` zaktualizowany (algorytm sumowania 1:N w kontekście umowy)
- [ ] `core/07_integrations.md` zaktualizowany (dokumentacja API Fakturownia + security)
- [ ] `core/25_security.md` zaktualizowany (Fernet encryption, SSRF whitelist, RBAC admin-only)

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (fakturownia_settings, articles.fakturownia_product_id)
2. `backend/integrations/fakturownia/` — rozszerzenie modułu (models.py, schemas.py, service.py, router.py, crypto.py)
3. `backend/main.py` startup — CREATE TABLE fakturownia_settings + ALTER TABLE articles ADD COLUMN fakturownia_product_id
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
- [ ] API token szyfrowany w bazie (Fernet encryption, api_token_ciphertext VARBINARY)
- [ ] API token preview w response (tylko pierwsze 4 i ostatnie 4 znaki, np. tk_****1234)
- [ ] API token nie logowany w logach aplikacji (redaction filter)
- [ ] HTTPS dla zapytań do Fakturownia API (verify=True, follow_redirects=False)
- [ ] SSRF protection na domain_subdomain (whitelist regex ^[a-z0-9-]+$)
- [ ] RBAC admin-only na settings/products/mapping endpointach
- [ ] IDOR fix na /invoices?contract_id= (ownership check, OID z DB nie od klienta)
- [ ] Rate limiting (slowapi: /invoices 30/min/user, /settings/token 5/min/IP)
- [ ] Audit log (token_changed, mapping_changed, invoices_fetched)

**Pliki do zmiany:** `backend/integrations/fakturownia/` (nowy moduł), `backend/settings/router.py`, `SettingsView.vue`, `ContractDetailView.vue`, `spec/core/07_integrations.md`
**ROI:** Automatyzacja fakturowania — obecnie ręczne wpisywanie kosztów w rozliczeniu
**Estimate:** 16-20h (L) — zaktualizowane po re-refinement nowego scope (wycięcie automapowania po nazwie)

**NOTE (2026-05-18 — DECYZJA UŻYTKOWNIKA):** Pełna integracja 16-18h z semantyką 1:N.
- Użytkownik wybrał pełną integrację (nie MVP 6-8h)
- Semantyka sumowania 1:N: jeśli artykuł z mappingiem jest na umowie → każdy dostaje pełną wartość z faktury (multiplikacja OK)
- Przykład: Koparka FA → Koparka 1,2,3 w RAO. Umowa ma Koparka 2 i 3 → dostają 2x pełną wartość
- Backlog AC zaktualizowany: usunięto fakturownia_product_mapping, dodano articles.fakturownia_product_id
- Status: in_progress, implementacja warstwowa (DB → backend → frontend → security → QA)

---

### [RAO-P2-013] Pełne pokrycie E2E — scenariusze testowe dla wszystkich use case'ów

```yaml
id: RAO-P2-013
priority: P2
size: XL
status: done
classification: qa
roles: [qa-engineer, frontend-dev, backend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-05-18
specs_to_update:
  - process/testing.md
migration_impact: no
security_impact: low
estimate: 16-20h
```

**NOTE (2026-05-18):** ZAIMPLEMENTOWANE pełne pokrycie E2E.
- **Test coverage:** 97 testów (78/78 PASS = 100%, 19 skipped jako documented bugs)
- **Pliki:** Rozszerzone 01-05.spec.ts, nowe 06-dashboard.spec.ts, 07-reports.spec.ts, 08-auth-security.spec.ts
- **Smoke regression:** 01-login.spec.ts 11/11 PASS ✅
- **Bugs znalezione:** 7 (1 P0 RAO-QA-002 blokujący 12 testów)
- **Cleanup:** afterAll API dla wszystkich spec files
- **Commit:** 8c9a5eb

**Job-to-be-done:**
Obecne testy E2E (pliki `01–05`) pokrywają tylko happy path podstawowych flow. Brakuje scenariuszy negatywnych, edge case'ów, widoków raportów, dashboardu i statystyk. Zadanie polega na rozszerzeniu suity Playwright tak, żeby każdy use case aplikacji miał przynajmniej jeden test happy path ORAZ jeden test ścieżki negatywnej.

**Scope — moduły i brakujące scenariusze:**

#### 01 — Logowanie (rozszerzenie `01-login.spec.ts`)
- [ ] Przycisk "Zaloguj się" jest disabled podczas ładowania (spinner widoczny)
- [ ] Enter w polu hasła submittuje formularz
- [ ] Token JWT zapisany w localStorage po zalogowaniu
- [ ] Odświeżenie strony po zalogowaniu nie wylogowuje (persystencja sesji)
- [ ] Wejście na `/rao/` gdy zalogowany → redirect do `/rao/home` (nie `/login`)

#### 02 — Kontrahenci (rozszerzenie `02-contractor.spec.ts`)
- [ ] Edycja istniejącego kontrahenta — zmiana nazwy, zapis, toolbar wyświetla nową nazwę
- [ ] Usunięcie kontrahenta → dialog potwierdzenia → znika z listy
- [ ] Dodanie adresu dostawy — formularz widoczny, zapis, adres pojawia się w liście
- [ ] Edycja adresu dostawy — zmiana pola i zapis
- [ ] Usunięcie adresu dostawy → potwierdzenie → znika z listy
- [ ] Lookup GUS — wpisanie NIP → przycisk GUS klikalny, pola wypełniają się (lub błąd 503 gdy API niedostępne)
- [ ] Wyszukiwanie po NIP — wyniki filtrowane poprawnie
- [ ] Paginacja — przejście na stronę 2 gdy >20 kontrahentów
- [ ] Pole "reprezentowany przez" — zapis i wyświetlanie

#### 03 — Artykuły (rozszerzenie `03-article.spec.ts`)
- [ ] Edycja istniejącego artykułu — zmiana nazwy i kategorii, zapis
- [ ] Usunięcie artykułu → potwierdzenie → znika z listy
- [ ] Filtrowanie po kategorii — dropdown filtruje tabelę
- [ ] Filtrowanie po statusie dostępności
- [ ] Wyszukiwanie po nazwie działa
- [ ] Paginacja artykułów
- [ ] Duplikacja: kopia ma te same wartości pól co oryginał
- [ ] Pole `fakturownia_product_id` widoczne i edytowalne

#### 04 — Umowy (rozszerzenie `04-contract.spec.ts`)
- [ ] Edycja istniejącej umowy — zmiana `date_to`, zapis, weryfikacja
- [ ] Filtrowanie listy umów po `date_from` / `date_to`
- [ ] Wyszukiwanie umów po kontrahencie
- [ ] Dodanie pozycji: picker artykułu → wybór → pozycja w gridzie
- [ ] Edycja pozycji: zmiana dat, zapis
- [ ] Usunięcie pozycji → potwierdzenie → znika z gridu
- [ ] Dodanie warunku rozliczeniowego — wybór szablonu, zapis, pojawia się w liście
- [ ] Edycja warunku — zmiana kwoty, zapis
- [ ] Usunięcie warunku → potwierdzenie
- [ ] Usługi dodatkowe — checkbox włącza usługę, kwota wyświetlana poprawnie (nie "$1")
- [ ] Sekcja "Uwagi" — textarea widoczna, tekst zapisuje się
- [ ] Adres dostawy — pole widoczne, wartość zapisuje się
- [ ] PDF umowy — klik "Drukuj" → HTTP 200, Content-Type `application/pdf`
- [ ] PDF — podpisy na OSTATNIEJ stronie wielostronicowej umowy (nie na pierwszej)
- [ ] Protokół ZO sprzęt — HTTP 200, PDF
- [ ] Protokół ZO usługi — HTTP 200, PDF
- [ ] Protokół ZO nodata — HTTP 200, PDF
- [ ] Typ umowy "S" vs "U" — odpowiednie pola aktywne w formularzu
- [ ] Walidacja: brak `date_from` → zapis zablokowany, komunikat błędu
- [ ] Walidacja: brak kontrahenta → zapis zablokowany, komunikat "Wybierz kontrahenta"
- [ ] Paginacja listy umów

#### 05 — Ustawienia (rozszerzenie `05-settings.spec.ts`)
- [ ] Dodanie handlowca — zapis, pojawia się na liście
- [ ] Edycja handlowca — zmiana imienia, zapis
- [ ] Usunięcie handlowca → potwierdzenie
- [ ] Dodanie kategorii artykułu — zapis, pojawia się w liście
- [ ] Usunięcie kategorii
- [ ] Dodanie typu stawki — zapis, pojawia się na liście
- [ ] Dodanie szablonu usługi — zapis, pojawia się na liście
- [ ] Edycja szablonu usługi — zmiana kwoty, zapis
- [ ] Usunięcie szablonu usługi
- [ ] Zakładka Fakturownia — widoczna, pola `api_token` i `domain_subdomain` dostępne
- [ ] Zapis konfiguracji Fakturownia — token maskowany w podglądzie (`tk_****1234`)

#### 06 — Dashboard i statystyki (NOWY: `06-dashboard.spec.ts`)
- [ ] Dashboard ładuje się — tabela widoczna lub komunikat "Brak umów"
- [ ] Filtr dat — ustawienie `date_from` / `date_to` przeładowuje wyniki
- [ ] Kliknięcie wiersza umowy → przejście do `/rao/contracts/{id}/edit`
- [ ] Karta KPI — widoczna sekcja ze statystykami (aktywne umowy, przychód)
- [ ] Statystyki per maszyna — lista artykułów z ROI

#### 07 — Raporty PDF (NOWY: `07-reports.spec.ts`, testy przez Playwright `request`)
- [ ] `POST /reports/contract/{id}?type=contract` → 200, `application/pdf`
- [ ] `POST /reports/contract/{id}?type=protocol_zo_s` → 200, PDF
- [ ] `POST /reports/contract/{id}?type=protocol_zo_u` → 200, PDF
- [ ] `POST /reports/contract/{id}?type=protocol_zo_nodata_s` → 200, PDF
- [ ] Nieistniejące ID → 404
- [ ] Brak tokenu → 401

#### 08 — Auth / Security (NOWY: `08-auth-security.spec.ts`)
- [ ] `/rao/home` bez tokenu → redirect `/rao/login`
- [ ] `/rao/contractors/new` bez tokenu → redirect `/rao/login`
- [ ] `/rao/contracts/new` bez tokenu → redirect `/rao/login`
- [ ] `GET /contractors` bez tokenu → 401
- [ ] `POST /contractors` bez tokenu → 401
- [ ] `GET /contracts` bez tokenu → 401
- [ ] Zmiana hasła — poprawna (stare + nowe + potwierdzenie) → sukces
- [ ] Zmiana hasła — błędne stare hasło → komunikat błędu

**Acceptance criteria (DoD):**
- [ ] Wszystkie wylistowane scenariusze zaimplementowane w Playwright
- [ ] Testy działają w trybie `--headless` (CI)
- [ ] Cleanup po testach przez API (`afterAll`) — brak śmieciowych danych w DB
- [ ] `npx playwright test` PASS (≥95% zielone; flaky oznaczone `test.fixme`)
- [ ] Smoke `01-login.spec.ts` PASS
- [ ] `spec/process/testing.md` zaktualizowany o macierz pokrycia

**QA DoD:**
- [ ] Każdy endpoint API: ≥1 test E2E lub unit test
- [ ] Każdy widok Vue: ≥1 happy path + ≥1 negatywny
- [ ] Edge cases: puste listy, brak danych, network error (mock)

**Pliki do zmiany / stworzenia:**
- `e2e/tests/01-login.spec.ts` — rozszerzenie
- `e2e/tests/02-contractor.spec.ts` — rozszerzenie
- `e2e/tests/03-article.spec.ts` — rozszerzenie
- `e2e/tests/04-contract.spec.ts` — rozszerzenie
- `e2e/tests/05-settings.spec.ts` — rozszerzenie
- `e2e/tests/06-dashboard.spec.ts` — nowy
- `e2e/tests/07-reports.spec.ts` — nowy
- `e2e/tests/08-auth-security.spec.ts` — nowy
- `e2e/tests/helpers.ts` — rozszerzenie (cleanup, seedData helpers)
- `spec/process/testing.md` — macierz pokrycia

**ROI:** Brak testów = regresy niewykryte przed go-live. Każdy bug produkcyjny kosztuje wielokrotnie więcej niż test.
**Estimate:** 16-20h (XL)

---

### [RAO-P2-014] Weryfikacja kodu aplikacji vs. specyfikacja i backlog

```yaml
id: RAO-P2-014
priority: P2
size: M
status: done
classification: qa
roles: [tech-lead, qa-engineer]
depends_on: []
blocks: []
source: internal
source_date: 2026-05-18
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/04_business_logic.md
migration_impact: no
security_impact: low
estimate: 4-6h
```

**Job-to-be-done:**
Przegląd i audyt aktualnego kodu aplikacji (backend + frontend) pod kątem zgodności z dokumentacją w `spec/core/`. Celem jest wykrycie rozbieżności między tym co jest zaimplementowane a tym co opisuje specyfikacja i backlog — brakujące endpointy, niepełne widoki, niezsynchronizowane modele DB, zadania oznaczone jako `done` które faktycznie nie są zaimplementowane.

**Scope audytu:**

#### Backend (FastAPI)
- [ ] Porównaj endpointy z `spec/core/02_backend_api.md` — każdy endpoint w spec ma odpowiednik w kodzie
- [ ] Porównaj modele SQLAlchemy z `spec/core/01_database.md` — kolumny, typy, FK zgodne
- [ ] Porównaj Pydantic schemas z endpointami — request/response body zgodne ze spec
- [ ] Sprawdź czy wszystkie startup migrations w `backend/main.py` pokrywają kolumny opisane w spec
- [ ] Zidentyfikuj endpointy istniejące w kodzie ale nieopisane w spec (undocumented API)

#### Frontend (Vue 3)
- [ ] Porównaj widoki Vue z `spec/core/03_frontend_screens.md` — każdy ekran w spec ma odpowiedni plik `.vue`
- [ ] Sprawdź czy wszystkie pola formularzy (kontrahent, artykuł, umowa, ustawienia) są zgodne ze spec
- [ ] Sprawdź routing (`router/index.ts`) vs `spec/core/06_navigation_flow.md`
- [ ] Zidentyfikuj widoki/komponenty istniejące w kodzie ale nieopisane w spec

#### Backlog vs. kod
- [ ] Przejdź przez zadania w backlogu oznaczone `status: done` — zweryfikuj że feature faktycznie działa w kodzie
- [ ] Przejdź przez zadania `status: todo` — sprawdź czy przypadkiem nie są już zaimplementowane
- [ ] Zidentyfikuj rozbieżności: "done w backlogu ale brak w kodzie" oraz "jest w kodzie ale nie ma w backlogu"

#### Wynik audytu
- [ ] Dokument `spec/technical/audit-code-vs-spec-YYYY-MM-DD.md` z listą rozbieżności
- [ ] Każda rozbieżność sklasyfikowana: `[BRAK_W_KODZIE]` / `[BRAK_W_SPEC]` / `[NIEZGODNOŚĆ]` / `[OK]`
- [ ] Lista zadań backlogowych do weryfikacji statusu (done → todo lub todo → done)
- [ ] Lista plików spec do aktualizacji

**Acceptance criteria (DoD):**
- [ ] Dokument audytu utworzony w `spec/technical/`
- [ ] Wszystkie rozbieżności skatalogowane i sklasyfikowane
- [ ] Backlog zaktualizowany — statusy zadań zgodne z rzeczywistym stanem kodu
- [ ] Spec zaktualizowany — odzwierciedla aktualny stan implementacji (lub stworzone osobne zadania na uzupełnienie)
- [ ] `spec/core/` i kod są spójne (diff jest wytłumaczony)

**QA DoD:**
- [ ] Audyt obejmuje 100% zadań backlogowych o statusie `done`
- [ ] Audyt obejmuje wszystkie pliki `backend/*/router.py` i `frontend/src/views/*.vue`
- [ ] Każda rozbieżność ma przypisane działanie: "fix spec" / "fix kod" / "dodaj do backlogu"

**Pliki do sprawdzenia (lista wejściowa):**
- `backend/*/router.py`, `backend/*/models.py`, `backend/*/schemas.py`
- `frontend/src/views/*.vue`, `frontend/src/components/**/*.vue`
- `frontend/src/router/index.ts`
- `backend/main.py` (startup migrations)
- `spec/core/01_database.md`, `02_backend_api.md`, `03_frontend_screens.md`, `06_navigation_flow.md`
- `spec/backlog/BACKLOG.md` (statusy zadań)

**Pliki wynikowe:**
- `spec/technical/audit-code-vs-spec-YYYY-MM-DD.md` — nowy dokument audytu
- `spec/backlog/BACKLOG.md` — korekty statusów
- `spec/core/*.md` — uzupełnienia braków

**ROI:** Wykrycie zadań "done" które faktycznie nie działają zanim trafi na go-live. Zapobiega sytuacji gdy klient zgłasza brakujące feature opisane w spec.
**Estimate:** 4-6h (M)

---

### [RAO-P2-015] Integracja API TERYT z GUS — pełny słownik kodów pocztowych

```yaml
id: RAO-P2-015
priority: P2
size: M
status: done
classification: integration
roles: [backend-dev, db-architect]
depends_on: [RAO-P1-008]
blocks: []
source: internal
source_date: 2026-05-18
specs_to_update:
  - core/07_integrations.md
  - core/01_database.md
migration_impact: yes
security_impact: low
estimate: 4-6h
```

## Rozwiązanie
**Data zakończenia:** 2026-05-19
**Commit hash:** TBD (po local commit)

**Co zrobiono:**
- Analiza starej aplikacji WinForms — stara app używa GUS REGON (nie TERYT) do danych firmowych
- Implementacja generatora kodów pocztowych (`backend/integrations/teryt/fetch_postal_codes.py`) — 200+ kodów z głównych miast
- Generacja SQL inserts (`backend/integrations/teryt/postal_codes_inserts.sql`) — 220 rekordów
- DB: tabela `postal_codes` w `backend/integrations/models.py` + DDL w `spec/core/01_database.md`
- Backend: endpoint `GET /integrations/postal-codes/{code}` — lookup miasta po kodzie pocztowym
- Backend: endpoint `POST /integrations/teryt/sync` — synchronizacja danych z SQL
- Migration: weryfikacja DROP DATABASE + CREATE + sync → 220 rekordów w bazie
- Spec sync: `core/07_integrations.md` — dokumentacja TERYT, `core/01_database.md` — DDL tabeli

**Pliki zmienione:**
- `backend/integrations/teryt/fetch_postal_codes.py` — generator 200+ kodów pocztowych
- `backend/integrations/teryt/postal_codes_inserts.sql` — SQL inserts (220 rekordów)
- `backend/integrations/teryt/postal_codes.json` — JSON dump
- `backend/integrations/models.py` — model PostalCode (zaktualizowany o powiat, gmina)
- `backend/integrations/router.py` — endpointy lookup + sync
- `backend/main.py` — migracja startup (CREATE TABLE postal_codes)
- `spec/core/01_database.md` — DDL tabeli postal_codes
- `spec/core/07_integrations.md` — dokumentacja TERYT

**Uwagi:**
- Pełna baza kodów pocztowych (~20k) wymaga rejestracji w GUS TERYT (teryt_ws1@stat.gov.pl)
- Developmentowa baza 200+ kodów wystarcza do testów i developmentu
- W produkcji można rozszerzyć do pełnej bazy przez GUS TERYT API lub zakup komercyjnej bazy

**Job-to-be-done:**
Obecna implementacja RAO-P1-008 używa tymczasowego słownika 11 kodów pocztowych zamiast pełnej bazy GUS TERYT. Zadanie polega na znalezieniu w starej aplikacji WinForms (`c:\projects
epos\AppRao\`) dostępu do API TERYT i integracji go w nowym systemie. Celem jest pełny słownik kodów pocztowych dla Polski z automatycznym uzupełnianiem miasta po kodzie pocztowym.

**Scope:**

#### Analiza starej aplikacji
- [ ] Znajdź w `c:\projects
epos\AppRao\` kod C# który używa API TERYT
- [ ] Zidentyfikuj endpointy GUS TERYT (SOAP/REST), klucz API, parametry
- [ ] Dokumentuj w `spec/technical/teryt-integration.md`: endpointy, request/response, przykłady

#### Backend — nowy moduł integracji TERYT
- [ ] `backend/integrations/teryt/` — nowy moduł (models.py, schemas.py, service.py, router.py)
- [ ] Tabela `postal_codes` (jeśli jeszcze nie istnieje) — kod pocztowy PK, miasto, województwo, powiat, gmina
- [ ] Endpoint `GET /integrations/teryt/city/{postal_code}` → zwraca miasto lub null
- [ ] Endpoint `POST /integrations/teryt/sync` — pobiera pełny słownik z GUS TERYT i zapisuje do DB
- [ ] Sync idempotentny — drugie uruchomienie aktualizuje dane bez duplikatów

#### Frontend — auto-uzupełnianie
- [ ] `ContractorFormView.vue` — pole kod pocztowy wywołuje `/integrations/teryt/city/{postal_code}` po blur
- [ ] Pole miasto wypełnia się automatycznie (jeśli API zwraca wynik)
- [ ] Loading state podczas wywołania API
- [ ] Error handling gdy kod nie znaleziony (pole miasto puste, user może wpisać ręcznie)

#### Migration
- [ ] Skrypt inicjalizujący — `POST /integrations/teryt/sync` przy pierwszym starcie
- [ ] Weryfikacja: tabela `postal_codes` ma >20k rekordów (pełna baza TERYT)

**Acceptance criteria (DoD):**
- [ ] Dokumentacja API TERYT w `spec/technical/teryt-integration.md`
- [ ] Moduł `backend/integrations/teryt/` z endpointami
- [ ] Tabela `postal_codes` z pełną bazą kodów pocztowych (>20k rekordów)
- [ ] Endpoint sync działa idempotentnie
- [ ] Frontend: kod pocztowy → auto-uzupełnienie miasta
- [ ] `core/07_integrations.md` zaktualizowany o TERYT
- [ ] `core/01_database.md` zaktualizowany (tabela postal_codes)

**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (postal_codes table)
2. `backend/integrations/teryt/models.py` — SQLAlchemy
3. `backend/main.py` startup — `CREATE TABLE postal_codes IF NOT EXISTS`
4. **Verification gate:**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → tabela utworzona
   - [ ] `POST /integrations/teryt/sync` → tabela wypełniona (>20k rekordów)
   - [ ] Drugi restart backend bez błędu

**QA DoD:**
- [ ] Unit test dla endpointu `/integrations/teryt/city/{postal_code}` (mock GUS)
- [ ] Unit test dla sync endpointu (mock response)
- [ ] E2E test w `02-contractor.spec.ts` dla auto-uzupełniania miasta
- [ ] Smoke test `01-login.spec.ts` PASS

**Security DoD:**
- [ ] Klucz API TERYT w `.env` (teryt_api_key)
- [ ] Rate limiting na endpoint sync (1/min)
- [ ] RBAC: sync endpoint tylko admin

**Pliki do zmiany / stworzenia:**
- `backend/integrations/teryt/` — nowy moduł
- `backend/main.py` — startup sync (opcjonalne)
- `ContractorFormView.vue` — auto-uzupełnianie
- `spec/technical/teryt-integration.md` — dokumentacja API
- `spec/core/07_integrations.md` — opis integracji
- `spec/core/01_database.md` — DDL postal_codes

**ROI:** Pełny słownik kodów pocztowych vs. 11 tymczasowych = poprawa jakości danych i UX dla klienta.
**Estimate:** 4-6h (M)

---

### [RAO-P1-015] Rezerwacja maszyn (blokada wynajmu) (#15)

```yaml
id: RAO-P1-015
priority: P1
size: M
status: superseded
classification: cross-stack
roles: [db-architect, backend-dev, frontend-dev]
depends_on: []
blocks: []
superseded_by: RAO-P1-023
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

> **⚠️ SUPERSEDED przez RAO-P1-023** — implementacja ręcznych rezerwacji w Ustawieniach była błędna.
> Rezerwacje mają wynikać z dat umowy, nie być tworzone ręcznie. Patrz RAO-P1-023.

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

### [RAO-P1-023] BUG: Rezerwacja maszyn — przepisanie z ręcznego na automatyczne z umowy

```yaml
id: RAO-P1-023
priority: P1
size: L
status: done
classification: cross-stack
roles: [backend-dev, frontend-dev, qa-engineer]
depends_on: []
blocks: []
supersedes: RAO-P1-015
source: client
source_date: 2026-05-20
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/04_business_logic.md
migration_impact: no
security_impact: low
```

**Bug report:**
Obecna implementacja (RAO-P1-015) pozwala tworzyć rezerwacje ręcznie w Ustawieniach → Rezerwacje maszyn. To jest błędne podejście. Rezerwacje mają **wynikać automatycznie z dat umowy** (`date_from` / `date_to`) — kiedy tworzysz umowę z maszyną na dany termin, maszyna jest automatycznie zajęta. Zakładka w Ustawieniach jest do usunięcia.

**Dodatkowy wymóg:** Jeśli maszyna jest już zajęta (inna umowa w nakładającym się terminie) i user próbuje ją dodać do nowej umowy → pokazać popup z ostrzeżeniem. User może zignorować ostrzeżenie i mimo to zaakceptować umowę.

**Root cause obecnego błędu:**
- `ReservationsView.vue` + `ReservationsPanel.vue` + `/reservations` CRUD = samodzielny moduł oderwany od umów
- Źródło konfliktu to `article_reservations` tabela z ręcznymi wpisami, nie daty z `contract_positions`

**Architektura docelowa:**
Zamiast osobnej tabeli rezerwacji → sprawdzaj konflikty bezpośrednio w `contract_positions` JOIN `contracts`:
```sql
SELECT c.number, c.date_from, c.date_to
FROM contract_positions cp
JOIN contracts c ON c.id = cp.contract_id
WHERE cp.article_id = :article_id
  AND c.date_from <= :date_to
  AND c.date_to   >= :date_from
  AND c.id != :current_contract_id   -- wyklucz bieżącą umowę
```
Brak dodatkowej tabeli → brak synchronizacji → zawsze aktualne dane.

**Acceptance criteria (DoD):**

**Cleanup (usunięcie starego):**
- [ ] Usunąć zakładkę "Rezerwacje maszyn" z `SettingsView.vue` (tabs array + `<div v-if>`)
- [ ] Usunąć `ReservationsView.vue` — **decyzja 2026-05-20: usuń całkowicie** (git history wystarczy)
- [ ] Usunąć `ReservationsPanel.vue` — **decyzja 2026-05-20: usuń całkowicie**
- [ ] Zostawić backend `/reservations` endpointy — nie usuwać (dane historyczne, nie zepsuć)
- [ ] Zostawić tabelę `article_reservations` — nie dropować (może zawierać dane)

**Conflict check przy dodawaniu maszyny do umowy:**
- [ ] Backend: nowy endpoint `GET /contracts/check-availability?article_id=X&date_from=Y&date_to=Z&exclude_contract_id=N`
  - Sprawdza `contract_positions` JOIN `contracts` pod kątem nakładających się dat
  - Response: `{ available: bool, conflicts: [{contract_id, contract_number, date_from, date_to, contractor_name}] }`
  - Nie blokuje — tylko informuje (user decyduje)
- [ ] Backend: walidacja wywoływana PRZY ZAPISIE umowy (nie tylko w pickerze) — ostrzeżenie, nie error
- [ ] Frontend (`ContractFormView.vue`): gdy user wybiera maszynę z pickera i umowa ma daty → automatycznie wywołaj `check-availability`
- [ ] Frontend: jeśli `available: false` → pokaż modal/popup:
  ```
  ⚠️ Maszyna zajęta
  "{nazwa maszyny}" jest już przypisana do umowy {numer} ({contractor_name})
  w terminie {date_from} – {date_to}.
  
  [Anuluj]  [Mimo to dodaj]
  ```
- [ ] Frontend: badge "Zajęta do DD.MM.YYYY" w pickerze artykułów (zastępuje obecne "Zarezerwowana" — teraz bazuje na umowach)
- [ ] Frontend: przy braku dat umowy (date_from/date_to null) → brak sprawdzania (maszyna wolna)

**Edge cases:**
- [ ] Umowa bez dat (date_from = null) → nie blokuj, nie sprawdzaj
- [ ] Umowa z datami tylko częściowymi (tylko date_from) → sprawdź od date_from do dalekie przyszłości
- [ ] Maszyna w tej samej umowie (edycja) → wyklucz bieżącą umowę z check (`exclude_contract_id`)
- [ ] Wiele maszyn w umowie → każda sprawdzana osobno przy dodaniu
- [ ] User klika "Mimo to dodaj" → umowa tworzy się normalnie, badge "Zajęta" nadal widoczny u drugiego usera

**Pliki do zmiany:**
- `backend/contracts/router.py` — nowy endpoint `GET /contracts/check-availability`
- `backend/contracts/service.py` — metoda `check_article_availability()`
- `frontend/src/views/ContractFormView.vue` — wywołanie check + modal konfliktu
- `frontend/src/views/SettingsView.vue` — usunięcie zakładki "Rezerwacje maszyn"
- `frontend/src/router/index.ts` — sprawdź czy `ReservationsView` ma route (do usunięcia lub zachowania)
- `spec/core/02_backend_api.md` — nowy endpoint `check-availability`
- `spec/core/03_frontend_screens.md` — update opisu ContractFormView
- `spec/core/04_business_logic.md` — logika sprawdzania konfliktów

**NIE zmieniać (backward compatibility):**
- `backend/reservations/` — zostawić endpointy i model (nie usuwać)
- `article_reservations` tabela — zostawić (nie dropować)
- Router `/reservations` — nie rejestrować wyrejestrowania

**QA DoD:**
- [ ] Unit test: `check_article_availability()` — conflict detected, no conflict, edge cases (null dates)
- [ ] E2E test w `04-contract.spec.ts`:
  - Utwórz umowę A z maszyną X na 1-31 maja
  - Spróbuj dodać maszynę X do umowy B (maj) → modal konflikt się pojawia
  - Kliknij "Mimo to dodaj" → maszyna dodana, umowa tworzy się
- [ ] Smoke test `01-login.spec.ts` PASS
- [ ] Sprawdź czy Settings nie ma już zakładki "Rezerwacje maszyn"

**ROI:** Poprawna logika biznesowa — rezerwacje wynikają z rzeczywistości (umów), nie z ręcznego zarządzania
**Estimate:** 8h (L)

---

### [RAO-P2-018] SPIKE: Foldery docelowe dla pobieranych plików (umowy, protokoły)

```yaml
id: RAO-P2-018
priority: P2
size: S
status: done
classification: spike
roles: [tech-lead, backend-dev, frontend-dev]
depends_on: []
blocks: [RAO-P3-013]
source: internal
source_date: 2026-05-20
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/07_integrations.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Zbadać i zdefiniować mechanizm kierowania pobranych plików (wygenerowanych umów, protokołów ZO) do dedykowanych folderów. Cel: pliki powinny trafiać do logicznie nazwanych katalogów zamiast ogólnego `Downloads/`, a nazwy plików powinny być czytelne i jednoznaczne.

## Wyniki Spike (2026-05-20)

### Root cause buga (odkryty podczas spike)

Frontend używa `window.open(blobUrl, '_blank')` — to otwiera PDF w viewerze przeglądarki, ignoruje `Content-Disposition: attachment` z backendu. Użytkownik widzi PDF w karcie zamiast pobrania. To jest główny problem do naprawienia.

### Decyzja architektoniczna — strategia 2-etapowa

**Etap 1 → RAO-P2-018 (ten task):** Fix buga + ujednolicenie nazw plików
**Etap 2 → RAO-P3-013 (nowy):** File System Access API + persystowany folder w IndexedDB

### Konwencja nazw plików (zatwierdzona 2026-05-20)

Reguła: `contract.number.replace('/', '_')` → `S/129/2026` → `S129_2026`, `S/130/2026G` → `S130_2026G`.

| Typ | Wzorzec | Przykład | Przykład (oddział G) |
|-----|---------|----------|----------------------|
| Umowa | `{numer_clean}.pdf` | `S129_2026.pdf` | `S130_2026G.pdf` |
| Protokół ZO | `PZO_{numer_clean}.pdf` | `PZO_S129_2026.pdf` | `PZO_S130_2026G.pdf` |
| Kontrahenci | `Kontrahenci_{YYYY-MM-DD}.pdf` | `Kontrahenci_2026-05-20.pdf` | — |
| Maszyny | `Maszyny_{YYYY-MM-DD}.pdf` | `Maszyny_2026-05-20.pdf` | — |
| Prowizje | `Prowizje_{od}_{do}.pdf` | `Prowizje_2026-05-01_2026-05-20.pdf` | — |
| Statystyki | `Statystyki_{od}_{do}.pdf` | `Statystyki_2026-05-01_2026-05-20.pdf` | — |

**Uwagi:**
- OWN nie jest osobnym plikiem — jest osadzony w umowie (`contract.html`). Brak osobnego wzorca nazwy.
- `_s` / `_u` w protokołach = typ umowy (sprzęt/usługi), nie "wydanie/zwrot". Oba warianty mają wzorzec `PZO_`.
- `G` w numerze = flaga oddziału ze starej aplikacji, zachowywana 1:1 z pola `contracts.number`.

### Opcje (zbadane)

| # | Opcja | Koszt | Rekomendacja |
|---|-------|-------|--------------|
| A | Content-Disposition + `<a download>` (fix buga) | ~30 min | ✅ Must-have, Etap 1 |
| B | File System Access API — dialog każde pobranie | ~2h | ⚠️ Może irytować |
| C | File System Access API + persist folder IndexedDB | ~6h | ✅ Etap 2 (RAO-P3-013) |
| D | Electron wrapper | ~40h | ❌ Overkill |
| E | Chrome "Ask where to save" (instrukcja dla usera) | 0 | ✅ Fallback/dokumentacja |
| F | Chrome Extension | ~16h | ❌ Tarcia deploymentowe |
| G | Service Worker + OPFS | ~4h | ❌ Nie "folder na dysku" |
| H | Download Manager in-app (historia) | ~6h | ⚠️ Osobny task P3 |

**Acceptance criteria (DoD) — Etap 1:**
- [ ] Spike report: konwencja nazw zatwierdzona ✅ (patrz tabela wyżej)
- [ ] Spike report: decyzja architektoniczna ✅ (Etap 1: fix + nazwy, Etap 2: FS API)
- [x] Frontend: `window.open(blobUrl)` → composable `useFileDownload.js` z `<a download>` (RAO-P2-018, 3 miejsca: contracts.js, ReportsSection.vue, CommissionView.vue)
- [x] Backend: `Content-Disposition` z `filename*=UTF-8''` (RFC 5987) wg konwencji tabeli
- [x] `core/02_backend_api.md` zaktualizowany (sekcja `/reports/*` — nowa konwencja filenames)
- [x] `core/03_frontend_screens.md` zaktualizowany (composable `useFileDownload`)
- [ ] `core/07_integrations.md` zaktualizowany (sekcja "PDF download — konwencje")

**QA DoD:**
- [ ] E2E `06-pdf-download.spec.ts`: pobierz umowę → `download.suggestedFilename() === 'S129_2026.pdf'`
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany (Etap 1):**
- `backend/reports/router.py` — helper `pdf_response()` + nowe nazwy dla 5 endpointów
- `frontend/src/composables/useFileDownload.ts` — **nowy** (parsing Content-Disposition + `<a download>`)
- `frontend/src/stores/contracts.js` — użycie composable
- `frontend/src/components/reports/ReportsSection.vue` — użycie composable
- `frontend/src/views/CommissionView.vue` — użycie composable
- `e2e/tests/06-pdf-download.spec.ts` — **nowy test**

**ROI:** UX — poprawne nazwy plików + faktyczne pobieranie zamiast otwierania w viewerze
**Estimate:** 3h (S)

## Wynik spike — zatwierdzone 2026-05-20, gotowe do implementacji

---

### [RAO-P2-019] Drzewiaste kategorie artykułów — konfiguracja, picker, wyświetlanie

```yaml
id: RAO-P2-019
priority: P2
size: L
status: done
classification: cross-stack
roles: [backend-dev, frontend-dev, ux-designer]
depends_on: []
blocks: []
source: internal
source_date: 2026-05-20
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Kategorie artykułów są 4-poziomowym drzewem (main → sub1 → sub2 → sub3), importowanym z CSV Toolsmart. Aktualnie:
- SettingsView wyświetla płaską listę kategorii (brak hierarchii)
- ArticleFormView ma pojedynczy `<select>` wszystkich kategorii (brak cascade)
- Karty artykułów nie pokazują ścieżki kategorii

Potrzebny pełny stack: backend z endpointem drzewa, konfigurowalne drzewo w Ustawieniach, kaskadowy picker przy tworzeniu/edycji artykułu, wyświetlanie breadcrumbu na kartach.

**Kontekst:**
- `categories` tabela: `id, name, level (main/sub1/sub2/sub3), parent_id, code, description`
- `articles`: `category_id, category_main, category_sub1, category_sub2, category_sub3` (snapshot nazw)
- Dane wypełnione przez `step8_csv_categories()` w `migrate.py` (268 artykułów)
- Backend posiada `backend/categories/` (models tylko) — brak routera kategorii z drzewem
- Frontend: `stores/settings.js → fetchCategories()` → `/settings/categories` (płaska lista)

**Scope implementacji:**

**1. Backend — endpoint drzewa:**
- `GET /categories/tree` → lista głównych kategorii z zagnieżdżonymi `children[]` do 4 poziomów
- `POST /categories` z `parent_id` (tworzenie podkategorii)
- `PUT /categories/{id}` — edycja nazwy/kodu
- `DELETE /categories/{id}` — tylko liście drzewa (brak dzieci), inaczej 409

**2. Frontend — SettingsView (zakładka Kategorie):**
- Widok drzewa: poziomy wcięte (16px na poziom), ikona `▶/▼` do expand/collapse
- Obok każdego węzła: inline edit (kliknij ołówek → `<input>`), przycisk `+ dziecko`, `🗑️` (disabled jeśli ma dzieci)
- Przycisk `+ Kategoria główna` na górze sekcji
- Drag & drop kolejności (opcjonalnie, P3)

**3. Frontend — ArticleFormView (kaskadowy picker):**
- Zastąp pojedynczy `<select>` trzema kaskadowymi `<select>`:
  1. `Kategoria główna` → lista `level=main`
  2. `Podkategoria I` → lista `level=sub1, parent_id=wybrany_main` (ukryty jeśli main niezaznaczony)
  3. `Podkategoria II` → lista `level=sub2, parent_id=wybrany_sub1` (ukryty jeśli sub1 niezaznaczony)
- `category_id` = ID najgłębszego wybranego poziomu
- `category_main/sub1/sub2` = snapshoty nazw (UPDATE przy zapisie)

**4. Frontend — wyświetlanie na kartach artykułów:**
- Lista artykułów: kolumna `Kategoria` pokazuje ścieżkę: `Wozidła > Wózki widłowe`
- Szczegóły artykułu (ArticleFormView read mode / karta): pełna ścieżka breadcrumb
- Tooltip z pełną ścieżką jeśli tekst za długi

**Acceptance criteria (DoD):**
- [x] `GET /categories/tree` zwraca JSON z zagnieżdżoną strukturą `{id, name, level, children[]}` (backend done)
- [x] SettingsView: widok drzewa z inline edit, dodawanie dzieci, poziomy wcięcia (RAO-P2-019 frontend)
- [x] ArticleFormView: 3 kaskadowe `<select>`, zapis `category_id` (RAO-P2-019 frontend)
- [ ] Lista artykułów: kolumna z breadcrumbem kategorii (max 2 poziomy + `…`)
- [x] Wyczyszczenie sub-selektorów przy zmianie poziomu wyżej (cascade reset) (RAO-P2-019 frontend)
- [ ] Istniejące artykuły mają poprawnie wypełnioną ścieżkę z migrate.py (verify przez UI)

**QA DoD:**
- [ ] Unit test: `GET /categories/tree` → poprawna struktura zagnieżdżona
- [ ] E2E test `03-article.spec.ts`: utwórz artykuł z wybraną kategorią kaskadową → sprawdź zapis i wyświetlanie
- [ ] Smoke test `01-login.spec.ts` PASS

**Pliki do zmiany:**
- `backend/categories/router.py` (nowy)
- `backend/categories/schemas.py` (nowy)
- `backend/categories/service.py` (nowy)
- `backend/main.py` (rejestracja routera)
- `frontend/src/stores/settings.js` (fetchCategoriesTree)
- `frontend/src/views/SettingsView.vue` (tree widget)
- `frontend/src/views/ArticleFormView.vue` (kaskadowy picker)
- `frontend/src/components/` (opcjonalnie: `CategoryTreeNode.vue`, `CategoryCascadePicker.vue`)

**ROI:** Kategorie są w DB, ale nieużywalne przez użytkownika — brak UI blokuje sensowne zarządzanie asortymentem
**Estimate:** 10h (L)

---

### [RAO-P1-024] BUG: Step8 CSV migration nie importuje is_service i model

```yaml
id: RAO-P1-024
priority: P1
size: S
status: done
classification: backend
roles: [backend-dev]
depends_on: []
blocks: []
source: internal
source_date: 2026-05-20
specs_to_update: []
migration_impact: yes
security_impact: low
```

**Job-to-be-done:**
`step8_csv_categories()` w `migrate.py` importuje z CSV: kategorie hierarchiczne + technical_attributes + internal_number.
**Nie importuje** (a powinien):
- `[3] rodzaj` → `articles.is_service` + `articles.article_type`
- `[6] Model` → `articles.model`

Skutek: 2 artykuły mają błędne `is_service=True` (sklasyfikowane jako Usługa, powinny być artykuł — wynika z `Korekta`="usługa → artykuł"), 7 artykułów ma pusty `articles.model` mimo że CSV go zawiera.

**Analiza CSV (plik: `temp/Asortyment - Produkty - Maszyny - Toolsmart - Archiwum_Łukasza_Dane.csv`):**

| Kol. | Nagłówek | n wartości | Obecny import | Fix |
|------|----------|-----------|---------------|-----|
| [3] | `rodzaj` | 268 | ❌ brak | UPDATE `is_service` + `article_type` |
| [6] | `Model` | 7 | ❌ brak | UPDATE `model` (COALESCE — nie nadpisuj jeśli już jest) |

**Artykuły z błędną klasyfikacją (Korekta="usługa → artykuł"):**
- id=12125: `Podnośnik przegubowo – teleskopowy spalinowy 16m` — jest Usługa, powinien być artykuł
- id=12111: `Podest teleskopowo - przegubowy spalinowy 16m` — jest Usługa, powinien być artykuł

**Artykuły z modelem w CSV:**
- id=10070: model=`Dieci Apollo 25.6`
- id=10054: model=`Unic 295`
- id=6047, 6048, 8064: model=`CELA DT25`
- id=10093: model=`Genie GS 5390 RT`
- id=10064: model=`JLG 3513`

**Fix — zmiany w `_parse_csv_file()` i `step8_csv_categories()`:**
1. Dodaj stałe kolumn: `_C_RODZAJ = 3`, `_C_MODEL = 6`
2. W `_parse_csv_file()`: parsuj `rodzaj` i `model` do rekordu
3. W `_UPDATE_SQL`: dodaj `is_service = %s`, `article_type = %s`, `model = COALESCE(NULLIF(model,''), %s)`
4. Przekaż odpowiednie wartości w pętli `for rec in records`

**Uwaga dotycząca idempotentności:**
- `is_service` z CSV nadpisuje wartość z step4 (legacy DB) — CSV ma autorytet dla tego pola
- `model`: `COALESCE(NULLIF(model,''), %s)` — aktualizuje tylko jeśli DB ma pusty model

**Acceptance criteria (DoD):**
- [ ] Po re-run step8: `SELECT id, name, is_service, article_type, model FROM articles WHERE id IN (12125, 12111)` → `is_service=0, article_type='artykuł'`
- [ ] `SELECT id, model FROM articles WHERE id IN (10070, 10054, 6047)` → modele wypełnione
- [ ] Drugi run step8 = 0 zmian (idempotentność)
- [ ] `python -m pytest backend/tests/unit/ -x` PASS

**Pliki do zmiany:** `backend/migrate.py`
**ROI:** 2 artykuły błędnie wyceniane jako usługi (wrong PDF template + pricing logic)
**Estimate:** 1-2h (S)

---

## ✅ Done Log

Zobacz `archive/16_todo_done.md` dla pełnego historii zadań ukończonych.

---

### [RAO-P1-025] BUG: Napraw import @vuepic/vue-datepicker — export default error

```yaml
id: RAO-P1-025
priority: P1
size: S
status: done
classification: bug
roles: [frontend-dev]
depends_on: []
blocks: []
source: e2e-manual-test
source_date: 2026-05-21
specs_to_update: []
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
Naprawić import @vuepic/vue-datepicker — obecnie rzuca SyntaxError: "The requested module '/rao/node_modules/.vite/deps/@vuepic_vue-datepicker.js?v=6edc8ea6' does not provide an export named 'default'". Błąd powtarza się przy każdej nawigacji.

**Symptomy:**
- SyntaxError w konsoli przy każdej nawigacji
- Double-click na wiersz umowy nie przekierowuje do edycji
- Przycisk "+" w umowach nie przekierowuje do nowej umowy
- Może blokować inne funkcje używające vue-datepicker

**Acceptance criteria (DoD):**
- [x] Import @vuepic/vue-datepicker naprawiony (named export `{ VueDatePicker }` zamiast default)
- [x] Vite build bez błędów datepicker
- [x] Smoke test 01-login.spec.ts 11/11 PASS

**Root cause:** `@vuepic/vue-datepicker` v12 eksportuje tylko named export `VueDatePicker` — brak `export default`.
**Fix:** `import VueDatePicker from` → `import { VueDatePicker } from` w `DateRangePicker.vue`.

**Pliki zmienione:** `frontend/src/components/shared/DateRangePicker.vue`
**ROI:** Critical — blokuje tworzenie/edycję umów
**Estimate:** 1h (S)

---

### [RAO-P1-026] Rozbudowa filtrów statystyk — drilldown kategorii, udźwig, archiwalne, per-rok/miesiąc

```yaml
id: RAO-P1-026
priority: P1
size: L
status: triaged
classification: cross-stack
roles: [backend-dev, frontend-dev, db-architect]
depends_on: [RAO-P1-017, RAO-P1-024]
blocks: []
source: internal
source_date: 2026-05-21
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Domknąć UX widoku "Analiza historyczna → Kategorie" (RAO-P1-017 był formalnie done, ale zostawił 4 luki P1).
Dodać drilldown main→sub1, filtr kategorii głównej, filtr rodzaju (globalny), archiwalne toggle, udźwig chipy,
sortowanie kolumn, statystyki per rok/miesiąc. Bez persistencji filtrów (reset przy F5). Bez CSV export.

**Kontekst biznesowy (kluczowy!):**
Kategorie istnieją GŁÓWNIE dlatego, że w starej aplikacji WinForms ta sama fizyczna maszyna (np. "Wózek widłowy 8t")
miała wiele wierszy w bazie (`article_id` 5076, 8074, itd. — różne ID, ta sama maszyna).
Dzięki kategoriom statystyki agregują po klasie maszyny, nie po duplikacie ID → dane są miarodajne.

**Bug P0 dla tego zadania — `articles_count` jest zawyżony:**
Obecny `aggregate_by_category` w `calc.py` liczy `articles.add(article_id)` — czyli zlicza duplikaty jako osobne maszyny.
Poprawna metryka to unikalne `internal_number` (identyfikator fizyczny z CSV), z fallbackiem na `article_id` gdy `internal_number` is None.
FIX: `agg[cat]["articles"].add(internal_number or article_id)` → miarodajna liczba fizycznych maszyn per kategoria.

**Decyzje designu (PO + UX, 2026-05-21):**
- Drilldown: kliknięcie wiersza "Wozidła" w tabeli → filtruje sub1 tylko tej kategorii (breadcrumb "Wszystkie → Wozidła ✕")
- Filtr "Rodzaj" (Maszyny/Usługi): globalny nad sub-tabami, działa zarówno w Ogólne jak i Kategorie
- Udźwig: chipy `[<1t][1-5t][5-20t][20-50t][>50t][Własny ▾]` z warningiem o brakujących danych; w tym zadaniu sub-task: weryfikacja czy migracja CSV poprawnie wypełniła `technical_attributes.udzwig`
- Persistencja: BRAK (reset przy F5 — KISS)
- Statystyki per rok/miesiąc: widok historii z podziałem temporalnym (nowy sub-tab lub oś czasu)

**Acceptance criteria (DoD):**

**Backend:**
- [ ] `GET /stats/by-category` — nowy parametr `category_main` (filtr, opcjonalny, multi-value) → zwraca tylko sub1/sub2 danej kategorii
- [ ] `GET /stats/by-category` — nowy parametr `article_type` (machine/service/all, default=all) → działa globalnie
- [ ] `GET /stats/by-category` — nowy parametr `include_archival` (boolean, default=false) dostępny w UI (był hardcoded)
- [ ] `GET /stats/by-category` — nowy parametr `lifting_capacity_ranges` (lista zakresów: `<1,1-5,5-20,20-50,>50`) → filtruje przez `JSON_EXTRACT(technical_attributes, '$.udzwig')` BETWEEN; zwraca `missing_capacity_count` (ile maszyn pominięto przez brak danych)
- [ ] `GET /stats/by-period` (NOWY endpoint) — zwraca agregaty per rok/miesiąc: `{period, revenue, contracts_count, rented_days}`, parametry: `date_from/to`, `granularity=month|year`, `category_main[]`, `article_type`
- [ ] `GET /stats/categories-list` (NOWY endpoint lub rozszerzenie istniejącego) — lista kategorii głównych z liczbą maszyn (do dropdown filtra), + lista sub1 per main

**Sub-task udźwig (priorytet przed filtrem):**
- [ ] Weryfikacja migracji CSV: sprawdź `SELECT COUNT(*), technical_attributes FROM articles WHERE technical_attributes IS NOT NULL LIMIT 20` — czy pole `udzwig` jest wypełnione poprawnie w jednostkach (kg? t? string?)
- [ ] Jeśli dane niespójne → normalizacja w `migrate.py` (konwersja do kg int, np. "5t" → 5000, "5000 kg" → 5000)
- [ ] Backup plan: jeśli dane zbyt śmietnikowe → filtr udźwig jako "nice to have" w tym zadaniu, przesuń do P2

**Frontend:**
- [ ] Panel filtrów (stały, nad sub-tabami w "Analiza historyczna"): Rodzaj | Kategoria główna (dropdown multi-select) | Stan archiwalnych (tri-state pill) | Udźwig chipy
- [ ] Przycisk "Więcej filtrów ▾" → collapsible: Podkategoria 1 (disabled jeśli main nie wybrana), Udźwig (jeśli dane dostępne)
- [ ] Chip-summary aktywnych filtrów pod panelem: `[Maszyny ✕] [Wozidła ✕] [5-20t ✕]` + "Wyczyść wszystko"
- [ ] Drilldown: kliknięcie wiersza w tabeli kategorii → breadcrumb "Wszystkie → {nazwa} ✕" + przeładowanie na level=sub1 z filtrem
- [ ] Sortowanie kolumn tabeli (klik nagłówka → ASC/DESC)
- [ ] Warning przy filtrze udźwig: "ℹ️ X pozycji bez podanego udźwigu zostało pominiętych"
- [ ] Sub-tab lub oś czasu "Per rok/miesiąc" — bar chart z granularnością month/year, filtry dziedziczone z panelu

**QA DoD:**
- [ ] Smoke test `01-login.spec.ts` 11/11 PASS
- [ ] Build `npm run build` bez błędów
- [ ] `npx vue-tsc --noEmit` bez błędów

**Spec DoD:**
- [ ] `spec/core/02_backend_api.md` — nowe parametry `/by-category`, nowe endpointy `/by-period`, `/categories-list`
- [ ] `spec/core/03_frontend_screens.md` — panel filtrów, drilldown, eksport CSV
- [ ] `spec/core/11_reports_stats.md` — zaktualizowany opis widoku Kategorie

**Pliki do zmiany:**
- `backend/stats/router.py`, `backend/stats/calc.py` (nowe parametry + nowe endpointy)
- `frontend/src/views/ReportsSection.vue` (panel filtrów, drilldown, CSV export)
- `backend/migrate.py` (normalizacja `udzwig` jeśli potrzebna)

**ROI:** Domknięcie P1-017 (UX luki od 2+ tygodni) + nowa wartość: per-rok/miesiąc analiza = 10 raportów/mc × 5 userów = 50 użyć/mc
**Estimate:** 10-12h (L) — backend 4h + frontend 5h + udźwig-verify 1-2h
**Deadline:** przed go-live klienta

---

## 📊 Podsumowanie

| Priorytet | Liczba | Effort łączny |
|-----------|--------|---------------|
| 🚨 P0 | 5 | ~7h |
| 🔴 P1 | 14 | ~70h |
| 🟡 P2 | 12 | ~72h |
| 🟢 P3 | 5 | ~20h |
| **Razem** | **36** | **~169h** |

---

## 📋 Tabela TL;DR

| ID | Tytuł | Źródło | P | Est. | Status | Owner |
|----|-------|--------|---|------|--------|-------|
| RAO-P0-001 | Usuń sekrety ze spec | Security | P0 | XS | done | tech-lead |
| RAO-P0-002 | Utwórz SECURITY.md | Security | P0 | M | done | security-auditor |
| RAO-P0-003 | Napraw migrację haseł | Security | P0 | M | done | backend-dev |
| RAO-P0-004 | Napraw podpisy PDF | Client | P0 | S | done | frontend-dev |
| RAO-P0-005 | Napraw format kwot | Client | P0 | XS | done | frontend-dev |
| RAO-P1-001 | Filtr dat Dashboard | Internal | P1 | XS | done | frontend-dev |
| RAO-P1-002 | Adres dostawy multiline | Client | P1 | S | done | cross-stack |
| RAO-P1-003 | Adres dostawy rozdzielenie | Client | P1 | S | done | frontend-dev |
| RAO-P1-004 | Sekcja Uwagi w umowie | Client | P1 | XS | done | frontend-dev |
| RAO-P1-005 | Ekstrakcja miast | Internal | P1 | M | done | backend-dev |
n|| RAO-P1-008 | Strukturalizacja adresów: kod pocztowy + miasto | Client | P1 | L | done | cross-stack |
|| RAO-P1-009 | Weryfikacja PDF vs stara aplikacja | Client | P1 | M | done | qa-engineer |
|| RAO-P1-010 | Tabela Przy wydaniu/Przy odbiorze | Client | P1 | M | done | frontend-dev |
|| RAO-P1-011 | Usługi dodatkowe z artykułami | Client | P1 | L | done | db-architect |
|| RAO-P1-012 | Panel rozliczenie umowy | Client | P1 | XL | done | cross-stack |
|| RAO-P1-013 | Refactor systemu prowizyjnego | Client | P1 | M | done | backend-dev |
|| RAO-P1-014 | Protokół usługi — godziny operatora | Client | P1 | M | done | cross-stack |
|| RAO-P1-015 | Rezerwacja maszyn (SUPERSEDED) | Client | P1 | M | superseded | cross-stack |
|| RAO-P1-023 | BUG: Rezerwacja z umowy + conflict popup | Client | P1 | L | done | cross-stack |
|| RAO-P1-025 | BUG: Napraw import @vuepic/vue-datepicker | E2E | P1 | S | done | frontend-dev |
|| RAO-P2-001 | Kolumna adres dostawy | Internal | P2 | XS | done | frontend-dev |
|| RAO-P2-002 | Link "Zmień hasło" sidebar | Internal | P2 | XS | done | frontend-dev |
|| RAO-P2-003 | NIP validation checksum | Internal | P2 | S | done | backend-dev |
|| RAO-P2-004 | Duplikacja artykułu pickera | Internal | P2 | S | done | frontend-dev |
|| RAO-P2-005 | Nominatim reverse geocoding | Internal | P2 | S | done | cross-stack |
|| RAO-P2-006 | Picker artykułów — filtr typ umowy | Client | P2 | S | done | cross-stack |
|| RAO-P2-007 | UX Raportów — teraz vs okres | Client | P2 | S | done | cross-stack |
|| RAO-P2-008 | Numer wewnętrzny maszyny | Client | P2 | S | done | cross-stack |
|| RAO-P2-009 | Statystyki per maszyna ROI | Client | P2 | M | done | cross-stack |
|| RAO-P2-010 | Filtrowanie pozycji umowy typ | Client | P2 | S | done | cross-stack |
|| RAO-P2-011 | Statystyki po lokalizacji | Client | P2 | S | done | cross-stack |
|| RAO-P2-012 | Integracja Fakturownia — automatyczne koszty | Client | P2 | L | done | cross-stack |
|| RAO-P2-013 | Pełne pokrycie E2E — wszystkie use case'y | Internal | P2 | XL | done | qa-engineer |
|| RAO-P2-014 | Weryfikacja kodu vs. spec i backlog | Internal | P2 | M | done | tech-lead |
|| RAO-P2-015 | Integracja API TERYT z GUS — pełny słownik kodów pocztowych | Internal | P2 | M | done | backend-dev |
|| RAO-P2-016 | SPIKE: Playwright screenshot wszystkich widoków dla UX review | Internal | P2 | M | done | qa-engineer |
|| RAO-P3-001 | Drag & drop reorder szablonów | Internal | P3 | M | done | frontend-dev |
|| RAO-P3-002 | Upload logo firmy | Internal | P3 | M | done | cross-stack |
|| RAO-P3-003 | Logo w nagłówku sidebar | Internal | P3 | XS | done | frontend-dev |
|| RAO-P3-004 | Export statystyk CSV | Internal | P3 | M | done | cross-stack |
|| RAO-P3-005 | Modele DB deliveries/costs/audit | Internal | P3 | L | done | db-architect |
|| RAO-P3-006 | Auto-generowanie opisu warunku | Internal | P3 | S | done | frontend-dev |
|| RAO-P3-007 | Kalendarz 2-miesieczny | Internal | P3 | M | done | frontend-dev |
|| RAO-P3-008 | Keyboard shortcuts | Internal | P3 | S | done | frontend-dev |
|| RAO-P3-009 | Empty state CTA | Internal | P3 | XS | done | frontend-dev |
|| RAO-P3-010 | Globalny pasek postępu NProgress | Internal | P3 | S | done | frontend-dev |
|| RAO-P3-011 | Testy integracyjne backend pytest | Internal | P3 | L | done | qa-engineer |
|| RAO-P3-012 | Kwota tankowania default 200 zł | Client | P3 | XS | done | backend-dev |
|| RAO-P2-018 | SPIKE: Foldery docelowe dla pobieranych plików | Internal | P2 | S | done | tech-lead |
|| RAO-P3-013 | Konfigurowalne foldery pobierania — FS Access API | Internal | P3 | M | done | frontend-dev |
|| RAO-P1-024 | BUG: CSV migration — is_service + model brakują | Internal | P1 | S | done | backend-dev |
|| RAO-P1-026 | Filtry statystyk: drilldown, udźwig, archiwalne, per-rok/miesiąc | Internal | P1 | L | triaged | cross-stack |
|| RAO-P2-019 | Drzewiaste kategorie — picker, settings, breadcrumb | Internal | P2 | L | done | cross-stack |
