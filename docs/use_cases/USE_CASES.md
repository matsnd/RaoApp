# RAO — Use Cases (kompletny zbiór)

> **Wersja:** 1.0 | **Data:** 2026-07-11
> **Źródła:** `frontend/src/router/index.js`, 15 widoków `frontend/src/views/*.vue`, `backend/main.py` (14 routerów), `spec/core/06_navigation_flow.md`, analizy Phase 0 (Tech Lead, Security Auditor, QA Engineer, Product Owner)
> **Zakres:** 15 widoków aplikacji RAO, ~80 scenariuszy użycia (happy path + edge cases)

---

## Spis treści

| # | Widok | Rola | Use case'y | Status |
|---|-------|------|------------|--------|
| 1 | LoginView | Wszyscy | UC-AUTH-01..03 | Aktywny |
| 2 | ResetPasswordView | Wszyscy | UC-AUTH-04..05 | Aktywny |
| 3 | ChangePasswordView | Zalogowany | UC-AUTH-06 | Aktywny |
| 4 | HomeView | Zalogowany | UC-HOME-01..03 | Aktywny |
| 5 | DashboardView | Zalogowany | UC-DASH-01..04 | Aktywny |
| 6 | ContractorFormView | Admin/User | UC-CONT-01..05 | Aktywny |
| 7 | ArticleFormView | Admin/User | UC-ART-01..05 | Aktywny |
| 8 | ReservationsView | Admin/User | UC-RES-01..04 | Aktywny |
| 9 | ContractFormView | Admin/User | UC-CON-01..12 | Aktywny (największy) |
| 10 | WorkerView | Worker | UC-WORK-01..02 | Aktywny |
| 11 | CommissionView | Manager | UC-COMM-01..02 | Aktywny |
| 12 | SettingsView | Admin | UC-SET-01..09 | Aktywny |
| 13 | AdminView | Admin | UC-ADM-01..04 | Aktywny |
| 14 | ArchiveView | Admin/User | UC-ARCH-01..04 | Aktywny |
| 15 | AnalyticsView | Admin/User | UC-ANL-01..05 | Aktywny |

**Pomiń (już usunięte):** StatsView, ReportsSection, ReservationsPanel — status "USUNIĘTY" w `spec/core/03_frontend_screens.md`.

---

## 1. LoginView (`/login`)

**Plik:** `frontend/src/views/LoginView.vue` (10 KB)
**Endpointy:** `POST /auth/login`, `POST /auth/forgot-password`
**Role:** Wszyscy (publiczny)

### UC-AUTH-01: Logowanie użytkownika (happy path)
**Aktor:** Dowolny użytkownik (admin, user, viewer)
**Warunki wstępne:** Konto istnieje w DB, konto aktywne (`is_active=true`)
**Kroki:**
1. Wejdź na `http://localhost:5173/rao/login`
2. Wpisz login w polu "Login" (np. `admin`)
3. Wpisz hasło w polu "Hasło" (np. `admin123`)
4. Kliknij "Zaloguj"
**Oczekiwany rezultat:**
- Backend `POST /auth/login` zwraca 200 + `{access_token, token_type, user, must_change_password}`
- Frontend zapisuje token w `localStorage.rao_token`
- Przekierowanie na `/home` (lub `?redirect=...` jeśli było)
**Edge cases:**
- Błędne hasło → 401 + animacja "shake" pola hasła
- Rate limit 5 prób/60s/IP → 429 (wyłączony w `environment=development`)
- `must_change_password=true` → przekierowanie na `/password`
- Nieaktywne konto → 401

### UC-AUTH-02: Wniosek o reset hasła (forgot password)
**Aktor:** Użytkownik bez dostępu
**Kroki:**
1. Na stronie `/login` kliknij "Nie pamiętam hasła"
2. Wpisz email w polu "Email"
3. Kliknij "Wyślij link resetujący"
**Oczekiwany rezultat:**
- `POST /auth/forgot-password` → generuje `secrets.token_urlsafe(32)`, hash SHA256 zapisany w `users.password_reset_token`, expiracja 1h
- Email z linkiem `{FRONTEND_URL}/reset-password?token=...` wysłany przez SMTP (Mailpit w dev)
- Odpowiedź 200 zawsze identyczna (nie ujawnia istnienia emaila)
**Edge cases:**
- Nieistniejący email → 200 (anti-enumeration)
- Rate limit → 429

### UC-AUTH-03: Wylogowanie
**Aktor:** Zalogowany użytkownik
**Kroki:**
1. Kliknij awatar/user name w prawym górnym rogu
2. Kliknij "Wyloguj"
**Oczekiwany rezultat:**
- `localStorage.rao_token` usuwany
- Przekierowanie na `/login`
- Brak endpointu backend (JWT stateless — brak blacklist)

