# RAO Deployment Package

**Data migracji:** 2026-05-22  
**Wersja bazy:** rao_new  
**Plik dump:** `rao_new_20260522_112746.sql`

---

## 📋 Zawartość paczki

```
deployment/
├── backend/              # FastAPI backend (bez .venv i __pycache__)
├── frontend/             # Vue 3 frontend (zbuildowany - dist/)
├── rao_new_20260522_112746.sql  # Dump bazy danych
└── README.md            # Ten plik
```

---

## 🚀 Instrukcja deploymentu

### 1. Wymagania

- MariaDB 10.11+
- Python 3.11+
- Node.js 18+ (tylko do budowy frontendu, nie wymagane w produkcji)

### 2. Import bazy danych

```bash
# Utwórz bazę danych
mysql -u root -p -e "CREATE DATABASE rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"

# Utwórz użytkownika
mysql -u root -p -e "CREATE USER 'rao_user'@'localhost' IDENTIFIED BY 'RaoPass2026!';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON rao_new.* TO 'rao_user'@'localhost'; FLUSH PRIVILEGES;"

# Importuj dump
mysql -u rao_user -pRaoPass2026! rao_new < rao_new_20260522_112746.sql
```

### 3. Konfiguracja backendu

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # na Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Utwórz `.env`:
```env
RAO_DATABASE_URL=mysql+aiomysql://rao_user:RaoPass2026!@localhost:3306/rao_new
RAO_DB_USER=rao_user
RAO_DB_PASSWORD=RaoPass2026!
RAO_DB_NAME=rao_new
RAO_DB_HOST=localhost
RAO_DB_PORT=3306
RAO_SECRET_KEY=super-secret-jwt-key-change-in-production-min-32-chars-rao2026
RAO_ACCESS_TOKEN_EXPIRE_MINUTES=480
RAO_SMTP_HOST=localhost
RAO_SMTP_PORT=1025
RAO_SMTP_FROM=noreply@rao-app.pl
RAO_FRONTEND_URL=http://localhost:5173
RAO_CORS_ORIGINS=["http://localhost:5173","http://localhost:5174"]
```

Uruchom backend:
```bash
uvicorn main:app --reload --port 8000
```

**Produkcja:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Konfiguracja frontendu

Frontend jest już zbudowany (folder `frontend/`).

**Opcja A - Serwowanie statyczne (nginx/apache):**
```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/deployment/frontend;
        try_files $uri $uri/ /index.html;
    }
    
    location /rao/api/ {
        proxy_pass http://localhost:8000/rao/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Opcja B - Serwowanie przez Python (dev):**
```bash
cd frontend
python -m http.server 5173
```

**Uwaga:** W produkcji frontend musi być serwowany przez nginx/apache, nie przez Python.

---

## 👥 Dane logowania (testowe)

| Login | Hasło | Rola |
|-------|-------|------|
| admin | admin123 | admin |
| lukasz | lukasz123 | user |
| test | test123 | user |
| patrycja | patrycja123 | user |

**Uwaga:** Hasła są testowe. Zmień je w produkcji.

---

## 📊 Statystyki po migracji

- **Kontrahenci:** 632
- **Artykuły:** 418 (wszystkie archiwalne po migracji CSV)
- **Umowy:** 697 (wszystkie oznaczone jako rozliczone - dane historyczne)
- **Pozycje umów:** 828
- **Warunki rozliczeniowe:** 1194
- **Szablony opłat:** 10
- **Opłaty umów:** 3209
- **Kategorie:** 64

---

## ⚠️ Uwagi

- Wszystkie umowy ze starej bazy są oznaczone jako `is_settled=TRUE` (rozliczone)
- `settled_at` ustawiony na `date_to` dla spójności danych
- Loginy użytkowników są lowercasowane
- Wszystkie artykuły oznaczone jako `is_archival=TRUE` po migracji CSV kategorii
- Użytkownicy mają `must_change_password=FALSE` (hasła testowe ustawione)
- Frontend jest zbudowany bez type-checking (TS errors pominięte dla deploymentu)

---

## 🔒 Security

- Hasła są hashowane bcrypt (cost=12)
- Sekrety w `.env` - nie commitować do repo
- W produkcji zmień `RAO_SECRET_KEY` i hasła użytkowników
- Skonfiguruj prawdziwy SMTP dla emaili
- Użyj HTTPS w produkcji

---

## 📞 Wsparcie

- **Specyfikacja:** `spec/`
- **Dokumentacja migracji:** `spec/process/migrations.md`
- **Logika biznesowa:** `spec/core/04_business_logic.md`
- **Security:** `spec/core/25_security.md`
