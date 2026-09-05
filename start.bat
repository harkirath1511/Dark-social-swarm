@echo off
title Dark Social Swarm Launcher
cls
echo ==========================================================
echo   Starting Dark Social Swarm...
echo ==========================================================

cd /d "%~dp0"

:: 1. Copy .env if not exists
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        echo Creating backend\.env from backend\.env.example...
        copy "backend\.env.example" "backend\.env" >nul
    )
)

:: 2. Find Python
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

:: 3. Start Backend in new window
echo Starting Backend on http://localhost:8000...
start "Dark Social Swarm - Backend" cmd /k "cd backend && "%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: 4. Start Frontend in new window
echo Starting Frontend on http://localhost:3000...
start "Dark Social Swarm - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================================
echo   Dark Social Swarm is RUNNING!
echo     Dashboard:  http://localhost:3000
echo     Backend:    http://localhost:8000
echo     API Docs:   http://localhost:8000/docs
echo ==========================================================
echo Both servers have been launched in separate terminal windows.
pause