---

## 2. ResetPasswordView (`/reset-password`)

**Plik:** `frontend/src/views/ResetPasswordView.vue` (3 KB)
**Endpointy:** `POST /auth/reset-password`
**Role:** Publiczny (z tokenem)

### UC-AUTH-04: Reset hasła z tokenu (happy path)
**Warunki wstępne:** Token reset w URL (`?token=...`), token ważny (<1h), niezużyty
**Kroki:**
1. Kliknij link w emailu → `/reset-password?token=...`
2. Wpisz nowe hasło (min. 6 znaków — **UWAGA: spec mówi 12, kod ma 6** — bug RAO-SEC-006)
3. Powtórz nowe hasło
4. Kliknij "Zresetuj hasło"
**Oczekiwany rezultat:**
- `POST /auth/reset-password` → hash SHA256 tokena porównany z DB → bcrypt hash nowego hasła → czyszczenie tokenu
- Przekierowanie na `/login` z komunikatem sukcesu
**Edge cases:**
- Wygasły token (>1h) → 400
- Zużyty token → 400
- Hasła niezgodne → walidacja frontend
- Hasło < 6 znaków → 422

### UC-AUTH-05: Reset hasła bez tokenu (direct navigation)
**Kroki:** Wejdź na `/reset-password` bez `?token=`
**Oczekiwany rezultat:** Komunikat "Brak tokenu resetu" + link do `/login`

---

## 3. ChangePasswordView (`/password`)

**Plik:** `frontend/src/views/ChangePasswordView.vue` (3 KB)
**Endpointy:** `PUT /auth/change-password`
**Role:** Zalogowany

### UC-AUTH-06: Zmiana hasła (zalogowany)
**Warunki wstępne:** Użytkownik zalogowany
**Kroki:**
1. Kliknij awatar → "Zmień hasło" (lub przekierowanie z login gdy `must_change_password=true`)
2. Wpisz aktualne hasło
3. Wpisz nowe hasło (min. 6)
4. Powtórz nowe hasło
5. Kliknij "Zmień hasło"
**Oczekiwany rezultat:**
- `PUT /auth/change-password` → bcrypt verify aktualnego → sprawdzenie nowe≠aktualne → bcrypt hash nowego
- Komunikat sukcesu
- **UWAGA:** Nie unieważnia innych sesji (brak jti blacklist — bug RAO-SEC-005)
**Edge cases:**
- Błędne aktualne hasło → 400
- Nowe = aktualne → 400
- Hasła niezgodne → walidacja frontend

---

## 4. HomeView (`/home`)

**Plik:** `frontend/src/views/HomeView.vue` (27 KB)
**Endpointy:** `GET /stats/fleet-summary`, `GET /stats/expiring-contracts`, `GET /stats/deliveries-today`, `GET /stats/unprinted-contracts`, `GET /stats/stale-print-contracts`, `GET /contracts/overdue`
**Role:** Zalogowany

### UC-HOME-01: Pulpit startowy — KPI floty
**Kroki:** Zaloguj się → `/home`
**Oczekiwany rezultat:**
- KPI "Flota teraz": liczba maszyn aktywnie wypożyczonych (`fleet-summary`)
- KPI "Umowy wygasające": kontrakty kończące się w ciągu 7 dni (`expiring-contracts`)
- KPI "Dostawy dzisiaj": maszyny do zwrotu dziś (`deliveries-today`)
- KPI "Nie wydrukowane": umowy bez PDF (`unprinted-contracts`)
- KPI "Przeterminowane": umowy po terminie (`overdue`)
- KPI "Stare druki": umowy z PDF starszym niż N dni (`stale-print-contracts`)
- Kliknięcie KPI → nawigacja do DashboardView z filtrem

### UC-HOME-02: Lista umów przeterminowanych
**Kroki:** Sekcja "Przeterminowane" na HomeView
**Oczekiwany rezultat:** Lista umów `date_to < today AND is_settled=false`, sortowana po dacie, z linkami do edycji umowy

### UC-HOME-03: Nawigacja do akcji
**Kroki:** Klik KPI → DashboardView z预设 filter
**Oczekiwany rezultat:** Przekierowanie `/dashboard/contracts?filter=expiring` (lub podobny)

---

## 5. DashboardView (`/dashboard/:section`)

**Plik:** `frontend/src/views/DashboardView.vue` (37 KB)
**Endpointy:** `GET /contracts`, `GET /contracts/overdue`, `GET /contractors`, `GET /articles`, `GET /settings/salespeople`
**Role:** Zalogowany (admin: wszystkie; user: własny branch; viewer: read-only)

