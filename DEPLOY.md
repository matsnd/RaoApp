# Instrukcja Wdrożenia RAO App — www.toolsmart.pl/rao

## Docelowe adresy
| Co | URL |
|----|-----|
| Frontend (aplikacja) | `https://www.toolsmart.pl/rao` |
| Backend API | `https://www.toolsmart.pl/rao/api` |
| Health check | `https://www.toolsmart.pl/rao/api/health` |

## Stos techniczny
| Warstwa | Technologia | Hosting |
|---------|------------|---------|
| Frontend | Vue 3 + Vite (statyczne pliki) | `public_html/rao/` |
| Backend | FastAPI + Python 3.11 + uvicorn | Python app (WSGI/ASGI) |
| Baza | MariaDB | PhpMyAdmin |

---

## KROK 0 — Sprawdź hosting ZANIM zaczniesz

Zaloguj się do panelu i zweryfikuj poniższe. Jeśli cokolwiek nie zgadza się → napisz do supportu **PRZED** wdrożeniem.

### 0a. Python ≥ 3.10

Panel → **Web Applications → Create Application → Python** → kliknij dropdown **Python version**.  
Domyślnie może pokazywać `2.7.18` — **MUSISZ** zmienić na `3.10`, `3.11` lub `3.12`.

> ⚠️ Jeśli w dropdownie **nie ma** Pythona 3.10+ → FastAPI nie zadziała. Skontaktuj się z supportem hostingu.

### 0b. SSH / Terminal

Sprawdź czy panel daje dostęp **SSH** lub **Terminal**. Będzie potrzebny do:
- `pip install` zależności Pythona
- sprawdzenia logów
- ewentualnego debugowania

> Bez SSH wdrożenie backendu będzie dużo trudniejsze. Niektóre panele mają wbudowany terminal webowy.

### 0c. WeasyPrint — biblioteki systemowe (PDF raporty)

Raporty PDF używają **WeasyPrint**, który wymaga bibliotek systemowych: `pango`, `cairo`, `gdk-pixbuf`.  
Na większości shared hosting z CloudLinux te biblioteki **są zainstalowane**.

Jeśli po wdrożeniu raporty PDF nie działają (błąd `OSError: cannot load library 'pango'`):
- Zapytaj support czy zainstalowane jest `pango` i `cairo`
- Lub wyłącz raporty PDF tymczasowo (reszta aplikacji będzie działać)

### 0d. Rozmiar bazy danych

Sprawdź limit importu w PhpMyAdmin (zazwyczaj 50–512 MB). Nasz dump powinien zmieścić się bez problemu.

---

## KROK 1 — Baza danych: eksport z DBeaver → import via PhpMyAdmin

### 1a. Eksport dumpa lokalnej bazy (DBeaver)

1. Otwórz **DBeaver → Navigator** → prawym na bazę `rao_new`
2. Wybierz **Tools → Dump Database**
3. Ustawienia eksportu:
   - Format: **SQL**
   - ✅ Add DROP statements
   - ✅ Add CREATE statements
   - ✅ Add INSERT statements
   - Character set: **utf8mb4**
4. Zapisz plik np. `rao_dump_YYYY-MM-DD.sql`
5. **Otwórz plik w edytorze** i upewnij się, że pierwsza linia to:
   ```sql
   -- Usuń USE jeśli istnieje, PhpMyAdmin sam ustawia bazę docelową
   ```
   Usuń linię `USE rao_new;` z dumpa (PhpMyAdmin zignoruje ją lub spowoduje błąd).

### 1b. Utwórz bazę na hostingu (Panel → MySQL/MariaDB)

1. Zaloguj się do panelu hostingowego (toolsmart.pl)
2. Przejdź do **Bazy danych → MySQL/MariaDB → Utwórz nową bazę**
   - Nazwa: `toolsmart_rao` (panel zazwyczaj dodaje prefix konta, np. `ts123_rao`)
   - Kodowanie: **utf8mb4_unicode_ci**
