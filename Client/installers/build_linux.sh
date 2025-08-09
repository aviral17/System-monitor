#!/bin/bash
pip install pyinstaller
pip install -r requirements.txt
pyinstaller --onefile --add-data "requirements.txt:." --hidden-import=psutil system_utility.py
mv dist/system_utility .
rm -rf build dist
echo "Build complete! Executable: system_utility"