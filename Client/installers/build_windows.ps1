pip install pyinstaller
pip install -r requirements.txt
pyinstaller --onefile --add-data "requirements.txt;." --hidden-import=psutil --console system_utility.py
Move-Item dist\system_utility.exe .\
Remove-Item -Recurse -Force build, dist
Write-Host "Build complete! Executable: system_utility.exe"