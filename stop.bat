@echo off
title Stopping MathModelAgent
cd /d %~dp0

echo === Stopping MathModelAgent ===

REM ---- read backend port ----
set "BACKEND_PORT=8000"
for /f "tokens=2 delims==" %%a in ('type backend\.env 2^>nul ^| find "PORT="') do set "BACKEND_PORT=%%a"

REM ---- kill backend ----
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| find ":%BACKEND_PORT%" ^| find "LISTENING"') do (
    echo [stop] backend PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM ---- kill frontend ----
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| find ":5174" ^| find "LISTENING"') do (
    echo [stop] frontend PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM ---- stop docker containers ----
docker ps --format "{{.Names}}" 2>nul | find "chromadb" >nul
if not errorlevel 1 (
    echo [stop] chromadb container
    docker stop chromadb >nul 2>&1
    docker rm chromadb >nul 2>&1
)

docker ps --format "{{.Names}}" 2>nul | find "math-redis" >nul
if not errorlevel 1 (
    echo [stop] redis container
    docker stop math-redis >nul 2>&1
    docker rm math-redis >nul 2>&1
)

echo All stopped.
timeout /t 3 >nul
exit