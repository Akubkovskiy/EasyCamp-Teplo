@echo off
chcp 65001 >nul
echo Stopping Teplo Bot...
echo.

REM Kill uvicorn processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul

REM Alternative: kill all Python processes running uvicorn
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID:"') do (
    netstat -ano | find "8000" | find "%%a" >nul
    if not errorlevel 1 (
        echo Killing process %%a on port 8000...
        taskkill /F /PID %%a
    )
)

echo.
echo Bot stopped.
pause
