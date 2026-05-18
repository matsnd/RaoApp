# Port Management Pattern (Windows)

## Opis
Wzorzec do obsługi zajętych portów na Windows. Kluczowa zasada: **NIGDY nie zabijaj cudzych procesów**.

## Domyślne porty

| Usługa | Port | Alternatywy |
|--------|------|-------------|
| Backend (FastAPI) | 8000 | 8001, 8002, 8003 |
| Frontend (Vite) | 5173 | 5174, 5175, 5176 |
| SMTP dev (Mailpit) | 1025 / UI 8025 | - |
| MariaDB | 3306 | - |

## Zasady

### ✅ DO
- Użyj kolejnego wolnego portu (8001, 5174)
- Zaktualizuj `.env` przy zmianie portu backendu
- Zaktualizuj `VITE_API_URL` w `frontend/.env` przy zmianie portu backendu
- Sprawdź czy port jest zajęty przed uruchomieniem

### ❌ NIE
- NIGDY `taskkill` / `pkill` / `kill-port` cudzych procesów
- NIE zmieniaj portu MariaDB (3306)
- NIE uruchamiaj wielu instancji tego samego serwisu na tym samym porcie

## Sprawdzenie czy port jest zajęty

### Windows (PowerShell)
```powershell
# Sprawdź czy port 8000 jest zajęty
netstat -ano | findstr :8000

# Wynik:
# TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       12345
# PID: 12345
```

### Windows (CMD)
```cmd
netstat -ano | findstr :8000
```

### Linux/Mac
```bash
lsof -i :8000
# lub
netstat -tulpn | grep :8000
```

## Uruchomienie z alternatywnym portem

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8001
```

### Frontend
```bash
cd frontend
npm run dev -- --port 5174
```

## Aktualizacja konfiguracji

### Backend port 8001 → zaktualizuj frontend/.env
```env
# frontend/.env
VITE_API_URL=http://localhost:8001/rao/api
```

### Backend port 8001 → zaktualizuj .env
```env
# .env
BACKEND_PORT=8001
```

## Przykład scenariusza

### Scenariusz: Port 8000 zajęty
```bash
# 1. Sprawdź czy port jest zajęty
netstat -ano | findstr :8000

# 2. Wynik: TCP 0.0.0.0:8000 LISTENING 12345
# 3. Użyj kolejnego wolnego portu: 8001

# 4. Uruchom backend na 8001
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8001

# 5. Zaktualizuj frontend/.env
echo "VITE_API_URL=http://localhost:8001/rao/api" > frontend/.env

# 6. Uruchom frontend
cd frontend
npm run dev
```

## Użycie w RAO

### Development
- Wielu deweloperów na tej samej maszynie
- Wiele sesji Devina równolegle
- Testy różnych wersji backendu

### Testing
- Równoległe testy E2E
- Mock serwery na różnych portach
- Izolacja środowisk testowych

## Powiązane
- Config: `backend/config.py`
- Frontend config: `frontend/.env`
- Backend config: `.env`
- AGENTS.md: sekcja "Port management na Windows"

## Wymagania
- Dostęp do terminala (PowerShell/CMD)
- Prawa do uruchamiania procesów
- Znajomość netstat / lsof