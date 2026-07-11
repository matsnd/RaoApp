# RAO — User Manual (kompletny)

> **Wersja:** 1.0 | **Data:** 2026-07-11
> **Aplikacja:** RAO — Wynajem maszyn budowlanych
> **Stack:** FastAPI (backend, port 8000) + Vue 3 (frontend, port 5173) + MariaDB
> **Login demo:** `admin` / `admin123`

---

## Spis treści

1. [Wprowadzenie](#1-wprowadzenie)
2. [Role i uprawnienia](#2-role-i-uprawnienia)
3. [Konwencje UI](#3-konwencje-ui)
4. [LoginView — Logowanie](#4-loginview--logowanie)
5. [ResetPasswordView — Reset hasła](#5-resetpasswordview--reset-hasła)
6. [ChangePasswordView — Zmiana hasła](#6-changepasswordview--zmiana-hasła)
7. [HomeView — Pulpit startowy](#7-homeview--pulpit-startowy)
8. [DashboardView — Lista umów/kontrahentów/maszyn](#8-dashboardview--listy)
9. [ContractorFormView — Kontrahenci](#9-contractorformview--kontrahenci)
10. [ArticleFormView — Maszyny/artykuły](#10-articleformview--maszynyartykuły)
11. [ReservationsView — Rezerwacje](#11-reservationsview--rezerwacje)
12. [ContractFormView — Umowy](#12-contractformview--umowy)
13. [WorkerView — Pulpit pracownika](#13-workerview--pulpit-pracownika)
14. [CommissionView — Prowizje](#14-commissionview--prowizje)
15. [SettingsView — Ustawienia](#15-settingsview--ustawienia)
16. [AdminView — Administracja](#16-adminview--administracja)
17. [ArchiveView — Archiwum](#17-archiveview--archiwum)
18. [AnalyticsView — Analityka](#18-analyticsview--analityka)
19. [FAQ / Troubleshooting](#19-faq--troubleshooting)

---

## 1. Wprowadzenie

RAO to aplikacja do zarządzania wynajmem maszyn budowlanych. Migracja z legacy WinForms (C# .NET) do nowoczesnego stacku webowego.

**Funkcje główne:**
- Zarządzanie kontrahentami (z integracją GUS)
- Zarządzanie maszynami/artykułami (z cennikami kaskadowymi)
- Umowy najmu (z pozycjami, warunkami rozliczeniowymi, usługami dodatkowymi)
- Rozliczenia umów (ręczne + integracja Fakturownia)
- Raporty PDF (umowa, protokół zdawczo-odbiorczy, prowizje, statystyki)
- Rezerwacje maszyn (kalendarz)
- Analityka (KPI floty, top maszyny, lokalizacje, okresy)
- Archiwum (historia umów i maszyn)
- Administracja użytkownikami (RBAC: admin/user/viewer)

**Dostęp:**
- Frontend: `http://localhost:5173/rao/`
- Backend API: `http://localhost:8000/rao/api/`
- API docs (dev): `http://localhost:8000/rao/api/docs`

---

## 2. Role i uprawnienia

| Rola | Opis | Uprawnienia |
|------|------|-------------|
| **admin** | Administrator | Pełny dostęp do wszystkich zasobów, wszystkich filii, ustawień, administracji użytkownikami |
| **user** | Pracownik | Dostęp do zasobów własnej filii (branch_id). Odczyt kontrahentów (współdzielone). Brak dostępu do ustawień (write) i administracji |
| **viewer** | Obserwator | Tylko odczyt zasobów własnej filii. Brak możliwości modyfikacji |

**Zasady IDOR (Insecure Direct Object Reference) — zabezpieczenia:**
- Umowy: branch-scoped (admin: wszystkie; user/viewer: własny branch + NULL=legacy)
- Rozliczenia: branch-scoped (jak umowy)
- Artykuły: branch-scoped (jak umowy)
- Kontrahenci: odczyt dla wszystkich, modyfikacja tylko admin (encje współdzielone)
- Raporty zbiorcze: tylko admin
- Archiwum: branch-scoped

---

## 3. Konwencje UI

**Kolory (design system Toolsmart):**
- Primary: `#1D2B53` (navy)
- Error: `#DC2626` (red)
- Background: białe karty na jasnym tle
- Border radius: 12px (karty), 8px (pola)

**Stany elementów:**
- **Loading:** spinner w przycisku, szary overlay na liście
- **Error:** czerwony komunikat z ikoną ⚠️
- **Empty:** komunikat "Brak danych" z ilustracją
- **Success:** zielony komunikat (toast)

**Nawigacja:**
- Sidebar po lewej (zwija się na mobile)
- KPI na górze (klikalne → nawigacja z filtrem)
- Tabele z sortowaniem po kolumnie, paginacją, filtrami

---

## 4. LoginView — Logowanie

**Route:** `/login` | **Plik:** `LoginView.vue` | **Screenshot:** `../screenshots/01_login_loginview.png`

**Role:** Publiczny (wszyscy)

**Endpointy:**
- `POST /auth/login` — logowanie
- `POST /auth/forgot-password` — reset hasła (link email)

**Pola formularza:**

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| Login | text | Tak | Nazwa użytkownika (np. `admin`) |
| Hasło | password | Tak | Hasło (min. 8 znaków dla nowych) |
| Zapamiętaj mnie | checkbox | Nie | Zachowaj sesję |

**Przyciski:**

| Przycisk | Akcja | Opis |
|----------|-------|------|
| Zaloguj się | Submit | Wysyła `POST /auth/login`, zapisuje JWT w localStorage |
| 👁️/🙈 | Toggle | Pokaż/ukryj hasło |
| Nie pamiętam hasła | Modal | Otwiera modal resetu hasła |

**Kroki obsługi (happy path):**
1. Wejdź na `http://localhost:5173/rao/login`
2. Wpisz login (np. `admin`)
3. Wpisz hasło (np. `admin123`)
4. Kliknij "Zaloguj się"
5. Przekierowanie na `/home` (lub `?redirect=...` jeśli było)

**Edge cases:**
- Błędne hasło → 401 + animacja "shake" pola
- Rate limit 5 prób/60s/IP → 429 (wyłączony w dev)
- `must_change_password=true` → przekierowanie na `/password`
- Nieaktywne konto → 401

---

## 5. ResetPasswordView — Reset hasła

**Route:** `/reset-password?token=...` | **Plik:** `ResetPasswordView.vue` | **Screenshot:** `../screenshots/02_reset_password_resetpasswordview.png`

**Role:** Publiczny (z tokenem z emaila)

**Endpointy:**
- `POST /auth/reset-password` — reset hasła z tokenu

**Pola:**

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| Nowe hasło | password | Tak | Min. 8 znaków |
| Powtórz hasło | password | Tak | Musi być identyczne |

**Kroki:**
1. Kliknij link w emailu → `/reset-password?token=...`
2. Wpisz nowe hasło (min. 8 znaków)
3. Powtórz hasło
4. Kliknij "Zresetuj hasło"
5. Przekierowanie na `/login` z komunikatem sukcesu

**Edge cases:**
- Wygasły token (>1h) → 400
- Zużyty token → 400
- Hasła niezgodne → walidacja frontend
- Brak tokenu w URL → komunikat "Brak tokenu"

---

## 6. ChangePasswordView — Zmiana hasła

**Route:** `/password` | **Plik:** `ChangePasswordView.vue` | **Screenshot:** `../screenshots/03_change_password_changepasswordview.png`

**Role:** Zalogowany

**Endpointy:**
- `PUT /auth/change-password` — zmiana hasła

**Pola:**

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| Aktualne hasło | password | Tak | Obecne hasło (weryfikacja bcrypt) |
| Nowe hasło | password | Tak | Min. 8 znaków, ≠ aktualne |
| Powtórz hasło | password | Tak | Musi być identyczne |

**Kroki:**
1. Kliknij awatar → "Zmień hasło" (lub przekierowanie z login gdy `must_change_password`)
2. Wpisz aktualne hasło
3. Wpisz nowe hasło
4. Powtórz nowe hasło
5. Kliknij "Zmień hasło"

**Edge cases:**
- Błędne aktualne hasło → 400
- Nowe = aktualne → 400
- **UWAGA:** Nie unieważnia innych sesji (brak jti blacklist — RAO-SEC-005 pending)

---

## 7. HomeView — Pulpit startowy

**Route:** `/home` | **Plik:** `HomeView.vue` | **Screenshot:** `../screenshots/04_home_homeview.png`

**Role:** Zalogowany

**Endpointy:**
- `GET /stats/fleet-summary` — KPI floty
- `GET /stats/expiring-contracts` — umowy wygasające (7 dni)
- `GET /stats/deliveries-today` — dostawy dzisiaj
- `GET /stats/unprinted-contracts` — nie wydrukowane umowy
- `GET /stats/stale-print-contracts` — stare druki
- `GET /contracts/overdue` — przeterminowane

**KPI (kafelki na górze):**

| KPI | Opis | Klik → |
|-----|------|--------|
| Flota teraz | Liczba maszyn aktywnie wypożyczonych | Dashboard |
| Umowy wygasające | Kontrakty kończące się w ciągu 7 dni | Dashboard z filtrem |
| Dostawy dzisiaj | Maszyny do zwrotu dziś | Dashboard |
| Nie wydrukowane | Umowy bez PDF | Dashboard |
| Przeterminowane | Umowy po terminie (`date_to < today AND is_settled=false`) | Dashboard |
| Stare druki | Umowy z PDF starszym niż N dni | Dashboard |

**Kroki:**
1. Zaloguj się → automatyczne przekierowanie na `/home`
2. Przeglądaj KPI — kliknij kafeldek aby przejść do szczegółów
3. Sekcja "Przeterminowane" — lista umów z linkami do edycji

---

## 8. DashboardView — Listy

**Route:** `/dashboard/:section` | **Plik:** `DashboardView.vue` | **Screenshot:** `../screenshots/05_dashboard_contracts_dashboardview.png`

**Role:** Zalogowany (admin: wszystkie; user: własny branch; viewer: read-only)

**Sekcje:**
- `/dashboard/contracts` — lista umów
- `/dashboard/contractors` — lista kontrahentów
- `/dashboard/articles` — lista maszyn
- `/dashboard/overdue` — umowy przeterminowane

**Endpointy:**
- `GET /contracts` — lista umów (branch-scoped)
- `GET /contracts/overdue` — przeterminowane
- `GET /contractors` — lista kontrahentów
- `GET /articles` — lista maszyn
- `GET /settings/salespeople` — handlowcy (do filtrów)

**Filtry (sekcja contracts):**

| Filtr | Typ | Opis |
|-------|-----|------|
| Handlowiec | select | Filtr po salesperson_id |
| Miasto | text | Filtr po city |
| Status | select | Aktywna / Przeterminowana / Rozliczona |
| Data od/do | date range | Filtr po date_from/date_to |

**Kroki:**
1. Sidebar → "Umowy" / "Kontrahenci" / "Maszyny"
2. Ustaw filtry (handlowiec, miasto, status, data)
3. Sortuj po kolumnie (klik nagłówka)
4. Klik wiersz → edycja (umowa/kontrahent/maszyna)

---

## 9. ContractorFormView — Kontrahenci

**Route:** `/contractors/new`, `/contractors/:id/edit` | **Plik:** `ContractorFormView.vue` | **Screenshot:** `../screenshots/08_contractor_new_contractorformview.png`

**Role:** Odczyt — wszyscy; Modyfikacja — admin tylko (RAO-SEC-002)

**Endpointy:**
- `POST /contractors` — tworzenie (admin)
- `GET /contractors/:id` — szczegóły
- `PUT /contractors/:id` — edycja (admin)
- `DELETE /contractors/:id` — usuwanie (admin)
- `POST/PUT/DELETE /contractors/:id/addresses[/:addr]` — adresy (admin)
- `POST /integrations/gus-lookup` — auto-uzupełnianie z GUS

**Pola:**

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| Nazwa | text | Tak | Nazwa firmy |
| NIP | text | Tak | NIP (walidacja checksum) |
| REGON | text | Nie | REGON |
| Telefon | text | Nie | Telefon kontaktowy |
| Email | email | Nie | Email kontaktowy |
| Miasto | text | Nie | Miasto |
| Ulica | text | Nie | Ulica + numer |
| Kod pocztowy | text | Nie | Format XX-XXX |

**Przyciski:**

| Przycisk | Akcja | Opis |
|----------|-------|------|
| Pobierz z GUS | API call | Auto-uzupełnia nazwę, adres, REGON z NIP |
| Zapisz | Submit | Zapisuje kontrahenta |
| Anuluj | Nawigacja | Powrót do listy |

**Kroki (tworzenie):**
1. Dashboard → "Nowy kontrahent"
2. Wpisz NIP
3. Klik "Pobierz z GUS" → auto-uzupełnienie
4. Uzupełnij brakujące pola (telefon, email)
5. Klik "Zapisz"

**Edge cases:**
- NIP nie znaleziony w GUS → komunikat, ręczne uzupełnienie
- NIP nieunikalny → 400
- User/viewer próbuje zapisać → 403

---

## 10. ArticleFormView — Maszyny/artykuły

**Route:** `/articles/new`, `/articles/:id/edit` | **Plik:** `ArticleFormView.vue` | **Screenshot:** `../screenshots/09_article_new_articleformview.png`

**Role:** Odczyt — branch-scoped; Modyfikacja — branch-scoped (RAO-SEC-003)

**Endpointy:**
- `POST /articles` — tworzenie
- `GET /articles/:id` — szczegóły
- `PUT /articles/:id` — edycja
- `DELETE /articles/:id` — usuwanie
- `POST /articles/:id/duplicate` — duplikowanie
- `GET/POST /settings/articles/:id/rate-presets` — cenniki rozliczeń
- `GET /integrations/fakturownia/products` — produkty FA (do mapowania)

**Pola:**

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| Nazwa | text | Tak | Nazwa maszyny/usługi |
| Kategoria | tree select | Nie | Drzewo kategorii (main/sub1) |
| Typ | select | Tak | Maszyna / Usługa |
| Nr wewnętrzny | text | Nie | Numer wewnętrzny |
| Nr rejestracyjny | text | Nie | Dla maszyn |
| Marka | text | Nie | Producent |
| Model | text | Nie | Model |
| Cena bazowa | number | Nie | Wartość zastępcza |
| Oddział | select | Nie | Branch (NULL = legacy) |
| Zasilanie | select | Nie | Diesel / Elektryk / Hydrauliczny (power_type) |

**Cennik rozliczeń (rate presets):**
- Dodaj warunki: zakres dni (1-3, 4-16, >16), typ stawki (dniowa/godzinowa/km/tygodniowa/miesięczna), kwota
- Nakładające się zakresy → 422

**Mapowanie Fakturownia:**
- Klik "Mapuj z Fakturownia" → wybierz produkt z listy → zapis `fakturownia_product_id`

**Kroki (tworzenie):**
1. Dashboard → "Nowa maszyna"
2. Wypełnij nazwę, kategorię, typ, markę, model
3. Dodaj cennik (sekcja "Cennik" → "Dodaj warunek")
4. Opcjonalnie: mapuj z Fakturownia
5. Klik "Zapisz"

---

## 11. ReservationsView — Rezerwacje

**Route:** `/reservations` | **Plik:** `ReservationsView.vue` | **Screenshot:** `../screenshots/10_reservations_reservationsview.png`

**Role:** Admin/User

**Endpointy:**
- `GET /reservations/calendar?month=YYYY-MM` — kalendarz
- `POST /reservations` — tworzenie
- `PUT /reservations/:id` — edycja
- `DELETE /reservations/:id` — usuwanie
- `GET /articles` — lista maszyn
- `GET /contractors` — lista kontrahentów

**Pola (formularz rezerwacji):**

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| Maszyna | select | Tak | Tylko maszyny wewnętrzne (is_external=false) |
| Kontrahent | select | Tak | Wybór z listy |
| Data od | date | Tak | Początek rezerwacji |
| Data do | date | Tak | Koniec rezerwacji |

**Kroki:**
1. Sidebar → "Rezerwacje" → kalendarz miesięczny
2. Klik "Nowa rezerwacja"
3. Wybierz maszynę, kontrahenta, daty
4. Klik "Zapisz"
5. Rezerwacja pojawia się w kalendarzu

**Edge cases:**
- Konflikt dat z inną rezerwacją → 409
- Maszyna zewnętrzna (is_external) → niedostępna w liście

---

## 12. ContractFormView — Umowy

**Route:** `/contracts/new`, `/contracts/:id/edit` | **Plik:** `ContractFormView.vue` (128 KB — największy) | **Screenshot:** `../screenshots/11_contract_new_contractformview.png`

**Role:** Admin (all), User (własny branch), Viewer (read-only)

**Endpointy (~30):**
- `POST/GET/PUT /contracts[/:id]` — CRUD umowy
- `GET/POST/PUT/DELETE /contracts/:id/positions[/:pid]` — pozycje (maszyny)
- `GET/POST/PUT/DELETE /contracts/:id/positions/:pid/conditions[/:cid]` — warunki rozliczeniowe
- `GET/POST/PUT/DELETE /contracts/:id/service-fees[/:fid]` — usługi dodatkowe
- `POST /contracts/:id/service-fees/reset` — reset opłat
- `POST /contracts/:id/service-fees/apply-preset` — aplikowanie presetu
- `POST /contracts/:id/recalculate` — przeliczenie
- `PATCH /contracts/:id/settle` — oznacz jako rozliczona
- `GET/POST/PUT/DELETE /settlements/contract/:id[/:sid]` — rozliczenia
- `POST /settlements/contract/:id/init` — inicjalizacja ręczna
- `POST /settlements/contract/:id/init-from-fakturownia` — inicjalizacja z FA
- `POST /reports/contract/:id` — generowanie PDF
- `GET /integrations/postal-codes/:code` — auto-uzupełnianie PNA
- `POST /integrations/extract-address` — ekstrakcja adresu
- `POST /integrations/geocode` — geokodowanie Nominatim
- `GET /integrations/fakturownia/invoices` — faktury FA
- `GET /articles/:id/availability` — dostępność maszyny
- `GET /articles/:id/last-conditions` — auto-prefill warunków

### 12.1 Dane umowy

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| Kontrahent | select | Tak | Wybór z listy |
| Handlowiec | select | Nie | Salesperson |
| Oddział | select | Nie | Branch (user: własny; admin: dowolny) |
| Data od | date | Tak | Początek umowy (RAO-QA-002: wymagane) |
| Data do | date | Nie | Koniec umowy |
| Typ | select | Tak | S (najem) / U (usługa) |
| OID | text | Nie | OID Fakturownia (puste = użyj numeru umowy) |
| Adres dostawy | text | Nie | Adres budowy |
| Kod pocztowy | text | Nie | Auto-uzupełnianie miasta z PNA |
| Miasto | text | Nie | Auto-uzupełniane z PNA |
| Osoba kontaktowa 1 | text | Nie | Z pokazuj na PDF |
| Osoba kontaktowa 2 | text | Nie | Z pokazuj na PDF |
| Email | email | Nie | Email kontaktowy |
| Telefon | text | Nie | Telefon kontaktowy |
| Notatki | textarea | Nie | Notatki wewnętrzne |

### 12.2 Pozycje umowy (maszyny)

**Kroki:**
1. W umowie → sekcja "Pozycje" → "Dodaj pozycję"
2. Wybierz maszynę z listy (z sprawdzaniem dostępności)
3. Ustaw ilość, daty
4. Klik "Zapisz"
5. `GET /articles/:id/availability` sprawdza konflikty z innymi umowami/rezerwacjami

**Edge cases:**
- Maszyna niedostępna w dacie → 409
- Auto-prefill warunków z ostatniej umowy tej maszyny (`GET /articles/:id/last-conditions`)

### 12.3 Warunki rozliczeniowe (kaskadowe)

**Kroki:**
1. W pozycji → "Warunki" → "Dodaj warunek"
2. Ustaw zakres dni (np. 1-3, 4-16, >16)
3. Wybierz typ stawki: dniowa, godzinowa, km, tygodniowa, miesięczna, jednorazowa
4. Ustaw kwotę
5. Klik "Zapisz"

**Edge cases:**
- Nakładające się zakresy → 422

### 12.4 Usługi dodatkowe (service fees)

**Kroki:**
1. W umowie → "Usługi dodatkowe" → "Dodaj"
2. Wybierz usługę: Transport, Czyszczenie, Tankowanie, Przestój, Serwis, Przegląd Diesel, Przegląd Elektryk
3. Ustaw kwotę, datę
4. Klik "Zapisz"

**Preset usług:**
- Klik "Aplikuj preset" → wybierz zestaw:
  - Najem (podstawowy)
  - Z operatorem
  - Długoterminowy
  - Weekend
  - Zagraniczny
  - Operator premium

### 12.5 Auto-uzupełnianie adresu z PNA

**Kroki:**
1. Wpisz kod pocztowy w polu "Kod pocztowy"
2. Klik "Pobierz lokalizację"
3. `GET /integrations/postal-codes/:code` → miasto, ulica (z cache `postal_codes`)
4. Jeśli nie znaleziono → fallback do Nominatim `POST /integrations/geocode`

### 12.6 Rozliczenie ręczne (manual settlement)

**Kroki:**
1. W umowie → sekcja "Rozliczenie" → "Inicjalizuj ręcznie"
2. `POST /settlements/contract/:id/init` → tworzy pozycje rozliczenia z pozycji umowy
3. Wypełnij ilości, kwoty
4. Klik "Zapisz"

### 12.7 Rozliczenie z Fakturownia (FA integration)

**Kroki:**
1. W umowie FA-pending (`is_settled=false`) z kontrahentem mającym faktury w FA
2. Sekcja "Rozliczenie" → przycisk "💰 Pobierz z Fakturownia"
   - Disabled jeśli FA nie skonfigurowane
3. Klik → `POST /settlements/contract/:id/init-from-fakturownia`
4. Backend:
   - Pobiera faktury z FA (OID z DB — IDOR fix)
   - Mapuje pozycje umowy z produktami FA (`pid_to_positions`)
   - Mapuje usługi dodatkowe (`pid_to_service_fees`)
   - Tworzy `ContractSettlement` (`source=fakturownia`, `settled_at=invoice.issue_date`)
   - Niezmapowane pozycje → `source=fa_unmapped` z `article_name_snapshot`
   - Idempotentność: `UNIQUE(unmapped_key)`
   - Semantyka 1:N: produkt FA na wielu artykułach → każdy dostaje pełną wartość

**Edge cases:**
- Brak faktur w FA → 404 "Brak faktur w Fakturownia dla tej umowy"
- Umowa bez OID → 422 "Umowa nie posiada numeru OID"
- Błąd FA API → komunikat błędu
- Umowa już rozliczona → modyfikacja zablokowana
- Rate limit 30/min/user → 429

### 12.8 Generowanie PDF

**Kroki:**
1. W umowie → "Generuj PDF"
2. Wybierz typ: Umowa / Protokół ZO / Protokół ZO (S) / Protokół ZO (U) / Protokół ZO (bez danych) / ...
3. `POST /reports/contract/:id?type=...` → PDF (WeasyPrint, Jinja2)
4. Auto-zapis do folderu PDF (per oddział: report_main, protocol_main, report_gdansk, protocol_gdansk)
5. Status "Wydrukowano" ustawiony na umowie (`print_date`)

### 12.9 Edycja umowy rozliczonej (lock)

- Umowa z `is_settled=true` → mutacje zablokowane
- Frontend: pola disabled
- Backend: 409 "Umowa jest rozliczona — modyfikacja zablokowana. Najpierw cofnij rozliczenie."

### 12.10 Usuwanie umowy (guard)

- `DELETE /contracts/:id` → 200 (jeśli bez pozycji/rozliczeń) lub 400 (jeśli z danymi)
- `verify_contract_access` chroni przed IDOR

---

## 13. WorkerView — Pulpit pracownika

**Route:** `/worker` | **Plik:** `WorkerView.vue` | **Screenshot:** `../screenshots/12_worker_workerview.png`

**Role:** Worker (rola operacyjna)

**Endpointy:**
- `GET /stats/expiring-contracts` — wygasające (7 dni)
- `GET /stats/deliveries-today` — dostawy dzisiaj
- `GET /stats/unprinted-contracts` — nie wydrukowane
- `GET /stats/stale-print-contracts` — stare druki
- `GET /stats/overdue-contracts` — przeterminowane

**Sekcje:**

| Sekcja | Opis |
|--------|------|
| Dostawy dzisiaj | Maszyny do zwrotu dziś |
| Umowy wygasające | Kończące się w ciągu 7 dni |
| Nie wydrukowane | Umowy bez PDF |
| Stare druki | Umowy z PDF starszym niż N dni |
| Przeterminowane | Umowy po terminie |

**Kroki:**
1. Sidebar → "Pulpit pracownika"
2. Przeglądaj listy akcji operacyjnych
3. Klik pozycji → `/contracts/:id/edit`

---

## 14. CommissionView — Prowizje

**Route:** `/commissions` | **Plik:** `CommissionView.vue` | **Screenshot:** `../screenshots/13_commissions_commissionview.png`

**Role:** Manager/Admin (raporty zbiorcze tylko admin — RAO-SEC-009)

**Endpointy:**
- `GET /reports/summary/commissions` — PDF prowizji (admin only)
- `GET /stats/commissions` — dane do tabeli

**Tabela:**

| Kolumna | Opis |
|---------|------|
| Handlowiec | Imię i nazwisko |
| Liczba umów | Liczba umów w okresie |
| Suma | Suma wartości umów |
| Prowizja % | Procent prowizji (np. 5%, 3.5%) |
| Prowizja PLN | Kwota prowizji |

**Kroki:**
1. Sidebar → "Prowizje"
2. Przeglądaj tabelę prowizji
3. Klik "Eksportuj PDF" → zapis do folderu PDF (admin only)

---

## 15. SettingsView — Ustawienia

**Route:** `/settings` | **Plik:** `SettingsView.vue` (61 KB, 1240 linii) | **Screenshot:** `../screenshots/14_settings_settingsview.png`

**Role:** Admin (write), User (read)

**Zakładki (9):**

### 15.1 Firma

**Endpoint:** `GET/PUT /settings/company`, `POST /settings/company/logo`

| Pole | Typ | Opis |
|------|-----|------|
| Nazwa | text | Nazwa firmy |
| Skrócona nazwa | text | Krótka nazwa |
| NIP | text | NIP firmy |
| REGON | text | REGON |
| Kod pocztowy | text | Kod |
| Miasto | text | Miasto |
| Ulica | text | Ulica |
| Nagłówek PDF | textarea | Tekst na nagłówku PDF |
| Bank | text | Nazwa banku |
| Rachunek | text | Numer konta |
| Numeracja | select | Schemat numeracji umów |
| Logo | file upload | Logo firmy na PDF (PNG/JPEG, max 5MB) |

### 15.2 Handlowcy

**Endpoint:** `GET/POST/PUT/DELETE /settings/salespeople[/:id][/:toggle]`

| Pole | Typ | Opis |
|------|-----|------|
| Imię | text | Imię |
| Nazwisko | text | Nazwisko |
| Prowizja % | number | Procent prowizji |
| Aktywny | toggle | Status aktywności |

### 15.3 Kategorie

**Endpoint:** `GET/POST/PUT/DELETE /settings/categories[/:id]`, `GET /settings/categories/tree`

Drzewo kategorii hierarchiczne (main → sub1). Używane w ArticleFormView i AnalyticsView.

### 15.4 Typy stawek

**Endpoint:** `GET/POST/PUT/DELETE /settings/rate-types[/:id]`

CRUD typów stawek: dniowa, godzinowa, km, tygodniowa, miesięczna, jednorazowa.

### 15.5 Zestawy usług dodatkowych

**Endpoint:** `GET/POST/PUT/DELETE /settings/fee-preset-groups[/:id]`, `POST/PUT/DELETE/PATCH /settings/fee-preset-groups/:id/templates[/:tid][/:reorder]`

Zestawy presetów usług: Najem, Z operatorem, Długoterminowy, Weekend, Zagraniczny, Operator premium.

### 15.6 Cenniki rozliczeń maszyn (read-only)

**Endpoint:** `GET /settings/articles/:id/rate-presets`

Przegląd cenników per maszyna. Edycja w ArticleFormView.

### 15.7 Fakturownia

**Endpoint:** `GET/PUT /integrations/fakturownia/settings`

| Pole | Typ | Opis |
|------|-----|------|
| Subdomena | text | Subdomena konta FA (np. `matsnd`) |
| API Token | password | Token API (maskowany: `tk_****1234`, NIGDY plaintext) |
| Aktywna | toggle | Włącz/wyłącz integrację |

**Bezpieczeństwo:**
- Token szyfrowany Fernet (AES-128-CBC + HMAC)
- W DB: `api_token_ciphertext` (VARBINARY)
- W odpowiedzi: tylko `api_token_preview` (maskowany)
- Audit trail: `api_token_updated_at`, `api_token_updated_by`
- Rate limit: 5/min/IP (settings), 30/min/user (invoices)

### 15.8 Folder RAO (legacy)

**Uwaga:** Nakłada się z `pdf-folders` (kandydat na konsolidację). Pojedynczy folder główny RAO przez `useTargetFolder` (IndexedDB).

### 15.9 Foldery PDF (per-oddział)

**Endpoint:** Brak (IndexedDB via `usePdfFolders`)

4 foldery auto-zapisu PDF:
- `report_main` — raporty umów (oddział główny)
- `protocol_main` — protokoły ZO (oddział główny)
- `report_gdansk` — raporty umów (Gdańsk)
- `protocol_gdansk` — protokoły ZO (Gdańsk)

---

## 16. AdminView — Administracja

**Route:** `/admin` | **Plik:** `AdminView.vue` | **Screenshot:** `../screenshots/15_admin_adminview.png`

**Role:** Admin (`requiresAdmin: true`)

**Endpointy:**
- `GET /admin/users` — lista użytkowników
- `POST /admin/users` — tworzenie
- `PUT /admin/users/:id` — edycja
- `PATCH /admin/users/:id/deactivate` — dezaktywacja
- `PATCH /admin/users/:id/activate` — aktywacja
- `POST /admin/users/:id/force-password-reset` — wymuszenie resetu hasła

**Pola (tworzenie użytkownika):**

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| Login | text | Tak | Unikalny login (^[a-zA-Z0-9_]+$) |
| Email | email | Tak | Email |
| Rola | select | Tak | admin / user / viewer |
| Oddział | select | Nie | Branch |
| Hasło | password | Tak | Min. 8 znaków |

**Kroki (tworzenie użytkownika):**
1. Sidebar → "Administracja" (tylko admin)
2. "Nowy użytkownik"
3. Wpisz login, email, rolę, oddział
4. Klik "Zapisz" → 201 (z `must_change_password=true`)

**Akcje na liście:**

| Akcja | Opis |
|-------|------|
| Edytuj | Zmiana roli, oddziału, email |
| Deztywuj | Blokuje login (self-deactivate zablokowane) |
| Aktywuj | Odblokowuje login |
| Wymuś reset hasła | Ustawia `must_change_password=true` |

---

## 17. ArchiveView — Archiwum

**Route:** `/archive` | **Plik:** `ArchiveView.vue` (57 KB) | **Screenshot:** `../screenshots/16_archive_archiveview.png`

**Role:** Admin (all), User (własny branch — RAO-SEC-010)

**Endpointy:**
- `GET /archive/contracts` — lista umów archiwalnych
- `GET /archive/contracts/:id` — szczegóły (branch-scoped)
- `GET /archive/articles` — lista maszyn archiwalnych
- `GET/PATCH /archive/articles/:id/category` — zmiana kategorii
- `GET/POST/PUT/DELETE /archive/categories[/:id]` — CRUD kategorii archiwum
- `GET /archive/categories/tree` — drzewo
- `GET /archive/stats/summary` — podsumowanie
- `GET /archive/stats/top-machines` — ranking maszyn
- `GET /archive/stats/by-category` — per kategoria
- `GET /archive/stats/machine-roi` — ROI per maszyna
- `GET /archive/stats/by-city` — per miasto

**Sekcje:**
1. **Umowy archiwalne** — lista z datami, kontrahentem, wartością
2. **Maszyny archiwalne** — lista z możliwością reorganizacji kategorii
3. **Kategorie archiwum** — drzewo kategorii (osobne od aktywnych)
4. **Statystyki archiwum** — KPI, top maszyny, ROI, per kategoria/miasto

---

## 18. AnalyticsView — Analityka

**Route:** `/analytics` | **Plik:** `AnalyticsView.vue` | **Screenshot:** `../screenshots/17_analytics_analyticsview.png`

**Role:** Admin/User

**Endpointy:**
- `GET /stats/fleet-summary` — KPI floty
- `GET /stats/top-machines` — ranking maszyn
- `GET /stats/currently-rented` — aktualnie wypożyczone
- `GET /stats/machine-roi` — ROI per maszyna
- `GET /stats/additional-fees` — opłaty dodatkowe
- `GET /stats/locations` — lokalizacje
- `GET /stats/by-category` — per kategoria
- `GET /stats/by-period` — per okres
- `GET /stats/categories-list` — lista kategorii
- `GET /stats/positions` — pozycje umów
- `GET /explorer/locations` — eksplorator lokalizacji
- `GET /explorer/machines/:id` — drilldown maszyny
- `GET /explorer/locations/:postal` — drilldown PNA
- `GET /explorer/locations/city/:city` — drilldown miasto
- `GET /explorer/services/:id` — drilldown usługi

**Zakładki:**

| Tab | Opis | Drilldown |
|-----|------|-----------|
| Maszyny | Ranking maszyn z ROI | Klik → `/explorer/machines/:id` (historia umów, lokalizacje) |
| Lokalizacje | Mapa/lista miast | Klik miasto → `/explorer/locations/city/:city` |
| Okresy | Wykres czasowy | Wybierz zakres dat → `/stats/by-period` |
| Opłaty dodatkowe | Sumy per usługa | Klik → `/explorer/services/:id` |
| Kategorie | Per kategoria maszyn | — |

**KPI (pulpit):**
- Liczba maszyn (aktywne, wypożyczone, dostępne)
- ROI średni
- Przychód w okresie

---

## 19. FAQ / Troubleshooting

### Q1: Nie mogę się zalogować — "Błędne dane"
**A:** Sprawdź login i hasło. Demo: `admin` / `admin123`. Rate limit 5 prób/60s/IP (wyłączony w dev).

### Q2: Token wygasł — przekierowanie na login
**A:** JWT TTL = 60 min. Zaloguj się ponownie. Token w `localStorage.rao_token`.

### Q3: "Brak uprawnień" (403) przy zapisie kontrahenta
**A:** Tylko admin może modyfikować kontrahentów (RAO-SEC-002). User/viewer = read-only.

### Q4: "Brak uprawnień" (403) przy raportach zbiorczych
**A:** Raporty zbiorcze (contractors, machines, commissions, stats) są admin-only (RAO-SEC-009).

### Q5: Nie widzę umów z innej filii
**A:** User/viewer widzi tylko umowy z własnego branch + NULL (legacy). Admin widzi wszystkie. To jest feature, nie bug (IDOR protection).

### Q6: "Umowa jest rozliczona — modyfikacja zablokowana"
**A:** Umowa z `is_settled=true` jest zablokowana. Najpierw cofnij rozliczenie (admin).

### Q7: Fakturownia — "Brak faktur dla tej umowy"
**A:** Sprawdź: (1) FA skonfigurowane w Settings, (2) umowa ma OID, (3) kontrahent ma faktury w FA, (4) produkty FA są zmapowane z artykułami RAO.

### Q8: PDF nie generuje się
**A:** Sprawdź: (1) WeasyPrint zainstalowany, (2) umowa istnieje (404), (3) typ raportu poprawny.

### Q9: Auto-uzupełnianie GUS nie działa
**A:** Sprawdź: (1) GUS_API_KEY w .env, (2) NIP poprawny (checksum), (3) GUS API dostępne.

### Q10: Reset hasła — email nie dociera
**A:** W dev: sprawdź Mailpit UI (`http://localhost:8025`). W prod: sprawdź konfigurację SMTP w .env.

---

## Załączniki

- [Use Cases](../use_cases/USE_CASES.md) — 80 scenariuszy użycia
- [Bugfix Log](../BUGFIX_LOG.md) — historia naprawionych bugów
- [Screenshots](../screenshots/) — 17 zrzutów ekranu z adnotacjami
