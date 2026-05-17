#!/usr/bin/env bash
# ============================================================
# RAO — Devin / Ubuntu run script
# Uruchamia backend (FastAPI) + frontend (Vite) równolegle.
# Użycie:  bash .devin/run.sh
# Zatrzymanie: Ctrl+C (zabije oba procesy, dzięki trap)
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Upewnij się że MariaDB działa
sudo service mariadb start 2>/dev/null || sudo service mysql start 2>/dev/null || true

# ------------------------------------------------------------
# Backend
# ------------------------------------------------------------
echo "==> Start backend (uvicorn :8000)"
cd backend
# shellcheck disable=SC1091
source .venv/bin/activate
uvicorn main:app --reload --port 8000 --host 0.0.0.0 >/tmp/rao-backend.log 2>&1 &
BACKEND_PID=$!
deactivate
cd "$REPO_ROOT"

# ------------------------------------------------------------
# Frontend
# ------------------------------------------------------------
echo "==> Start frontend (Vite :5173)"
cd frontend
npm run dev -- --host 0.0.0.0 >/tmp/rao-frontend.log 2>&1 &
FRONTEND_PID=$!
cd "$REPO_ROOT"

# ------------------------------------------------------------
# Cleanup on exit
# ------------------------------------------------------------
cleanup() {
    echo ""
    echo "==> Zatrzymuję serwery..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait 2>/dev/null || true
    echo "    OK"
}
trap cleanup EXIT INT TERM

# ------------------------------------------------------------
# Wait for health
# ------------------------------------------------------------
echo "==> Czekam na backend (max 30s)..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/rao/api/health >/dev/null 2>&1; then
        echo "    Backend OK (po ${i}s)"
        break
    fi
    sleep 1
done

echo "==> Czekam na frontend (max 30s)..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:5173 >/dev/null 2>&1; then
        echo "    Frontend OK (po ${i}s)"
        break
    fi
    sleep 1
done

echo ""
echo "✅ RAO działa"
echo ""
echo "  Backend:  http://localhost:8000/rao/api/health"
echo "  API docs: http://localhost:8000/rao/api/docs"
echo "  Frontend: http://localhost:5173"
echo "  Login:    admin / admin123"
echo ""
echo "  Logi: tail -f /tmp/rao-backend.log /tmp/rao-frontend.log"
echo ""
echo "Naciśnij Ctrl+C aby zatrzymać oba serwery."

# Czekaj na sygnał
wait
