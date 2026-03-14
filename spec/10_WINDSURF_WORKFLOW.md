# 10 — Windsurf Agent Workflow: Budowa RAO App od zera do produkcji

> **KONTEKST DLA AGENTA:** Jesteś najlepszym full-stack developerem Python (FastAPI) + Vue.js 3
> z głębokim doświadczeniem w C#, SQL i nowoczesnym programowaniu.
> Masz perfekcyjne wyczucie Clean Architecture, SOLID, i pięknego UI.
>
> **CEL:** Zbudować aplikację RAO (wynajem maszyn budowlanych) od zera, identyczną 1:1
> z istniejącą aplikacją WinForms. Spec w plikach `docs/spec/01-09`.
>
> **TRYB PRACY:** Agresywna, self-healing, iteracyjna automatyzacja.
> NIE PYTAJ — RÓB. Jak coś nie działa — napraw i jedź dalej.
> Zakończ dopiero gdy WSZYSTKO działa, jest przetestowane i wygląda tip-top.

---

## ⚠️ WERYFIKACJA: Sprawdzaj swoją pracę ze starą aplikacją

**NIE WAHASZ SIĘ weryfikować nowego kodu ze starą aplikacją:**

### Źródła do weryfikacji
- **Stara aplikacja:** `c:\projects\repos\AppRao\rao\` (C# WinForms)
- **Stara baza:** DSN `BazaDanychRao` (konfiguracja w `App.config`)

### Kiedy WERYFIKUJ:
1. ✅ Nowy endpoint działa → sprawdź czy wynik zgadza się ze starą aplikacją
2. ✅ Nowy formularz → porównaj pola ze starym FormK.cs / FormU4.cs
3. ✅ Nowy algorytm → sprawdź czy wynik identyczny jak w C#
4. ✅ Nowy widok SQL → porównaj ze starymi VIEW w bazie

### Jak weryfikować:
```bash
# Odpytaj starą bazę
mariadb -u root -p -D rao -e "SELECT * FROM kontrahent2 LIMIT 5;"

# Sprawdź stare VIEW
mariadb -u root -p -D rao -e "SHOW FULL TABLES WHERE Table_type = 'VIEW';"

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
# Mailpit: fake SMTP z web UI — http://localhost:8025 (podgląd emaili)
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
Po każdym etapie — aktualizuj status. Format:

```markdown
# RAO Build Progress

## Phase 1: Infrastructure [ ] → [x] po zakończeniu
## Phase 2: Backend API [ ]
## Phase 3: Frontend [ ]
## Phase 4: Integration [ ]
## Phase 5: Testing [ ]
## Phase 6: Polish & Verification [ ]
```

---

## PHASE 1: Infrastructure (baza + środowisko)

### 1.1 Utwórz bazę danych MariaDB

```bash
# Zaloguj się do MariaDB jako root i utwórz bazę + użytkownika
mariadb -u root -p$RAO_DB_ROOT_PASSWORD -e "
CREATE DATABASE IF NOT EXISTS rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;
CREATE USER IF NOT EXISTS 'rao_user'@'localhost' IDENTIFIED BY 'RaoPass2026!';
GRANT ALL PRIVILEGES ON rao_new.* TO 'rao_user'@'localhost';
FLUSH PRIVILEGES;
"
```

### 1.2 Wykonaj DDL z `docs/spec/01_DATABASE_DDL.md`

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
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux:
# source .venv/bin/activate

pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncmy \
    pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] \
    bcrypt python-multipart httpx lxml jinja2 weasyprint alembic
pip freeze > requirements.txt
```

### 1.4 Ustaw frontend Vue.js

```bash
cd ..
npx -y create-vite@latest frontend -- --template vue
cd frontend
npm install
npm install vue-router@4 pinia axios
npm install -D @vitejs/plugin-vue
```

### 1.5 Zainstaluj Mailpit (fake SMTP dev server)

Mailpit przechwytuje WSZYSTKIE emaile i wyświetla je w web UI.
Żaden email nie wychodzi na zewnątrz — idealne do developmentu.

```bash
# Windows — pobierz binary:
curl -Lo mailpit.exe https://github.com/axllent/mailpit/releases/latest/download/mailpit-windows-amd64.exe

# LUB przez Go:
go install github.com/axllent/mailpit@latest

