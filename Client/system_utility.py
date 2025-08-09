import platform
import subprocess
import time
import json
import os
import uuid
import requests
import psutil
import getpass
import re
import tempfile
from pathlib import Path

# API_URL = "https://192.168.1.100:5000/api/report"
API_URL = "https://192.168.0.105:5000/api/report"
# API_URL = "https://127.0.0.1:5000/api/report"


def get_ssl_cert():
    cert_folder = Path(tempfile.gettempdir()) / "ssl_certificates"
    cert_folder.mkdir(exist_ok=True)
    cert_path = cert_folder / "backend-cert.pem"
    
    if not cert_path.exists():
        cert_url = API_URL.replace("/api/report", "/cert.pem")
        try:
            cert = requests.get(cert_url, verify=False, timeout=5).text
            cert_path.write_text(cert)
        except:
            return False
    return str(cert_path)


def get_machine_id():
    id_path = os.path.expanduser("~/.system_monitor_id")
    if os.path.exists(id_path):
        with open(id_path, "r") as f:
            return f.read().strip()
    new_id = str(uuid.uuid4())
    with open(id_path, "w") as f:
        f.write(new_id)
    return new_id

def get_system_info():
    return {
        "hostname": platform.node(),
        "os_platform": platform.system(),
        "os_version": platform.release(),
        "username": getpass.getuser(),
        "cpu_cores": psutil.cpu_count(logical=False),
        "memory_mb": int(psutil.virtual_memory().total / (1024 * 1024))
    }

def human_readable_size(num, decimals=2):
    if num is None:
        return "N/A"
    step = 1024.0
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB"]
    if num == 0:
        return "0 Bytes"
    i = 0
    while num >= step and i < len(units) - 1:
        num /= step
        i += 1
    return f"{num:.{decimals}f} {units[i]}"

def _linux_disk_type_map():
    try:
        res = subprocess.run(["lsblk", "-J", "-o", "NAME,MOUNTPOINT,ROTA,TYPE"], capture_output=True, text=True, timeout=5)
        if not res.stdout:
            return {}
        data = json.loads(res.stdout)
        mapping = {}
        def walk(nodes):
            for n in nodes:
                mp = n.get("mountpoint")
                rota = n.get("rota", None)
                if mp:
                    mapping[mp] = "HDD" if str(rota) == "1" else "SSD" if str(rota) == "0" else "unknown"
                if "children" in n and n["children"]:
                    walk(n["children"])
        if "blockdevices" in data:
            walk(data["blockdevices"])
        return mapping
    except Exception:
        return {}

def _windows_disk_type_map():
    try:
        ps_script = r'''
$results = @()
try {
  $disks = Get-Disk -ErrorAction SilentlyContinue
  foreach ($d in $disks) {
    $parts = @(Get-Partition -DiskNumber $d.Number -ErrorAction SilentlyContinue)
    foreach ($p in $parts) {
      $v = $null
      try { $v = Get-Volume -Partition $p -ErrorAction SilentlyContinue } catch { $v = $null }
      if ($v -and $v.DriveLetter) {
        $drive = ($v.DriveLetter + ':\')
        $type = 'unknown'
        try {
          if ($null -ne $d.IsSSD) {
            if ($d.IsSSD -eq $true) { $type = 'SSD' } elseif ($d.IsSSD -eq $false) { $type = 'HDD' }
          } elseif ($null -ne $d.MediaType) {
            if ($d.MediaType -match 'SSD') { $type = 'SSD' } elseif ($d.MediaType -match 'HDD') { $type = 'HDD' }
          } else {
            try {
              $pd = Get-PhysicalDisk -DiskNumber $d.Number -ErrorAction SilentlyContinue
              if ($pd -and $pd.MediaType -match 'SSD') { $type = 'SSD' }
              elseif ($pd -and $pd.MediaType -match 'HDD') { $type = 'HDD' }
            } catch {}
          }
        } catch {}
        $results += [PSCustomObject]@{ Drive = $drive; Type = $type }
      }
    }
  }
} catch {}
if ($results.Count -eq 0) {
  try {
    $drives = Get-WmiObject Win32_DiskDrive -ErrorAction SilentlyContinue
    foreach ($d in $drives) {
      $parts = @(Get-WmiObject -Query ("ASSOCIATORS OF {Win32_DiskDrive.DeviceID=`'" + $d.DeviceID + "`'} WHERE AssocClass=Win32_DiskDriveToDiskPartition") -ErrorAction SilentlyContinue)
      foreach ($p in $parts) {
        $logs = @(Get-WmiObject -Query ("ASSOCIATORS OF {Win32_DiskPartition.DeviceID=`'" + $p.DeviceID + "`'} WHERE AssocClass=Win32_LogicalDiskToPartition") -ErrorAction SilentlyContinue)
        foreach ($l in $logs) {
          if ($l.DeviceID) {
            $drive = $l.DeviceID + ':\'
            $type = 'unknown'
            if ($d.Model -and ($d.Model -match 'SSD' -or $d.Model -match 'NVMe' -or $d.InterfaceType -match 'PCI')) { $type = 'SSD' }
            elseif ($d.MediaType -and ($d.MediaType -match 'Fixed' -or $d.MediaType -match 'Hard')) { $type = 'HDD' }
            $results += [PSCustomObject]@{ Drive = $drive; Type = $type; Device = $d.DeviceID; Model = $d.Model }
          }
        }
      }
    }
  } catch {}
}
$results | Select-Object -Unique | ConvertTo-Json -Depth 5 -Compress
'''
        res = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_script], capture_output=True, text=True, timeout=8)
        out = res.stdout.strip()
        if not out:
            return {}
        first = None
        for ch in ('[','{'):
            idx = out.find(ch)
            if idx != -1:
                first = idx
                break
        if first is not None:
            out = out[first:]
        parsed = json.loads(out)
        mapping = {}
        if isinstance(parsed, list):
            for item in parsed:
                drive = item.get("Drive") or item.get("drive")
                typ = item.get("Type") or item.get("type") or "unknown"
                if drive:
                    dnorm = drive.upper()
                    if not dnorm.endswith("\\"):
                        dnorm = dnorm + "\\"
                    mapping[dnorm] = typ
        elif isinstance(parsed, dict):
            drive = parsed.get("Drive") or parsed.get("drive")
            typ = parsed.get("Type") or parsed.get("type") or "unknown"
            if drive:
                dnorm = drive.upper()
                if not dnorm.endswith("\\"):
                    dnorm = dnorm + "\\"
                mapping[dnorm] = typ
        return mapping
    except Exception:
        return {}

