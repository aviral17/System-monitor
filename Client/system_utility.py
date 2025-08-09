# import platform
# import subprocess
# import time
# import json
# import os
# import uuid
# import requests
# import psutil
# import getpass

# API_URL = "http://localhost:5000/api/report"

# def get_machine_id():
#     id_path = os.path.expanduser("~/.system_monitor_id")
#     if os.path.exists(id_path):
#         with open(id_path, "r") as f:
#             return f.read().strip()
#     else:
#         new_id = str(uuid.uuid4())
#         with open(id_path, "w") as f:
#             f.write(new_id)
#         return new_id

# def get_system_info():
#     return {
#         "hostname": platform.node(),
#         "os_platform": platform.system(),
#         "os_version": platform.release(),
#         "username": getpass.getuser(),
#         "cpu_cores": psutil.cpu_count(logical=False),
#         "memory_mb": int(psutil.virtual_memory().total / (1024 * 1024))
#     }

# def get_disk_info():
#     disks = []
#     for partition in psutil.disk_partitions(all=False):
#         if partition.mountpoint:
#             try:
#                 usage = psutil.disk_usage(partition.mountpoint)
#                 disk_type = "Unknown"
                
                
#                 if platform.system() == "Windows":
#                     try:
                        
#                         cmd = f"""wmic logicaldisk where "DeviceID='{partition.device.split(':')[0]}:'" 
#                                  get DeviceID, Size, FreeSpace /format:list"""
#                         result = subprocess.run(
#                             ["powershell", "-Command", cmd],
#                             capture_output=True, 
#                             text=True, 
#                             creationflags=subprocess.CREATE_NO_WINDOW
#                         )
#                         output = result.stdout
                        
                        
#                         if "SSD" in output or "Solid State" in output:
#                             disk_type = "SSD"
#                         elif "HDD" in output or "Hard Disk" in output:
#                             disk_type = "HDD"
#                         else:
#                             cmd = f"Get-PhysicalDisk | Where-Object {{ $_.DeviceID -eq {partition.device[-1]} }} | Select-Object MediaType"
#                             result = subprocess.run(
#                                 ["powershell", "-Command", cmd],
#                                 capture_output=True, 
#                                 text=True, 
#                                 creationflags=subprocess.CREATE_NO_WINDOW
#                             )
#                             if "SSD" in result.stdout:
#                                 disk_type = "SSD"
#                             elif "HDD" in result.stdout:
#                                 disk_type = "HDD"
#                     except:
#                         pass
                
#                 elif platform.system() in ["Linux", "Darwin"]:
#                     try:
#                         device = partition.device.split('/')[-1]
#                         if 'nvme' in device or 'ssd' in device:
#                             disk_type = "SSD"
#                         else:
#                             result = subprocess.run(
#                                 ["cat", f"/sys/block/{device[:3]}/queue/rotational"],
#                                 capture_output=True, 
#                                 text=True
#                             )
#                             disk_type = "SSD" if result.stdout.strip() == "0" else "HDD"
#                     except:
#                         pass
                
#                 disks.append({
#                     "mountpoint": partition.mountpoint,
#                     "device": partition.device,
#                     "total": usage.total,
#                     "used": usage.used,
#                     "free": usage.free,
#                     "percent": usage.percent,
#                     "type": disk_type
#                 })
#             except Exception as e:
#                 print(f"Error getting disk info for {partition.mountpoint}: {str(e)}")
#     return disks    

# def check_disk_encryption():
#     system = platform.system()
#     try:
#         if system == "Darwin":
#             result = subprocess.run(["fdesetup", "status"], capture_output=True, text=True)
#             return "FileVault is On" in result.stdout
#         elif system == "Windows":
#             result = subprocess.run(
#                 ["powershell", "-Command", "Get-BitLockerVolume -MountPoint C: | Select-Object -ExpandProperty ProtectionStatus"],
#                 capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
#             )
#             return "On" in result.stdout
#         elif system == "Linux":
#             result = subprocess.run(["lsblk", "-f"], capture_output=True, text=True)
#             return "crypt" in result.stdout
#     except Exception as e:
#         print(f"Disk encryption check error: {str(e)}")
#     return False

