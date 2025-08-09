#!/bin/bash
pyinstaller --onefile --add-data="cert.pem:." --hidden-import=requests --hidden-import=psutil --hidden-import=uuid system_utility.py
hdiutil create -fs HFS+ -srcfolder dist/system_utility -volname "SystemMonitor" system-monitor.dmg
rm -rf build dist system_utility.spec