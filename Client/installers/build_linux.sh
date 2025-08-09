#!/bin/bash
pyinstaller --onefile --add-data="cert.pem:." --hidden-import=requests --hidden-import=psutil --hidden-import=uuid system_utility.py
cp dist/system_utility .
rm -rf build dist system_utility.spec
fpm -s dir -t deb -n system-monitor -v 1.0.0 --config-files /etc/systemd/system/system-monitor.service system_utility=/usr/bin/ /etc/systemd/system/system-monitor.service
rm system_utility