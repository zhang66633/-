@echo off
REM MathModelAgent one-click start (Windows)
REM Reads PORT from backend\.env (default 8000 if missing).

cd /d %~dp0

REM ── Read backend port from .env ──
set "BACKEND_PORT=8000"
if exist backend\.env (
  for /f "tokens=1,* delims==" %%a in ('findstr /b "PORT=" backend\.env') do set "BACKEND_PORT=%%b"
)
REM Trim trailing spaces / CR
for /f "tokens=1" %%p in ("%BACKEND_PORT%") do set "BACKEND_PORT=%%p"

echo [info] backend port = %BACKEND_PORT%

REM Skip a service if its port is already listening (avoid duplicates)
netstat -ano | findstr ":%BACKEND_PORT%" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo [skip] backend already running on %BACKEND_PORT%
) else (
  echo [start] backend http://127.0.0.1:%BACKEND_PORT%
  start "math_backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
)

netstat -ano | findstr ":5174" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo [skip] frontend already running on 5174
) else (
  echo [start] frontend http://localhost:5174
  start "math_frontend" cmd /k "cd /d %~dp0frontend && pnpm dev"
)

echo.
echo Done. Frontend: http://localhost:5174   API docs: http://127.0.0.1:%BACKEND_PORT%/docs
ping -n 5 127.0.0.1 >nul
