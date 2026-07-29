@echo off
REM MathModelAgent one-click stop: kill backend + frontend + Docker containers

cd /d %~dp0

REM ── Read backend port ──
set "BACKEND_PORT=8000"
if exist backend\.env (
  for /f "tokens=1,* delims==" %%a in ('findstr /b "PORT=" backend\.env') do set "BACKEND_PORT=%%b"
)
for /f "tokens=1" %%p in ("%BACKEND_PORT%") do set "BACKEND_PORT=%%p"

echo === Stopping services ===

REM ── Kill backend ──
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%" ^| findstr "LISTENING"') do (
  echo [stop] backend PID %%a
  taskkill /PID %%a /F >nul 2>&1
)

REM ── Kill frontend ──
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5174" ^| findstr "LISTENING"') do (
  echo [stop] frontend PID %%a
  taskkill /PID %%a /F >nul 2>&1
)

REM ── Stop Docker containers ──
docker ps --format "{{.Names}}" | findstr "chromadb" >nul
if %errorlevel%==0 (
  echo [stop] chromadb container
  docker stop chromadb >nul 2>&1
  docker rm chromadb >nul 2>&1
)

docker ps --format "{{.Names}}" | findstr "math-redis" >nul
if %errorlevel%==0 (
  echo [stop] redis container
  docker stop math-redis >nul 2>&1
  docker rm math-redis >nul 2>&1
)

echo Stopped.
ping -n 3 127.0.0.1 >nul