# LUB Docker:
docker run -d --name mailpit -p 8025:8025 -p 1025:1025 axllent/mailpit
```

**Uruchom:**
```bash
# Terminal 0 — Mailpit
mailpit --smtp 0.0.0.0:1025 --listen 0.0.0.0:8025
# Web UI: http://localhost:8025  (przeglądarka — podgląd emaili)
# SMTP:   localhost:1025          (backend wysyła tutaj)
```

**Weryfikacja:**
1. Otwórz http://localhost:8025 → powinien być pusty inbox
2. Po wysłaniu email z aplikacji (np. forgot-password) → email pojawi się w Mailpit
3. Kliknij email → widzisz treść HTML z linkiem do resetu hasła

### 1.6 Sprawdź że wszystko startuje

```bash
# Terminal 1 — backend
cd backend
uvicorn main:app --reload --port 8000
# Oczekiwane: Uvicorn running on http://127.0.0.1:8000

# Terminal 2 — frontend
cd frontend
npm run dev
# Oczekiwane: VITE ready on http://localhost:5173
```

**Self-healing:** Jeśli nie startuje → czytaj error → napraw → restart.

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

1. **Przeczytaj specyfikację** z `docs/spec/02_BACKEND_API.md` — precyzyjne typy, walidacje, algorytmy
2. **Utwórz model SQLAlchemy** — dokładnie jak DDL w `01_DATABASE_DDL.md`
3. **Utwórz schematy Pydantic** — dokładnie jak w specyfikacji, z `Field(...)` constraints
4. **Utwórz service** — logika biznesowa z `04_BUSINESS_LOGIC.md`
5. **Utwórz router** — endpointy z prawidłowymi dependency injections
6. **Zarejestruj router** w `main.py`
7. **TESTUJ NATYCHMIAST:**
   ```bash
   # Sprawdź czy app startuje
   curl http://localhost:8000/docs
   # Przetestuj endpoint
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"login":"admin","password":"admin"}'
   ```

### Kluczowe algorytmy do implementacji (z `04_BUSINESS_LOGIC.md`):

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
- [ ] Settings CRUD działa
- [ ] Numeracja umów generuje prawidłowe numery

---

## PHASE 3: Frontend Vue.js

### Kolejność implementacji

```
3.1  Design System (CSS variables, global styles)    → 09_DESIGN_REFERENCE.md
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
3.12 SettingsView (konfiguracja firmy)
3.13 ResetPasswordView + ChangePasswordView
3.14 Reports (PDF download)
```

### Dla KAŻDEGO komponentu:

1. **Przeczytaj wireframe** z `docs/spec/03_FRONTEND_SCREENS.md`
2. **Przeczytaj design** z `docs/spec/09_DESIGN_REFERENCE.md`
3. **Zaimplementuj komponent** — Composition API, `<script setup>`
4. **CSS** — użyj TYLKO zmiennych z design systemu Toolsmart (navy #1D2B53, Montserrat)
5. **Podłącz do API** — Axios z JWT interceptor
6. **SPRAWDŹ W PRZEGLĄDARCE:**
   - Otwórz przegledarkę Playwright MCP → `http://localhost:5173`
   - Zrzut ekranu → porównaj z wireframe
   - Jeśli nie wygląda → napraw CSS → ponownie sprawdź

### Design System (MUSI być zaimplementowany PIERWSZY):

```css
/* Klucz z 09_DESIGN_REFERENCE.md: */
--color-primary: #1D2B53;    /* Navy — sidebar, nagłówki, buttons, table headers */
--color-bg-white: #FFFFFF;    /* Tło */
--color-bg-light: #F8F9FA;   /* Alternate sections */
--font-family: 'Montserrat', sans-serif;
--border-radius: 12px;        /* Rounded cards */
--shadow-card: 0 1px 3px rgba(0,0,0,0.08);
```

### Nawigacja (MUSI być 1:1 z WinForms):

Przeczytaj `06_NAVIGATION_FLOW.md` — każdy route, każdy transition, każdy context menu.

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
     - Czy sidebar wygląda jak w 09_DESIGN_REFERENCE.md?
  5. Jeśli NIE → napraw → GOTO 1
  6. Sprawdź interakcje:
     - Kliknij przycisk → oczekiwany efekt?
     - Wpisz dane → formularz waliduje?
     - Double-click na wiersz → otwiera formularz?
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
- [ ] Settings: firma + opłaty + handlowcy
- [ ] Password reset flow (forgot → email → reset)

