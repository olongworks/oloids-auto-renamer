@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%cd%\src"
set "APP_PYTHON=%cd%\.venv\Scripts\python.exe"
if not exist "%APP_PYTHON%" (
  echo Virtual environment not found. Please recreate .venv first.
  pause
  exit /b 1
)
"%APP_PYTHON%" -m oloids_auto_renamer
pause