# def check_os_updates():
#     system = platform.system()
#     try:
#         if system == "Darwin":
#             result = subprocess.run(["softwareupdate", "-l"], capture_output=True, text=True)
#             return "*" in result.stdout
#         elif system == "Windows":
#             result = subprocess.run(
#                 ["powershell", "-Command", "(Get-WindowsUpdate -IsInstalled:$false -IsHidden:$false).Count -gt 0"],
#                 capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
#             )
#             return "True" in result.stdout
#         elif system == "Linux":
#             if os.path.exists("/etc/apt/sources.list"):
#                 subprocess.run(["sudo", "apt", "update"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#                 result = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True)
#                 return "upgradable" in result.stdout
#             elif os.path.exists("/etc/yum.conf"):
#                 result = subprocess.run(["yum", "check-update"], capture_output=True, text=True, stderr=subprocess.DEVNULL)
#                 return result.returncode == 100
#     except Exception as e:
#         print(f"OS updates check error: {str(e)}")
#     return False

# def check_antivirus():
#     system = platform.system()
#     try:
#         if system == "Darwin":
#             processes = [p.name() for p in psutil.process_iter()]
#             av_processes = ["Sophos", "Bitdefender", "Avast", "Kaspersky", "Norton"]
#             return any(av in " ".join(processes) for av in av_processes)
#         elif system == "Windows":
#             result = subprocess.run(
#                 ["powershell", "-Command", "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Where-Object {$_.productState -ne 0} | Measure-Object | Select-Object -ExpandProperty Count"],
#                 capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
#             )
#             try:
#                 return int(result.stdout.strip()) > 0
#             except:
#                 return False
#         elif system == "Linux":
#             result = subprocess.run(["clamscan", "--version"], capture_output=True, text=True)
#             return result.returncode == 0
#     except Exception as e:
#         print(f"Antivirus check error: {str(e)}")
#     return False

# def check_sleep_settings():
#     system = platform.system()
#     try:
#         if system == "Darwin":
#             result = subprocess.run(["pmset", "-g"], capture_output=True, text=True)
#             sleep_lines = [line for line in result.stdout.splitlines() if "sleep" in line]
#             sleep_value = next((int(line.split()[1]) for line in sleep_lines if "sleep" in line), 0)
#             return sleep_value <= 10
#         elif system == "Windows":
#             result = subprocess.run(
#                 ["powercfg", "/q"],
#                 capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
#             )
#             sleep_lines = [line for line in result.stdout.splitlines() if "Sleep After" in line and "AC Power Setting" in line]
#             if sleep_lines:
#                 sleep_value = int(sleep_lines[0].split()[-1])
#                 return sleep_value <= 10 * 60
#             return False
#         elif system == "Linux":
#             try:
#                 result = subprocess.run(["gsettings", "get", "org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-timeout"], capture_output=True, text=True)
#                 if result.stdout.strip() == "":
#                     return False
#                 sleep_value = int(result.stdout.strip().split()[0])
#                 return sleep_value <= 10
#             except:
#                 return False
#     except Exception as e:
#         print(f"Sleep settings check error: {str(e)}")
#     return False

# def get_system_metrics():
#     return {
#         "cpu_usage": psutil.cpu_percent(interval=1),
#         "memory_usage": psutil.virtual_memory().percent,
#         "disk_usage": psutil.disk_usage('/').percent
#     }

# # ----- New: disk detection helpers -----
# def _linux_disk_type_map():
#     """
#     Returns mapping of mountpoint -> 'SSD'|'HDD'|'unknown' using lsblk JSON (ROTA)
#     """
#     try:
#         res = subprocess.run(["lsblk", "-J", "-o", "NAME,MOUNTPOINT,ROTA,TYPE"], capture_output=True, text=True)
#         data = json.loads(res.stdout)
#         mapping = {}

