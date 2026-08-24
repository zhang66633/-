@echo off
REM ============================================================
REM  MathModelAgent one-click installer - entry point
REM
REM  IMPORTANT: this file must stay pure ASCII (no Chinese text).
REM  cmd.exe reads batch files byte-wise; multibyte text can be
REM  split mid-character inside cmd's internal read buffer, and
REM  the stray fragment is then executed as a command, causing
REM  random "'xxx' is not recognized" errors. All logic and
REM  Chinese output live in install.py (UTF-8, immune to cmd).
REM ============================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 goto no_python
python -c "import sys;print(sys.version)" >nul 2>nul
if errorlevel 1 goto no_python
if not exist "%~dp0install.py" goto no_installer

python "%~dp0install.py" %*
set "EC=%errorlevel%"
goto after_install

:no_python
echo [ERROR] Python not found. Please install Python 3.11+ from:
echo         https://www.python.org/downloads/
echo         and check "Add python.exe to PATH" during setup.
set "EC=1"
goto after_install

:no_installer
echo [ERROR] install.py is missing - the download is incomplete.
echo         Please re-download the full project and retry.
set "EC=1"

:after_install
if "%EC%"=="0" goto final_pause
echo.
echo [ERROR] Installation failed with exit code %EC%. See the messages above.
:final_pause
pause
exit /b %EC%