### UC-DASH-01: Lista umów z filtrami
**Sekcja:** `dashboard/contracts`
**Kroki:**
1. Sidebar → "Umowy"
2. Filtry: handlowiec, miasto, status (aktywna/przeterminowana/rozliczona), data
3. Sortowanie po kolumnie
4. Klik umowę → `/contracts/:id/edit`
**Oczekiwany rezultat:** Tabela z umowami (branch-scoped dla non-admin), paginacja, eksport

### UC-DASH-02: Lista kontrahentów
**Sekcja:** `dashboard/contractors`
**Kroki:** Sidebar → "Kontrahenci" → lista z NIP, miastem, liczbą umów
**Edge cases:** **IDOR — brak ownership check (RAO-SEC-002)** — każdy user czyta wszystkich kontrahentów

### UC-DASH-03: Lista maszyn (artykułów)
**Sekcja:** `dashboard/articles`
**Kroki:** Sidebar → "Maszyny" → lista z kategorią, dostępnością, ostatnimi warunkami
**Edge cases:** **IDOR — brak ownership check (RAO-SEC-003)** — każdy user czyta wszystkie maszyny

### UC-DASH-04: Lista umów przeterminowanych
**Sekcja:** `dashboard/overdue`
**Kroki:** Sidebar → "Przeterminowane" → lista `date_to < today AND is_settled=false`

---

## 6. ContractorFormView (`/contractors/new`, `/contractors/:id/edit`)

**Plik:** `frontend/src/views/ContractorFormView.vue` (19 KB)
**Endpointy:** `POST/GET/PUT /contractors[/:id]`, `POST/PUT/DELETE /contractors/:id/addresses[/:addr]`, `POST /integrations/gus-lookup`
**Role:** Admin (write), User (read+write własnych), Viewer (read-only)

### UC-CONT-01: Tworzenie kontrahenta (happy path)
**Kroki:**
1. Dashboard → "Nowy kontrahent"
2. Wypełnij: nazwa, NIP, REGON, telefon, email, miasto, ulica, kod pocztowy
3. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /contractors` → 201 + redirect do edycji
**Edge cases:** NIP nieunikalny → 400; NIP invalid → 422

### UC-CONT-02: Auto-uzupełnianie z GUS
**Kroki:**
1. Wpisz NIP w formularzu
2. Klik "Pobierz z GUS"
**Oczekiwany rezultat:** `POST /integrations/gus-lookup` → SOAP do GUS → wypełnienie nazwy, adresu, REGON
**Edge cases:** NIP nie znaleziony w GUS → komunikat; GUS API down → fallback ręczny

### UC-CONT-03: Edycja kontrahenta
**Kroki:** Dashboard → kontrahent → "Edytuj" → zmiana pól → "Zapisz"
**Oczekiwany rezultat:** `PUT /contractors/:id` → 200
**Edge cases:** **IDOR (RAO-SEC-002)** — brak ownership check

### UC-CONT-04: Zarządzanie adresami kontrahenta
**Kroki:** W formularzu kontrahenta → sekcja "Adresy" → dodaj/edytuj/usuń
**Oczekiwany rezultat:** `POST/PUT/DELETE /contractors/:id/addresses[/:addr]`

### UC-CONT-05: Usuwanie kontrahenta
**Kroki:** Lista kontrahentów → "Usuń" → potwierdzenie
**Oczekiwany rezultat:** `DELETE /contractors/:id` → 200 (jeśli bez umów) lub 400 (jeśli z umowami)
**Edge cases:** **IDOR (RAO-SEC-002)** — każdy user może usunąć

---

## 7. ArticleFormView (`/articles/new`, `/articles/:id/edit`)

**Plik:** `frontend/src/views/ArticleFormView.vue` (23 KB)
**Endpointy:** `POST/GET/PUT /articles[/:id]`, `GET /contractors`, `GET /settings/categories/tree`, `GET /settings/branches`, `GET /settings/rate-types`, `GET/POST /settings/articles/:id/rate-presets`, `GET /integrations/fakturownia/products`
**Role:** Admin (write), User (read+write własnych), Viewer (read-only)

### UC-ART-01: Tworzenie maszyny (happy path)
**Kroki:**
1. Dashboard → "Nowa maszyna"
2. Wypełnij: nazwa, kategoria (drzewo), typ (maszyna/usługa), NIP dostawcy, cena, oddział
3. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /articles` → 201

### UC-ART-02: Cennik rozliczeń maszyn (rate presets)
**Kroki:** W formularzu maszyny → sekcja "Cennik" → dodaj warunki (1-3 dni, 4-16 dni, >16 dni)
**Oczekiwany rezultat:** `POST /settings/articles/:id/rate-presets` → 201
**Edge cases:** Nakładające się zakresy → 422

