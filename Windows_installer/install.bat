@echo off
setlocal

REM Elevate to admin if not already
fltmc >nul 2>&1 || (
    powershell -Command "Start-Process cmd -ArgumentList '/c','""%~f0""' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo Working... Please wait.

REM create program data dir if missing
if not exist "%ProgramData%\SystemMonitor" (
  mkdir "%ProgramData%\SystemMonitor"
)

REM copy files
xcopy "%~dp0*" "%ProgramData%\SystemMonitor\" /E /I /Y >nul

REM ensure Python exists
where python >nul 2>&1 || (
    echo Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

for /f "delims=" %%P in ('where python') do set "PYTHON_EXE=%%P"
set "SCRIPT_PATH=%ProgramData%\SystemMonitor\system_utility.py"

REM OPTIONAL: remove stored machine_id to create a fresh machine on reinstall
REM del /F /Q "%ProgramData%\SystemMonitor\machine_id" >nul 2>&1

REM Remove any old scheduled task or service leaving traces
schtasks /Query /TN "SystemMonitor" >nul 2>&1 && schtasks /Delete /TN "SystemMonitor" /F >nul 2>&1

REM Create scheduled task to run at logon with highest privileges
schtasks /Create /TN "SystemMonitor" /TR "\"%PYTHON_EXE%\" \"%SCRIPT_PATH%\"" /SC ONLOGON /RL HIGHEST /F

REM Run the task immediately once
schtasks /Run /TN "SystemMonitor" >nul 2>&1

REM Also launch it right now for the installer run (so user sees it start)
start "" "%PYTHON_EXE%" "%SCRIPT_PATH%"

echo Scheduled task + immediate run created.
echo Check Task Scheduler -> Task Scheduler Library -> SystemMonitor
pause
