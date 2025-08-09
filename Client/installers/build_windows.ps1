pyinstaller --onefile --add-data "cert.pem;." --hidden-import=requests --hidden-import=psutil --hidden-import=uuid system_utility.py
$serviceScript = @"
import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import subprocess

class SystemMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'SystemMonitor'
    _svc_display_name_ = 'System Health Monitor'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        subprocess.call(['dist\\system_utility.exe'])
"@
Set-Content -Path "service.py" -Value $serviceScript
pyinstaller --onefile service.py
Move-Item -Path dist\service.exe -Destination dist\system-monitor-service.exe
Remove-Item service.py