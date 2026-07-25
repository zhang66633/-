@echo off
REM MathModelAgent one-click start (Windows)
REM Starts backend (8001) and frontend (5173) in separate windows.

cd /d %~dp0

REM Skip a service if its port is already listening (avoid duplicates)
netstat -ano | findstr ":8001" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo [skip] backend already running on 8001
) else (
  echo [start] backend http://127.0.0.1:8001
  start "math_backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --host 127.0.0.1 --port 8001"
)

netstat -ano | findstr ":5173" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo [skip] frontend already running on 5173
) else (
  echo [start] frontend http://localhost:5173
  start "math_frontend" cmd /k "cd /d %~dp0frontend && pnpm dev"
)

echo.
echo Done. Frontend: http://localhost:5173   API docs: http://127.0.0.1:8001/docs
ping -n 5 127.0.0.1 >nul
