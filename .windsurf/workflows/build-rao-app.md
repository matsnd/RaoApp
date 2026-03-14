---
description: Budowa aplikacji RAO od zera do produkcji
---

> **KONTEKST DLA AGENTA:** Jesteś najlepszym full-stack developerem Python (FastAPI) + Vue.js 3
> z głębokim doświadczeniem w C#, SQL i nowoczesnym programowaniu.
> Masz perfekcyjne wyczucie Clean Architecture, SOLID, i pięknego UI.
>
> **CEL:** Zbudować aplikację RAO (wynajem maszyn budowlanych) od zera, identyczną 1:1
> z istniejącą aplikacją WinForms. Spec w plikach `spec/01-12`.
>
> **TRYB PRACY:** Agresywna, self-healing, iteracyjna automatyzacja.
> NIE PYTAJ — RÓB. Jak coś nie działa — napraw i jedź dalej.
> Zakończ dopiero gdy WSZYSTKO działa, jest przetestowane i wygląda tip-top.

---

## ⚠️ WERYFIKACJA: Sprawdzaj swoją pracę ze starą aplikacją

**NIE WAHASZ SIĘ weryfikować nowego kodu ze starą aplikacją:**

### Źródła do weryfikacji
- **Stara aplikacja:** `c:\projects\repos\AppRao\rao\` (C# WinForms)
- **Stara baza:** konfiguracja w `spec/DB_CONFIG.md` (credentials do starej bazy)

### Kiedy WERYFIKUJ:
1. ✅ Nowy endpoint działa → sprawdź czy wynik zgadza się ze starą aplikacją
2. ✅ Nowy formularz → porównaj pola ze starym FormK.cs / FormU4.cs
3. ✅ Nowy algorytm → sprawdź czy wynik identyczny jak w C#
4. ✅ Nowy widok SQL → porównaj ze starymi VIEW w bazie

### Jak weryfikować:
```bash
# Odpytaj starą bazę (credentials w spec/DB_CONFIG.md)
mariadb -h localhost -u <USER> -p<PASSWORD> -D <DB_NAME> -e "SELECT * FROM kontrahent2 LIMIT 5;"

# Sprawdź stare VIEW
mariadb -h localhost -u <USER> -p<PASSWORD> -D <DB_NAME> -e "SHOW FULL TABLES WHERE Table_type = 'VIEW';"

# Porównaj z nową bazą
mariadb -u rao_user -pRaoPass2026! rao_new -e "DESCRIBE users;"
```

---

## Konfiguracja środowiska — Plik `.env`

Przed startem utwórz plik `.env` w katalogu głównym projektu:

```env
# === DATABASE ===
RAO_DATABASE_URL=mariadb+asyncmy://rao_user:RaoPass2026!@localhost:3306/rao_new
RAO_DB_ROOT_PASSWORD=rootpass
RAO_DB_USER=rao_user
RAO_DB_PASSWORD=RaoPass2026!
RAO_DB_NAME=rao_new
RAO_DB_HOST=localhost
RAO_DB_PORT=3306

# === AUTH ===
RAO_SECRET_KEY=super-secret-jwt-key-change-in-production-min-32-chars
RAO_ACCESS_TOKEN_EXPIRE_MINUTES=480

# === SMTP (DEV → Mailpit, PROD → prawdziwy SMTP) ===
RAO_SMTP_HOST=localhost
RAO_SMTP_PORT=1025
RAO_SMTP_USER=
RAO_SMTP_PASSWORD=
RAO_SMTP_FROM=noreply@rao-app.pl
RAO_SMTP_TLS=false
RAO_FRONTEND_URL=http://localhost:5173

# === INTEGRATIONS ===
RAO_GUS_API_KEY=
RAO_NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org

# === CORS ===
RAO_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

---

## Master Plan — Fazy budowy

Agent musi prowadzić plik **`BUILD_PROGRESS.md`** w katalogu głównym projektu.
**Aktualizuj po KAŻDYM kroku** — nie po fazie, po każdym pojedynczym kroku.

### Zasady aktualizacji BUILD_PROGRESS.md

```
KIEDY aktualizować:
  - Przed startem kroku → dodaj wiersz ze statusem ⏳
  - Po zakończeniu kroku → zmień na ✅ lub ❌, uzupełnij resztę pól
  - Po każdym self-heal retry → zaktualizuj kolumnę "Retries" i "Problemy"
  - Po każdym commicie → wklej hash commita

NIE POMIJAJ żadnego kroku — nawet jeśli trwał 30 sekund.
```

