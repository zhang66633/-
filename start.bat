@echo off
title MathModelAgent
cd /d "%~dp0"

echo.
echo ============================================
echo   MathModelAgent
echo ============================================
echo.
echo [start] backend ...
start "backend" cmd /c "cd /d %~dp0backend && uvicorn app.main:app --host 127.0.0.1 --port 8002 --workers 1 --limit-concurrency 4 --timeout-keep-alive 30 && pause"

echo [start] frontend ...
start "frontend" cmd /c "cd /d %~dp0frontend && pnpm dev && pause"

echo.
echo ============================================
echo   Frontend : http://localhost:5174
echo   API docs : http://127.0.0.1:8002/docs
echo ============================================
echo.
echo [tip] 首次启动后端会自动重建向量索引(93篇)
echo [tip] Docker: docker compose up -d chromadb redis
echo.
pause