3. Utwórz **użytkownika bazy**:
   - Login: `ts123_rao_user`
   - Hasło: (silne, zapisz!)
4. Przypisz użytkownika do bazy i nadaj uprawnienia — **zaznacz dokładnie te pola**:

| Uprawnienie | Zaznacz | Po co |
|-------------|---------|-------|
| `SELECT` | ✅ | odczyt danych |
| `INSERT` | ✅ | dodawanie rekordów |
| `UPDATE` | ✅ | edycja rekordów |
| `DELETE` | ✅ | usuwanie rekordów |
| `CREATE` | ✅ | tworzenie tabel (migracje Alembic) |
| `DROP` | ✅ | usuwanie tabel (migracje) |
| `ALTER` | ✅ | zmiana struktury tabel (migracje) |
| `INDEX` | ✅ | tworzenie indeksów |
| `REFERENCES` | ✅ | klucze obce (foreign keys) |
| `CREATE TEMPORARY TABLES` | ✅ | operacje tymczasowe |
| `LOCK TABLES` | ✅ | import dumpów |
| `EXECUTE` | ❌ | nie potrzebne |
| `GRANT OPTION` | ❌ | nie dawaj — pozwala nadawać prawa innym |
| `SUPER` | ❌ | nie potrzebne, zbyt szerokie |

> **Najszybsza opcja w panelu DirectAdmin**: przy przypisywaniu użytkownika do bazy kliknij **"ALL PRIVILEGES"** — to zaznacza wszystkie powyższe naraz (z wyjątkiem GRANT OPTION i SUPER). Na shared hostingu panel zazwyczaj nie daje SUPER i GRANT OPTION nawet przez ALL PRIVILEGES — więc jest bezpieczne.

5. Zanotuj:
   ```
   DB_HOST=localhost
   DB_NAME=ts123_rao
   DB_USER=ts123_rao_user
   DB_PASS=TwojeHaslo123!
   ```

### 1c. Import dumpa via PhpMyAdmin

1. Otwórz **PhpMyAdmin** z panelu hostingowego
2. Wybierz po lewej bazę `ts123_rao`
3. Zakładka **Import**
4. Kliknij **Wybierz plik** → wskaż `rao_dump_YYYY-MM-DD.sql`
5. Kodowanie: **utf8mb4**, Format: **SQL**
6. Kliknij **Wykonaj**

> **Uwaga**: Jeśli dump jest > 50 MB, podziel go lub użyj klienta CLI via SSH (jeśli hosting udostępnia).

### 1d. Weryfikacja importu

W PhpMyAdmin sprawdź, czy istnieją tabele:
```sql
SHOW TABLES;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM contracts;
```

---

## KROK 2 — Frontend: Build lokalny + upload

### 2a. Przygotuj kod przed buildem (już zrobione w repozytorium)

W kodzie wprowadzono 3 zmiany pod path `/rao`:

| Plik | Zmiana |
|------|--------|
| `frontend/vite.config.ts` | `base: '/rao/'` |
| `frontend/src/router/index.js` | `createWebHistory('/rao')` |
| `frontend/src/composables/useApi.js` | redirect 401 → `/rao/login` |

Plik `frontend/.env.production` zawiera:
```dotenv
VITE_API_URL=https://www.toolsmart.pl/rao/api
```

> Jeśli URL backendu się zmieni, edytuj tylko `frontend/.env.production` i przebuduj.

### 2b. Buduj frontend lokalnie

```bash
cd frontend
npm install
npm run build
```

Wynik: folder `frontend/dist/` z plikami statycznymi pod bazą `/rao/`.

### 2c. Upload plików frontend

1. Przez **Menadżer plików** panelu lub **FTP** (FileZilla)
2. Połącz się z serwerem:
   - Host: `toolsmart.pl` | Port: `21` (FTP) lub `22` (SFTP)
   - Login/hasło: dane FTP z panelu
3. **Utwórz folder** `public_html/rao/` jeśli nie istnieje
4. Wgraj całą zawartość `frontend/dist/` do katalogu `public_html/rao/`
5. Utwórz plik `public_html/rao/.htaccess`:

