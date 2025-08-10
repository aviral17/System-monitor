# System Monitor Dashboard

A real-time system monitoring dashboard with backend API, frontend UI, and cross-platform client agents.

## Project Structure
project/
├── Backend/ # Flask server (Python 3.12)
├── Frontend/ # React application
└── client/
└── installers/ # Agent installers for all platforms


## Prerequisites

- **Python 3.12** (64-bit)
- **Node.js** (v22.18.0)
- **Pip** (Python package manager)
- **npm** (Node package manager)

## Setup Instructions



```bash
1. Backend Setup

cd Backend
pip install -r requirements.txt
uvicorn main:python app.py```

2. Frontend Setup
cd Frontend
npm install
npm run dev

--METHOD A--

### INSTALLATION VIA PACKAGES created in respective folders in ROOT Project as Linux_installer, Windows_installer and MacOS_installer ###########
(Windows Installation)
Extract the Windows zip package

--> Right-click install.bat > Run as administrator


(Linux Installation)
tar -xzf SystemMonitor-1.0.0-linux.tar.gz
cd SystemMonitor
sudo ./install.sh


(macOS Installation)
unzip SystemMonitor-1.0.0-macos.zip
cd SystemMonitor
sudo ./install.sh

METHOD B

### MANUAL INSTALLATION VIA CLIENT FOLDER CODE ###########
3. Client Agent Installation
Build and distribute these agents to machines you want to monitor:

For (Windows) Machines:
cd client/installers
.\build_windows.ps1


For (Linux) Machines:
cd client/installers
chmod +x build_linux.sh
./build_linux.sh

For (macOS) Machines:
cd client/installers
chmod +x build_macos.sh
./build_macos.sh


##################################################

Using the Dashboard
Start Backend: python app.py

Start Frontend: npm run dev

Access dashboard at: http://localhost:5173

OPTIONALLY if you want to run Client for testing purposes ------>
cd Client ---> python system_utility.py 

Install agents on target machines (Via METHOD A or METHOD B)
Machines will appear in dashboard within 30 seconds

## Managing Background Agents
To Stop All Monitoring Agents:

# Windows (Admin CMD):
taskkill /F /IM python.exe

# Linux/macOS:
sudo pkill -f system_utility.py

--------------------------------

To Uninstall Agents:
# Windows: Run uninstall.bat as Admin
# Linux: sudo ./uninstall.sh
# macOS: sudo ./uninstall.sh

------------------------------------------------

## Troubleshooting
Common Issues:
Agent not appearing in dashboard:

Check backend is running: http://localhost:5000/health

Verify firewall allows traffic on port 5000

Check agent logs:

Windows: Task Scheduler > SystemMonitor

Linux: journalctl -u systemmonitor

macOS: /var/log/systemmonitor.out.log

---> Permission denied during build:

sudo chown -R $USER:$USER client/installers/dist/
sudo chmod -R 755 client/installers/dist/
rm -rf client/installers/dist/
