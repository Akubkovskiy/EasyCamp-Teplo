@echo off
chcp 65001 >nul
echo Stopping Teplo Bot...

REM Kill processes by Window Title
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Teplo*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul

REM Kill processes by Command Line match
wmic process where "name='python.exe' and commandline like '%EasyCamp-Teplo%'" call terminate >nul 2>nul

echo.
echo Bot stopped.
pause