---

## PHASE 4: Integration

### 4.1 GUS API

```
1. Przeczytaj 07_INTEGRATIONS.md sekcja GUS
2. Zaimplementuj GusClient
3. Podłącz do ContractorFormView przycisk [GUS]
4. Test: wpisz NIP prawdziwej firmy → czy auto-fill działa?
5. Self-heal do skutku
```

### 4.2 Nominatim Geocoding

```
1. Przeczytaj 07_INTEGRATIONS.md sekcja Nominatim
2. Zaimplementuj NominatimClient
3. Podłącz do ContractFormView przycisk [>>]
4. Test: wpisz współrzędne → czy adres się wypełnia?
5. Self-heal do skutku
```

### 4.3 Raporty PDF

```
1. Przeczytaj 07_INTEGRATIONS.md sekcja Raporty
2. Zaimplementuj ReportService z WeasyPrint
3. Utwórz szablony HTML/Jinja2
4. Test: context menu → Wydruk → Umowa → pobiera się PDF?
5. Otwórz PDF → czy wygląda jak formatka umowy?
6. Self-heal do skutku
```

### 4.4 Migracja danych

```
1. Przeczytaj 08_MIGRATION_PLAN.md
2. Zaimplementuj skrypt migracyjny Python (alembic lub standalone)
3. Test: uruchom na starej bazie → dane przeniesione?
4. Weryfikacja: old_count == new_count per tabela
5. Post-migracja: hashuj hasła bcrypt
6. Self-heal do skutku
```

### ✅ Checkpoint Phase 4

- [ ] GUS auto-fill działa
- [ ] Nominatim reverse geocoding działa
- [ ] PDF report generuje się poprawnie
- [ ] Migracja danych: stare → nowe → count match

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
  1. Kliknij "Kontrahenci" w sidebar
  2. ASSERT: URL = /dashboard/contractors
  3. ASSERT: DataGrid z kontrahentami
  4. Kliknij "Artykuły"
  5. ASSERT: URL = /dashboard/articles
  6. ASSERT: DataGrid z artykułami
  7. Kliknij "Umowy"
  8. ASSERT: URL = /dashboard/contracts

TEST-03: CRUD Kontrahent
  1. Na dashboard/contractors kliknij [+]
  2. ASSERT: URL = /contractors/new
  3. Wypełnij: Nazwa="Test Firma", NIP="1234567890", miasto="Warszawa"
  4. Kliknij Zatwierdź
  5. ASSERT: powrót do dashboard, nowy kontrahent na liście
  6. Double-click na "Test Firma"
  7. ASSERT: formularz z danymi
  8. Zmień nazwę na "Test Firma Zmieniona"
  9. Kliknij Zatwierdź
  10. ASSERT: nazwa zmieniona na liście

TEST-04: CRUD Umowa
  1. Na dashboard/contracts kliknij [+]
  2. ASSERT: URL = /contracts/new
  3. Kliknij [Kontrahent] → dialog picker → wybierz "Test Firma Zmieniona"
  4. ASSERT: kontrahent wypełniony
  5. Ustaw daty od/do
  6. Kliknij [+] w pozycjach → Article picker
  7. Wybierz artykuł → ASSERT: pozycja dodana do grida
  8. Otwórz warunki → dodaj warunek z opłatą
  9. Kliknij Zapisz
  10. ASSERT: powrót do dashboard, umowa na liście

TEST-05: Search / Filter
  1. Na dashboard/contracts wpisz w search "S001"
  2. ASSERT: lista filtrowana do umów zawierających "S001"
  3. Wyczyść search
  4. ASSERT: pełna lista

TEST-06: Context Menu
  1. Right-click na umowę
  2. ASSERT: menu kontekstowe z opcjami (Edytuj/Usuń/Wydruk)
  3. Kliknij "Edytuj"
  4. ASSERT: otwarty formularz umowy

TEST-07: Settings
  1. Kliknij "Ustawienia" w sidebar
  2. ASSERT: formularz z danymi firmy
  3. Zmień nazwę firmy
  4. Kliknij Zapisz
  5. ASSERT: zapis pomyślny (toast/notification)

