@echo off
title MathModelAgent
cd /d %~dp0

echo.
echo ============================================
echo   MathModelAgent - One-Click Start
echo ============================================
echo.

REM ---- read backend port from .env ----
set "BACKEND_PORT=8000"
for /f "tokens=2 delims==" %%a in ('type backend\.env 2^>nul ^| find "PORT="') do set "BACKEND_PORT=%%a"
echo [config] backend port = %BACKEND_PORT%

REM ---- check if Docker is available ----
set "HAS_DOCKER=0"
docker ps >nul 2>&1 && set "HAS_DOCKER=1"

REM ---- Docker services ----
if %HAS_DOCKER% equ 1 (
    echo.
    echo === Docker Services ===

    docker ps --format "{{.Names}}" 2>nul | find "chromadb" >nul
    if errorlevel 1 (
        echo [docker] starting chromadb on :8001 ...
        docker rm -f chromadb >nul 2>&1
        docker run -d --name chromadb -p 8001:8000 -v "%cd%\backend\data\chroma_db:/chroma/chroma" -e IS_PERSISTENT=TRUE -e ANONYMIZED_TELEMETRY=FALSE --restart unless-stopped chromadb/chroma:latest >nul 2>&1
        if errorlevel 1 (echo [warn] chromadb failed) else (echo [ ok ] chromadb started)
    ) else (
        echo [skip] chromadb already running
    )

    docker ps --format "{{.Names}}" 2>nul | find "math-redis" >nul
    if errorlevel 1 (
        echo [docker] starting redis on :6379 ...
        docker rm -f math-redis >nul 2>&1
        docker run -d --name math-redis -p 6379:6379 --restart unless-stopped redis:7-alpine >nul 2>&1
        if errorlevel 1 (echo [warn] redis failed) else (echo [ ok ] redis started)
    ) else (
        echo [skip] redis already running
    )
) else (
    echo [info] Docker not available - ChromaDB/Redis use local/fakeredis mode
)

REM ---- Docker sandbox image (lazy build on first run) ----
if %HAS_DOCKER% equ 1 (
    echo.
    echo === Docker Sandbox Image ===
    docker images -q mathmodel-sandbox >nul 2>&1
    if errorlevel 1 (
        echo [build] mathmodel-sandbox image (first run, takes ~2min) ...
        docker build -t mathmodel-sandbox -f "%~dp0backend\Dockerfile.sandbox" "%~dp0backend" >nul 2>&1
        if errorlevel 1 (echo [warn] sandbox image build failed - will use subprocess) else (echo [ ok ] sandbox image ready)
    ) else (
        echo [skip] sandbox image already exists
    )
)

REM ---- Backend ----
echo.
echo === Backend ===
netstat -ano 2>nul | find ":%BACKEND_PORT%" | find "LISTENING" >nul
if errorlevel 1 (
    echo [start] backend on http://127.0.0.1:%BACKEND_PORT%
    start "math_backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT% --workers 1 --limit-concurrency 4 --timeout-keep-alive 30"
) else (
    echo [skip] backend already running on %BACKEND_PORT%
)

REM ---- Frontend ----
echo.
echo === Frontend ===
netstat -ano 2>nul | find ":5174" | find "LISTENING" >nul
if errorlevel 1 (
    echo [start] frontend on http://localhost:5174
    start "math_frontend" cmd /k "cd /d %~dp0frontend && pnpm dev"
) else (
    echo [skip] frontend already running on 5174
)

echo.
echo ============================================
echo   All services started!
echo   Frontend : http://localhost:5174
echo   API docs : http://127.0.0.1:%BACKEND_PORT%/docs
echo ============================================

timeout /t 3 >nul
pause