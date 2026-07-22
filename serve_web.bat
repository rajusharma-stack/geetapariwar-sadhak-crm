@echo off
title Geeta Pariwar CRM - Web Server
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo ============================================
echo  Geeta Pariwar Nepal Sadhak CRM
echo  Web Server Mode
echo ============================================
echo.

:: Check .venv exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

:: Kill any previous instances
taskkill /f /im ngrok.exe > nul 2>&1
powershell -NoProfile -Command "netstat -ano | Select-String ':3201' | ForEach-Object { $pid = $_ -replace '.*\s+(\d+)$', '$1'; Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue }" > nul 2>&1

:: Clean stale web lock
powershell -NoProfile -Command "Remove-Item \"$env:TEMP\geetapariwar_web.lock\" -Force -ErrorAction SilentlyContinue" > nul 2>&1

:: ── Step 1: Start web server first ────────────
echo [1/3] Starting web server on port 3201...
start /B "" .venv\Scripts\python.exe -c "from waitress import serve; from app import app; serve(app, host='0.0.0.0', port=3201)" > server.log 2>&1

:: Wait for port 3201 to be open (up to 15 seconds)
echo       Waiting for server (up to 15s)...
set WAIT_COUNT=0
:wait_port
powershell -NoProfile -Command "$c = New-Object System.Net.Sockets.TcpClient; try { $c.Connect('127.0.0.1', 3201); $c.Close(); exit 0 } catch { exit 1 }" > nul 2>&1
if not errorlevel 1 goto port_ready
set /a WAIT_COUNT+=1
if %WAIT_COUNT% geq 15 (
    echo ERROR: Web server failed to start. Check server.log
    echo.
    type server.log 2>nul
    pause
    exit /b 1
)
timeout /t 1 /nobreak > nul
goto wait_port
:port_ready
echo       Web server is ready.
echo.

:: ── Step 2: Start ngrok tunnel ──────────────────
echo [2/3] Starting ngrok tunnel to port 3201...
start /B "" ngrok http 3201 --log=stdout > ngrok.log 2>&1

:: Wait for ngrok to initialize
echo       Waiting for ngrok to connect...
timeout /t 5 /nobreak > nul

:: ── Step 3: Get public URL from ngrok API ──────
echo [3/3] Fetching public URL...
set NGROK_URL=
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels' -ErrorAction Stop; $url = $r.tunnels[0].public_url; if ($url) { Write-Output $url } else { Write-Output 'ERROR' } } catch { Write-Output 'ERROR' }"`) do set NGROK_URL=%%i

if "!NGROK_URL!"=="ERROR" (
    echo WARNING: Could not fetch ngrok URL. Check ngrok.log
    echo.
    set NGROK_URL=http://localhost:3201
)

echo.
echo ============================================
echo   SHARE THIS LINK WITH ANYONE:
echo.
echo     !NGROK_URL!
echo.
echo ============================================
echo   Local access: http://localhost:3201
echo   Press Ctrl+C to stop
echo ============================================
echo.

echo.
echo ============================================
echo   Watchdog active - checking every 15s
echo   Press Ctrl+C to stop everything
echo ============================================

:watchdog
timeout /t 15 /nobreak > nul

:: ── Check web server on port 3201 ──────────────
powershell -NoProfile -Command "$c = New-Object System.Net.Sockets.TcpClient; try { $c.Connect('127.0.0.1', 3201); $c.Close(); exit 0 } catch { exit 1 }" > nul 2>&1
if errorlevel 1 (
    echo [WATCHDOG] Web server down - restarting...
    start /B "" .venv\Scripts\python.exe -c "from waitress import serve; from app import app; serve(app, host='0.0.0.0', port=3201)" > server.log 2>&1
    timeout /t 3 /nobreak > nul
)

:: ── Check ngrok process ────────────────────────
tasklist /fi "imagename eq ngrok.exe" 2>nul | find /i "ngrok.exe" > nul
if errorlevel 1 (
    echo [WATCHDOG] ngrok died - restarting...
    start /B "" ngrok http 3201 --log=stdout > ngrok.log 2>&1
    timeout /t 5 /nobreak > nul
    goto fetch_url
)

:: ── Check ngrok API is responsive ──────────────
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels' -ErrorAction Stop; if ($r.tunnels.Count -eq 0) { exit 1 } exit 0 } catch { exit 1 }" > nul 2>&1
if errorlevel 1 (
    echo [WATCHDOG] ngrok tunnel lost - restarting...
    taskkill /f /im ngrok.exe > nul 2>&1
    start /B "" ngrok http 3201 --log=stdout > ngrok.log 2>&1
    timeout /t 5 /nobreak > nul
    goto fetch_url
)

goto watchdog

:: ── Fetch and display current URL ──────────────
:fetch_url
set NGROK_URL=
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels' -ErrorAction Stop; $url = $r.tunnels[0].public_url; if ($url) { Write-Output $url } else { Write-Output 'ERROR' } } catch { Write-Output 'ERROR' }"`) do set NGROK_URL=%%i

if "!NGROK_URL!"=="ERROR" (
    echo [WATCHDOG] Could not get new URL yet
) else (
    echo.
    echo ============================================
    echo   NEW TUNNEL URL:
    echo     !NGROK_URL!
    echo ============================================
)
goto watchdog
