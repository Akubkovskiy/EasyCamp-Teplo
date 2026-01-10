@echo off
chcp 65001 >nul
echo ==========================================
echo    Teplo Bot - Environment Setup
echo ==========================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org
    pause
    exit /b
)

REM 2. Create Virtual Environment
if not exist "venv" (
    echo [INFO] Creating virtual environment venv...
    python -m venv venv
) else (
    echo [INFO] Virtual environment already exists.
)

REM 3. Activate and Install
echo [INFO] Activating venv...
call venv\Scripts\activate

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing requirements...
pip install -r requirements.txt

REM 4. Check .env
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env
        echo [WARNING] Please edit .env file and add your tokens!
    )
)

echo.
echo ==========================================
echo    Setup Complete!
echo ==========================================
echo.
echo To run the bot, type: start_bot.bat
echo.
pause