### UC-ART-03: Mapowanie produktu Fakturownia
**Kroki:** W formularzu maszyny → "Mapuj z Fakturownia" → wybierz produkt z listy
**Oczekiwany rezultat:** `GET /integrations/fakturownia/products` → lista produktów FA → zapis `fakturownia_product_id`

### UC-ART-04: Edycja maszyny
**Kroki:** Dashboard → maszyna → "Edytuj" → zmiana pól → "Zapisz"
**Edge cases:** **IDOR (RAO-SEC-003)** — brak ownership check

### UC-ART-05: Duplikowanie maszyny
**Kroki:** Lista maszyn → "Duplikuj"
**Oczekiwany rezultat:** `POST /articles/:id/duplicate` → 201 (nowa maszyna z skopiowanym cennikiem)

---

## 8. ReservationsView (`/reservations`)

**Plik:** `frontend/src/views/ReservationsView.vue` (36 KB)
**Endpointy:** `GET/POST/PUT/DELETE /reservations[/:id]`, `GET /reservations/calendar`, `GET /reservations/with-articles`, `GET /articles`, `GET /contractors`
**Role:** Admin/User

### UC-RES-01: Kalendarz rezerwacji
**Kroki:** Sidebar → "Rezerwacje" → kalendarz miesięczny
**Oczekiwany rezultat:** `GET /reservations/calendar?month=YYYY-MM` → wydarzenia z maszyną, kontrahentem, datami
**Edge cases:** Brak rezerwacji w seed_demo_data → pusty kalendarz (do demo)

### UC-RES-02: Tworzenie rezerwacji
**Kroki:**
1. Klik "Nowa rezerwacja"
2. Wybierz maszynę, kontrahenta, daty od/do
3. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /reservations` → 201
**Edge cases:** Konflikt dat z inną rezerwacją → 409

### UC-RES-03: Edycja rezerwacji
**Kroki:** Klik rezerwację w kalendarzu → "Edytuj" → zmiana dat → "Zapisz"
**Oczekiwany rezultat:** `PUT /reservations/:id` → 200
**Edge cases:** **IDOR (RAO-SEC)** — brak ownership check

### UC-RES-04: Usuwanie rezerwacji
**Kroki:** Klik rezerwację → "Usuń" → potwierdzenie
**Oczekiwany rezultat:** `DELETE /reservations/:id` → 200

---

## 9. ContractFormView (`/contracts/new`, `/contracts/:id/edit`)

**Plik:** `frontend/src/views/ContractFormView.vue` (128 KB — największy)
**Endpointy:** ~30 (umowy, pozycje, warunki, service-fees, rozliczenia, rezerwacje, integracje, PDF)
**Role:** Admin (all), User (własny branch), Viewer (read-only)

### UC-CON-01: Tworzenie umowy (happy path)
**Kroki:**
1. Dashboard → "Nowa umowa"
2. Wybierz kontrahenta, handlowca, oddział, daty, typ (S/U)
3. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /contracts` → 201 + redirect do edycji
**Edge cases:** POST bez `date_from` → 500 (bug RAO-QA-002 — brak default)

### UC-CON-02: Dodawanie pozycji umowy (maszyny)
**Kroki:**
1. W umowie → sekcja "Pozycje" → "Dodaj pozycję"
2. Wybierz maszynę z listy (z dostępnością)
3. Ustaw ilość, daty
4. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /contracts/:id/positions` → 201
**Edge cases:** Maszyna niedostępna w dacie → 409; `GET /articles/:id/availability` sprawdza konflikty

### UC-CON-03: Dodawanie warunków rozliczeniowych (kaskadowe)
**Kroki:**
1. W pozycji → "Warunki" → "Dodaj warunek"
2. Ustaw zakres dni (1-3, 4-16, >16), typ stawki (dniowa/godzinowa/km), kwotę
3. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /contracts/:id/positions/:pid/conditions` → 201
**Edge cases:** Nakładające się zakresy → 422

