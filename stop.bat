@echo off
REM MathModelAgent one-click stop: kill backend and frontend (5173)
REM Reads PORT from backend\.env (default 8000 if missing).

cd /d %~dp0

set "BACKEND_PORT=8000"
if exist backend\.env (
  for /f "tokens=1,* delims==" %%a in ('findstr /b "PORT=" backend\.env') do set "BACKEND_PORT=%%b"
)
for /f "tokens=1" %%p in ("%BACKEND_PORT%") do set "BACKEND_PORT=%%p"

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%" ^| findstr "LISTENING"') do (
  echo [stop] backend PID %%a
  taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
  echo [stop] frontend PID %%a
  taskkill /PID %%a /F >nul 2>&1
)
echo Stopped.
ping -n 3 127.0.0.1 >nul