#         def walk(blocks):
#             for b in blocks:
#                 # partitions may have mountpoints
#                 mp = b.get("mountpoint")
#                 rota = b.get("rota", None)
#                 typ = b.get("type", "").lower()
#                 if mp:
#                     if rota is not None:
#                         mapping[mp] = "HDD" if str(rota) == "1" else "SSD"
#                     else:
#                         mapping[mp] = "unknown"
#                 # children
#                 if "children" in b and b["children"]:
#                     walk(b["children"])

#         if "blockdevices" in data:
#             walk(data["blockdevices"])
#         return mapping
#     except Exception:
#         return {}

# def _windows_disk_type_map():
#     """
#     Use PowerShell to map drive letters to IsSSD if possible.
#     Returns mapping like 'C:\\' -> 'SSD'|'HDD'|'unknown'
#     """
#     try:
#         # Build mapping: for each partition with DriveLetter, get parent disk IsSSD property
#         ps_script = r"""
# $results = @()
# Get-Partition | Where-Object DriveLetter -NE $null | ForEach-Object {
#   $driveLetter = ($_.DriveLetter + ':\')
#   try {
#     $disk = Get-Disk -Number $_.DiskNumber -ErrorAction Stop
#     $isSSD = $disk.IsSSD
#     $mt = if ($isSSD) {'SSD'} else {'HDD'}
#   } catch {
#     $mt = 'unknown'
#   }
#   $results += [PSCustomObject]@{ Drive = $driveLetter; Type = $mt }
# }
# $results | ConvertTo-Json -Compress
# """
#         res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
#         out = res.stdout.strip()
#         if not out:
#             return {}
#         parsed = json.loads(out)
#         mapping = {}
#         # parsed could be list or single object
#         if isinstance(parsed, list):
#             for item in parsed:
#                 drive = item.get("Drive")
#                 typ = item.get("Type", "unknown")
#                 # normalize drive to have trailing backslash
#                 if drive and not drive.endswith("\\"):
#                     drive = drive + "\\"
#                 mapping[drive] = typ
#         elif isinstance(parsed, dict):
#             drive = parsed.get("Drive")
#             typ = parsed.get("Type", "unknown")
#             if drive and not drive.endswith("\\"):
#                 drive = drive + "\\"
#             mapping[drive] = typ
#         return mapping
#     except Exception:
#         return {}

# def detect_disk_type_for_mount(mountpoint):
#     system = platform.system()
#     if system == "Linux":
#         mapping = _linux_disk_type_map()
#         # lsblk mountpoints often equal exactly mountpoint; try exact and fallback by prefix
#         if mountpoint in mapping:
#             return mapping[mountpoint]
#         # fallback: try shorter matching
#         for k in mapping:
#             if mountpoint.startswith(k):
#                 return mapping[k]
#         return "unknown"
#     elif system == "Windows":
#         mapping = _windows_disk_type_map()
#         # psutil mountpoint likely 'C:\\', mapping keys are normalized
#         mp = mountpoint
#         if mp in mapping:
#             return mapping[mp]
#         # try drive letter without backslash
#         try:
#             driveletter = os.path.splitdrive(mp)[0] + "\\"
#             if driveletter in mapping:
#                 return mapping[driveletter]
#         except:
#             pass
#         return "unknown"
#     else:
#         # macOS detection could be added using diskutil; fallback to unknown
#         return "unknown"

# def collect_disks():
#     disks = []
#     partitions = psutil.disk_partitions(all=False)
#     for p in partitions:
#         mount = p.mountpoint
#         try:
#             usage = psutil.disk_usage(mount)
#         except Exception:
#             continue
#         disk_type = detect_disk_type_for_mount(mount)
#         disks.append({
#             "device": p.device,
#             "mountpoint": mount,
#             "total": usage.total,
#             "used": usage.used,
#             "free": usage.free,
#             "percent": usage.percent,
#             "type": disk_type
#         })
#     return disks