### UC-CON-04: Dodawanie usług dodatkowych (service fees)
**Kroki:**
1. W umowie → "Usługi dodatkowe" → "Dodaj"
2. Wybierz usługę (transport, czyszczenie, tankowanie, przestój, serwis, przegląd)
3. Ustaw kwotę, datę
4. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /contracts/:id/service-fees` → 201

### UC-CON-05: Aplikowanie presetu usług
**Kroki:** W umowie → "Aplikuj preset" → wybierz zestaw (Najem, z operatorem, długoterminowy, weekend, zagraniczny, premium)
**Oczekiwany rezultat:** `POST /contracts/:id/service-fees/apply-preset` → 201 (lista opłat z presetu)

### UC-CON-06: Auto-uzupełnianie adresu z PNA (kod pocztowy)
**Kroki:**
1. Wpisz kod pocztowy w polu "Kod pocztowy"
2. Klik "Pobierz lokalizację"
**Oczekiwany rezultat:** `GET /integrations/postal-codes/:code` → miasto, ulica (z cache `postal_codes`)
**Edge cases:** Nieznany PNA → fallback do Nominatim `POST /integrations/geocode`

### UC-CON-07: Recalculacja umowy
**Kroki:** W umowie → "Przelicz" → `POST /contracts/:id/recalculate`
**Oczekiwany rezultat:** Aktualizacja sum pozycji, opłat, totalnej wartości umowy

### UC-CON-08: Generowanie PDF umowy
**Kroki:** W umowie → "Generuj PDF"
**Oczekiwany rezultat:**
- `POST /reports/contract/:id` → PDF (WeasyPrint, Jinja2)
- Auto-zapis do folderu PDF (`usePdfFolders`: report_main, protocol_main, report_gdansk, protocol_gdansk)
- Status "Wydrukowano" ustawiony na umowie
**Edge cases:** Nieistniejący `contract_id` → 500 (bug RAO-QA-003)

### UC-CON-09: Rozliczenie ręczne (manual settlement)
**Kroki:**
1. W umowie → sekcja "Rozliczenie" → "Inicjalizuj ręcznie"
2. Wypełnij pozycje rozliczenia (ilość, kwota)
3. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /settlements/contract/:id/init` → 201 (`source=manual`)
**Edge cases:** **IDOR (RAO-SEC-001)** — brak ownership check

### UC-CON-10: Rozliczenie z Fakturownia (FA integration)
**Kroki:**
1. W umowie FA-pending (`is_settled=false`) → sekcja "Rozliczenie"
2. Klik "💰 Pobierz z Fakturownia" (disabled jeśli FA nie skonfigurowane)
**Oczekiwany rezultat:**
- `POST /settlements/contract/:id/init-from-fakturownia`
- Backend pobiera faktury z FA (OID z DB — IDOR fix)
- Mapuje pozycje umowy z produktami FA (`pid_to_positions`)
- Mapuje usługi dodatkowe (`pid_to_service_fees`)
- Tworzy `ContractSettlement` (`source=fakturownia`, `settled_at=invoice.issue_date`)
- Niezmapowane pozycje → `source=fa_unmapped` z `article_name_snapshot`
- Idempotentność `UNIQUE(unmapped_key)`, semantyka 1:N
**Edge cases:**
- Brak faktur w FA → komunikat
- Błąd FA API → komunikat
- Umowa już rozliczona → 409
- Rate limit 30/min/user → 429

### UC-CON-11: Edycja umowy rozliczonej (lock)
**Kroki:** Otwórz rozliczoną umowę (`is_settled=true`) → spróbuj edytować pozycję
**Oczekiwany rezultat:** Mutacje zablokowane (frontend disable + backend 409)

### UC-CON-12: Usuwanie umowy (guard)
**Kroki:** Lista umów → "Usuń" → potwierdzenie
**Oczekiwany rezultat:**
- `DELETE /contracts/:id` → 200 (jeśli bez pozycji/rozliczeń) lub 400 (jeśli z danymi)
- `verify_contract_access` chroni przed IDOR (admin: all; user: własny branch)

---

## 10. WorkerView (`/worker`)

**Plik:** `frontend/src/views/WorkerView.vue` (18 KB)
**Endpointy:** `GET /stats/expiring-contracts`, `GET /stats/deliveries-today`, `GET /stats/unprinted-contracts`, `GET /stats/stale-print-contracts`, `GET /stats/overdue-contracts`
**Role:** Worker (rola operacyjna)

### UC-WORK-01: Pulpit operacyjny
**Kroki:** Sidebar → "Pulpit pracownika"
**Oczekiwany rezultat:**
- Lista "Dostawy dzisiaj" (maszyny do zwrotu)
- Lista "Umowy wygasające" (7 dni)
- Lista "Nie wydrukowane"
- Lista "Stare druki"
- Lista "Przeterminowane"

### UC-WORK-02: Nawigacja do akcji
**Kroki:** Klik pozycji na liście → `/contracts/:id/edit`

---

## 11. CommissionView (`/commissions`)

**Plik:** `frontend/src/views/CommissionView.vue` (8 KB)
**Endpointy:** `GET /reports/summary/commissions`, `GET /stats/commissions`
**Role:** Manager/Admin

### UC-COMM-01: Raport prowizji
**Kroki:** Sidebar → "Prowizje"
**Oczekiwany rezultat:**
- `GET /reports/summary/commissions` → PDF z prowizjami handlowców
- `GET /stats/commissions` → dane do tabeli (handlowiec, liczba umów, suma, prowizja %)
**Edge cases:** **Brak branch filter (RAO-SEC-009)** — każdy user widzi prowizje wszystkich handlowców