TEST-08: Password Change
  1. Z profilu użytkownika → Zmień hasło
  2. Wpisz stare i nowe hasło
  3. ASSERT: hasło zmienione
  4. Wyloguj → zaloguj nowym hasłem
  5. ASSERT: login pomyślny

TEST-09: Responsive & Visual
  1. Sprawdź czy sidebar ma bg #1D2B53
  2. Sprawdź czy font to Montserrat
  3. Sprawdź czy karty mają border-radius 12px
  4. Sprawdź czy DataGrid header ma bg #1D2B53

TEST-10: Delete with Cascade
  1. Utwórz umowę z pozycją i warunkiem
  2. Z dashboard usuń umowę
  3. Confirm dialog → Tak
  4. ASSERT: umowa usunięta, pozycje i warunki też

TEST-11: Password Reset (Mailpit)
  1. Otwórz ekran logowania
  2. Kliknij "Zapomniałem hasła"
  3. Wpisz email admina
  4. Przejdź do http://localhost:8025 (Mailpit)
  5. ASSERT: nowy email na liście
  6. Otwórz email → wydobądź link resetujący
  7. Otwórz link resetujący (powinien kierować na frontend)
  8. Wpisz nowe hasło i zatwierdź
  9. ASSERT: hasło zmienione pomyślnie
```

### Self-healing pattern testów:

```
FOR each TEST in [TEST-01..TEST-10]:
  LOOP max 5 attempts:
    1. Uruchom test via Playwright MCP
    2. Jeśli PASS → next TEST
    3. Jeśli FAIL:
       a. Przeczytaj error/screenshot
       b. Zidentyfikuj przyczynę (backend bug? frontend bug? CSS?)
       c. Napraw kod
       d. Restart dev servers jeśli trzeba
       e. GOTO 1
    4. Jeśli 5 attempts failed → zaloguj w BUILD_PROGRESS.md i przejdź dalej
```

### ✅ Checkpoint Phase 5

- [ ] TEST-01 do TEST-10: PASS
- [ ] Zero konsolowych errorów JavaScript
- [ ] Zero niezłapanych wyjątków w backend logach
- [ ] Wszystkie API responses zwracają poprawne dane

---

## PHASE 6: Polish & Final Verification

### 6.1 Wizualne porównanie z Toolsmart

```
1. Otwórz Playwright MCP → http://localhost:5173
2. Screeny każdego ekranu:
   - Login
   - Dashboard/Umowy
   - Dashboard/Kontrahenci
   - Dashboard/Artykuły
   - Formularz kontrahenta
   - Formularz umowy
   - Warunki rozliczenia
   - Ustawienia