```apache
# public_html/rao/.htaccess
Options -MultiViews
RewriteEngine On
RewriteBase /rao/

# WAŻNE: NIE przechwytuj requestów do API (obsługuje je Python app)
RewriteCond %{REQUEST_URI} !^/rao/api
# Standardowe SPA fallback — pliki i foldery serwuj normalnie
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.html [QSA,L]
```

Struktura po uploaderze:
```
public_html/
└── rao/
    ├── index.html
    ├── .htaccess
    └── assets/
        ├── index-XXXX.js
        └── index-XXXX.css
```

> **Opcja B — Node.js app**: jeśli chcesz serwować przez Node.js zamiast Apache — patrz Krok 4.

---

## KROK 3 — Backend: Python App na hostingu

### 3a. Przygotuj pliki backendu

Pliki już istnieją w repozytorium:

| Plik | Opis |
|------|------|
| `backend/wsgi.py` | Wrapper ASGI→WSGI (a2wsgi) — wymagany przez panel hostingowy |
| `backend/requirements-prod.txt` | Zależności **bez** playwright (nie działa na shared hosting) |
| `backend/reports/service.py` | PDF przez WeasyPrint (fallback z Playwright) |

Utwórz plik `backend/.env` z konfiguracją produkcyjną (NIE commituj go do git!):

```dotenv
# backend/.env — PRODUKCJA
RAO_DATABASE_URL=mysql+aiomysql://ts123_rao_user:TwojeHaslo123!@localhost:3306/ts123_rao
RAO_SECRET_KEY=wygeneruj-losowy-klucz-64-znaki-min
RAO_ACCESS_TOKEN_EXPIRE_MINUTES=480
RAO_SMTP_HOST=mail.toolsmart.pl
RAO_SMTP_PORT=587
RAO_SMTP_USER=noreply@toolsmart.pl
RAO_SMTP_PASSWORD=HasloDoPoczty
RAO_SMTP_FROM=noreply@toolsmart.pl
RAO_SMTP_TLS=True
RAO_FRONTEND_URL=https://www.toolsmart.pl/rao
RAO_GUS_API_KEY=twoj_klucz_gus
RAO_CORS_ORIGINS=["https://www.toolsmart.pl","https://toolsmart.pl"]
RAO_PDF_RENDERER=weasyprint
```

> **Generowanie SECRET_KEY** (uruchom lokalnie):
> ```python
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 3b. Upload backendu na serwer

Przez FTP/SFTP wgraj folder `backend/` do katalogu na serwerze, np. `/home/ts123/rao_backend/`.

**NIE wgrywaj** tych folderów/plików:
- `.venv/` (virtualenv — serwer stworzy swój)
- `__pycache__/` (cache Pythona)
- `.pytest_cache/`

Struktura docelowa na serwerze:
```
/home/ts123/
├── public_html/
│   └── rao/                  ← frontend (dist/)
│       ├── index.html
│       ├── .htaccess
│       └── assets/
└── rao_backend/              ← backend (POZA public_html!)
    ├── main.py
    ├── wsgi.py               ← entry point dla panelu
    ├── .env                  ← konfiguracja (utwórz na serwerze!)
    ├── requirements-prod.txt ← zależności produkcyjne
    ├── config.py
    ├── database.py
    ├── auth/
    ├── contractors/
    ├── contracts/
    ├── articles/
    ├── reports/
    │   ├── service.py
    │   └── templates/        ← szablony HTML dla PDF!
    ├── settings/
    ├── integrations/
    └── stats/