### UC-COMM-02: Eksport PDF prowizji
**Kroki:** Klik "Eksportuj PDF" → zapis do folderu PDF

---

## 12. SettingsView (`/settings`)

**Plik:** `frontend/src/views/SettingsView.vue` (61 KB, 1240 linii)
**Endpointy:** 37 (company, salespeople, categories, rate-types, fee-presets, machine-rate-presets, fakturownia, folder, pdf-folders)
**Role:** Admin (write), User (read)

### UC-SET-01: Konfiguracja firmy
**Kroki:** Settings → "Firma" → edycja NIP, REGON, konto bankowe, header_text PDF, numeracja
**Oczekiwany rezultat:** `GET/PUT /settings/company`
**UWAGA:** Pola `report_folder`/`protocol_folder`/`app_version`/`logo` są w DB ale NIE w formularzu (martwe kolumny — RAO-TECH-002)

### UC-SET-02: Zarządzanie handlowcami
**Kroki:** Settings → "Handlowcy" → dodaj/edytuj/usuń/toggle aktywny
**Oczekiwany rezultat:** `GET/POST/PUT/DELETE /settings/salespeople[/:id][/:toggle]`

### UC-SET-03: Drzewo kategorii
**Kroki:** Settings → "Kategorie" → dodaj/edytuj/usuń (hierarchiczne main/sub1)
**Oczekiwany rezultat:** `GET/POST/PUT/DELETE /settings/categories[/:id]`, `GET /settings/categories/tree`

### UC-SET-04: Typy stawek
**Kroki:** Settings → "Typy stawek" → CRUD (dniowa, godzinowa, km, tygodniowa, miesięczna, jednorazowa)
**Oczekiwany rezultat:** `GET/POST/PUT/DELETE /settings/rate-types[/:id]`

### UC-SET-05: Zestawy usług dodatkowych (fee presets)
**Kroki:** Settings → "Zestawy usług" → CRUD grup + szablonów
**Oczekiwany rezultat:** `GET/POST/PUT/DELETE /settings/fee-preset-groups[/:id]`, `POST/PUT/DELETE/PATCH /settings/fee-preset-groups/:id/templates[/:tid][/:reorder]`

### UC-SET-06: Cenniki rozliczeń maszyn (read-only overview)
**Kroki:** Settings → "Cenniki maszyn" → przegląd `article_rate_presets`
**Oczekiwany rezultat:** `GET /settings/articles/:id/rate-presets` (edycja w ArticleFormView)

### UC-SET-07: Konfiguracja Fakturownia
**Kroki:**
1. Settings → "Fakturownia"
2. Wpisz subdomene, API token
3. Klik "Zapisz"
**Oczekiwany rezultat:**
- `GET /integrations/fakturownia/settings` → `api_token_preview` (np. `tk_****1234`, NIGDY plaintext)
- `PUT /integrations/fakturownia/settings` → Fernet encryption → zapis `api_token_ciphertext`
- Audit trail: `api_token_updated_at`, `api_token_updated_by`
**Edge cases:** Rate limit 5/min/IP → 429

### UC-SET-08: Folder RAO (legacy)
**Kroki:** Settings → "Folder" → wybierz folder główny RAO
**Oczekiwany rezultat:** `useTargetFolder` → IndexedDB
**UWAGA:** Nakłada się z `pdf-folders` (RAO-TECH-004 — kandydat na konsolidację)

### UC-SET-09: Foldery PDF (per-oddział)
**Kroki:** Settings → "Foldery PDF" → ustaw 4 foldery (report_main, protocol_main, report_gdansk, protocol_gdansk)
**Oczekiwany rezultat:** `usePdfFolders` → IndexedDB

---

## 13. AdminView (`/admin`)

**Plik:** `frontend/src/views/AdminView.vue` (9 KB)
**Endpointy:** `GET/POST /admin/users`, `PUT /admin/users/:id`, `PATCH /admin/users/:id/deactivate`, `PATCH /admin/users/:id/activate`, `POST /admin/users/:id/force-password-reset`
**Role:** Admin (`requiresAdmin: true`)

### UC-ADM-01: Lista użytkowników
**Kroki:** Sidebar → "Administracja" (tylko admin)
**Oczekiwany rezultat:** `GET /admin/users` → lista z loginem, emailem, rolą, statusem, oddziałem

### UC-ADM-02: Tworzenie użytkownika
**Kroki:**
1. "Nowy użytkownik"
2. Wpisz login, email, rolę (admin/user/viewer), oddział
3. Klik "Zapisz"
**Oczekiwany rezultat:** `POST /admin/users` → 201 (losowe hasło tymczasowe lub `must_change_password=true`)