### Szablon BUILD_PROGRESS.md

```markdown
# RAO App — Build Progress

> Ostatnia aktualizacja: {DATA} {GODZINA} | Kontekst: {AGENT}

---

## Statusy faz

| Faza | Status | Ukończono | Czas łączny |
|------|--------|-----------|-------------|
| Phase 1: Infrastructure | ⏳ | 0/5 kroków | - |
| Phase 2: Backend API    | ⬜ | 0/10 kroków | - |
| Phase 3: Frontend       | ⬜ | 0/14 kroków | - |
| Phase 4: Integration    | ⬜ | 0/4 kroków | - |
| Phase 5: Testing        | ⬜ | 0/13 testów | - |
| Phase 6: Polish         | ⬜ | 0/4 kroków | - |

Legenda: ⬜ nie zaczęte · ⏳ w toku · ✅ ukończone · ❌ błąd · 🔄 retry

---

## Dziennik kroków

| # | Data & Godzina | Faza.Krok | Kontekst agenta | Status | Co zrobiono (1 zdanie) | Pliki zmienione | Problemy napotkane | Retries | Commit |
|---|---------------|-----------|-----------------|--------|------------------------|-----------------|-------------------|---------|--------|
| 1 | 2026-03-14 22:15 | 1.1 | dev-db | ✅ | Utworzono bazę rao_new i użytkownika rao_user | - | Brak | 0 | `a1b2c3d` |
| 2 | 2026-03-14 22:18 | 1.2 | dev-db | ✅ | Wykonano DDL — 16 tabel | `01_DATABASE_DDL.md` (ref) | FK błąd na costs → poprawiono kolejność | 1 | `e4f5g6h` |
| 3 | 2026-03-14 22:35 | 1.3 | dev-infra | ⏳ | Konfiguracja venv i pip install | `requirements.txt` | - | 0 | - |

---

## Otwarte problemy (self-heal queue)

| ID | Faza.Krok | Opis problemu | Próby | Ostatnia próba | Rozwiązanie |
|----|-----------|---------------|-------|----------------|-------------|
| P1 | 2.3 | 422 Unprocessable Entity na POST /contractors | 2 | 2026-03-14 23:10 | ⏳ W toku |

---

## Metryki sesji

| Metryka | Wartość |
|---------|---------|
| Sesja rozpoczęta | {DATA} {GODZINA} |
| Łączne kroki ukończone | 0 |
| Łączne retries (self-heal) | 0 |
| Aktualny kontekst agenta | {AGENT} |
| Ostatni commit | - |
| Kolejny krok | 1.1 — Utwórz bazę danych |

---

## Historia kontekstów agenta

| Data & Godzina | Poprzedni kontekst | Nowy kontekst | Powód rotacji |
|---------------|-------------------|---------------|---------------|
| 2026-03-14 22:15 | - | dev-db | Start sesji, Phase 1 |
| 2026-03-14 22:35 | dev-db | dev-infra | Przejście do setupu środowiska |
```

### Reguły wypełniania tabeli

```
Kolumna "Kontekst agenta":
  Wybierz z listy rotacji (sekcja Self-Review Workflow):
  dev-db / dev-backend-1..4 / dev-frontend-1..3 / dev-infra / dev-review

Kolumna "Status":
  ⏳ = zaczęty, nie ukończony
  ✅ = ukończony, testy zielone
  ❌ = zakończony błędem (opisz w "Problemy")
  🔄 = w trakcie self-heal retry

Kolumna "Pliki zmienione":
  Lista plików oddzielona przecinkami, np.: "backend/auth/router.py, main.py"
  Jeśli >5 plików → wpisz "16 plików (feat: auth module)"

Kolumna "Retries":
  Liczba iteracji self-heal zanim krok przeszedł.
  0 = za pierwszym razem, 3 = trzecia próba zadziałała.

Kolumna "Commit":
  Skrócony hash (7 znaków) po `git log --oneline -1`
  Wpisz "-" jeśli krok nie generował commitu
```

---

## PHASE 1: Infrastructure (baza + środowisko)

### 1.1 Utwórz bazę danych MariaDB

```bash
mariadb -u root -p$RAO_DB_ROOT_PASSWORD -e "
CREATE DATABASE IF NOT EXISTS rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;
CREATE USER IF NOT EXISTS 'rao_user'@'localhost' IDENTIFIED BY 'RaoPass2026!';
GRANT ALL PRIVILEGES ON rao_new.* TO 'rao_user'@'localhost';
FLUSH PRIVILEGES;
"
```

