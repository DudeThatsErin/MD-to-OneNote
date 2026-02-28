@echo off
setlocal

:: md-to-onenote - Windows one-click runner
:: Double-click this file or run it from a terminal.

set SCRIPT_DIR=%~dp0

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not on your PATH.
    echo Download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install dependencies if not already installed
echo Checking dependencies...
python -m pip install -r "%SCRIPT_DIR%requirements.txt" --quiet

:: Prompt for vault path if not provided
if "%~1"=="" (
    set /p VAULT="Enter the full path to your vault/backup folder: "
) else (
    set VAULT=%~1
)

:: Prompt for notebook name if not provided
if "%~2"=="" (
    set /p NOTEBOOK="Enter the OneNote notebook name to import into: "
) else (
    set NOTEBOOK=%~2
)

echo.
echo Starting import...
echo   Vault:    %VAULT%
echo   Notebook: %NOTEBOOK%
echo.

python "%SCRIPT_DIR%main.py" import --vault "%VAULT%" --notebook "%NOTEBOOK%"

echo.
pause