```

### 3c. Konfiguracja Python App w panelu — wypełnienie formularza

Panel → **Web Applications → Create Application → Python**

```
┌─────────────────────────────────────────────────────────────────┐
│  Python                                                         │
├──────────────────────────┬──────────────────────────────────────┤
│ Python version           │ [3.11.x ▼]  ← ZMIEŃ z 2.7 na 3.11! │
│ Application root         │ rao_backend                          │
│   (ścieżka względna      │   (panel doda prefix /home/ts123/)   │
│    od katalogu konta)    │                                      │
│ Application URL          │ [toolsmart.pl ▼]  /rao/api            │
│   (domena + ścieżka)     │   wpisz: rao/api  w polu obok domeny │
│ Application startup file │ wsgi.py                              │
│ Application Entry point  │ application                          │
│   (WSGI callable)        │                                      │
└──────────────────────────┴──────────────────────────────────────┘
```

> **Uwaga do Application root**: panel zazwyczaj oczekuje ścieżki względem katalogu domowego konta (`/home/ts123/`), więc wpisz samo `rao_backend` — nie pełną ścieżkę. Jeśli wymaga pełnej, wpisz `/home/ts123/rao_backend`.

> **Uwaga do Application URL**: w polu obok domeny `toolsmart.pl` wpisz `rao/api` — backend będzie dostępny pod `https://www.toolsmart.pl/rao/api/...`

Następnie kliknij **+ ADD VARIABLE** i dodaj po kolei każdą zmienną:

| Variable (klucz) | Value (wartość) |
|-----------------|-----------------|
| `RAO_DATABASE_URL` | `mysql+aiomysql://ts123_rao_user:TwojeHaslo@localhost:3306/ts123_rao` |
| `RAO_SECRET_KEY` | `(wygenerowany hex — patrz niżej)` |
| `RAO_CORS_ORIGINS` | `["https://www.toolsmart.pl","https://toolsmart.pl"]` |
| `RAO_FRONTEND_URL` | `https://www.toolsmart.pl/rao` |
| `RAO_SMTP_HOST` | `mail.toolsmart.pl` |
| `RAO_SMTP_PORT` | `587` |
| `RAO_SMTP_USER` | `noreply@toolsmart.pl` |
| `RAO_SMTP_PASSWORD` | `(hasło skrzynki)` |
| `RAO_SMTP_TLS` | `True` |
| `RAO_PDF_RENDERER` | `weasyprint` |

Po uzupełnieniu wszystkich pól kliknij **CREATE**.

### 3d. Zainstaluj zależności Pythona

> **WAŻNE**: Na serwerze plik z zależnościami musi się nazywać `requirements.txt`.  
> Przez FTP zmień nazwę `requirements-prod.txt` → `requirements.txt` w katalogu `rao_backend/`.  
> (Plik produkcyjny nie zawiera playwright ani watchfiles — nie działają na shared hosting.)

#### Wariant A — Panel sam instaluje (bez SSH)

Większość paneli DirectAdmin z **Setup Python App** automatycznie instaluje pakiety:

1. Po kliknięciu **CREATE** w formularzu Python App, panel tworzy virtualenv
2. Panel szuka pliku `requirements.txt` w Application root (`rao_backend/`)
3. Jeśli go znajdzie — uruchamia `pip install -r requirements.txt` automatycznie
4. Sprawdź status w panelu → przy aplikacji powinien być status **Running** (zielony)

Jeśli panel ma przycisk **"Run pip install"** lub **"Restart"** — kliknij go po wgraniu plików.

#### Wariant B — Przez SSH (jeśli dostępne)

```bash
# 1. Połącz się z serwerem
ssh twoj_login@toolsmart.pl

# 2. Wejdź do katalogu backendu
cd /home/ts123/rao_backend

# 3. Aktywuj virtualenv (ścieżka zależy od panelu — sprawdź w ustawieniach app)
source /home/ts123/virtualenv/rao_backend/3.11/bin/activate

# 4. Zainstaluj zależności
pip install -r requirements.txt

# 5. Sprawdź czy FastAPI się importuje
python -c "from main import app; print('OK')"
```

#### Wariant C — Poproś support

Napisz do supportu hostingu:  
*"Proszę o uruchomienie `pip install -r requirements.txt` w virtualenv aplikacji Python w katalogu `rao_backend/`. Ewentualnie proszę o dostęp SSH."*