### 1.2 Wykonaj DDL z `spec/01_DATABASE_DDL.md`

Przeczytaj plik `01_DATABASE_DDL.md` i wykonaj WSZYSTKIE `CREATE TABLE` query w odpowiedniej kolejności.
**NIE POMIJAJ żadnej tabeli.** Sprawdź po wykonaniu:

```bash
mariadb -u rao_user -pRaoPass2026! rao_new -e "SHOW TABLES;"
# Oczekiwane: 14+ tabel
```

**Self-healing:** Jeśli DDL się nie wykona → przeczytaj error → popraw query → spróbuj ponownie.

### 1.3 Ustaw backend Python

```bash
mkdir -p backend
python -m venv backend/.venv
# Windows:
backend\.venv\Scripts\activate
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncmy \
    pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] \
    bcrypt python-multipart httpx lxml jinja2 weasyprint alembic
pip freeze > backend/requirements.txt
```

### 1.4 Ustaw frontend Vue.js

```bash
npx -y create-vite@latest frontend -- --template vue
cd frontend
npm install
npm install vue-router@4 pinia axios
npm install -D @vitejs/plugin-vue
```

### 1.5 Zainstaluj Mailpit (fake SMTP dev server)

```bash
# Windows — pobierz binary:
curl -Lo mailpit.exe https://github.com/axllent/mailpit/releases/latest/download/mailpit-windows-amd64.exe

# LUB Docker:
docker run -d --name mailpit -p 8025:8025 -p 1025:1025 axllent/mailpit

# Uruchom:
mailpit --smtp 0.0.0.0:1025 --listen 0.0.0.0:8025
# Web UI: http://localhost:8025 | SMTP: localhost:1025
```

### 1.6 Sprawdź że wszystko startuje

```bash
# Terminal 1 — backend
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
npm run dev
# Oczekiwane: VITE ready on http://localhost:5173
```

### ✅ Checkpoint Phase 1

- [ ] MariaDB działa, `rao_new` istnieje z 14+ tabelami
- [ ] Backend startuje na :8000 bez errorów
- [ ] Frontend startuje na :5173 bez errorów
- [ ] `GET http://localhost:8000/docs` zwraca Swagger UI

---

## PHASE 2: Backend API

### Kolejność implementacji (dependencies-first)

```
2.1  config.py + database.py + main.py              (foundation)
2.2  auth/ (models → schemas → service → router)    (musisz być zalogowany)
2.3  contractors/ (models → schemas → service → router)
2.4  articles/ (models → schemas → service → router)
2.5  contracts/ (models → schemas → service → router)
2.6  positions/ (models → schemas → service → router)
2.7  conditions/ (models → schemas → service → router)
2.8  settings/ (models → schemas → service → router)
2.9  reports/ (service → router → templates)
2.10 integrations/ (gus.py, nominatim.py)
```

### Dla KAŻDEGO modułu:

1. **Przeczytaj specyfikację** z `spec/02_BACKEND_API.md`
2. **Utwórz model SQLAlchemy** — dokładnie jak DDL w `01_DATABASE_DDL.md`
3. **Utwórz schematy Pydantic** — z `Field(...)` constraints
4. **Utwórz service** — logika biznesowa z `04_BUSINESS_LOGIC.md`
5. **Utwórz router** — endpointy z prawidłowymi dependency injections
6. **Zarejestruj router** w `main.py`
7. **TESTUJ NATYCHMIAST** curlem / Swagger UI

### Przed implementacją — przeczytaj KONIECZNIE:

```
- spec/12_LOGIC_AUDIT.md — audyt spaghetti kodu C#, lista dziur w specyfikacji
  WAŻNE: LOG-05 (GUS + propagacja adresów do Pydantic) — DZIURA do uzupełnienia!
- spec/05_CROSS_CHECK.md — macierz: stary GUI ↔ SQL ↔ obiekty DB ↔ nowe endpointy
  Użyj do weryfikacji czy każda akcja GUI ma odpowiedni endpoint
```

### Kluczowe algorytmy (z `spec/04_BUSINESS_LOGIC.md`):

- **Numeracja umów:** `generate_contract_number()` → format `S001/2026`
- **Kalkulacja wartości:** Progowa, z warunkami per pozycja
- **Duplikacja artykułu:** Kopiuj bez nr rej. i nr ser.
- **Sprawdzenie dostępności:** Overlap dat
- **Kaskadowe usuwanie:** Warunki → pozycje → umowa
- **GUS SOAP:** Login → search → parse XML
- **Nominatim:** Reverse geocode
- **Walidacja NIP:** Checksum algorithm