def detect_disk_type_for_mount(mountpoint):
    system = platform.system()
    
    if system == "Windows":
        try:
            # Get drive letter from mountpoint
            drive_letter = os.path.splitdrive(mountpoint)[0].upper()
            if not drive_letter:
                return "unknown"
            
            # Normalize drive letter to have a trailing backslash
            drive_letter = drive_letter + "\\"
            
            # Try to get disk type using PowerShell
            ps_script = f'''
            $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='{drive_letter}'" | 
                      Select-Object -ExpandProperty DeviceID
            if ($disk) {{
                $partition = Get-WmiObject -Class Win32_DiskPartition | 
                             Where-Object {{ $_.Bootable -eq $true }}
                if ($partition) {{
                    $diskDrive = Get-WmiObject -Class Win32_DiskDrive | 
                                 Where-Object {{ $_.Index -eq $partition.DiskIndex }}
                    if ($diskDrive) {{
                        if ($diskDrive.Model -like "*SSD*" -or $diskDrive.Model -like "*Solid State*") {{
                            "SSD"
                        }} elseif ($diskDrive.MediaType -like "*fixed*" -or $diskDrive.MediaType -like "*hard disk*") {{
                            "HDD"
                        }} else {{
                            # Try to determine by interface type
                            if ($diskDrive.InterfaceType -eq "SCSI" -or $diskDrive.InterfaceType -eq "NVMe") {{
                                "SSD"
                            }} else {{
                                "unknown"
                            }}
                        }}
                    }} else {{
                        "unknown"
                    }}
                }} else {{
                    "unknown"
                }}
            }} else {{
                "unknown"
            }}
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            disk_type = result.stdout.strip()
            if disk_type in ["SSD", "HDD"]:
                return disk_type
                
            # Fallback to previous method
            return _windows_disk_type_map().get(drive_letter, "unknown")
        except Exception:
            return "unknown"
    
    elif system == "Linux":
        try:
            # Get device path for mountpoint
            device_path = None
            for partition in psutil.disk_partitions(all=False):
                if partition.mountpoint == mountpoint:
                    device_path = partition.device
                    break
            
            if not device_path:
                return "unknown"
            
            # Get device name (e.g., sda, nvme0n1)
            device_name = os.path.basename(device_path)
            
            # Remove partition number if present (e.g., sda1 -> sda)
            if device_name[-1].isdigit():
                # Handle cases like nvme0n1p1 -> nvme0n1
                if 'nvme' in device_name:
                    device_name = re.sub(r'p\d+$', '', device_name)
                else:
                    device_name = re.sub(r'\d+$', '', device_name)
            
            # Check if device is rotational
            rotational_path = f"/sys/block/{device_name}/queue/rotational"
            if os.path.exists(rotational_path):
                with open(rotational_path, "r") as f:
                    rotational = f.read().strip()
                    if rotational == "0":
                        return "SSD"
                    elif rotational == "1":
                        return "HDD"
            
            
            model_path = f"/sys/block/{device_name}/device/model"
            if os.path.exists(model_path):
                with open(model_path, "r") as f:
                    model = f.read().strip().lower()
                    if "ssd" in model or "solid state" in model:
                        return "SSD"
            
            
            type_path = f"/sys/block/{device_name}/device/type"
            if os.path.exists(type_path):
                with open(type_path, "r") as f:
                    device_type = f.read().strip()
                    if device_type == "0":
                        return "SSD"
            
            
            return _linux_disk_type_map().get(mountpoint, "unknown")
        except Exception:
            return "unknown"
    
    elif system == "Darwin":  # macOS
        try:
            
            device_path = None
            for partition in psutil.disk_partitions(all=False):
                if partition.mountpoint == mountpoint:
                    device_path = partition.device
                    break
            
            if not device_path:
                return "unknown"
            
            
            result = subprocess.run(
                ["diskutil", "info", device_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            
            
            if "solid state" in output or "ssd" in output:
                return "SSD"
            
            
            if "rotational" in output or "hard disk" in output:
                return "HDD"
            
            
            if "device / media type:" in output:
                lines = output.split("\n")
                for line in lines:
                    if "device / media type:" in line:
                        if "ssd" in line:
                            return "SSD"
                        elif "hdd" in line or "rotational" in line:
                            return "HDD"
            
            return "unknown"
        except Exception:
            return "unknown"
    
    else:
        return "unknown"

def collect_disks():
    disks = []
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        mount = p.mountpoint
        try:
            usage = psutil.disk_usage(mount)
        except Exception:
            continue
        
        disk_type = detect_disk_type_for_mount(mount)
        
        disks.append({
            "device": p.device,
            "mountpoint": mount,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
            "type": disk_type,
            "total_human": human_readable_size(usage.total),
            "used_human": human_readable_size(usage.used),
            "free_human": human_readable_size(usage.free)
        })
    
    return disks

def check_disk_encryption():
    system = platform.system()
    try:
        if system == "Darwin":
            result = subprocess.run(["fdesetup", "status"], capture_output=True, text=True, timeout=5)
            return "FileVault is On" in result.stdout
        if system == "Windows":
            result = subprocess.run(["powershell", "-Command", "Get-BitLockerVolume -MountPoint C: | Select-Object -ExpandProperty ProtectionStatus"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=6)
            return "On" in result.stdout
        if system == "Linux":
            result = subprocess.run(["lsblk", "-f"], capture_output=True, text=True, timeout=5)
            return "crypt" in result.stdout
    except Exception:
        pass
    return False

def check_os_updates():
    system = platform.system()
    try:
        if system == "Darwin":
            result = subprocess.run(["softwareupdate", "-l"], capture_output=True, text=True, timeout=10)
            return "*" in result.stdout
        if system == "Windows":
            result = subprocess.run(["powershell", "-Command", "(Get-WindowsUpdate -IsInstalled:$false -IsHidden:$false).Count -gt 0"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=8)
            return "True" in result.stdout
        if system == "Linux":
            if os.path.exists("/etc/apt/sources.list"):
                subprocess.run(["sudo", "apt", "update"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                result = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True)
                return "upgradable" in result.stdout
            if os.path.exists("/etc/yum.conf"):
                result = subprocess.run(["yum", "check-update"], capture_output=True, text=True, stderr=subprocess.DEVNULL)
                return result.returncode == 100
    except Exception:
        pass
    return False

def check_antivirus():
    system = platform.system()
    try:
        if system == "Darwin":
            processes = [p.name() for p in psutil.process_iter()]
            av_processes = ["Sophos", "Bitdefender", "Avast", "Kaspersky", "Norton"]
            return any(av in " ".join(processes) for av in av_processes)
        if system == "Windows":
            result = subprocess.run(["powershell", "-Command", "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Where-Object {$_.productState -ne 0} | Measure-Object | Select-Object -ExpandProperty Count"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=6)
            try:
                return int(result.stdout.strip()) > 0
            except Exception:
                return False
        if system == "Linux":
            result = subprocess.run(["clamscan", "--version"], capture_output=True, text=True, timeout=6)
            return result.returncode == 0
    except Exception:
        pass
    return False

def check_sleep_settings():
    system = platform.system()
    try:
        if system == "Darwin":
            result = subprocess.run(["pmset", "-g"], capture_output=True, text=True, timeout=5)
            sleep_lines = [line for line in result.stdout.splitlines() if "sleep" in line]
            sleep_value = next((int(line.split()[1]) for line in sleep_lines if "sleep" in line), 0)
            return sleep_value <= 10
        if system == "Windows":
            result = subprocess.run(["powercfg", "/q"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=6)
            sleep_lines = [line for line in result.stdout.splitlines() if "Sleep After" in line and "AC Power Setting" in line]
            if sleep_lines:
                sleep_value = int(sleep_lines[0].split()[-1])
                return sleep_value <= 10 * 60
            return False
        if system == "Linux":
            try:
                result = subprocess.run(["gsettings", "get", "org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-timeout"], capture_output=True, text=True, timeout=5)
                if result.stdout.strip() == "":
                    return False
                sleep_value = int(result.stdout.strip().split()[0])
                return sleep_value <= 10
            except Exception:
                return False
    except Exception:
        pass
    return False

def get_system_metrics():
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }

def get_system_state():
    return {
        "os_name": platform.system(),
        "os_version": platform.release(),
        "machine_name": platform.node(),
        "disk_encryption": check_disk_encryption(),
        "os_updates": check_os_updates(),
        "antivirus": check_antivirus(),
        "sleep_settings": check_sleep_settings()
    }

# def main():
#     machine_id = get_machine_id()
#     system_info = get_system_info()

#     while True:        
#         try:
#             current_state = get_system_state()
#             metrics = get_system_metrics()
#             disks = collect_disks()
#             print(json.dumps({"disks": disks}, indent=2))
#             payload = {
#                 "machine_id": machine_id,
#                 "timestamp": int(time.time()),
#                 "system_info": system_info,
#                 "state": current_state,
#                 "metrics": { **metrics, "disks": disks },
#                 "raw": json.dumps({"state": current_state, "metrics": metrics, "disks": disks})
#             }
#             try:
#                 response = requests.post(API_URL, json=payload, timeout=10)
#                 if response.status_code != 200:
#                     print("Server responded:", response.status_code, response.text)
#             except Exception as e:
#                 print("Error sending report:", str(e))
#         except Exception as e:
#             print("Error:", str(e))
#         time.sleep(60)


# def main():
#     machine_id = get_machine_id()
#     system_info = get_system_info()
#     last_state = None
#     last_metrics = None
#     last_disks = None
    
#     while True:
#         try:
#             current_state = get_system_state()
#             current_metrics = get_system_metrics()
#             current_disks = collect_disks()
            
#             if (current_state != last_state or 
#                 current_metrics != last_metrics or 
#                 json.dumps(current_disks) != json.dumps(last_disks)):
                
#                 payload = {
#                     "machine_id": machine_id,
#                     "timestamp": int(time.time()),
#                     "system_info": system_info,
#                     "state": current_state,
#                     "metrics": { **current_metrics, "disks": current_disks },
#                     "raw": json.dumps({"state": current_state, "metrics": current_metrics, "disks": current_disks})
#                 }
                
#                 try:
#                     cert_path = get_ssl_cert()
#                     verify = cert_path if cert_path else False
#                     response = requests.post(API_URL, json=payload, timeout=10, verify=verify)
#                     if response.status_code != 200:
#                         print("Server responded:", response.status_code, response.text)
#                 except Exception as e:
#                     print("Error sending report:", str(e))
                
#                 last_state = current_state
#                 last_metrics = current_metrics
#                 last_disks = current_disks
            
#         except Exception as e:
#             print("Error:", str(e))
#         time.sleep(900)


def main():
    machine_id = get_machine_id()
    system_info = get_system_info()
    last_state = None
    last_metrics = None
    last_disks = None
    
    while True:
        try:
            current_state = get_system_state()
            current_metrics = get_system_metrics()
            current_disks = collect_disks()
            
            if (current_state != last_state or 
                current_metrics != last_metrics or 
                json.dumps(current_disks) != json.dumps(last_disks)):
                
                payload = {
                    "machine_id": machine_id,
                    "timestamp": int(time.time()),
                    "system_info": system_info,
                    "state": current_state,
                    "metrics": { **current_metrics, "disks": current_disks },
                    "raw": json.dumps({"state": current_state, "metrics": current_metrics, "disks": current_disks})
                }
                
                try:
                    cert_path = get_ssl_cert()
                    verify = cert_path if cert_path else False
                    session = requests.Session()
                    session.verify = verify
                    response = session.post(API_URL, json=payload, timeout=10)
                    if response.status_code != 200:
                        print("Server responded:", response.status_code, response.text)
                except requests.exceptions.SSLError:
                    response = requests.post(API_URL, json=payload, timeout=10, verify=False)
                    if response.status_code != 200:
                        print("Server responded:", response.status_code, response.text)
                except Exception as e:
                    print("Error sending report:", str(e))
                
                last_state = current_state
                last_metrics = current_metrics
                last_disks = current_disks
            
        except Exception as e:
            print("Error:", str(e))
        time.sleep(900)

if __name__ == '__main__':
    main()