### UC-ADM-03: Blokowanie/odblokowanie użytkownika
**Kroki:** Lista → user → "Dezaktywuj"/"Aktywuj"
**Oczekiwany rezultat:** `PATCH /admin/users/:id/deactivate` / `activate` → 200
**Edge cases:** Self-deactivate zablokowany (backend sprawdza)

### UC-ADM-04: Wymuszenie reset hasła
**Kroki:** Lista → user → "Wymuś reset hasła"
**Oczekiwany rezultat:** `POST /admin/users/:id/force-password-reset` → 200 → `must_change_password=true` → user przy następnym loginie przekierowany na `/password`

---

## 14. ArchiveView (`/archive`)

**Plik:** `frontend/src/views/ArchiveView.vue` (57 KB)
**Endpointy:** `GET /archive/contracts`, `GET /archive/contracts/:id`, `GET /archive/articles`, `GET/PATCH /archive/articles/:id/category`, `GET/POST/PUT/DELETE /archive/categories[/:id]`, `GET /archive/categories/tree`, `GET /archive/stats/summary`, `GET /archive/stats/top-machines`, `GET /archive/stats/by-category`, `GET /archive/stats/machine-roi`, `GET /archive/stats/by-city`
**Role:** Admin/User

### UC-ARCH-01: Przeglądanie archiwum umów
**Kroki:** Sidebar → "Archiwum" → lista umów historycznych (z `archive_contracts`)
**Oczekiwany rezultat:** `GET /archive/contracts` → tabela z datami, kontrahentem, wartością
**Edge cases:** **Brak branch check (RAO-SEC-010)** — każdy user czyta archiwum

### UC-ARCH-02: Szczegóły umowy archiwalnej
**Kroki:** Klik umowę → `GET /archive/contracts/:id` → pozycje, warunki, rozliczenia
**Edge cases:** Nieistniejący ID → 404

### UC-ARCH-03: Reorganizacja kategorii archiwalnych
**Kroki:** Archive → "Kategorie" → drag&drop / CRUD
**Oczekiwany rezultat:** `GET/POST/PUT/DELETE /archive/categories[/:id]`, `PATCH /archive/articles/:id/category`

### UC-ARCH-04: Statystyki archiwum
**Kroki:** Archive → "Statystyki"
**Oczekiwany rezultat:**
- `GET /archive/stats/summary` — podsumowanie
- `GET /archive/stats/top-machines` — ranking maszyn
- `GET /archive/stats/by-category` — per kategoria
- `GET /archive/stats/machine-roi` — ROI per maszyna
- `GET /archive/stats/by-city` — per miasto

---

## 15. AnalyticsView (`/analytics`)

**Plik:** `frontend/src/views/AnalyticsView.vue` (24 KB)
**Endpointy:** `GET /stats/fleet-summary`, `GET /stats/top-machines`, `GET /stats/currently-rented`, `GET /stats/machine-roi`, `GET /stats/additional-fees`, `GET /stats/locations`, `GET /stats/by-category`, `GET /stats/by-period`, `GET /stats/categories-list`, `GET /stats/positions`, `GET /explorer/locations`, `GET /explorer/machines/:id`, `GET /explorer/locations/:postal`, `GET /explorer/locations/city/:city`, `GET /explorer/services/:id`
**Role:** Admin/User

### UC-ANL-01: Pulpit analityczny — KPI floty
**Kroki:** Sidebar → "Analityka"
**Oczekiwany rezultat:** `GET /stats/fleet-summary` → KPI (liczba maszyn, wypożyczone, dostępne, ROI)

### UC-ANL-02: Top maszyny (drilldown)
**Kroki:** Tab "Maszyny" → klik maszynę → drilldown
**Oczekiwany rezultat:** `GET /stats/top-machines` → `GET /explorer/machines/:id` (historia umów, ROI, lokalizacje)

### UC-ANL-03: Analiza lokalizacji
**Kroki:** Tab "Lokalizacje" → mapa/lista miast → klik miasto → drilldown
**Oczekiwany rezultat:** `GET /stats/locations` → `GET /explorer/locations/city/:city` (umowy w mieście)

### UC-ANL-04: Analiza okresowa
**Kroki:** Tab "Okresy" → wybierz zakres dat → wykres
**Oczekiwany rezultat:** `GET /stats/by-period?from=...&to=...` → dane do wykresu

### UC-ANL-05: Analiza opłat dodatkowych
**Kroki:** Tab "Opłaty dodatkowe" → lista usług z sumami
**Oczekiwany rezultat:** `GET /stats/additional-fees` → `GET /explorer/services/:id` (drilldown per usługa)

