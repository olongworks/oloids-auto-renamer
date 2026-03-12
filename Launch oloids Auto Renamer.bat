@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%cd%\src"
set "APP_PYTHON=%cd%\.venv\Scripts\pythonw.exe"
if not exist "%APP_PYTHON%" (
  echo Virtual environment not found. Please recreate .venv first.
  pause
  exit /b 1
)
start "oloids Auto Renamer" /D "%cd%" "%APP_PYTHON%" -m oloids_auto_renamer
exit /b 0
