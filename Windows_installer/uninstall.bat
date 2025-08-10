@echo off
setlocal

fltmc >nul 2>&1 || (
    powershell -Command "Start-Process cmd -ArgumentList '/c','""%~f0""' -Verb RunAs"
    exit /b
)

REM Stop and delete scheduled task
schtasks /Query /TN "SystemMonitor" >nul 2>&1 && schtasks /Delete /TN "SystemMonitor" /F >nul 2>&1

REM Kill running copy (best-effort)
for /f "tokens=2 delims=," %%p in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /I "system_utility.py"') do (
  taskkill /PID %%~p /F >nul 2>&1
)

REM Remove installed files
rmdir /s /q "%ProgramData%\SystemMonitor" >nul 2>&1

echo Uninstalled scheduled task and removed files.
pause