---

## Edge cases transversalne (cross-view)

### EC-1: Brak uprawnień (RBAC 403)
**Widoki:** AdminView (admin-only), SettingsView write (admin-only)
**Scenariusz:** User/viewer próbuje dostać się do admin-only endpoint
**Oczekiwany rezultat:** 403 Forbidden

### EC-2: Sesja wygasła (JWT 8h)
**Scenariusz:** Token wygasa po 8h (config) — **UWAGA: spec mówi 60min (RAO-SEC-004)**
**Oczekiwany rezultat:** 401 → interceptor `useApi.js:21` czyści token → redirect `/login`

### EC-3: Brak danych (empty state)
**Widoki:** ReservationsView (brak rezerwacji w seed), AnalyticsView (brak danych)
**Oczekiwany rezultat:** Komunikat "Brak danych" + ilustracja

### EC-4: Błąd sieci / backend down
**Oczekiwany rezultat:** Komunikat błędu + retry

---

## Bugfixy priorytetyzowane (z Phase 0)

| # | ID | Severity | Widok | Opis | Plik |
|---|----|----------|-------|------|------|
| 1 | RAO-SEC-001 | CRITICAL | ContractFormView | IDOR settlements — brak ownership check | `settlements/router.py` |
| 2 | RAO-SEC-002 | CRITICAL | ContractorFormView | IDOR contractors — PII dostępna dla każdego | `contractors/router.py` |
| 3 | RAO-SEC-003 | HIGH | ArticleFormView | IDOR articles — modyfikacja/usuwanie bez gate | `articles/router.py` |
| 4 | RAO-SEC-004 | HIGH | (auth) | JWT TTL 480min vs spec 60min | `config.py:11` |
| 5 | RAO-SEC-005 | HIGH | ChangePasswordView | Brak session invalidation po change-password | `auth/service.py` |
| 6 | RAO-SEC-006 | HIGH | ResetPasswordView | Password min 6 vs spec 12 | `auth/schemas.py:36,45` |
| 7 | RAO-SEC-007 | HIGH | (global) | Brak security headers (CSP, HSTS, X-Frame) | `main.py:912` |
| 8 | RAO-SEC-008 | MEDIUM | (global) | CORS zbyt permisywny | `main.py:916-918` |
| 9 | RAO-SEC-009 | MEDIUM | CommissionView | Brak branch filter w summary PDF | `reports/router.py:101-164` |
| 10 | RAO-SEC-010 | MEDIUM | ArchiveView | Brak branch check w archive | `archive/router.py:65` |
| 11 | RAO-TECH-001 | LOW | SettingsView | Martwy store `feeTemplates` | `stores/settings.js:97-107` |
| 12 | RAO-TECH-002 | LOW | SettingsView | Martwe kolumny Company (report_folder, protocol_folder, app_version, logo) | `settings/models.py:9-29` |
| 13 | RAO-TECH-003 | LOW | SettingsView | Zakładka `folder` vs `pdf-folders` (nakładanie) | `SettingsView.vue` |
| 14 | RAO-TECH-004 | LOW | (spec) | STALE notatka RAO-P1-023 (ReservationsView usunięty — ale istnieje) | `spec/core/03_frontend_screens.md:837-839` |
| 15 | RAO-TECH-005 | LOW | (spec) | STALE ASCII layout SettingsView (Folder [___]) | `spec/core/03_frontend_screens.md:849` |
| 16 | RAO-TECH-006 | LOW | (spec) | `spec/core/15_build_progress.md` STALE | `spec/core/15_build_progress.md` |
| 17 | RAO-SEC-011 | HIGH | (spec) | DB password w `spec/process/migrations.md` | `spec/process/migrations.md:100,105` |
| 18 | RAO-QA-002 | MEDIUM | ContractFormView | POST contracts bez date_from → 500 | `contracts/router.py` |
| 19 | RAO-QA-003 | MEDIUM | ContractFormView | PDF nieistniejący contract_id → 500 | `reports/router.py` |
| 20 | RAO-QA-004 | MEDIUM | ContractFormView | PDF nieistniejący contractor_id → 500 | `reports/router.py` |

---

## Następne kroki

1. **Faza 2:** E2E testy + screenshoty z adnotacjami (strzałki przez PIL) dla każdego widoku
2. **Faza 3:** User manual markdown (15 widoków) — szczegółowy opis każdego pola, przycisku, akcji
3. **Faza 4:** Bugfixy (CRITICAL IDOR first) + `BUGFIX_LOG.md`
4. **Faza 5:** Cleanup historycznych (martwy store, martwe kolumny Company, STALE spec)
5. **Faza 6:** PDF generation (user manual jako PDF)
6. **Faza 7:** Spec sync + final report
