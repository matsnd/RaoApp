# Audyt Wszystkich Procesów: Stara App (WinForms) vs Nowa App (Vue+FastAPI)

> **Data:** 2026-03-15 | **Wersja:** 1.0  
> **Metoda:** Cross-role team analysis (Analityk Biznesowy + DBA + UX + Frontend Architect + Backend Architect)  
> **Nota:** Proces #1 (Dodawanie Umowy) opisany szczegółowo w `AUDIT_CONTRACT_PROCESS.md`

> ⚠️ **ARCHIWUM** — Ten dokument odzwierciedla stan z 2026-03-15. Większość P0 i P1 zidentyfikowanych tutaj zostało zaimplementowanych do 2026-04-07.  
> **Aktualny backlog → patrz `backlog/BACKLOG.md`**

---

## SPIS PROCESÓW

| # | Proces | Stara forma | Nowa forma | Status |
|---|--------|-------------|------------|--------|
| 1 | [Dodawanie/edycja umowy](#1-dodawanieedycja-umowy) | FormU4.cs + FormW.cs | ContractFormView.vue | 🔴 KRYTYCZNE BRAKI |
| 2 | [Zarządzanie kontrahentami](#2-zarządzanie-kontrahentami) | FormK.cs | ContractorFormView.vue | 🟡 DROBNE BRAKI |
| 3 | [Zarządzanie artykułami](#3-zarządzanie-artykułami) | FormA.cs + FormAwybor.cs | ArticleFormView.vue | 🟡 DROBNE BRAKI |
| 4 | [Dashboard / lista główna](#4-dashboard--lista-główna) | Form2.cs | DashboardView.vue | 🟡 DROBNE BRAKI |
| 5 | [Raporty PDF](#5-raporty-pdf) | Crystal Reports | Jinja2 + Playwright | ✅ + 🟡 |
| 6 | [Konfiguracja / Ustawienia](#6-konfiguracja--ustawienia) | Konfiguracja.cs | SettingsView.vue | 🟡 DROBNE BRAKI |
| 7 | [Logowanie i autoryzacja](#7-logowanie-i-autoryzacja) | Logowanie.cs | LoginView.vue + auth module | ✅ LEPSZE NIŻ STARE |
| 8 | [Statystyki i analityka](#8-statystyki-i-analityka) | *(nie było)* | ReportsSection.vue + stats API | ✅ NOWE |
| 9 | [Integracje zewnętrzne](#9-integracje-zewnętrzne) | GUS SOAP (C#) + Nominatim | GUS API + Nominatim API | ✅ + 🟡 |

---

## 1. Dodawanie/edycja umowy

> **Pełny szczegółowy audyt → patrz `AUDIT_CONTRACT_PROCESS.md`**

### Podsumowanie braków:

| Priorytet | Brak | Wpływ |
|-----------|------|-------|
| 🔴 P0 | Brak UI warunków rozliczenia (ConditionPanel) | System bezużyteczny — brak definiowania stawek |
| 🔴 P0 | Brak auto-kalkulacji total_value | Wartości umów = 0, raporty puste |
| 🔴 P0 | Modal pozycji brakuje 6 z 11 pól | billing_frequency, billing_unit, rate_type_id, delivery_date, supplier_id, costs |
| 🟡 P1 | Brak dropdown adresów kontrahenta | Ręczne wpisywanie adresu dostawy |
| 🟡 P1 | Brak pola "Pozostało" (total-prepay-invoice) | Brak kontroli finansowej |
| 🟡 P1 | Brak branch/oddział selector | Pole w modelu, brak w UI |
| 🟡 P1 | Service fees read-only | Brak edycji per umowa |
| 🟡 P1 | Brak sprawdzania dostępności artykułu | Możliwy podwójny wynajem |
| 🟡 P1 | Bug: param `type` vs `contract_type` | Filtr typu nie działa |

---

## 2. Zarządzanie kontrahentami

### Stary proces (FormK.cs):

| # | Akcja użytkownika | Opis | Tabele DB |
|---|---|---|---|
| 1 | Otwarcie FormK | Lista kontrahentów z VIEW `kontrahenci` | `kontrahent2` via VIEW |
| 2 | Dodaj/edytuj kontrahenta | Formularz: nazwa, NIP, REGON, PESEL, adres, kontakty, uwagi, dostawca | `kontrahent2` |
| 3 | Przycisk GUS | Pobranie danych z GUS API po NIP → auto-fill formularza | SOAP API → `kontrahent2` |
| 4 | Po GUS: propagacja adresu | Jeśli flaga `siedziba=1` → aktualizacja adresu głównego kontrahenta | `kontrahent2` + `adres` |
| 5 | Zarządzanie adresami | Lista adresów (dodaj/edytuj/usuń), flagi: siedziba, domyślna dostawa | `adres` |
| 6 | Telefon stacjonarny | Osobne pole na telefon stacjonarny | `kontrahent2.tel_stac` |
| 7 | Folder plików | Ścieżka do folderu z plikami kontrahenta | `kontrahent2.pliki` |
| 8 | Data GUS | Automatyczne zapisanie daty ostatniego pobrania z GUS | `kontrahent2.gus_data` |
| 9 | Usuwanie | Sprawdzenie aktywnych umów → blokada lub potwierdzenie | `umowa2` check → `kontrahent2` DELETE |
| 10 | Context menu "Dodaj umowę" | Z listy kontrahentów → nowa umowa z pre-fill kontrahenta | Navigacja do FormU4 |

### Nowy proces (ContractorFormView.vue):

| Element | Status | Uwagi |
|---------|--------|-------|
| Formularz kontrahenta (nazwa, NIP, REGON, PESEL) | ✅ | Kompletny |
| Adres główny (kod, miasto, ulica, lokal) | ✅ | Kompletny |
| Kontakt (2x osoba+tel, email, www) | ✅ | Kompletny |
| Checkbox dostawca | ✅ | `is_supplier` |
| Uwagi | ✅ | Textarea |
| Przycisk GUS → auto-fill | ✅ | Działa, pobiera dane SOAP |
| Adresy dostawy (CRUD) | ✅ | Panel prawy, modal dodaj/edytuj/usuń |
| Flagi: siedziba, domyślna dostawa | ✅ | Checkboxy w modalu adresu |
| Usuwanie z walidacją aktywnych umów | ✅ | Backend blokuje |
| Split-layout (formularz + adresy) | ✅ | Dobre UX |

### Cross-role analiza:

**🟡 ANALITYK BIZNESOWY:**
> Proces kontrahenta jest **prawie kompletny**. Brakuje drobnostek:
> 1. Po GUS — brak automatycznej propagacji adresu jako nowego adresu dostawy (stary app tworzył rekord w tabeli `adres` z `siedziba=1`)
> 2. Brak pola `landline_phone` (telefon stacjonarny) w UI — pole jest w modelu i schemacie, nie w formularzu
> 3. Brak pola `files_folder` — ale to legacy, nie potrzebne w web app
> 4. Brak pola `gus_date` — data ostatniego pobrania z GUS nie jest zapisywana

**🟡 DBA:**
> Model `Contractor` ma pole `landline_phone` i `gus_date` ale frontend ich nie wyświetla. Pole `files_folder` jest w DDL ale nie w modelu ORM — do usunięcia z DDL albo dodania.

**🟡 UX DESIGNER:**
> Brak kontekstowej akcji "Dodaj umowę" z poziomu kontrahenta. W starym systemie był context menu "dodaj umowę dla tego kontrahenta" → otwierał FormU4 z pre-fill. Nowa app ma to w `route.query.contractor_id` ale brak przycisku w UI kontrahenta.

**🟢 FRONTEND ARCHITECT:**
> Jedyne poprawki to: dodanie pola `landline_phone`, przycisku "Dodaj umowę dla tego kontrahenta", i opcjonalnie auto-tworzenie adresu po GUS. Niewielki effort.

**🟢 BACKEND ARCHITECT:**
> Backend jest kompletny. GUS lookup działa. CRUD kontrahentów i adresów kompletny. Walidacja NIP checksum (spec 04_BUSINESS_LOGIC.md §13) — NIE zaimplementowana, ale to P2.

### Braki — podsumowanie:

| # | Brak | Priorytet | Effort |
|---|------|-----------|--------|
| 2.1 | Pole `landline_phone` w formularzu | 🟡 P1 | XS |
| 2.2 | Przycisk "Dodaj umowę" w formularzu kontrahenta | 🟡 P1 | XS |
| 2.3 | Auto-tworzenie adresu siedziby po GUS lookup | 🟡 P1 | S |
| 2.4 | Zapis `gus_date` przy GUS lookup | 🟢 P2 | XS |
| 2.5 | Walidacja NIP checksum | 🟢 P2 | XS |
| 2.6 | Pole `latitude/longitude` w adresie (reverse geocoding) | 🟢 P2 | S |

---

## 3. Zarządzanie artykułami

### Stary proces (FormA.cs + FormAwybor.cs):

| # | Akcja użytkownika | Opis | Tabele DB |
|---|---|---|---|
| 1 | Otwarcie FormA | Formularz artykułu | `artykul3` |
| 2 | Wypełnienie danych | Nazwa, typ, nr wew., nr rej., nr seryjny, marka, model, wartość odtworzeniowa | `artykul3` |
| 3 | Kategoria | Wpisanie nazwy tekstowo → SELECT id FROM kategoria WHERE nazwa=X | `kategoria` → `artykul3.id_kategorii` |
| 4 | Właściciel (dostawca) | Wybór z listy kontrahentów-dostawców | `kontrahent2 WHERE dostawca=1` |
| 5 | Oddział | Wybór z dropdown | `oddzial` |
| 6 | Checkbox usługa | Flaga BIT | `artykul3.usluga` |
| 7 | Min. dni najmu | Pole numeryczne | `artykul3.rental_days` |
| 8 | Duplikacja | Przycisk → `CALL duplikujartykul2(id)` — kopia bez nr rej. i seryjnego | `artykul3` INSERT |
| 9 | FormAwybor (picker) | Lista artykułów z **kolorowym oznaczeniem zajętości** | VIEW `artykulyy` + procedury `sprUmowyArtykulu5/6` |
| 10 | Dostępność w pickerze | Moccasin (żółty) = na aktywnej umowie, biały = wolny | `sprDostepnosc` |
| 11 | Usuwanie | Sprawdzenie aktywnych umów → blokada | CHECK → DELETE |

### Nowy proces (ArticleFormView.vue):

| Element | Status | Uwagi |
|---------|--------|-------|
| Formularz artykułu | ✅ | Wszystkie pola: nazwa, typ, nr wew./rej./ser., marka, model, wartość |
| Kategoria (dropdown z ID) | ✅ | `settingsStore.categories` — LEPSZE niż stary system (string→ID) |
| Właściciel (dostawca) picker | ✅ | Modal z wyszukiwaniem, filtr `supplier=true` |
| Oddział (branch) dropdown | ✅ | `settingsStore.branches` |
| Checkbox usługa | ✅ | `is_service` |
| Article type dropdown | ✅ | machine/vehicle/tool/service — NOWE |
| Min. dni najmu | ✅ | `rental_days` |
| Duplikacja | ✅ | Przycisk ⎘ w toolbar → backend `ArticleService.duplicate()` |
| Opis + uwagi | ✅ | Textarea fields |
| Usuwanie z walidacją | ✅ | Backend blokuje przy aktywnych umowach |

### Cross-role analiza:

**🟢 ANALITYK BIZNESOWY:**
> Formularz artykułu jest **kompletny i lepszy niż stary**. Kategoria przez FK ID zamiast tekstu eliminuje "rozjazd" danych (LOG-06 z audytu). Typ artykułu (machine/vehicle/tool/service) to nowa, potrzebna klasyfikacja. Jedyny brak:
> 1. **W pickerze artykułów (w umowie)** — brak oznaczenia dostępności (Moccasin highlight). To KRYTYCZNE przy dodawaniu pozycji do umowy.
> 2. **Brak sprawdzania dostępności** — backend `ArticleService.check_availability()` istnieje ale frontend go nie wywołuje.

**🟢 DBA:**
> Wszystkie pola z DDL mają odpowiedniki w modelu ORM. Brak rozbieżności. Procedura `duplikujartykul2` poprawnie zrefaktoryzowana na Pythona.

**🟡 UX DESIGNER:**
> Sam formularz artykułu jest dobry. Problem jest **w pickerze artykułów w formularzu umowy** (ContractFormView.vue) — nie pokazuje dostępności. To nie jest problem FormA, ale FormAwybor.

**🟢 BACKEND ARCHITECT:**
> Backend kompletny. `check_availability` endpoint istnieje. Duplikacja działa. CRUD kompletny.

### Braki — podsumowanie:

| # | Brak | Priorytet | Effort | Uwaga |
|---|------|-----------|--------|-------|
| 3.1 | Oznaczenie dostępności w article picker (w umowie) | 🟡 P1 | S | Problem w ContractFormView, nie tu |
| 3.2 | Wywołanie check_availability przy dodawaniu pozycji | 🟡 P1 | S | j.w. |
| 3.3 | Duplikacja z poziomu pickera (w umowie) | 🟢 P2 | S | Wygoda użytkownika |

---

## 4. Dashboard / lista główna

### Stary proces (Form2.cs):

| # | Funkcja | Opis | Implementacja |
|---|---------|------|---------------|
| 1 | Lista umów | DataGrid z VIEW `umowy`, sortowanie po autonumer DESC | SQL VIEW z JOINami |
| 2 | Wyszukiwanie | Filtr po numerze umowy i nazwie kontrahenta | WHERE LIKE |
| 3 | Dodaj [+] | Otwarcie FormU4 w trybie nowa | Nawigacja |
| 4 | Edytuj (dblclick) | Otwarcie FormU4 w trybie edycja | Nawigacja |
| 5 | Usuń [-] | Confirm → kaskadowe usuwanie (warunki→pozycje→umowa) | 4× DELETE SQL |
| 6 | Context menu: Wydruk | Crystal Report → PDF preview | Crystal Reports |
| 7 | Context menu: Edytuj | j.w. punkt 4 | Nawigacja |
| 8 | Kalendarz 2-miesieczny | Wizualna nawigacja dat | UserControl |
| 9 | Lista kontrahentów | Osobna zakładka/widok | VIEW `kontrahenci` |
| 10 | Lista artykułów | Osobna zakładka/widok | VIEW `artykuly`/`artykulyy` |
| 11 | Duplikacja artykułu | Context menu na liście artykułów | `CALL duplikujartykul2` |
| 12 | Status wydruku | Znacznik czy wydruk aktualny | `print_date` vs `updated_at` |

### Nowy proces (DashboardView.vue):

| Element | Status | Uwagi |
|---------|--------|-------|
| Lista umów (grid + paginacja) | ✅ | Kompletna z sortowaniem |
| Wyszukiwanie umów | ✅ | Debounced search |
| Filtr typu umowy (S/U) | ⚠️ | **BUG: wysyła `type` zamiast `contract_type`** |
| Dodaj [+] | ✅ | `router.push('/contracts/new')` |
| Edytuj (dblclick) | ✅ | `router.push('/contracts/:id/edit')` |
| Usuń [-] z potwierdzeniem | ✅ | ConfirmDialog → backend cascade delete |
| Context menu: Umowa PDF | ✅ | `contractStore.generateReport(id, 'contract')` |
| Context menu: Protokół ZO | ✅ | `generateReport(id, 'protocol_zo')` |
| Context menu: Protokół ZO bez danych | ✅ | `generateReport(id, 'protocol_zo_nodata')` |
| Context menu: Edytuj | ✅ | Nawigacja |
| Kolumny: numer, kontrahent, typ, daty, wartość, handlowiec, wydruk | ✅ | Wszystkie obecne |
| Status wydruku (badge) | ✅ | Aktualny/Nieaktualny/Brak |
| Lista kontrahentów (sekcja) | ✅ | Osobna sekcja z grid + search + paginacja |
| Lista artykułów (sekcja) | ✅ | Osobna sekcja z grid + search + paginacja |
| Toolbar z przyciskami +/- | ✅ | AppToolbar component |
| Sidebar nawigacja | ✅ | AppSidebar: Umowy, Kontrahenci, Artykuły, Raporty, Ustawienia |

### Cross-role analiza:

**🟢 ANALITYK BIZNESOWY:**
> Dashboard jest **funkcjonalnie kompletny** z jednym bugiem i kilkoma brakami:
> 1. **BUG:** Filtr typu umowy nie działa (param `type` vs `contract_type`)
> 2. Brak kontekstowego "Dodaj umowę" z listy kontrahentów
> 3. Brak duplikacji artykułu z context menu na liście artykułów
> 4. Brak kalendarza 2-miesiecznego (stary app miał wizualny widget dat)

**🟡 UX DESIGNER:**
> Nowy dashboard jest **LEPSZY** niż stary pod kilkoma względami:
> - Responsywna paginacja
> - Czysty context menu z preview raportów  
> - Badge'e statusów (typ, wydruk)
> - Sidebar nawigacja zamiast zakładek
>
> Brakuje:
> 1. Filtrowanie po dacie od/do (stary app miał kalendarz)
> 2. "Dodaj umowę" na prawy klik kontrahenta
> 3. Kolumna "Adres dostawy" w liście umów (był w starym)

**🟡 FRONTEND ARCHITECT:**
> Bug jest trywialny — 1 linia. Reszta to drobne rozszerzenia context menu.

**🟢 BACKEND ARCHITECT:**
> Backend `list_contracts` poprawnie obsługuje parametr `contract_type`. Problem jest po stronie frontendu.

### Braki — podsumowanie:

| # | Brak | Priorytet | Effort |
|---|------|-----------|--------|
| 4.1 | **BUG: `type` → `contract_type` w DashboardView** | 🟡 P1 | XS |
| 4.2 | Filtrowanie po zakresie dat | 🟡 P1 | S |
| 4.3 | Context "Dodaj umowę" z listy kontrahentów | 🟡 P1 | XS |
| 4.4 | Duplikacja artykułu z context menu | 🟢 P2 | S |
| 4.5 | Kolumna "Adres dostawy" w liście umów | 🟢 P2 | XS |
| 4.6 | Kalendarz 2-miesieczny | 🟢 P2 | M |

---

## 5. Raporty PDF

### Stary proces (Crystal Reports):

| # | Raport | Format | Źródło danych |
|---|--------|--------|---------------|
| 1 | Umowa najmu (S) | A4, 2+ strony, header z logo+danymi firmy | Crystal Report `ownA.rpt` |
| 2 | Umowa usługi (U) | A4, j.w. ale inny OWU | Crystal Report `ownU.rpt` |
| 3 | Protokół ZO (S) | Protokół zdawczo-odbiorczy najem | Crystal Report |
| 4 | Protokół ZO (U) | Protokół zdawczo-odbiorczy usługa | Crystal Report |
| 5 | Protokół ZO bez danych (S) | Pusty protokół do wypełnienia | Crystal Report |
| 6 | Protokół ZO bez danych (U) | j.w. | Crystal Report |
| 7 | Dane na raporcie | Firma, kontrahent, handlowiec, pozycje z warunkami, usługi dodatkowe, osoby kontaktowe | VIEWs + JOINs |

### Nowy proces (Jinja2 + Playwright PDF):

| Element | Status | Uwagi |
|---------|--------|-------|
| 6 typów raportów (S/U × contract/protocol/protocol_nodata) | ✅ | Kompletne template mapping |
| Template routing wg typu umowy | ✅ | `contract.html` / `contract_u.html` + protokoły |
| Dane: firma + kontrahent + handlowiec | ✅ | `build_contract_data()` |
| Dane: pozycje z warunkami | ✅ | `_build_conditions_text()` |
| Dane: usługi dodatkowe | ✅ | `generate_fees_text()` |
| Dane: osoby kontaktowe | ✅ | Z kontraktu |
| Formatowanie: daty PL, kwoty PL | ✅ | Jinja2 filters `datepl`, `money` |
| Renderer: Playwright Chromium | ✅ | `_html_to_pdf_sync()` |
| Footer z datą i paginacją | ✅ | Template footer |
| Raporty summary: kontrahenci | ✅ | `GET /reports/summary/contractors` |
| Raporty summary: maszyny | ✅ | `GET /reports/summary/machines` |
| OWU wbudowane w template | ✅ | Zgodnie ze spec 11 |
| Download jako blob | ✅ | Frontend `contractStore.generateReport()` |
| Print date tracking | ✅ | `contract.print_date` |
| Context menu w Dashboard | ✅ | 3 opcje wydruku |

### Cross-role analiza:

**🟢 ANALITYK BIZNESOWY:**
> Raporty są **funkcjonalnie kompletne**. Wszystkie 6 typów obsłużone. Dodane 2 nowe raporty summary (kontrahenci, maszyny) których nie było w starym systemie. 
> 
> Jedyny problem: jeśli warunki rozliczenia nie są uzupełnione (bo brak UI — patrz Proces #1), to raporty PDF będą miały **puste sekcje cenowe**.

**🟡 UX DESIGNER:**
> Brak preview PDF w przeglądarce — stary Crystal Reports miał okno preview. Nowy system od razu pobiera plik. Warto dodać preview w iframe/modal.

**🟢 BACKEND ARCHITECT:**
> Solidna implementacja. Jinja2 + Playwright to dobre rozwiązanie. `build_contract_data()` zbiera wszystkie potrzebne dane. Formattery walutowe i datowe poprawne.

### Braki — podsumowanie:

| # | Brak | Priorytet | Effort |
|---|------|-----------|--------|
| 5.1 | Preview PDF w przeglądarce (zamiast auto-download) | 🟢 P2 | S |
| 5.2 | Raporty puste gdy brak warunków (zależne od P0 procesu #1) | 🔴 P0 | — (zależność) |
| 5.3 | Brak update `print_date` po generowaniu PDF | 🟡 P1 | XS |

---

## 6. Konfiguracja / Ustawienia

### Stary proces (Konfiguracja.cs):

| # | Sekcja | Funkcje | Tabele DB |
|---|--------|---------|-----------|
| 1 | Dane firmy | Nazwa, NIP, REGON, adres, bank, nr konta, numeracja, krok | `firma` |
| 2 | Logo | Upload/zmiana logo firmy (BLOB) | `firma.logo` |
| 3 | Nagłówek wydruku | Tekst multiline na header raportu | `firma.naglowek` |
| 4 | Handlowcy | Lista: dodaj, edytuj nazwę+telefon, toggle aktywność | `handlowiec` |
| 5 | Usługi najem | Tekst usług dodatkowych dla umów najmu (S) | `firma.uslugi1` + `firma.oplata_*` |
| 6 | Usługi usługa | Tekst usług dodatkowych dla umów usługi (U) | `firma.uslugi2` + `firma.oplata_*` |
| 7 | Kategorie | Dodawanie kategorii artykułów | `kategoria` |
| 8 | Stawki | Dodawanie typów stawek rozliczeniowych | `stawka` |

### Nowy proces (SettingsView.vue):

| Element | Status | Uwagi |
|---------|--------|-------|
| Tab: Dane firmy (CRUD) | ✅ | Kompletny formularz z zapisem |
| Tab: Handlowcy (lista + dodaj + toggle) | ✅ | Tabela + inline form |
| Tab: Kategorie (lista + dodaj) | ✅ | Tabela + inline form |
| Tab: Typy stawek (lista + dodaj) | ✅ | Tabela + inline form |
| Tab: Szablony usług (lista + dodaj per typ) | ✅ | Z dropdown S/U, kwota od/do |
| Backend: pełny CRUD | ✅ | Company, salespeople, categories, rate_types, fee_templates |
| Reorder szablonów | ✅ | Backend endpoint `POST /reorder` |
| Toggle aktywności handlowca | ✅ | `PATCH /toggle` |
| Admin-only guards | ✅ | `require_admin` dependency |

### Cross-role analiza:

**🟢 ANALITYK BIZNESOWY:**
> Moduł ustawień jest **LEPSZY niż stary**:
> - Szablony usług są relacyjne (tabela) zamiast tekstu w jednym polu
> - Osobne szablony per typ umowy (S/U) z kwotami od/do
> - Kategorie i stawki mają pełen CRUD zamiast adhoc stringów
>
> Drobne braki:

**🟡 UX DESIGNER:**
> 1. **Brak edycji/usuwania** kategorii, typów stawek — tylko dodawanie
> 2. **Brak edycji** handlowców (nazwa/telefon) — tylko dodawanie i toggle
> 3. **Brak uploadu logo** — pole `logo LONGBLOB` w DB, brak obsługi w UI
> 4. Brak sortowania drag&drop szablonów usług (backend `reorder` istnieje, brak UI)

**🟡 DBA:**
> Model `Company` ma pola `report_folder`, `protocol_folder`, `app_version` — nie wyświetlane w UI, prawdopodobnie zbędne w web app.

**🟢 BACKEND ARCHITECT:**
> Backend kompletny. CRUD dla wszystkich encji settings. Reorder endpoint gotowy. Brakuje: upload/download logo (endpoint multipart), update/delete dla categories i rate_types.

### Braki — podsumowanie:

| # | Brak | Priorytet | Effort |
|---|------|-----------|--------|
| 6.1 | Edycja/usuwanie kategorii | 🟡 P1 | S |
| 6.2 | Edycja handlowców (nie tylko toggle) | 🟡 P1 | S |
| 6.3 | Edycja/usuwanie typów stawek | 🟡 P1 | S |
| 6.4 | Upload logo firmy | 🟢 P2 | M |
| 6.5 | Drag & drop reorder szablonów usług | 🟢 P2 | M |
| 6.6 | Edycja/usuwanie szablonów usług w UI | 🟡 P1 | S |

---

## 7. Logowanie i autoryzacja

### Stary proces (Logowanie.cs):

| # | Funkcja | Opis |
|---|---------|------|
| 1 | Login | Login + hasło, brak szyfrowania (plaintext w DB) |
| 2 | Reset hasła | Brak |
| 3 | Role | Brak systemu ról |
| 4 | Session | Brak — stan w RAM WinForms |
| 5 | Multi-user | Brak — 1 user na maszynę |

### Nowy proces (LoginView.vue + auth module):

| Element | Status | Uwagi |
|---------|--------|-------|
| Login page | ✅ | Gradient background, formularz, obsługa błędów |
| JWT token auth | ✅ | `create_access_token()`, `get_current_user` dependency |
| bcrypt hash | ✅ | Bezpieczne przechowywanie haseł |
| Reset hasła (email) | ✅ | `forgot-password` → email z tokenem → `reset-password` |
| Wymuszenie zmiany hasła | ✅ | `must_change_password` → redirect `/change-password` |
| Role (admin/user/viewer) | ✅ | `require_admin` guard na endpointach |
| Admin panel użytkowników | ✅ | CRUD users, activate/deactivate, force password reset |
| Profil użytkownika | ✅ | View/update profile |
| Route guard | ✅ | `router.beforeEach` → redirect do login |
| Logout | ✅ | Sidebar button → clear token |

### Cross-role analiza:

**✅ ANALITYK BIZNESOWY:**
> Moduł auth jest **znacząco lepszy niż stary system** w każdym aspekcie:
> - Bezpieczeństwo: bcrypt + JWT vs plaintext
> - Funkcjonalność: role, reset hasła, profil — nic z tego nie było
> - Multi-user: prawdziwy system wieloużytkownikowy

**🟡 UX DESIGNER:**
> Brak widoku "Zmień hasło" w routerze (jest route `/change-password` ale brak komponentu w navigation). Brak widoku "Zarządzaj użytkownikami" w sidebar (endpointy admin istnieją, brak UI).

### Braki — podsumowanie:

| # | Brak | Priorytet | Effort |
|---|------|-----------|--------|
| 7.1 | UI "Zarządzaj użytkownikami" (admin panel) | 🟡 P1 | M |
| 7.2 | Link "Zmień hasło" w profilu/sidebar | 🟢 P2 | XS |
| 7.3 | Widok ResetPasswordView (route istnieje, komponent?) | 🟢 P2 | S |

---

## 8. Statystyki i analityka

### Stary proces: **NIE ISTNIAŁ**

> W starej aplikacji WinForms nie było żadnego modułu statystyk ani analityki. Wszystkie dane analityczne były obliczane "na piechotę" przez użytkownika w Excelu.

### Nowy proces (ReportsSection.vue + stats API):

| Element | Status | Uwagi |
|---------|--------|-------|
| **KPI cards** (4 karty) | ✅ | Wynajętych, Wykorzystanie floty %, Przychód, Top maszyna |
| **TOP 10 maszyn** (bar chart) | ✅ | Chart.js, horizontal bar |
| **Wykorzystanie floty** (donut) | ✅ | Chart.js, center text |
| **Usługi dodatkowe** (tabela) | ✅ | Z mini-barami postępu |
| **Lokalizacje ranking** (tabela) | ✅ | Miasta wg liczby umów |
| **Aktualnie wynajęte** (tabela) | ✅ | Lista maszyn z datami zwrotu |
| **Date presets** (pills) | ✅ | Miesiąc/Kwartał/Rok/Wszystko/Własny |
| **Endpoints:** fleet-summary | ✅ | Obliczenia z algorytmu spec |
| **Endpoints:** top-machines | ✅ | Agregacja po artykule |
| **Endpoints:** currently-rented | ✅ | Aktywne umowy |
| **Endpoints:** machine-roi | ✅ | ROI per maszyna |
| **Endpoints:** additional-fees | ✅ | Suma usług |
| **Endpoints:** locations | ✅ | Ranking miast |
| **Obliczenia revenue** | ✅ | `calculate_position_value()` z spec 04 |

### Cross-role analiza:

**✅ ANALITYK BIZNESOWY:**
> To jest **zupełnie nowa wartość** — stary system tego nie miał. Dashboard analityczny z KPI, chartami i tabelami daje użytkownikowi natychmiastowy wgląd w kondycję biznesu. Algorytm revenue oparty na `rate1` z position_conditions — źródło prawdy.
>
> Jedyne ryzyko: jeśli warunki rozliczenia nie są uzupełniane (brak UI z Procesu #1), statystyki będą zaniżone.

**🟢 UX DESIGNER:**
> Świetny dashboard. KPI cards, responsywne charty, date presets. Mógłby mieć:
> 1. Export do CSV/Excel
> 2. Drukowanie dashboardu

**🟢 BACKEND ARCHITECT:**
> Implementacja solidna. `_compute_position_revenues()` poprawnie batch-fetchuje warunki i oblicza wartości. Spec 11 endpoints zrealizowane.

### Braki — podsumowanie:

| # | Brak | Priorytet | Effort |
|---|------|-----------|--------|
| 8.1 | Export statystyk do CSV/Excel | 🟢 P2 | M |
| 8.2 | Drukowanie dashboardu statystyk | 🟢 P2 | S |
| 8.3 | Dane zależne od uzupełnienia warunków (P0 z procesu #1) | 🔴 P0 | — (zależność) |

---

## 9. Integracje zewnętrzne

### Stary proces:

| # | Integracja | Opis | Implementacja |
|---|-----------|------|---------------|
| 1 | GUS API (SOAP) | Pobranie danych firmy po NIP | C# SOAP client → FormK.cs |
| 2 | Nominatim (reverse geocoding) | Zamiana współrzędnych na adres | HTTP GET → FormU4.cs |

### Nowy proces:

| Element | Status | Uwagi |
|---------|--------|-------|
| GUS API (SOAP) | ✅ | Backend `contractors/router.py` → `POST /contractors/gus-lookup` |
| GUS → auto-fill kontrahenta | ✅ | Frontend `gusLookup()` w ContractorFormView |
| Nominatim reverse geocoding | ✅ | Backend `POST /integrations/reverse-geocode` |
| Nominatim → adres dostawy | ❌ | **Endpoint istnieje, ale frontend go NIE UŻYWA** |

### Cross-role analiza:

**🟡 ANALITYK BIZNESOWY:**
> GUS działa dobrze. Nominatim ma endpoint ale nie jest zintegrowany z formularzem umowy (reverse geocoding adresu dostawy). W starym systemie to działało automatycznie po wyborze adresu z listy.

**🟢 BACKEND ARCHITECT:**
> Oba endpointy kompletne i działające. Problem jest wyłącznie po stronie frontendu — brak wywołania reverse-geocode w odpowiednim momencie.

### Braki — podsumowanie:

| # | Brak | Priorytet | Effort |
|---|------|-----------|--------|
| 9.1 | Frontend integracja Nominatim w formularzu umowy | 🟢 P2 | S |
| 9.2 | Zapis wyniku geocoding do tabeli `deliveries` | 🟢 P2 | S |

---

## PODSUMOWANIE GLOBALNE — Wszystkie Braki

### 🔴 P0 — BLOCKERY (bez tego app jest bezużyteczna biznesowo)

| # | Brak | Proces | Gdzie | Effort |
|---|------|--------|-------|--------|
| **P0-1** | **UI Warunków Rozliczenia (ConditionPanel)** | #1 Umowy | Frontend | L |
| **P0-2** | **Auto-kalkulacja total_value** | #1 Umowy | Backend+Frontend | M |
| **P0-3** | **Rozszerzenie modalu pozycji (6 pól)** | #1 Umowy | Frontend | S |

### 🟡 P1 — WAŻNE (pełna funkcjonalność procesowa)

| # | Brak | Proces | Effort |
|---|------|--------|--------|
| P1-1 | Dropdown adresów kontrahenta w umowie | #1 | S |
| P1-2 | Pole "Pozostało" (total-prepay-invoice) | #1 | XS |
| P1-3 | Branch/oddział selector w umowie | #1 | XS |
| P1-4 | Edycja service fees w umowie | #1 | M |
| P1-5 | Sprawdzanie dostępności + badge w pickerze | #1, #3 | S |
| P1-6 | **BUG: `type` → `contract_type`** w DashboardView | #4 | XS |
| P1-7 | Filtrowanie po zakresie dat w Dashboard | #4 | S |
| P1-8 | Pole `landline_phone` w kontrahencie | #2 | XS |
| P1-9 | Przycisk "Dodaj umowę" w kontrahencie | #2, #4 | XS |
| P1-10 | Auto-tworzenie adresu po GUS | #2 | S |
| P1-11 | Update `print_date` po generowaniu PDF | #5 | XS |
| P1-12 | Edycja/usuwanie kategorii, stawek, szablonów, handlowców | #6 | S |
| P1-13 | UI "Zarządzaj użytkownikami" (admin panel) | #7 | M |

### 🟢 P2 — ULEPSZENIA

| # | Brak | Proces | Effort |
|---|------|--------|--------|
| P2-1 | Brakujące modele DB: deliveries, costs, settlements, audit_log | #1 | M |
| P2-2 | NIP validation (checksum) | #2 | XS |
| P2-3 | Zapis `gus_date` | #2 | XS |
| P2-4 | Reverse geocoding lat/lng w adresach | #2, #9 | S |
| P2-5 | Duplikacja artykułu z pickera | #3 | S |
| P2-6 | Kalendarz 2-miesieczny | #4 | M |
| P2-7 | Kolumna "Adres dostawy" w liście umów | #4 | XS |
| P2-8 | Preview PDF (zamiast auto-download) | #5 | S |
| P2-9 | Upload logo firmy | #6 | M |
| P2-10 | Drag&drop reorder szablonów | #6 | M |
| P2-11 | Link "Zmień hasło" | #7 | XS |
| P2-12 | Export statystyk CSV/Excel | #8 | M |
| P2-13 | Auto-generowanie opisów warunków | #1 | S |
| P2-14 | Nominatim integracja w umowie | #9 | S |

---

## REKOMENDACJA SPRINTÓW

### Sprint 1 — P0 (unblock core process)
1. **ConditionPanel.vue** + integracja w ContractFormView
2. Rozszerzenie **position modal** o 6 brakujących pól
3. **Auto-recalculate total_value** — endpoint + trigger po zmianach warunków

### Sprint 2 — P1 (production-ready)
4. Bug fix: `type` → `contract_type`
5. Contractor address picker w umowie
6. "Pozostało" computed + branch selector
7. Service fees CRUD w umowie
8. Availability check + badge w article picker
9. Filtrowanie dat w Dashboard
10. Edycja/usuwanie w Settings (kategorie, stawki, szablony, handlowcy)
11. Pole `landline_phone` + "Dodaj umowę" w kontrahencie
12. Update `print_date`
13. Admin panel użytkowników

### Sprint 3 — P2 (polish & enhancements)
14. Brakujące modele DB (deliveries, costs, settlements, audit_log)
15. NIP validation, GUS date, reverse geocoding
16. Preview PDF, upload logo, drag&drop reorder
17. Export CSV, kalendarz, auto-opisy warunków
