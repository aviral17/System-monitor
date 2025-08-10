$APP_NAME = "SystemMonitor"
$VERSION = "1.0.0"
$OUTPUT_DIR = "dist"
$INSTALL_DIR = $APP_NAME

Remove-Item -Path $OUTPUT_DIR -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $OUTPUT_DIR | Out-Null
$installPath = Join-Path -Path $OUTPUT_DIR -ChildPath $INSTALL_DIR
New-Item -ItemType Directory -Path $installPath | Out-Null

Copy-Item "..\system_utility.py" -Destination $installPath

$installScript = @'
@echo off
setlocal

fltmc >nul 2>&1 || (
    powershell -Command "Start-Process cmd -ArgumentList '/c','""%~f0""' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

where python >nul || (
    echo Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

for /f "delims=" %%P in ('where python') do set "PYTHON_EXE=%%P"

sc query SystemMonitorService >nul 2>&1 && (
    sc stop SystemMonitorService
    timeout /t 3 >nul
    sc delete SystemMonitorService
    timeout /t 2 >nul
)

sc create SystemMonitorService binPath= "cmd /c start /b \"\" \"%PYTHON_EXE%\" \"%~dp0system_utility.py\" --service" start= auto

sc start SystemMonitorService

echo Service installed! Check services.msc to verify status
pause
'@

Set-Content -Path (Join-Path -Path $installPath -ChildPath "install.bat") -Value $installScript

$uninstallScript = @'
@echo off
setlocal

fltmc >nul 2>&1 || (
    powershell -Command "Start-Process cmd -ArgumentList '/c','""%~f0""' -Verb RunAs"
    exit /b
)

sc stop SystemMonitorService
timeout /t 3 >nul
sc delete SystemMonitorService

rmdir /s /q "%ProgramData%\SystemMonitor" >nul 2>&1

echo Service completely removed!
pause
'@

Set-Content -Path (Join-Path -Path $installPath -ChildPath "uninstall.bat") -Value $uninstallScript

Compress-Archive -Path "$installPath\*" -DestinationPath "$OUTPUT_DIR\$APP_NAME-$VERSION.zip" -Force
Write-Host "Installer created: $OUTPUT_DIR\$APP_NAME-$VERSION.zip"