3. Porównaj z wireframe'ami z 03_FRONTEND_SCREENS.md
4. Porównaj z designem Toolsmart z 09_DESIGN_REFERENCE.md
5. Napraw wszelkie różnice (kolory, spacing, font, shadows)
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
3. Upewnij się że `npm run build` produkuje producton bundle bez errorsów
4. Upewnij się że backend startuje z produkcyjnym gunicorn
5. Zamknij BUILD_PROGRESS.md → wszystkie fazy [x]
```

---

## Reguły dla agenta — NIENARUSZALNE

1. **NIE PYTAJ UŻYTKOWNIKA O NICZYM** — sam czytaj spec, sam decyduj, sam naprawiaj
2. **JEŚLI COŚ NIE DZIAŁA → NAPRAW I JEDŹ DALEJ** — zero manual fixów
3. **ZAWSZE TESTUJ PO KAŻDEJ ZMIANIE** — nie pisz 500 linii i potem "oby zadziałało"
4. **PROWADŹ BUILD_PROGRESS.md** — żeby widać co zrobione, co w toku
5. **CZYTAJ SPECYFIKACJĘ DOKŁADNIE** — odpowiedzi na 99% pytań są w plikach `docs/spec/`
6. **DESIGN TOOLSMART** — navy #1D2B53, Montserrat, rounded cards, shadows
7. **1:1 FEATURE PARITY** — każdy przycisk, każdy dialog, każdy flow z WinForms
8. **ORM ONLY** — zero procedur składowanych, cała logika w Pythonie
9. **ITERUJ DO SKUTKU** — kończy się dopiero gdy WSZYSTKO działa
10. **JAKOŚĆ KODU** — Clean Architecture, type hints, sensowne nazwy, zero magic strings

## Mapa plików specyfikacji — co gdzie szukać

```
docs/spec/
├── 01_DATABASE_DDL.md         ← DDL tabel, FK, indeksy, mapowanie
├── 02_BACKEND_API.md          ← WSZYSTKIE endpointy + Pydantic modele
├── 03_FRONTEND_SCREENS.md     ← Wireframe'y, komponenty Vue, routing
├── 04_BUSINESS_LOGIC.md       ← Algorytmy Python (numeracja, kalkulacja, GUS)
├── 05_CROSS_CHECK.md          ← Macierz: stary system ↔ nowy system
├── 06_NAVIGATION_FLOW.md      ← Flow diagram, routing rules
├── 07_INTEGRATIONS.md         ← GUS SOAP, Nominatim, PDF reporty
├── 08_MIGRATION_PLAN.md       ← Skrypty migracji starej bazy
├── 09_DESIGN_REFERENCE.md     ← Paleta Toolsmart, CSS, komponenty UI
└── 10_WINDSURF_WORKFLOW.md    ← TEN PLIK
```

**START → Przeczytaj `00_INDEX.md` → następnie `01` po kolei → buduj.**

---

## Self-Review Workflow — AGRESYWNA AUTOMATYZACJA

> **ZASADA:** Po każdym logicalznym kroku (max 50 linii kodu):
> 1. Zmień kontekst developera
> 2. Zrób self-review
> 3. Jeśli nie OK → napraw automatycznie
> 4. Jeśli OK → commituj natychmiast
> 5. Uruchom testy → jak nie OK → napraw → retry aż zadziała
>
> **NIE PYTAJ — RÓB. Iteruj do skutku.**

### 🔄 Rotacja kontekstu (wymuszona przed każdym commitem)

```
KONIECZNIE zmień "osobę" przed commitem (symulacja review):
┌─────────────────────────────────────────────────────────────┐
│ dev-db        → DDL, migracje, indeksy                    │
│ dev-backend-1 → Auth, users, security                     │
│ dev-backend-2 → Contractors, CRUD                         │
│ dev-backend-3 → Articles, CRUD                            │
│ dev-backend-4 → Contracts, positions, conditions          │
│ dev-frontend-1 → Router, stores, layout                   │
│ dev-frontend-2 → Komponenty, DataGrid, forms              │
│ dev-frontend-3 → Views, integracja z API                 │
│ dev-infra     → Docker, config, .env                      │
│ dev-review    → Final review, testy E2E                   │
└─────────────────────────────────────────────────────────────┘
```

### 🔍 Self-review PRZED commitem (obowiązkowe)

```bash
# KROK 1: Sprawdź co zmienione
git diff --cached --stat

# KROK 2: Analizuj jakość
echo "=== SELF-REVIEW CHECKLIST ==="
echo "[1] Czy kod zgodny ze specyfikacją (01-09)?"
echo "[2] Czy nazwy zmiennych sensowne (polski/angielski spójnie)?"
echo "[3] Czy są docstringi/komentarze gdzie potrzeba?"
echo "[4] Czy testy jednostkowe przechodzą?"
echo "[5] Czy NIE MA console.log / print / debug?"
echo "[6] Czy formatowanie spójne (ESLint/Black)?"
echo "[7] Czy commit message zgodny z Conventional Commits?"
echo "[8] Czy zmieniłeś kontekst developera?"

# KROK 3: Jeśli NIE OK → napraw natychmiast
# KROK 4: Jeśli OK → commit
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
# Po KAŻDYM commicie URUCHOM:
npm run lint          # Frontend lint
npm run test          # Frontend unit tests (jeśli są)

# Backend:
cd backend
python -m pytest     # Backend tests (jeśli są)
uvicorn main:app --port 8001 &
sleep 3
curl http://localhost:8001/docs | grep -q "swagger" && echo "Backend OK"
pkill -f "uvicorn main:app"

# Playwright E2E (kluczowe scenariusze):
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
  5. JEŚLI TESTY FAIL:
     a. Przeczytaj error log
     b. Zidentyfikuj przyczynę
     c. Napraw kod (krok 1)
     d. GOTO 2
  6. JEŚLI TESTY PASS:
     a. Zmień kontekst na następnego developera
     b. Następny krok
