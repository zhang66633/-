@echo off
REM MathModelAgent one-click start (Windows)
REM Starts: ChromaDB + Redis (Docker) → backend → frontend

cd /d %~dp0

REM ── Read backend port from .env ──
set "BACKEND_PORT=8000"
if exist backend\.env (
  for /f "tokens=1,* delims==" %%a in ('findstr /b "PORT=" backend\.env') do set "BACKEND_PORT=%%b"
)
for /f "tokens=1" %%p in ("%BACKEND_PORT%") do set "BACKEND_PORT=%%p"
echo [info] backend port = %BACKEND_PORT%

REM ── Docker services ──
echo.
echo === Docker services ===

docker ps --format "{{.Names}}" | findstr "chromadb" >nul
if %errorlevel%==0 (
  echo [skip] chromadb already running
) else (
  echo [start] chromadb container on port 8001 ...
  docker rm -f chromadb >nul 2>&1
  docker run -d --name chromadb -p 8001:8000 -v "%~dp0backend\data\chroma_db:/chroma/chroma" -e IS_PERSISTENT=TRUE -e ANONYMIZED_TELEMETRY=FALSE --restart unless-stopped chromadb/chroma:latest >nul 2>&1
  if %errorlevel%==0 (echo [ ok ] chromadb started) else (echo [warn] chromadb failed — Docker running? KB will use local mode)
)

docker ps --format "{{.Names}}" | findstr "math-redis" >nul
if %errorlevel%==0 (
  echo [skip] redis already running
) else (
  echo [start] redis container on port 6379 ...
  docker rm -f math-redis >nul 2>&1
  docker run -d --name math-redis -p 6379:6379 --restart unless-stopped redis:7-alpine >nul 2>&1
  if %errorlevel%==0 (echo [ ok ] redis started) else (echo [warn] redis failed — fakeredis fallback will be used)
)

REM ── Backend ──
echo.
echo === Backend ===
netstat -ano | findstr ":%BACKEND_PORT%" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo [skip] backend already running on %BACKEND_PORT%
) else (
  echo [start] backend http://127.0.0.1:%BACKEND_PORT%
  start "math_backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT% --workers 1 --limit-concurrency 4 --timeout-keep-alive 30"
)

REM ── Frontend ──
echo.
echo === Frontend ===
netstat -ano | findstr ":5174" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo [skip] frontend already running on 5174
) else (
  echo [start] frontend http://localhost:5174
  start "math_frontend" cmd /k "cd /d %~dp0frontend && pnpm dev"
)

echo.
echo ============================================
echo   Done!
echo   Frontend : http://localhost:5174
echo   API docs : http://127.0.0.1:%BACKEND_PORT%/docs
echo   ChromaDB : http://localhost:8001 (docker)
echo   Redis    : localhost:6379    (docker)
echo ============================================
ping -n 5 127.0.0.1 >nul