# def get_system_state():
#     return {
#         "os_name": platform.system(),
#         "os_version": platform.release(),
#         "machine_name": platform.node(),
#         "disk_encryption": check_disk_encryption(),
#         "os_updates": check_os_updates(),
#         "antivirus": check_antivirus(),
#         "sleep_settings": check_sleep_settings()
#     }

# def main():
#     machine_id = get_machine_id()
#     last_state = {}
#     system_info = get_system_info()

#     while True:
#         try:
#             current_state = get_system_state()
#             metrics = get_system_metrics()
#             disks = collect_disks()
#             # print disk info to terminal as requested
#             print("Disks:", json.dumps(disks, indent=2))
#             payload = {
#                 "machine_id": machine_id,
#                 "timestamp": int(time.time()),
#                 "system_info": system_info,
#                 "state": current_state,
#                 "metrics": { **metrics, "disks": disks },
#                 "raw": json.dumps({
#                     "state": current_state,
#                     "metrics": metrics,
#                     "disks": disks
#                 })
#             }
#             response = requests.post(API_URL, json=payload, timeout=10)
#             if response.status_code == 200:
#                 last_state = current_state
#             else:
#                 print("Server responded:", response.status_code, response.text)
#         except Exception as e:
#             print(f"Error: {str(e)}")
#         time.sleep(60)

# if __name__ == '__main__':
#     main()

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

API_URL = "http://localhost:5000/api/report"

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
            mp = mountpoint
            if not mp:
                return "unknown"
            driveletter = os.path.splitdrive(mp)[0].upper()
            if not driveletter:
                mp_norm = mp.upper()
            else:
                mp_norm = driveletter + "\\"
            mapping = _windows_disk_type_map()
            if mp_norm in mapping:
                return mapping[mp_norm]
            for k, v in mapping.items():
                if k and mp_norm.startswith(k):
                    return v
            return "unknown"
        except Exception:
            return "unknown"
    if system == "Linux":
        try:
            mapping = _linux_disk_type_map()
            if mountpoint in mapping:
                return mapping[mountpoint]
            for k, v in mapping.items():
                if k and mountpoint.startswith(k):
                    return v
            for p in psutil.disk_partitions(all=False):
                if p.mountpoint == mountpoint:
                    dev = os.path.basename(p.device)
                    base = re.sub(r'p?\d+$', '', dev)
                    sys_rot_path = f"/sys/block/{base}/queue/rotational"
                    if os.path.exists(sys_rot_path):
                        with open(sys_rot_path, "r") as f:
                            val = f.read().strip()
                            return "HDD" if val == "1" else "SSD" if val == "0" else "unknown"
            return "unknown"
        except Exception:
            return "unknown"
    try:
        for p in psutil.disk_partitions(all=False):
            if p.mountpoint == mountpoint:
                dev = p.device
                res = subprocess.run(["diskutil", "info", dev], capture_output=True, text=True, timeout=5)
                out = res.stdout.lower() if res.stdout else ""
                if "solid state" in out or "ssd" in out:
                    return "SSD"
                if "rotational" in out and "1" in out:
                    return "HDD"
    except Exception:
        pass
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

def main():
    machine_id = get_machine_id()
    system_info = get_system_info()
    while True:
        try:
            current_state = get_system_state()
            metrics = get_system_metrics()
            disks = collect_disks()
            print(json.dumps({"disks": disks}, indent=2))
            payload = {
                "machine_id": machine_id,
                "timestamp": int(time.time()),
                "system_info": system_info,
                "state": current_state,
                "metrics": { **metrics, "disks": disks },
                "raw": json.dumps({"state": current_state, "metrics": metrics, "disks": disks})
            }
            try:
                response = requests.post(API_URL, json=payload, timeout=10)
                if response.status_code != 200:
                    print("Server responded:", response.status_code, response.text)
            except Exception as e:
                print("Error sending report:", str(e))
        except Exception as e:
            print("Error:", str(e))
        time.sleep(60)

if __name__ == '__main__':
    main()

