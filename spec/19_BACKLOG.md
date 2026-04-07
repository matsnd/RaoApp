# RAO App — Master Backlog (Pozostałe zadania)

> **Ostatnia aktualizacja:** 2026-04-08  
> **Metoda weryfikacji:** Cross-role audit + inspekcja kodu (grep + odczyt plików) + **analiza kodu WinForms**  
> **Stan bazy:** Migracja OK — 516 umów, 614 pozycji, 875 warunków, 531 kontrahentów  
> **Poprzednie TODO:** `16_TODO.md` | **Poprzedni audit:** `13_AUDIT_ALL_PROCESSES.md` (archiwum) | **Instrukcja użytkownika:** `20_USER_GUIDE_SETTLEMENT.md`

---

## ✅ Co zostało zrobione (weryfikacja z kodem 2026-04-07)

| Blok | Element | Weryfikacja |
|------|---------|-------------|
| **P0 Umowy** | ConditionPanel.vue — UI warunków rozliczenia | `frontend/src/components/contracts/ConditionPanel.vue` ✅ |
| **P0 Umowy** | Auto-kalkulacja `total_value` (recalcTotal) | `ContractFormView` → `recalcTotal()` + `POST /contracts/{id}/recalculate` ✅ |
| **P0 Umowy** | Modal pozycji z 6 brakującymi polami (billing_freq, billing_unit, rate_type_id, delivery_date, supplier_id, costs) | `posForm` w ContractFormView ✅ |
| **P1 Umowy** | Dropdown adresów kontrahenta | `contractorAddresses` + `select` w ContractFormView ✅ |
| **P1 Umowy** | Pole "Pozostało" (computed) | `remainingValue = total - prepayment - invoice` ✅ |
| **P1 Umowy** | Branch/Oddział selector | `form.branch_id` + `settingsStore.branches` ✅ |
| **P1 Umowy** | Service fees CRUD (inline Excel-style) | `startEditFee`, `addFeeRow`, `deleteServiceFee`, `resetServiceFees`, `applyPreset` ✅ |
| **P1 Umowy** | Sprawdzanie dostępności artykułu + badge | `articleAvailability` + `checkAvailability` ✅ |
| **P1 Dashboard** | BUG `type` → `contract_type` w filtrze | `params.contract_type = contractTypeFilter.value` ✅ |
| **P1 Kontrahenci** | Pole `landline_phone` | `v-model="form.landline_phone"` ✅ |
| **P1 Kontrahenci** | Przycisk "Dodaj umowę" | `addContract()` → `router.push({path:'/contracts/new', query:{contractor_id}})` ✅ |
| **P1 Kontrahenci** | Auto-tworzenie adresu po GUS | `store.createAddress()` w `gusLookup()` ✅ |
| **P1 Kontrahenci** | Zapis `gus_date` | `form.value.gus_date = new Date().toISOString()` ✅ |
| **P1 Raporty** | Update `print_date` po PDF | `contract.print_date = datetime.utcnow()` w reports/router.py ✅ |
| **P1 Raporty** | PDF preview w nowej karcie | `window.open(url, '_blank')` ✅ |
| **P1 Settings** | Edit/delete kategorii, typów stawek, szablonów, handlowców | `deleteCat`, `deleteRt` + inline edit w SettingsView ✅ |
| **P1 Auth** | Admin panel użytkowników | `AdminView.vue` — pełny CRUD użytkowników ✅ |
| **Post-audit** | PDF czcionki na Linux | Roboto bundled `backend/reports/fonts/` ✅ |
| **Post-audit** | Niewydrukowane + Nieaktualne wydruki w HomeView/WorkerView | `/stats/unprinted-contracts`, `/stats/stale-print-contracts` ✅ |
| **Post-audit** | Responsywność formularzy | `forms.css` form-row-2/3/4 display:grid + media queries ✅ |

---

## 🔴 P1 — Ważne (pełna funkcjonalność)

### B1 · Filtrowanie po zakresie dat w Dashboard

**Co:** Na liście umów brak możliwości filtrowania po zakresie `date_from`/`date_to`.  
**Kontekst:** `DashboardView.vue` — sekcja contracts. Backend `list_contracts()` już przyjmuje `date_from` i `date_to` jako parametry query.  
**Do zrobienia:** Frontend — 2 inputy `type="date"` w toolbarze + `params.date_from / params.date_to` przy wywołaniu.  
**Effort:** XS · **Role:** Frontend  

---

## 🟡 P2 — Ulepszenia (produkcja lepsza)

### B2 · Kolumna "Adres dostawy" w liście umów

**Co:** W tabeli umów (DashboardView) brak kolumny z adresem dostawy.  
**Kontekst:** `contract.delivery_address` istnieje w modelu i API response. Dodać `<th>` + `<td>` w tabeli umów.  
**Effort:** XS · **Role:** Frontend  

