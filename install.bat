@echo off
REM ============================================================
REM  MathModelAgent one-click installer - entry point
REM
REM  This file must stay pure ASCII (no Chinese text) and must
REM  keep NOTHING after the "python install.py" call but exit+EOF.
REM  Two cmd.exe traps this guards against:
REM  1) cmd reads batch files byte-wise; multibyte text can be
REM     split mid-character inside its read buffer and the stray
REM     fragment is executed as a command (random "'xxx' is not
REM     recognized" errors).
REM  2) after a child python runs, cmd can resume reading this
REM     batch from a corrupted file position (lines get skipped,
REM     a "pause" far below can run instead). With only exit+EOF
REM     after the python call there is nothing left to misfire,
REM     and the process exit code still equals python's.
REM  Error labels sit BEFORE the python call in file order, so a
REM  forward-straying read position can never land on them.
REM ============================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 goto no_python
python -c "import sys;print(sys.version)" >nul 2>nul
if errorlevel 1 goto no_python
if not exist "%~dp0install.py" goto no_installer
goto run_install

:no_python
echo [ERROR] Python not found. Please install Python 3.11+ from:
echo         https://www.python.org/downloads/
echo         and check "Add python.exe to PATH" during setup.
set /p "=Press Enter to exit . . . "
exit /b 1

:no_installer
echo [ERROR] install.py is missing - the download is incomplete.
echo         Please re-download the full project and retry.
set /p "=Press Enter to exit . . . "
exit /b 1

:run_install
python "%~dp0install.py" %*
exit /b %errorlevel%
