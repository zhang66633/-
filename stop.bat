@echo off
REM MathModelAgent one-click stop: kill backend (8001) and frontend (5173)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr "LISTENING"') do (
  echo [stop] backend PID %%a
  taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
  echo [stop] frontend PID %%a
  taskkill /PID %%a /F >nul 2>&1
)
echo Stopped.
ping -n 3 127.0.0.1 >nul