### B3 · Link "Zmień hasło" w sidebar/profilu

**Co:** Brak dostępu do zmiany hasła z UI po zalogowaniu (endpoint `/auth/change-password` istnieje, route `/change-password` istnieje, brak przycisku/linku w nawigacji).  
**Kontekst:** `AppSidebar.vue` — dodać link przy "Wyloguj".  
**Effort:** XS · **Role:** Frontend  

### B4 · NIP validation (checksum algorytm)

**Co:** Przy tworzeniu/edycji kontrahenta brak walidacji sumy kontrolnej NIP (tylko sprawdzana długość 10 znaków).  
**Kontekst:** `backend/contractors/` — dodać funkcję `validate_nip_checksum()`. Spec: `04_BUSINESS_LOGIC.md §13`.  
**Effort:** XS · **Role:** Backend  

### B5 · Duplikacja artykułu z poziomu pickera w umowie

**Co:** W pickerze artykułów (modal w ContractFormView) brak przycisku "Duplikuj" — był w starym FormAwybor.  
**Kontekst:** `ContractFormView.vue` — article picker modal + `articleStore.duplicate(id)` już istnieje w backendzie.  
**Effort:** S · **Role:** Frontend  

### B6 · Drag & drop reorder szablonów usług

**Co:** Szablony usług można dodawać ale nie zmieniać kolejności przeciąganiem. Backend `POST /settings/fee-preset-groups/reorder` istnieje.  
**Kontekst:** `SettingsView.vue` — dodać `@draggable` lub bibliotekę `vuedraggable`.  
**Effort:** M · **Role:** Frontend  

### B7 · Upload logo firmy

**Co:** Pole `logo LONGBLOB` jest w tabeli `companies` ale brak UI do uploadu/zmiany logo. Logo nie pojawia się w nagłówku sidebar (hard-coded "TOOLSMART").  
**Kontekst:** `SettingsView.vue` + `backend/settings/router.py` — nowy endpoint `POST /settings/company/logo` (multipart).  
**Effort:** M · **Role:** Backend + Frontend  

### B8 · Export statystyk do CSV

**Co:** Panel statystyk (ReportsSection) brak eksportu danych do CSV/Excel.  
**Kontekst:** `frontend/src/views/HomeView.vue` lub `DashboardView.vue` (sekcja raporty) + backend endpoint lub client-side CSV generation.  
**Effort:** M · **Role:** Frontend (lub Backend)  

### B9 · Modele DB: deliveries, costs, cost_types, audit_log

**Co:** 4 tabele z DDL nie mają modeli ORM ani endpointów API:
- `deliveries` — dane dostawy z geolokalizacją
- `costs` — dodatkowe koszty per pozycja umowy (uwaga: `contract_positions.costs` jako pole decimal już działa)
- `cost_types` — typy kosztów  
- `audit_log` — log zdarzeń systemowych

**Weryfikacja kodu WinForms:** `settlements` (stara: `rozliczenie`) była **cache'm technicznym** — 1 wiersz/dzień maszyny, generowany przy kliknięciu "Rozlicz". Użytkownik NIE WIDZIAŁ tej tabeli w UI. Obecnie zastąpiona przez `calculate_position_value()`.

**Kontekst:** `backend/` — nowe moduły lub rozszerzenia istniejących.  
**Effort:** M (każda tabela) · **Role:** Backend + DBA  
**Priorytet:** P2 (nie blokuje produkcji — funkcjonalność pokryta przez warunki + auto-calc)  

### B10 · Nominatim — reverse geocoding w formularzu umowy

**Co:** Po wyborze adresu dostawy brak automatycznego geokodowania współrzędnych. Endpoint `POST /integrations/reverse-geocode` istnieje w backendzie, ale frontend go nie wywołuje.  
**Kontekst:** `ContractFormView.vue` — `onAddressSelect()` → wywołaj endpoint → zapisz lat/lng.  
**Effort:** S · **Role:** Frontend  

### B11 · Auto-generowanie opisu warunku w ConditionPanel

**Co:** W starym FormW.cs opis warunku był auto-generowany ("stawka 5000 zł/tyg. do 5 tygodni"). Nowy ConditionPanel nie generuje go automatycznie.  
**Kontekst:** `frontend/src/components/contracts/ConditionPanel.vue` — computed/watcher na zmianach rate1, period_count, billing_unit.  
**Effort:** S · **Role:** Frontend  

### B12 · Kalendarz 2-miesieczny zamiast date inputs w umowie

**Co:** W starym FormU4 wizualny kalendarz 2-miesieczny do wyboru dat od/do. Nowy formularz ma zwykłe `<input type="date">`.  
**Kontekst:** `ContractFormView.vue` — opcjonalnie zastąpić inputy data komponentem `vue-datepicker` lub własnym.  
**Effort:** M · **Role:** Frontend · **Uwaga:** Niski priorytet — obecna implementacja jest funkcjonalna.  

