#!/usr/bin/env bash

# ==========================================================
# Dark Social Swarm - Unified One-Click Launcher
# Starts both Backend (FastAPI :8000) & Frontend (Next.js :3000)
# ==========================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "=========================================================="
echo "  Starting Dark Social Swarm..."
echo "=========================================================="

# 1. Check & setup .env
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        echo "Creating backend/.env from backend/.env.example..."
        cp "backend/.env.example" "backend/.env"
    fi
fi

# 2. Find Python Interpreter
PYTHON_BIN=""
if [ -f "$ROOT_DIR/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/Scripts/python.exe"
elif [ -f "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
else
    echo "ERROR: Python not found! Please create a virtualenv or install Python."
    exit 1
fi

echo "Using Python: $PYTHON_BIN"

# Helper to ensure ports are freed before launching & on exit
free_port() {
    local port=$1
    if command -v powershell.exe &> /dev/null; then
        powershell.exe -NoProfile -Command "
            Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id \$_.OwningProcess -Force -ErrorAction SilentlyContinue }
        " 2>/dev/null || true
    elif command -v fuser &> /dev/null; then
        fuser -k "${port}/tcp" 2>/dev/null || true
    fi
}

# 3. Cleanup handler
cleanup() {
    echo ""
    echo "=========================================================="
    echo "  Shutting down Dark Social Swarm..."
    echo "=========================================================="
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    free_port 8000
    free_port 3000
    echo "All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Ensure ports 8000 and 3000 are not locked before starting
free_port 8000
free_port 3000

# 4. Start Backend (FastAPI on :8000)
echo "Starting Backend on http://localhost:8000..."
cd "$ROOT_DIR/backend"
"$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd "$ROOT_DIR"

# 5. Start Frontend (Next.js on :3000)
echo "Starting Frontend on http://localhost:3000..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

echo ""
echo "=========================================================="
echo "  Dark Social Swarm is RUNNING!"
echo "    Dashboard:  http://localhost:3000"
echo "    Backend:    http://localhost:8000"
echo "    API Docs:   http://localhost:8000/docs"
echo "  Press Ctrl+C to stop both servers."
echo "=========================================================="
echo ""

wait