### Self-healing pattern:

```
LOOP:
  1. Napisz kod
  2. Uruchom `uvicorn main:app --reload`
  3. Sprawdź logi
  4. Jeśli ERROR → przeczytaj traceback → napraw → GOTO 1
  5. Przetestuj endpoint curlem
  6. Jeśli response != expected → napraw → GOTO 1
  7. OK → następny moduł
```

### ✅ Checkpoint Phase 2

- [ ] Wszystkie 10 routerów zarejestrowanych w `main.py`
- [ ] Swagger UI (`/docs`) pokazuje WSZYSTKIE endpointy
- [ ] Login działa i zwraca JWT
- [ ] CRUD contractors działa
- [ ] CRUD articles działa
- [ ] CRUD contracts + positions + conditions działa
- [ ] Settings CRUD działa (firma, handlowcy, opłaty dodatkowe)
- [ ] GET/POST/PUT/DELETE `/settings/service-fee-templates` działa
- [ ] GET/POST/PUT/DELETE `/contracts/{id}/service-fees` działa
- [ ] Numeracja umów generuje prawidłowe numery
- [ ] LOG-05 z 12_LOGIC_AUDIT.md pokryte (GUS → Pydantic model kontrahenta)

---

## PHASE 3: Frontend Vue.js

### Kolejność implementacji

```
3.0  CSS Scraping z toolsmart.pl (OBOWIĄZKOWE przed 3.1)
     → Przeczytaj spec/09_DESIGN_REFERENCE.md sekcja "0. Scraping CSS"
     → Uruchom procedurę Playwright MCP (kroki 1-6 z sekcji 0)
     → Zaktualizuj wartości w 09_DESIGN_REFERENCE.md jeśli się różnią
3.1  Design System (CSS variables, global styles)    → spec/09_DESIGN_REFERENCE.md
3.2  Router + Auth Guard + Stores (Pinia)
3.3  Layout: AppSidebar + AppLayout
3.4  LoginView
3.5  DashboardView (Umowy tab + DataGrid + Toolbar)
3.6  DashboardView (Kontrahenci tab)
3.7  DashboardView (Artykuły tab)
3.8  ContractorFormView (pełny formularz + adresy)
3.9  ContractFormView (formularz umowy + kalendarz)
3.10 ArticlePicker dialog
3.11 ConditionFormView (warunki rozliczeniowe)
3.12 SettingsView (konfiguracja firmy + szablony usług)
3.13 ResetPasswordView + ChangePasswordView
3.14 Reports (PDF download)
```

### Dla KAŻDEGO komponentu:

1. **Przeczytaj wireframe** z `spec/03_FRONTEND_SCREENS.md`
2. **Przeczytaj design** z `spec/09_DESIGN_REFERENCE.md`
3. **Zaimplementuj komponent** — Composition API, `<script setup>`
4. **CSS** — użyj TYLKO zmiennych z design systemu Toolsmart (navy #1D2B53, Montserrat)
5. **Podłącz do API** — Axios z JWT interceptor
6. **SPRAWDŹ W PRZEGLĄDARCE** via Playwright MCP → zrzut ekranu → porównaj z wireframe

### Design System (MUSI być zaimplementowany PIERWSZY):

```css
/* Klucz z spec/09_DESIGN_REFERENCE.md: */
--color-primary: #1D2B53;    /* Navy — sidebar, nagłówki, buttons, table headers */
--color-bg-white: #FFFFFF;
--color-bg-light: #F8F9FA;
--font-family: 'Montserrat', sans-serif;
--border-radius: 12px;
--shadow-card: 0 1px 3px rgba(0,0,0,0.08);
```

### Nawigacja (MUSI być 1:1 z WinForms):

Przeczytaj `spec/06_NAVIGATION_FLOW.md` — każdy route, każdy transition, każdy context menu.

### Self-healing pattern:

```
LOOP:
  1. Napisz komponent
  2. Otwórz Playwright MCP → nawiguj do strony
  3. Zrzut ekranu
  4. Oceń wizualnie:
     - Czy layout odpowiada wireframe z 03_FRONTEND_SCREENS.md?
     - Czy kolory są Toolsmart navy (#1D2B53)?
     - Czy font to Montserrat?
     - Czy karty mają border-radius 12px i shadow?
  5. Jeśli NIE → napraw → GOTO 1
  6. Sprawdź interakcje (kliknięcia, walidacje, double-click)
  7. Jeśli NIE → napraw → GOTO 1
  8. OK → następny komponent
```

### ✅ Checkpoint Phase 3

- [ ] Login screen działa i wygląda jak Toolsmart
- [ ] Sidebar nawiguje między sekcjami (Umowy/Kontrahenci/Artykuły)
- [ ] Dashboard DataGrid wyświetla dane z API
- [ ] Search filtruje listę
- [ ] Double-click otwiera formularz edycji
- [ ] Toolbar [+][-] działa
- [ ] Context menu (right-click) działa
- [ ] Formularz kontrahenta: CRUD + adresy
- [ ] Formularz umowy: CRUD + pozycje + warunki + kalendarz
- [ ] Article picker: search + select + data dostawy
- [ ] Settings: firma + opłaty + handlowcy + szablony usług (lista, nie textarea!)
- [ ] Password reset flow (forgot → email → reset)

---

## PHASE 4: Integration

### 4.1 GUS API

```
1. Przeczytaj spec/07_INTEGRATIONS.md sekcja GUS
2. Zaimplementuj GusClient
3. Podłącz do ContractorFormView przycisk [GUS]
4. Test: wpisz NIP prawdziwej firmy → czy auto-fill działa?
5. Self-heal do skutku
```

### 4.2 Nominatim Geocoding

```
1. Przeczytaj spec/07_INTEGRATIONS.md sekcja Nominatim
2. Zaimplementuj NominatimClient
3. Podłącz do ContractFormView przycisk [>>]
4. Test: wpisz współrzędne → czy adres się wypełnia?
5. Self-heal do skutku
```

### 4.3 Raporty PDF

```
1. Przeczytaj spec/11_REPORTS_AND_STATS.md — CAŁY plik (6 wariantów, OWU, statystyki)
2. Przeczytaj spec/07_INTEGRATIONS.md sekcja Raporty
3. Zlokalizuj referencyjne PDF-y: spec/reference_reports/
   - Umowa Najmu, Umowa Usługi, Protokół Z-O (x2), Protokół Z-O bez kwot (x2)
   - ownA.pdf i ownU.pdf (OWU — wyekstrahuj tekst i wbuduj w szablony)
4. Zaimplementuj ReportService z WeasyPrint (6 szablonów Jinja2)
5. Zaimplementuj endpointy statystyk z 11_REPORTS_AND_STATS.md
6. Test każdego z 6 wariantów: context menu → Wydruk → pobiera się PDF?
7. Porównaj layout z reference_reports/*.pdf — musi być 1:1
8. Self-heal do skutku
```

### 4.4 Migracja danych

```
1. Przeczytaj spec/08_MIGRATION_PLAN.md — CAŁY plik, łącznie z sekcją weryfikacji [V1]-[V6]
2. Wykonaj SQL INSERT...SELECT dla wszystkich tabel (krok 1, 2, 3, 4, 5, 6...)
3. Uruchom: python migrator/migrate_service_fees.py
   - Parsuje firma.uslugi1/2 → service_fee_templates (po jednym wierszu per linia "-")
   - Parsuje umowa2.oplaty per umowa → contract_service_fees
4. Weryfikacja migracji usług dodatkowych (OBOWIĄZKOWA):
   a) [V1] SELECT COUNT(*) FROM service_fee_templates WHERE contract_type='S'
      → porównaj z: liczba linii "\n-" w toolsmart_roa_fake.firma.uslugi1
   b) [V2] SELECT COUNT(*) FROM service_fee_templates WHERE contract_type='U'
   c) [V3] SELECT name FROM service_fee_templates WHERE contract_type='S' ORDER BY sort_order
   d) [V4] SELECT COUNT(DISTINCT contract_id) FROM contract_service_fees
   e) [V5] min/max/avg pozycji per umowa (patrz query V5 w 08_MIGRATION_PLAN.md)
   f) [V6] 3 losowe umowy: porównaj stary tekst OPLATY z nowymi wierszami
5. Weryfikacja ogólna: old_count == new_count per każda tabela
6. Post-migracja: hashuj hasła bcrypt (stare mają prefix $PLAINTEXT$)
7. Self-heal do skutku — jeśli liczby się nie zgadzają popraw parse_fee_lines()
```

### ✅ Checkpoint Phase 4

- [ ] GUS auto-fill działa (z propagacją danych do Pydantic — LOG-05)
- [ ] Nominatim reverse geocoding działa
- [ ] Wszystkie 6 wariantów PDF generuje się poprawnie
- [ ] Layout PDF zgodny z spec/reference_reports/*.pdf
- [ ] OWU (ownA.pdf / ownU.pdf) wbudowane w szablony umów
- [ ] migrate_service_fees.py uruchomiony bez błędów
- [ ] [V1]-[V6] wszystkie weryfikacje przeszły (liczby się zgadzają)
- [ ] Migracja danych: stare → nowe → count match per tabela

---

## PHASE 5: Testing (Playwright MCP)

### Scenariusze testowe E2E — WSZYSTKIE muszą przejść

```
TEST-01: Login
  1. Otwórz http://localhost:5173
  2. Wpisz login: admin, hasło: admin
  3. Kliknij Zaloguj
  4. ASSERT: przekierowanie na /dashboard/contracts
  5. ASSERT: sidebar widoczny z sekcjami

TEST-02: Nawigacja sidebar
  1. Kliknij "Kontrahenci" → ASSERT: URL = /dashboard/contractors
  2. Kliknij "Artykuły"   → ASSERT: URL = /dashboard/articles
  3. Kliknij "Umowy"      → ASSERT: URL = /dashboard/contracts

TEST-03: CRUD Kontrahent
  1. Kliknij [+] → URL = /contractors/new
  2. Wypełnij: Nazwa="Test Firma", NIP="1234567890", miasto="Warszawa"
  3. Zatwierdź → ASSERT: powrót do dashboard, nowy kontrahent na liście
  4. Double-click → ASSERT: formularz z danymi
  5. Zmień nazwę → Zatwierdź → ASSERT: nazwa zmieniona

TEST-04: CRUD Umowa
  1. Kliknij [+] → URL = /contracts/new
  2. Wybierz kontrahenta → ustaw daty → dodaj pozycję → dodaj warunek
  3. Zapisz → ASSERT: umowa na liście z prawidłowym numerem

TEST-05: Search / Filter
  1. Wpisz "S001" → ASSERT: lista filtrowana
  2. Wyczyść → ASSERT: pełna lista

TEST-06: Context Menu
  1. Right-click na umowę → ASSERT: menu (Edytuj/Usuń/Wydruk)
  2. Kliknij "Edytuj" → ASSERT: formularz umowy

TEST-07: Settings
  1. Przejdź do Ustawienia → zmień nazwę firmy → Zapisz
  2. ASSERT: zapis pomyślny (toast/notification)

TEST-08: Password Change
  1. Zmień hasło → Wyloguj → zaloguj nowym hasłem → ASSERT: login pomyślny

TEST-09: Responsive & Visual
  1. Sidebar bg = #1D2B53 ✓
  2. Font = Montserrat ✓
  3. Karty border-radius = 12px ✓
  4. DataGrid header bg = #1D2B53 ✓

TEST-10: Delete with Cascade
  1. Utwórz umowę z pozycją i warunkiem → usuń → Potwierdź
  2. ASSERT: umowa + pozycje + warunki usunięte

TEST-11: Password Reset (Mailpit)
  1. Kliknij "Zapomniałem hasła" → wpisz email
  2. Przejdź do http://localhost:8025 → ASSERT: email na liście
  3. Otwórz link → wpisz nowe hasło → ASSERT: zmienione pomyślnie

TEST-12: Service Fee Templates
  1. Ustawienia → sekcja "Szablony usług" → ASSERT: lista pozycji (nie textarea)
  2. Dodaj: Nazwa="Transport", Kwota=400, Jednostka="zł"
  3. Utwórz nową umowę → ASSERT: pozycje auto-załadowane z szablonu
  4. Toggle wyłącz → ASSERT: pozycja wyszarzona ale zachowana

TEST-13: Raporty PDF — wszystkie 6 wariantów
  1. Right-click umowa najmu → Wydruk → Umowa Najmu → ASSERT: PDF pobrany
  2. → Protokół Z-O → ASSERT: PDF z tabelą maszyn
  3. → Protokół Z-O bez danych → ASSERT: brak kolumn kwot
  4. Analogicznie dla umowy usługowej (3 warianty)
  5. ASSERT: OWU jako ostatnie strony każdej umowy
```

### Self-healing pattern testów:

```
FOR each TEST in [TEST-01..TEST-13]:
  LOOP max 5 attempts:
    1. Uruchom test via Playwright MCP
    2. Jeśli PASS → next TEST
    3. Jeśli FAIL → przeczytaj error → zidentyfikuj przyczynę → napraw → GOTO 2
    4. Jeśli 5 attempts failed → zaloguj w BUILD_PROGRESS.md i przejdź dalej
```

### ✅ Checkpoint Phase 5

- [ ] TEST-01 do TEST-13: PASS
- [ ] Zero konsolowych errorów JavaScript
- [ ] Zero niezłapanych wyjątków w backend logach
- [ ] Wszystkie API responses zwracają poprawne dane

---

## PHASE 6: Polish & Final Verification

### 6.1 Wizualne porównanie z Toolsmart

```
1. Otwórz Playwright MCP → http://localhost:5173
2. Screeny każdego ekranu:
   - Login, Dashboard/Umowy, Dashboard/Kontrahenci, Dashboard/Artykuły
   - Formularz kontrahenta, Formularz umowy, Warunki rozliczenia
3. Porównaj z wireframe'ami z spec/03_FRONTEND_SCREENS.md
4. Porównaj z designem Toolsmart z spec/09_DESIGN_REFERENCE.md
5. Porównaj wygenerowane PDF z spec/reference_reports/*.pdf (1:1)
6. Napraw wszelkie różnice (kolory, spacing, font, shadows, PDF layout)
```

### 6.2 Performance Check

```
1. GET /contracts z 100+ rekordami → response < 500ms?
2. Frontend initial load < 3s?
3. Żaden memory leak w dev tools?
```

### 6.3 Security Basics

```
1. Hasła hashowane bcrypt (sprawdź w DB)
2. JWT wymagany na WSZYSTKICH chronionych endpointach
3. SQL injection niemożliwy (SQLAlchemy parameterized)
4. CORS skonfigurowany prawidłowo
5. .env NIE jest w git (.gitignore)
```

### 6.4 Finalizacja

```
1. Utwórz README.md z instrukcją instalacji
2. Utwórz docker-compose.yml (opcjonalnie)
3. `npm run build` → production bundle bez errorów
4. Backend startuje z produkcyjnym gunicorn
5. Zamknij BUILD_PROGRESS.md → wszystkie fazy [x]
```

---

## Reguły dla agenta — NIENARUSZALNE

1. **NIE PYTAJ UŻYTKOWNIKA O NICZYM** — sam czytaj spec, sam decyduj, sam naprawiaj
2. **JEŚLI COŚ NIE DZIAŁA → NAPRAW I JEDŹ DALEJ** — zero manual fixów
3. **ZAWSZE TESTUJ PO KAŻDEJ ZMIANIE** — nie pisz 500 linii i potem "oby zadziałało"
4. **PROWADŹ BUILD_PROGRESS.md** — po każdym kroku, z timestampem i kontekstem
5. **CZYTAJ SPECYFIKACJĘ DOKŁADNIE** — odpowiedzi na 99% pytań są w plikach `spec/`
6. **DESIGN TOOLSMART** — navy #1D2B53, Montserrat, rounded cards, shadows
7. **1:1 FEATURE PARITY** — każdy przycisk, każdy dialog, każdy flow z WinForms
8. **ORM ONLY** — zero procedur składowanych, cała logika w Pythonie
9. **ITERUJ DO SKUTKU** — kończy się dopiero gdy WSZYSTKO działa
10. **JAKOŚĆ KODU** — Clean Architecture, type hints, sensowne nazwy, zero magic strings

## Mapa plików specyfikacji — co gdzie szukać

```
spec/
├── 00_INDEX.md              ← Start tutaj — przegląd całości
├── 01_DATABASE_DDL.md       ← DDL tabel, FK, indeksy, mapowanie
├── 02_BACKEND_API.md        ← WSZYSTKIE endpointy + Pydantic modele
├── 03_FRONTEND_SCREENS.md   ← Wireframe'y, komponenty Vue, routing
├── 04_BUSINESS_LOGIC.md     ← Algorytmy Python (numeracja, kalkulacja, GUS)
├── 05_CROSS_CHECK.md        ← Macierz: stary GUI ↔ SQL ↔ DB ↔ nowe endpointy
├── 06_NAVIGATION_FLOW.md    ← Flow diagram, routing rules
├── 07_INTEGRATIONS.md       ← GUS SOAP, Nominatim, PDF reporty
├── 08_MIGRATION_PLAN.md     ← Skrypty migracji starej bazy + migrate_service_fees.py
├── 09_DESIGN_REFERENCE.md   ← Paleta Toolsmart, CSS, scraping procedure
├── 10_WINDSURF_WORKFLOW.md  ← Pełna wersja tego workflow (master copy)
├── 11_REPORTS_AND_STATS.md  ← 6 wariantów PDF, OWU, statystyki i KPI
└── 12_LOGIC_AUDIT.md        ← Audyt C# spaghetti: co pokryte, co dziura (czytaj PRZED Phase 2)
```

---

## Self-Review Workflow — AGRESYWNA AUTOMATYZACJA

> **ZASADA:** Po każdym logicznym kroku (max 50 linii kodu):
> 1. Zmień kontekst developera
> 2. Zrób self-review
> 3. Jeśli nie OK → napraw automatycznie
> 4. Jeśli OK → commituj natychmiast
> 5. Uruchom testy → jak nie OK → napraw → retry aż zadziała
>
> **NIE PYTAJ — RÓB. Iteruj do skutku.**

### 🔄 Rotacja kontekstu (wymuszona przed każdym commitem)

```
┌─────────────────────────────────────────────────────────────┐
│ dev-db        → DDL, migracje, indeksy                      │
│ dev-backend-1 → Auth, users, security                       │
│ dev-backend-2 → Contractors, CRUD                           │
│ dev-backend-3 → Articles, CRUD                              │
│ dev-backend-4 → Contracts, positions, conditions            │
│ dev-frontend-1 → Router, stores, layout                     │
│ dev-frontend-2 → Komponenty, DataGrid, forms                │
│ dev-frontend-3 → Views, integracja z API                    │
│ dev-infra     → Docker, config, .env                        │
│ dev-review    → Final review, testy E2E                     │
└─────────────────────────────────────────────────────────────┘
```

### 🔍 Self-review PRZED commitem (obowiązkowe)

```bash
git diff --cached --stat

echo "[1] Czy kod zgodny ze specyfikacją (01-12)?"
echo "[2] Czy nazwy zmiennych sensowne?"
echo "[3] Czy są docstringi/komentarze gdzie potrzeba?"
echo "[4] Czy testy jednostkowe przechodzą?"
echo "[5] Czy NIE MA console.log / print / debug?"
echo "[6] Czy formatowanie spójne (ESLint/Black)?"
echo "[7] Czy commit message zgodny z Conventional Commits?"
echo "[8] Czy zmieniłeś kontekst developera?"
```

### 📝 Format commit messages (OBOWIĄZKOWY)

```
<typ>(<zakres>): <opis>

Co zostało zrobione:
- <lista zmian w bullet points>

Dlaczego: <krótkie uzasadnienie biznesowe/techniczne>

Review: @<poprzedni_kontekst_developera>
```

**Typy:** `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`, `ci`, `revert`

### ⚡ Automatyczne testy PO każdym commicie

```bash
npm run lint && npm run test

cd backend
python -m pytest
uvicorn main:app --port 8001 &
sleep 3
curl http://localhost:8001/docs | grep -q "swagger" && echo "Backend OK"
pkill -f "uvicorn main:app --port 8001"

npx playwright test tests/login.spec.ts
npx playwright test tests/crud.spec.ts
```

### 🔄 Self-Healing Pattern (AGRESYWNY)

```
LOOP (max 10 iteracji):
  1. Wykonaj zmianę (max 50 linii)
  2. Self-review (checklist wyżej)
  3. Commit z opisem
  4. Uruchom testy
  5. JEŚLI TESTY FAIL → przeczytaj error → zidentyfikuj przyczynę → napraw → GOTO 2
  6. JEŚLI TESTY PASS → zmień kontekst → następny krok
```

### ✅ Checklist PRZED commitem

- [ ] **Kod działa** — testy przechodzą
- [ ] **Brak debug** — zero console.log, print, TODO bez opisu
- [ ] **Nazwy OK** — zmienne spójnie po polsku lub angielsku
- [ ] **Dokumentacja** — docstringi w Python, comments w Vue gdzie potrzeba
- [ ] **Formatowanie** — ESLint/Black
- [ ] **Commit message** — Conventional Commits
- [ ] **Kontekst zmieniony** — nowy "developer" przed commitem
- [ ] **Max 50 linii** — jeśli więcej, podziel

---

**START → Przeczytaj `spec/00_INDEX.md` → następnie `spec/12_LOGIC_AUDIT.md` → buduj iteracyjnie.**
