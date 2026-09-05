# Dark Social Swarm - PowerShell Launcher
$ErrorActionPreference = "Stop"
$rootDir = $PSScriptRoot
Set-Location $rootDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Dark Social Swarm..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Setup .env
if (-not (Test-Path "backend\.env")) {
    if (Test-Path "backend\.env.example") {
        Write-Host "Creating backend/.env from backend/.env.example..." -ForegroundColor Yellow
        Copy-Item "backend\.env.example" "backend\.env"
    }
}

# 2. Identify Python
$pythonExe = "$rootDir\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

# 3. Start Backend & Frontend as background jobs or processes
Write-Host "Starting Backend on http://localhost:8000..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory "$rootDir\backend" -PassThru

Write-Host "Starting Frontend on http://localhost:3000..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "$rootDir\frontend" -PassThru

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Dark Social Swarm is RUNNING!" -ForegroundColor Green
Write-Host "    Dashboard:  http://localhost:3000" -ForegroundColor White
Write-Host "    Backend:    http://localhost:8000" -ForegroundColor White
Write-Host "    API Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Press Enter or Ctrl+C in this terminal to stop both servers." -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

try {
    [Console]::ReadLine()
} finally {
    Write-Host "Shutting down servers..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "All servers stopped." -ForegroundColor Green
}