> **Jeśli pip install kończy się błędem na `weasyprint`**: hosting może nie mieć `pango`/`cairo`. Poproś support o instalację lub zakomentuj `weasyprint` w `requirements.txt` na serwerze (PDF raporty nie będą działać, reszta TAK).

---

## KROK 4 — Node.js App dla frontendu (opcjonalnie)

Jeśli chcesz serwować frontend przez Node.js zamiast bezpośrednio z public_html:

### 4a. Utwórz prosty serwer Express

Utwórz plik `frontend/server.js`:

```javascript
const express = require('express');
const path = require('path');
const app = express();

app.use(express.static(path.join(__dirname, 'dist')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Frontend running on port ${PORT}`));
```

Dodaj `express` do `frontend/package.json`:
```bash
npm install express --save
```

### 4b. Konfiguracja Node.js App w panelu — wypełnienie formularza

Panel → **Web Applications → Create Application → Node.js**

```
┌─────────────────────────────────────────────────────────────────┐
│  Node.js                                                        │
├──────────────────────────┬──────────────────────────────────────┤
│ Node.js version          │ [24.13.0 ▼]  (zostaw domyślną)      │
│ Application mode         │ [Production ▼]  ← ZMIEŃ z Dev!      │
│ Application root         │ rao_frontend                         │
│   (ścieżka względna)     │   (panel doda prefix /home/ts123/)   │
│ Application URL          │ [toolsmart.pl ▼]  /rao               │
│   (domena + ścieżka)     │   wpisz: rao  w polu obok domeny    │
│ Application startup file │ server.js                            │
└──────────────────────────┴──────────────────────────────────────┘
```

> **Application mode**: koniecznie ustaw `Production` — w trybie `Development` Node.js może ładować dodatkowe narzędzia dev i wolniej działać.

> **Application URL**: wpisz `rao` w polu obok `toolsmart.pl` — frontend będzie dostępny pod `https://www.toolsmart.pl/rao`.

Zmienne środowiskowe dla Node.js frontu — kliknij **+ ADD VARIABLE**:

| Variable | Value |
|----------|-------|
| `NODE_ENV` | `production` |

Po uzupełnieniu kliknij **CREATE**, następnie:

```bash
# przez SSH/terminal panelu:
cd /home/ts123/rao_frontend
npm install --production
```

---

## KROK 5 — Weryfikacja po wdrożeniu

### Sprawdź backend (API)
```bash
curl https://www.toolsmart.pl/rao/api/health
# Oczekiwany wynik: {"status":"ok","version":"1.0.0"}
```

### Sprawdź frontend
Otwórz `https://www.toolsmart.pl/rao` w przeglądarce → powinna pojawić się strona logowania RAO.

### Sprawdź logi błędów
- Panel hostingowy → **Logi → Error log** (Python app)
- PhpMyAdmin → weryfikuj dane (`SELECT * FROM users LIMIT 5;`)

---

## KROK 6 — Migracje danych (po wdrożeniu)

### 6a. Migracja RAO-P3-014: Placeholdery $1/$2 w opisach usług dodatkowych

**Data:** 2026-05-25  
**Cel:** Zamienić placeholdery `$1 zł`, `$2 zł` na konkretne wartości w `service_fee_templates`

**Problem:** Opisy w bazie używały placeholderów `$1`, `$2` zamiast konkretnych wartości z `amount_from`/`amount_to`, co powodowało wyświetlanie `$1 zł`, `$2 zł` w PDF zamiast rzeczywistych kwot.

**Rozwiązanie:** Skrypt SQL zastępuje placeholdery wartościami z kolumn `amount_from` i `amount_to`.

#### Instrukcja migracji na produkcji

1. **Zaloguj się do PhpMyAdmin** (panel hostingowy)
2. **Wybierz bazę danych** `toolsmart_rao` (lub nazwa z panelu)
3. **Zakładka SQL** (górna zakładka)
4. **Wklej skrypt migracyjny:**