```

### 📊 Przykładowa sekwencja commitów (agresywna)

```bash
# === Zadanie: implementuj logowanie ===

# dev-db: najpierw baza
chore(db): utworz tabele users zgodnie z 01_DATABASE_DDL
- dodano tabele users z polami login, email, password (bcrypt), role
- dodano indeksy na login i email
- dodano FK na branch_id

# dev-backend-1: model + auth
feat(auth): dodaj model Uzytkownik i serwis autoryzacji
- model SQLAlchemy zgodny z DDL
- hashowanie hasel bcrypt
- walidacja Pydantic

feat(auth): implementuj POST /auth/login
- weryfikacja credentials
- generowanie JWT tokena
- zwracanie user info

# dev-frontend-1: routing + store
feat(auth): dodaj router i auth store
- routes /login, /dashboard z guard
- Pinia store z token i user state
- JWT interceptor w axios

# dev-frontend-2: komponent logowania
feat(login): dodaj komponent LoginView
- formularz z polami login/haslo
- walidacja frontendowa
- obsluga blędow

# dev-frontend-3: style
style(login): dostosuj do design systemu Toolsmart
- kolory navy #1D2B53
- font Montserrat
- border-radius 12px

# dev-infra: konfiguracja
chore(env): dodaj .env z konfiguracja
- DATABASE_URL, SECRET_KEY, SMTP
- CORS_ORIGINS

# dev-review: testy E2E
test(e2e): dodaj testy logowania Playwright
- TEST-01: login poprawny
- TEST-02: login niepoprawny
- TEST-03: redirect po zalogowaniu
```

### ✅ Checklist PRZED commitem (NIE commituj bez tego)

- [ ] **Kod działa** — testy przechodzą (lub wiem dlaczego nie)
- [ ] **Brak debug** — zero console.log, print, TODO bez opisu
- [ ] **Nazwy OK** — zmienne po polsku lub angielsku (spójnie)
- [ ] **Dokumentacja** — docstringi w Python, comments w Vue gdzie potrzeba
- [ ] **Formatowanie** — ESLint/Black przeszły (lub wiem że nie ma)
- [ ] **Commit message** — zgodny z Conventional Commits
- [ ] **Kontekst zmieniony** — nowy "developer" przed commitem
- [ ] **Max 50 linii** — jeśli więcej, podziel na mniejsze commity

### 🎯 Reguły agresywnej automatyzacji

1. **Małe commity** — max 50 linii zmian, jeden logicalzny feature/fix
2. **Testuj NATYCHMIAST** — nie pisz 500 linii i "oby zadziałało"
3. **Iteruj do skutku** — max 10 retry per krok, potem loguj problem
4. **NIE POMIJAJ BŁĘDÓW** — jak coś nie działa, napraw aż zadziała
5. **Checkpointy** — po każdej fazie (01-06) weryfikuj całość
6. **Progress file** — prowadź BUILD_PROGRESS.md

### 📁 BUILD_PROGRESS.md (OBOWIĄZKOWY)

```markdown
# RAO Build Progress

## Phase 1: Infrastructure [ ]
- [ ] MariaDB + 14 tabel
- [ ] Backend startuje na :8000
- [ ] Frontend startuje na :5173

## Phase 2: Backend API [ ]
- [ ] Auth (login, register, reset-password)
- [ ] Contractors CRUD
- [ ] Articles CRUD
- [ ] Contracts + positions + conditions CRUD

## Phase 3: Frontend [ ]
- [ ] Login screen
- [ ] Dashboard (Umowy/Kontrahenci/Artykuły)
- [ ] Formularze (Contractor, Contract, Article)

## Phase 4: Integration [ ]
- [ ] GUS API
- [ ] Nominatim
- [ ] PDF Reports

## Phase 5: Testing [ ]
- [ ] TEST-01..TEST-10 E2E

## Phase 6: Polish [ ]
- [ ] Wizualne porównanie z Toolsmart
- [ ] Performance check
- [ ] README.md
```

---

**START → Przeczytaj `00_INDEX.md` → następnie `01` po kolei → buduj iteracyjnie.**
