import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import sys
import os

class SystemMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SystemMonitorService"
    _svc_display_name_ = "System Monitor Service"
    
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
        script_path = os.path.join(os.path.dirname(__file__), "system_utility.py")
        subprocess.call([sys.executable, script_path])

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SystemMonitorService)