```sql
-- Migration 003: Fix placeholders $1/$2 in service_fee_templates descriptions
-- Date: 2026-05-25
-- Description: Replace placeholders $1/$2 with actual values from amount_from/amount_to

-- Backup before migration
CREATE TABLE IF NOT EXISTS service_fee_templates_backup_20260525 AS SELECT * FROM service_fee_templates;

-- Update descriptions with actual values
-- Pattern: replace $1 with amount_from, $2 with amount_to
-- Format: "X zł" where X is the value formatted as decimal

UPDATE service_fee_templates 
SET description = REPLACE(
    REPLACE(
        description,
        '$1 zł',
        CONCAT(IFNULL(amount_from, ''), ' zł')
    ),
    '$2 zł',
    CONCAT(IFNULL(amount_to, ''), ' zł')
)
WHERE description LIKE '%$1%' OR description LIKE '%$2%';

-- Verify migration
SELECT 
    id, 
    name, 
    description, 
    amount_from, 
    amount_to,
    CASE 
        WHEN description LIKE '%$1%' OR description LIKE '%$2%' THEN 'STILL_HAS_PLACEHOLDERS'
        ELSE 'OK'
    END as status
FROM service_fee_templates
ORDER BY id;
```

5. **Kliknij "Wykonaj"** (Execute)
6. **Sprawdź wynik weryfikacji** - wszystkie rekordy powinny mieć status = `OK`

#### Przykłady zmian

| ID | Przed | Po |
|----|-------|----|
| 1 | `- Usługa tankowania: $1 zł (plus koszt paliwa)` | `- Usługa tankowania: 150.00 zł (plus koszt paliwa)` |
| 3 | `- Transport: $1 zł dostawa / $2 zł odbiór` | `- Transport: 400.00 zł dostawa / 400.00 zł odbiór` |
| 5 | `- Ponadnormatywny przestój transportu: $1 zł / h - $2 zł / h` | `- Ponadnormatywny przestój transportu: 200.00 zł / h - 300.00 zł / h` |

#### Rollback (jeśli coś pójdzie nie tak)

```sql
-- Przywrócić dane z backupu
DROP TABLE service_fee_templates;
RENAME TABLE service_fee_templates_backup_20260525 TO service_fee_templates;
```

#### Weryfikacja po migracji

1. **Sprawdź PDF** - wygeneruj umowę z usługami dodatkowymi i sprawdź czy wartości są widoczne (bez $1/$2)
2. **Sprawdź UI** - otwórz ustawienia → "Zestawy usług dodatkowych" i sprawdź czy opisy są poprawne
3. **Sprawdź bazę** - w PhpMyAdmin wykonaj:
   ```sql
   SELECT id, name, description FROM service_fee_templates;
   ```
   - Żaden rekord nie powinien zawierać `$1` lub `$2`

#### Automatyczna migracja w backend

**Uwaga:** Backend automatycznie wykonuje tę migrację przy starcie (w `backend/main.py` startup_migrations), ale ręczne wykonanie skryptu SQL na produkcji jest zalecane dla pewności i audytu.

---

## KROK 7 — Utwórz pierwszego admina

Po imporcie bazy sprawdź czy istnieje użytkownik admin:
```sql
SELECT id, login, role, is_active FROM users WHERE role = 'admin';
```

Jeśli nie, utwórz go przez PhpMyAdmin (hasło zahashowane bcrypt):
```sql
-- Wygeneruj hash lokalnie: python -c "import bcrypt; print(bcrypt.hashpw(b'Admin123!', bcrypt.gensalt()).decode())"
INSERT INTO users (login, email, password, role, is_active)
VALUES ('admin', 'admin@toolsmart.pl', '$2b$12$HASH_TUTAJ', 'admin', 1);
```

---

