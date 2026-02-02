@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1

echo [1/3] Cleaning up old processes...
REM Kill processes by Window Title or Image Name if they are related
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Teplo*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul

REM Kill processes by Command Line match using WMIC (Matches project path)
wmic process where "name='python.exe' and commandline like '%EasyCamp-Teplo%'" call terminate >nul 2>nul

echo.
echo [2/3] Checking environment...
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup_env.bat first.
    pause
    exit /b
)

echo.
echo [3/3] Starting Teplo Bot...
echo Press Ctrl+C to stop.
echo.

REM Activate venv
call venv\Scripts\activate

REM Run bot
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
