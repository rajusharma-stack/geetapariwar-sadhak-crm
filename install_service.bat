@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

set "TASK_NAME=GeetaPariwarCRM-Server"
set "SCRIPT_PATH=%~dp0start_server_daemon.ps1"

if /I "%1"=="--uninstall" goto uninstall
if /I "%1"=="/?" goto help

echo ============================================
echo  Geeta Pariwar CRM - Auto-start Installer
echo ============================================
echo.
echo This will register the server to start at Windows logon.
echo.

:: Check admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Re-running as administrator...
    powershell -NoProfile -Command "Start-Process '%~f0' -Verb RunAs -ArgumentList '--elevated'"
    exit /b 0
)

:install
echo Registering scheduled task "%TASK_NAME%"...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"%SCRIPT_PATH:\=\\%\"' -WorkingDirectory '%~dp0';" ^
"$trigger = New-ScheduledTaskTrigger -AtLogon;" ^
"$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 999 -Hidden;" ^
"$principal = New-ScheduledTaskPrincipal -UserId '%USERDOMAIN%\%USERNAME%' -LogonType Interactive -RunLevel Limited;" ^
"Register-ScheduledTask -TaskName '%TASK_NAME%' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null"

if %errorlevel% equ 0 (
    echo SUCCESS: Scheduled task registered.
    echo The server will start automatically next time you log in.
    echo.
    echo To uninstall later, run: %~nx0 --uninstall
) else (
    echo FAILED: Could not register scheduled task.
    echo Try running as Administrator.
)
echo.
pause
goto :eof

:uninstall
echo Removing scheduled task "%TASK_NAME%"...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo SUCCESS: Scheduled task removed.
) else (
    echo Task "%TASK_NAME%" not found or already removed.
)
echo.
pause
goto :eof

:help
echo Usage: %~nx0 [--uninstall]
echo.
echo   (no args)    Register the CRM server to auto-start at logon
echo   --uninstall  Remove the auto-start registration
echo.
pause
goto :eof