## Troubleshooting

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| `500 Internal Server Error` na API | Błąd w .env lub DB | Sprawdź logi Python app w panelu |
| CORS error w przeglądarce | Zły `RAO_CORS_ORIGINS` | Ustaw `["https://www.toolsmart.pl","https://toolsmart.pl"]` |
| `Module not found` | pip install nie wykonano | Uruchom `pip install -r requirements-prod.txt` w virtualenv przez SSH |
| Python 2.7 zamiast 3.x | Zły interpreter | Zmień wersję Pythona w ustawieniach aplikacji (min. 3.10) |
| Vue router 404 na F5 | Brak .htaccess lub zły RewriteBase | Sprawdź `.htaccess` w `public_html/rao/` — musi mieć `RewriteBase /rao/` |
| Biała strona po wejściu na `/rao` | Zły `base` w vite.config | Upewnij się że `base: '/rao/'` i przebuduj |
| Import SQL zbyt duży | Limit PhpMyAdmin | Podziel dump: `split -l 5000 dump.sql chunk_` |
| `aiomysql` crash na WSGI | ASGI/WSGI mismatch | Upewnij się że `wsgi.py` używa `a2wsgi.ASGIMiddleware` |
| API zwraca HTML zamiast JSON | `.htaccess` przechwytuje `/rao/api` | Dodaj `RewriteCond %{REQUEST_URI} !^/rao/api` w `.htaccess` |
| `playwright._impl` error | Playwright nie działa na shared hosting | Użyj `requirements-prod.txt` (bez playwright). PDF automatycznie użyje WeasyPrint |
| `OSError: cannot load library 'pango'` | Brak bibliotek systemowych | Napisz do supportu o zainstalowanie pango/cairo. Tymczasowo: zakomentuj weasyprint |
| `pip install` instaluje globalnie | Nie aktywowano virtualenv | Uruchom `source /home/ts123/virtualenv/.../bin/activate` przed pip install |
| `No module named 'a2wsgi'` | Brak a2wsgi w requirements | Użyj `requirements-prod.txt` (ma a2wsgi) zamiast `requirements.txt` |

---

## Szybki checklist wdrożenia

**Przed wdrożeniem (KROK 0):**
- [ ] Python 3.10+ dostępny w dropdownie panelu
- [ ] SSH / terminal dostępny

**Baza danych (KROK 1):**
- [ ] Baza utworzona na hostingu (utf8mb4_unicode_ci)
- [ ] Dump zaimportowany przez PhpMyAdmin (bez linii `USE rao_new;`)
- [ ] `SELECT COUNT(*) FROM users` zwraca wyniki

**Frontend (KROK 2):**
- [ ] `npm run build` wykonany lokalnie (z `base: '/rao/'` w vite.config)
- [ ] `frontend/dist/` wgrany do `public_html/rao/`
- [ ] `.htaccess` w `public_html/rao/` — ma `RewriteBase /rao/` ORAZ wykluczenie `/rao/api`

**Backend (KROK 3):**
- [ ] `backend/` wgrany do `rao_backend/` (poza public_html! bez `.venv/`, `__pycache__/`)
- [ ] `.env` produkcyjny na serwerze z poprawnymi danymi DB
- [ ] Python App w panelu: **Python 3.11+**, root=`rao_backend`, URL=`rao/api`, startup=`wsgi.py`, entry=`application`
- [ ] Zmienne środowiskowe dodane w panelu (RAO_DATABASE_URL, RAO_SECRET_KEY, RAO_CORS_ORIGINS)
- [ ] `pip install -r requirements-prod.txt` w virtualenv serwera
- [ ] `python -c "from main import app; print('OK')"` działa

**Weryfikacja (KROK 5):**
- [ ] `GET https://www.toolsmart.pl/rao/api/health` → `{"status":"ok"}`
- [ ] `https://www.toolsmart.pl/rao` → strona logowania RAO
- [ ] F5 na `/rao/home` nie daje 404
- [ ] Login działa, dane się ładują z bazy

**Migracje danych (KROK 6):**
- [ ] Skrypt SQL `003_fix_service_fee_placeholders.sql` wykonany w PhpMyAdmin
- [ ] Weryfikacja: wszystkie rekordy mają status = `OK` (brak $1/$2)
- [ ] PDF z usługami dodatkowymi pokazuje konkretne wartości (nie placeholdery)
- [ ] UI ustawienia → "Zestawy usług dodatkowych" pokazuje poprawne opisy
