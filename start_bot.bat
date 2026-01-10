@echo off
chcp 65001 >nul
echo Starting Teplo Bot...
echo Press Ctrl+C to stop.
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup_env.bat first.
    pause
    exit /b
)

REM Activate venv
call venv\Scripts\activate

REM Run bot
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
