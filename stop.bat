@echo off
title Stopping MathModelAgent
cd /d "%~dp0"

echo Stopping MathModelAgent...

for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| find ":8002" ^| find "LISTENING"') do (
    echo [stop] backend PID %%a
    taskkill /PID %%a /F 2>nul
)

for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| find ":5174" ^| find "LISTENING"') do (
    echo [stop] frontend PID %%a
    taskkill /PID %%a /F 2>nul
)

docker stop chromadb 2>nul
docker stop math-redis 2>nul

echo Done.
pause