---

## 🟢 P3 — Polishing (nice-to-have)

### B13 · Keyboard shortcuts

| Skrót | Akcja |
|-------|-------|
| `Ctrl+N` | Nowy rekord (kontekstowo) |
| `Escape` | Zamknij modal |
| `Enter` na wierszu tabeli | Otwórz edycję |

**Effort:** S · **Role:** Frontend  

### B14 · Empty state z CTA na nowej instalacji

**Co:** Na pustej bazie lista umów jest pusta bez wskazówki co zrobić.  
**Propozycja:** "Utwórz pierwszą umowę →" button w empty state.  
**Effort:** XS · **Role:** Frontend  

### B15 · Globalny pasek postępu (NProgress)

**Co:** Każdy widok ma własny spinner; brak globalnego feedbacku nawigacji.  
**Propozycja:** `NProgress.js` lub CSS progress bar w `AppLayout.vue` odpalany na każde zapytanie API.  
**Effort:** S · **Role:** Frontend  

### B16 · Logo firmy w nagłówku sidebar

**Co:** Sidebar ma "TOOLSMART" hard-coded. Po zaimplementowaniu B7 (upload logo) — podmienić na `<img>`.  
**Zależność:** B7 · **Effort:** XS · **Role:** Frontend  

### B17 · Testy integracyjne backend (pytest)

**Co:** `spec/17_TESTING_PLAN.md` definiuje testy które nie zostały zaimplementowane:
- Testy integracyjne API (pytest + httpx, SQLite in-memory)
- E2E scenariusze SC-01..SC-10 (Playwright)
- Testy migracji (row counts)  

**Kontekst:** `backend/tests/` (prawdopodobnie brak katalogu) + `e2e/tests/`.  
**Effort:** L · **Role:** QA + Backend  

---

## 📊 Podsumowanie

| Priorytet | Liczba | Effort łączny |
|-----------|--------|---------------|
| 🔴 P1 | 1 (B1) | XS (~30 min) |
| 🟡 P2 | 11 (B2–B12) | ~3–4 dni dev |
| 🟢 P3 | 5 (B13–B17) | ~2–3 dni dev |

---

## 🗺️ Rekomendowana kolejność (Sprint 4+)

### Sprint 4 — Quick wins + P1

1. **B1** — filtr dat w Dashboard (XS)
2. **B2** — kolumna adres dostawy (XS)
3. **B3** — link "Zmień hasło" (XS)
4. **B4** — NIP validation (XS)
5. **B5** — duplikacja artykułu z pickera (S)

### Sprint 5 — Settings + UX

6. **B6** — drag & drop reorder (M)
7. **B7** — upload logo (M)
8. **B11** — auto-opis warunku (S)
9. **B10** — Nominatim w umowie (S)

### Sprint 6 — Data + Export

10. **B8** — export CSV (M)
11. **B9** — modele deliveries/costs/audit_log (M)
12. **B17** — testy integracyjne (L)

### Sprint 7 — Polish

13. **B12** — kalendarz 2-miesieczny (M)
14. **B13–B16** — keyboard shortcuts, empty states, NProgress, logo sidebar

---

## 🗂️ Mapa spec plików

| Plik | Zawartość | Status |
|------|-----------|--------|
| `00_INDEX.md` | Indeks wszystkich spec plików | — |
| `01_DATABASE_DDL.md` | Schema DB | Aktualne |
| `02_BACKEND_API.md` | API endpoints spec | Aktualne |
| `03_FRONTEND_SCREENS.md` | Ekrany frontend | Aktualne |
| `04_BUSINESS_LOGIC.md` | Logika biznesowa | Aktualne |
| `05_CROSS_CHECK.md` | Cross-check GUI↔SQL | Aktualne (historyczne) |
| `12_LOGIC_AUDIT.md` | Audyt logiki WinForms | Historyczne (dla ref.) |
| `13_AUDIT_ALL_PROCESSES.md` | ⚠️ Audyt procesów (2026-03-15) | **ARCHIWUM** |
| `14_AUDIT_CONTRACT_PROCESS.md` | ⚠️ Audyt umów (2026-03-15) | **ARCHIWUM** |
| `15_BUILD_PROGRESS.md` | Dziennik buildów | Aktualizować |
| `16_TODO.md` | Historia zadań ✅ | Aktualne (19 pozycji Done) |
| `17_TESTING_PLAN.md` | Plan testów | Aktualne (do implementacji → B17) |
| `18_UX_IMPROVEMENTS.md` | ⚠️ UX propozycje (2026-03-15) | **ARCHIWUM** |
| **`19_BACKLOG.md`** | **← Ten plik. Aktualne remaining tasks** | **Aktualne** |
| **`20_USER_GUIDE_SETTLEMENT.md`** | **Instrukcja użytkownika: rozliczenie** | **Aktualne** |
