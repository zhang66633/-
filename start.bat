@echo off
title MathModelAgent
cd /d "%~dp0"

echo.
echo ============================================
echo   MathModelAgent - Starting all services
echo ============================================
echo.

REM ---- read backend port ----
set BACKEND_PORT=8000
for /f "tokens=2 delims==" %%a in ('type "backend\.env" 2^>nul ^| find "PORT="') do set BACKEND_PORT=%%a
echo [config] backend port = %BACKEND_PORT%

REM ---- check docker ----
set HAS_DOCKER=0
docker ps 1>nul 2>nul && set HAS_DOCKER=1

REM ---- docker services ----
if %HAS_DOCKER%==0 goto skip_docker

echo.
echo === Docker Services ===

docker ps --format "{{.Names}}" 2>nul | find "chromadb" 1>nul
if errorlevel 1 (
    echo [docker] starting chromadb on port 8001 ...
    docker rm -f chromadb 1>nul 2>nul
    docker run -d --name chromadb -p 8001:8000 -v "%cd%\backend\data\chroma_db:/chroma/chroma" -e IS_PERSISTENT=TRUE -e ANONYMIZED_TELEMETRY=FALSE --restart unless-stopped chromadb/chroma:latest 1>nul 2>nul
    if errorlevel 1 (echo [warn] chromadb failed) else (echo [ ok ] chromadb started)
) else (
    echo [skip] chromadb already running
)

docker ps --format "{{.Names}}" 2>nul | find "math-redis" 1>nul
if errorlevel 1 (
    echo [docker] starting redis on port 6379 ...
    docker rm -f math-redis 1>nul 2>nul
    docker run -d --name math-redis -p 6379:6379 --restart unless-stopped redis:7-alpine 1>nul 2>nul
    if errorlevel 1 (echo [warn] redis failed) else (echo [ ok ] redis started)
) else (
    echo [skip] redis already running
)

REM ---- sandbox image ----
echo.
echo === Docker Sandbox ===
docker images -q mathmodel-sandbox 1>nul 2>nul
if errorlevel 1 (
    echo [build] building sandbox image, first run takes ~2min ...
    docker build -t mathmodel-sandbox -f "%~dp0backend\Dockerfile.sandbox" "%~dp0backend" 1>nul 2>nul
    if errorlevel 1 (echo [warn] sandbox build failed) else (echo [ ok ] sandbox ready)
) else (
    echo [skip] sandbox image exists
)

:skip_docker
if %HAS_DOCKER%==0 echo [info] Docker not available, using local/fakeredis mode

REM ---- backend ----
echo.
echo === Backend ===
netstat -ano 2>nul | find ":%BACKEND_PORT%" | find "LISTENING" 1>nul
if errorlevel 1 (
    echo [start] backend http://127.0.0.1:%BACKEND_PORT%
    start "math_backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT% --workers 1 --limit-concurrency 4 --timeout-keep-alive 30"
) else (
    echo [skip] backend already running on %BACKEND_PORT%
)

REM ---- frontend ----
echo.
echo === Frontend ===
netstat -ano 2>nul | find ":5174" | find "LISTENING" 1>nul
if errorlevel 1 (
    echo [start] frontend http://localhost:5174
    start "math_frontend" cmd /k "cd /d %~dp0frontend && pnpm dev"
) else (
    echo [skip] frontend already running on 5174
)

echo.
echo ============================================
echo   All services starting...
echo   Frontend : http://localhost:5174
echo   API docs : http://127.0.0.1:%BACKEND_PORT%/docs
echo ============================================

pause
