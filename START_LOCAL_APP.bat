@echo off
title Tamil Ilakkiya AI - Local Server
echo ========================================================
echo   Tamil Ilakkiya AI (தமிழ் செவ்விலக்கிய ஆய்வு)
echo   Local Continuous Server Launcher
echo ========================================================
echo.

cd /d "%~dp0"

:: Check if server is already running on port 8000
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Backend server is already ACTIVE on port 8000.
) else (
    echo [*] Starting FastAPI Uvicorn Server on 0.0.0.0:8000...
    start /B python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
    timeout /t 3 /nobreak >nul
)

echo [*] Opening application in your default browser...
start http://localhost:8000

echo.
echo ========================================================
echo   App is always open and available for local use:
echo   - Local PC URL:  http://localhost:8000
echo   - LAN Wi-Fi URL: http://192.168.14.216:8000
echo ========================================================
echo.
pause
