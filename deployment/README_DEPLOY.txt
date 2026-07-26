RAO — Paczka wdrozeniowa
========================
Data: 20260723_074131
Branch: refactor/articles-split-machines-services-additional
Commit: fd44ec6

Zawartosc:
  backend/    — kod produkcyjny FastAPI (moduly + main.py + requirements)
  frontend/   — zbuildowane pliki statyczne (dist/: index.html + assets/ + logo)
  database/   — dump SQL bazy rao_new (schema + dane)

Wdrozenie:
  1. Baza:    mysql --default-character-set=utf8mb4 rao_new < database/rao_new_dump.sql
              (WAZNE: --default-character-set=utf8mb4 wymagane — bez tego polskie znaki
               sie zepsuja. Dump jest UTF-8 bez BOM.)
  2. Backend: cd backend && python -m venv .venv && source .venv/bin/activate
              pip install -r requirements-prod.txt
              cp .env.example .env  (wypelnij dane produkcyjne)
              uvicorn main:app --port 8000  (lub passenger_wsgi.py na shared hosting)
  3. Frontend: skopiuj zawartosc frontend/ do katalogu serwowanego przez nginx/apache
               (np. /var/www/rao/). Proxy /rao/api -> backend:8000.
               UWAGA: frontend jest juz zbuildowany — nie potrzebuje npm ci / npm run build.

UWAGA: .env NIE jest w paczce (sekrety). Skopiuj .env.example i wypelnij recznie.
