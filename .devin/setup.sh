#!/usr/bin/env bash
# ============================================================
# RAO — Devin / Ubuntu setup script
# Idempotentny: można uruchomić wielokrotnie bez efektów ubocznych.
# Użycie:  bash .devin/setup.sh
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> RAO setup — repo root: $REPO_ROOT"

# ------------------------------------------------------------
# 1. MariaDB (Devin base image zawiera mariadb-server)
# ------------------------------------------------------------
echo "==> [1/6] MariaDB"
if ! command -v mariadb >/dev/null 2>&1; then
    echo "    instaluję mariadb-server (apt)..."
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq mariadb-server
fi
sudo service mariadb start 2>/dev/null || sudo service mysql start 2>/dev/null || true
sleep 2

sudo mariadb -e "CREATE DATABASE IF NOT EXISTS rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"
sudo mariadb -e "CREATE USER IF NOT EXISTS 'rao_user'@'localhost' IDENTIFIED BY 'RaoPass2026!';"
sudo mariadb -e "GRANT ALL PRIVILEGES ON rao_new.* TO 'rao_user'@'localhost'; FLUSH PRIVILEGES;"
echo "    OK — baza rao_new + user rao_user"

# ------------------------------------------------------------
# 2. .env (z szablonu jeśli brak)
# ------------------------------------------------------------
echo "==> [2/6] .env"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "    UTWORZONO .env z .env.example — UZUPEŁNIJ sekrety produkcyjne!"
else
    echo "    .env już istnieje — pomijam"
fi

# ------------------------------------------------------------
# 3. Backend Python (FastAPI)
# ------------------------------------------------------------
echo "==> [3/6] Backend Python venv + deps"
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
deactivate
cd "$REPO_ROOT"
echo "    OK — backend/.venv gotowy"

# ------------------------------------------------------------
# 4. Frontend (Vue 3 + Vite)
# ------------------------------------------------------------
echo "==> [4/6] Frontend npm deps"
cd frontend
npm ci --silent
cd "$REPO_ROOT"
echo "    OK — frontend/node_modules gotowy"

# ------------------------------------------------------------
# 5. E2E (Playwright + Chromium)
# ------------------------------------------------------------
echo "==> [5/6] E2E + Playwright Chromium"
cd e2e
npm ci --silent
npx playwright install --with-deps chromium
cd "$REPO_ROOT"
echo "    OK — e2e gotowy"

# ------------------------------------------------------------
# 6. Pierwsze uruchomienie backendu (utworzy schemat z modeli SQLAlchemy)
# ------------------------------------------------------------
echo "==> [6/6] Inicjalizacja schematu DB (uvicorn startup events)"
cd backend
# shellcheck disable=SC1091
source .venv/bin/activate
# 10s timeout — backend uruchomi się, odpali Base.metadata.create_all + ALTER ... IF NOT EXISTS, potem zabijemy
timeout 10 uvicorn main:app --port 8000 >/tmp/rao-backend-init.log 2>&1 || true
deactivate
cd "$REPO_ROOT"

# Weryfikacja — czy tabele powstały
TABLE_COUNT=$(sudo mariadb rao_new -e "SHOW TABLES;" 2>/dev/null | wc -l)
echo "    Tabel w rao_new: $((TABLE_COUNT - 1))"

if [ "$TABLE_COUNT" -lt 5 ]; then
    echo ""
    echo "⚠️  UWAGA: schemat może nie być w pełni utworzony."
    echo "    Sprawdź log: cat /tmp/rao-backend-init.log"
fi

echo ""
echo "✅ Setup zakończony"
echo ""
echo "Co dalej:"
echo "  • Uruchomienie: bash .devin/run.sh"
echo "  • Backend health: curl http://localhost:8000/rao/api/health"
echo "  • Frontend: http://localhost:5173"
echo "  • Login: admin / admin123"
echo "  • Smoke test: cd e2e && npx playwright test tests/01-login.spec.ts"
