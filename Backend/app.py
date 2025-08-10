# import os
# import sys
# import socket
# import json
# import time
# import subprocess
# from pathlib import Path
# import ipaddress
# import platform

# # ------------------ Cross-platform admin check & inline elevation ------------------
# def is_admin():
#     """
#     Return True if current process has admin/root privileges.
#     """
#     system = platform.system().lower()
#     if system.startswith("win"):
#         try:
#             import ctypes
#             return ctypes.windll.shell32.IsUserAnAdmin() != 0
#         except Exception:
#             return False
#     else:
#         try:
#             return os.geteuid() == 0
#         except AttributeError:
#             return False

# def elevate_and_reexec():
#     """
#     Try to re-run this script with elevated privileges.
#     On Windows: use PowerShell Start-Process -Verb RunAs (UAC).
#     On macOS/Linux: use sudo to re-run python with same args.
#     This attempts to keep the flow in the same terminal (the UAC dialog is system-level).
#     """
#     system = platform.system().lower()
#     script = os.path.abspath(sys.argv[0])
#     args = sys.argv[1:]

#     if system.startswith("win"):
#         quoted_args = " ".join(f'"{a}"' for a in ([script] + args))
#         try:
#             # This triggers UAC; the new elevated process will start separately but we avoid ShellExecuteW and external cmd windows.
#             ps_cmd = f'Start-Process -FilePath "{sys.executable}" -ArgumentList {quoted_args} -Verb RunAs'
#             subprocess.check_call(["powershell", "-NoProfile", "-Command", ps_cmd])
#         except subprocess.CalledProcessError as e:
#             print("Failed to request elevation (Windows):", e)
#             sys.exit(1)
#         sys.exit(0)
#     else:
#         try:
#             os.execvp("sudo", ["sudo", sys.executable, script] + args)
#         except Exception as e:
#             print("Failed to elevate using sudo:", e)
#             sys.exit(1)

# if not is_admin():
#     print("Not running as admin/root. Requesting elevation...")
#     elevate_and_reexec()

# # ------------------ cryptography import (install if required) ------------------
# try:
#     from cryptography import x509
#     from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
#     from cryptography.hazmat.primitives import serialization, hashes
#     from cryptography.hazmat.primitives.asymmetric import rsa
#     from datetime import datetime, timedelta
# except Exception:
#     subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
#     from cryptography import x509
#     from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
#     from cryptography.hazmat.primitives import serialization, hashes
#     from cryptography.hazmat.primitives.asymmetric import rsa
#     from datetime import datetime, timedelta

# from flask import Flask, send_file, request, jsonify
# from flask_cors import CORS
# # keep your existing database import - ensure database.py exists and exports init_db, db_session, Machine, Report
# from database import init_db, db_session, Machine, Report
# import csv
# import io


# BASE = Path(__file__).resolve().parent
# SSL_DIR = BASE / "ssl"
# SSL_DIR.mkdir(exist_ok=True)
# CA_KEY = SSL_DIR / "ca-key.pem"
# CA_CERT = SSL_DIR / "ca.pem"
# SERVER_KEY = SSL_DIR / "key.pem"
# SERVER_CERT = SSL_DIR / "cert.pem"


# def get_local_ips():
#     ips = {"127.0.0.1", "localhost"}
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(("8.8.8.8", 80))
#         ips.add(s.getsockname()[0])
#         s.close()
#     except Exception:
#         pass
#     try:
#         for info in socket.getaddrinfo(socket.gethostname(), None):
#             a = info[4][0]
#             if ":" not in a:
#                 ips.add(a)
#     except Exception:
#         pass
#     return sorted(list(ips))


# def build_ca_and_server_cert(hosts):
#     # If all files exist, skip
#     if CA_CERT.exists() and CA_KEY.exists() and SERVER_CERT.exists() and SERVER_KEY.exists():
#         return

    
#     key_ca = rsa.generate_private_key(public_exponent=65537, key_size=2048)
#     name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"Local Dev CA")])
#     ca_cert = (
#         x509.CertificateBuilder()
#         .subject_name(name)
#         .issuer_name(name)
#         .public_key(key_ca.public_key())
#         .serial_number(x509.random_serial_number())
#         .not_valid_before(datetime.utcnow() - timedelta(days=1))
#         .not_valid_after(datetime.utcnow() + timedelta(days=3650))
#         .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
#         .sign(key_ca, hashes.SHA256())
#     )

#     with open(CA_KEY, "wb") as f:
#         f.write(key_ca.private_bytes(
#             encoding=serialization.Encoding.PEM,
#             format=serialization.PrivateFormat.TraditionalOpenSSL,
#             encryption_algorithm=serialization.NoEncryption()
#         ))
#     with open(CA_CERT, "wb") as f:
#         f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    
#     key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
#     subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"local-dev-server")])
#     san_list = []
#     for h in hosts:
#         try:
#             ip = ipaddress.ip_address(h)
#             san_list.append(x509.IPAddress(ip))
#         except Exception:
#             san_list.append(x509.DNSName(h))

#     cert_builder = (
#         x509.CertificateBuilder()
#         .subject_name(subject)
#         .issuer_name(ca_cert.subject)
#         .public_key(key.public_key())
#         .serial_number(x509.random_serial_number())
#         .not_valid_before(datetime.utcnow() - timedelta(days=1))
#         .not_valid_after(datetime.utcnow() + timedelta(days=3650))
#         .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
#         .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
#     )
#     cert = cert_builder.sign(private_key=key_ca, algorithm=hashes.SHA256())

#     with open(SERVER_KEY, "wb") as f:
#         f.write(key.private_bytes(
#             encoding=serialization.Encoding.PEM,
#             format=serialization.PrivateFormat.TraditionalOpenSSL,
#             encryption_algorithm=serialization.NoEncryption()
#         ))
#     with open(SERVER_CERT, "wb") as f:
#         f.write(cert.public_bytes(serialization.Encoding.PEM))


# def install_ca_linux(ca_path):
#     try:
#         dest = Path("/usr/local/share/ca-certificates/local-dev-ca.crt")
#         subprocess.run(["sudo", "cp", str(ca_path), str(dest)], check=True)
#         subprocess.run(["sudo", "chmod", "644", str(dest)], check=True)
#         subprocess.run(["sudo", "update-ca-certificates"], check=True)
#         return True
#     except Exception:
#         try:
#             dest2 = Path("/etc/pki/ca-trust/source/anchors/local-dev-ca.crt")
#             subprocess.run(["sudo", "cp", str(ca_path), str(dest2)], check=True)
#             subprocess.run(["sudo", "update-ca-trust"], check=True)
#             return True
#         except Exception:
#             return False

# def install_ca_macos(ca_path):
#     try:
#         subprocess.run(["sudo", "security", "add-trusted-cert", "-d", "-r", "trustRoot", "-k",
#                         "/Library/Keychains/System.keychain", str(ca_path)], check=True)
#         return True
#     except Exception:
#         return False

# def install_ca_windows(ca_path):
#     try:
        
#         subprocess.run(["certutil", "-addstore", "-f", "Root", str(ca_path)], check=True, shell=True)
#         return True
#     except Exception:
#         try:
            
#             ps = f"Start-Process powershell -ArgumentList 'certutil -addstore -f Root \"{ca_path}\"' -Verb runAs"
#             subprocess.run(["powershell", "-Command", ps], check=True)
#             return True
#         except Exception:
#             return False

# def attempt_install_ca(ca_path):
#     plat = sys.platform
#     if plat.startswith("linux"):
#         return install_ca_linux(ca_path)
#     if plat == "darwin":
#         return install_ca_macos(ca_path)
#     if plat.startswith("win"):
#         return install_ca_windows(ca_path)
#     return False


# hosts = get_local_ips()

# if "192.168.0.105" not in hosts:
#     hosts.append("192.168.0.105")
# if "127.0.0.1" not in hosts:
#     hosts.append("127.0.0.1")
# if "localhost" not in hosts:
#     hosts.append("localhost")
# hosts = list(dict.fromkeys(hosts))
# build_ca_and_server_cert(hosts)
# installed = attempt_install_ca(CA_CERT)
# if not installed:
#     print("Failed to auto-install CA into system trust. Import manually from:", CA_CERT)


# app = Flask(__name__)
# CORS(app)
# init_db()

# @app.route("/")
# def home():
#     return "System Monitor Backend is running"

# @app.route("/cert.pem")
# def get_cert():
#     return send_file(str(CA_CERT), mimetype="application/x-pem-file")

# @app.route("/api/report", methods=["POST"])
# def report_data():
#     session = db_session()
#     try:
#         data = request.json
#         mid = data.get("machine_id")
#         system_info = data.get("system_info", {})
#         state = data.get("state", {})
#         metrics = data.get("metrics", {})
#         disk_info = data.get("disk_info") or metrics.get("disks") or []
#         ts = data.get("timestamp", int(time.time()))
#         machine = session.query(Machine).filter_by(uuid=mid).first()
#         if not machine:
#             machine = Machine(uuid=mid)
#             session.add(machine)
#             session.commit()
#         machine.hostname = system_info.get("hostname") or machine.hostname
#         machine.os_platform = system_info.get("os_platform") or machine.os_platform
#         machine.os_version = system_info.get("os_version") or machine.os_version
#         machine.username = system_info.get("username") or machine.username
#         try:
#             machine.cpu_cores = int(system_info.get("cpu_cores") or 0)
#         except:
#             machine.cpu_cores = 0
#         try:
#             machine.memory_mb = int(system_info.get("memory_mb") or 0)
#         except:
#             machine.memory_mb = 0
#         machine.last_seen = ts
#         session.add(machine)
#         session.commit()
#         report = Report(
#             machine_id=machine.id,
#             timestamp=ts,
#             disk_encryption=bool(state.get("disk_encryption")),
#             os_updates=bool(state.get("os_updates")),
#             antivirus=bool(state.get("antivirus")),
#             sleep_settings=bool(state.get("sleep_settings")),
#             cpu_usage=float(metrics.get("cpu_usage") or 0.0),
#             memory_usage=float(metrics.get("memory_usage") or 0.0),
#             disk_usage=float(metrics.get("disk_usage") or 0.0),
#             raw=json.dumps(data),
#             disk_info=json.dumps(disk_info),
#         )
#         session.add(report)
#         session.commit()
#         return jsonify({"status": "success"}), 200
#     except Exception as e:
#         session.rollback()
#         return jsonify({"error": str(e)}), 500
#     finally:
#         session.close()

# @app.route("/api/machines", methods=["GET"])
# def get_machines():
#     session = db_session()
#     try:
#         machines = session.query(Machine).all()
#         result = []
#         for machine in machines:
#             last_report = session.query(Report).filter_by(machine_id=machine.id).order_by(Report.timestamp.desc()).first()
#             if last_report:
#                 try:
#                     disks = json.loads(last_report.disk_info) if last_report.disk_info else []
#                 except:
#                     disks = []
#                 result.append({
#                     "machine_id": machine.uuid,
#                     "hostname": machine.hostname,
#                     "os_platform": machine.os_platform,
#                     "os_version": machine.os_version,
#                     "username": machine.username,
#                     "cpu_cores": machine.cpu_cores,
#                     "memory_mb": machine.memory_mb,
#                     "last_seen": last_report.timestamp,
#                     "disk_encryption": last_report.disk_encryption,
#                     "os_updates": last_report.os_updates,
#                     "antivirus": last_report.antivirus,
#                     "sleep_settings": last_report.sleep_settings,
#                     "cpu_usage": last_report.cpu_usage,
#                     "memory_usage": last_report.memory_usage,
#                     "disk_usage": last_report.disk_usage,
#                     "disk_info": disks
#                 })
#         return jsonify(result)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         session.close()

# @app.route("/api/export", methods=["GET"])
# def export_csv():
#     session = db_session()
#     try:
#         si = io.StringIO()
#         cw = csv.writer(si)
#         cw.writerow([
#             'machine_id', 'hostname', 'os_platform', 'os_version', 'username',
#             'cpu_cores', 'memory_mb', 'timestamp', 'disk_encryption', 'os_updates',
#             'antivirus', 'sleep_settings', 'cpu_usage (%)', 'memory_usage (%)', 'disk_usage (%)', 'disk_info'
#         ])
#         reports = session.query(Report).order_by(Report.timestamp.desc()).all()
#         for report in reports:
#             machine = session.query(Machine).get(report.machine_id)
#             disk_encryption = "Encrypted" if report.disk_encryption else "Unencrypted"
#             os_updates = "Update Available" if report.os_updates else "Updated"
#             antivirus = "Active" if report.antivirus else "Inactive"
#             sleep_settings = "<=10 min" if report.sleep_settings else ">10 min"
#             cw.writerow([
#                 machine.uuid if machine else "",
#                 machine.hostname if machine else "",
#                 machine.os_platform if machine else "",
#                 machine.os_version if machine else "",
#                 machine.username if machine else "",
#                 machine.cpu_cores if machine else "",
#                 machine.memory_mb if machine else "",
#                 report.timestamp,
#                 disk_encryption,
#                 os_updates,
#                 antivirus,
#                 sleep_settings,
#                 f"{report.cpu_usage:.2f} %",
#                 f"{report.memory_usage:.2f} %",
#                 f"{report.disk_usage:.2f} %",
#                 report.disk_info or ""
#             ])
#         output = io.BytesIO()
#         output.write(si.getvalue().encode('utf-8'))
#         output.seek(0)
#         return send_file(output, mimetype='text/csv', as_attachment=True, download_name='system_report.csv')
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         session.close()


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=(str(SERVER_CERT), str(SERVER_KEY)))



# ---------------------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------------------------



import os
import sys
import socket
import json
import time
import subprocess
from pathlib import Path
import ipaddress
import platform
from uuid import uuid4

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from datetime import datetime, timedelta
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from datetime import datetime, timedelta

from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
from database import init_db, db_session, Machine, Report
import csv
import io

BASE = Path(__file__).resolve().parent
SSL_DIR = BASE / "ssl"
SSL_DIR.mkdir(exist_ok=True)
CA_KEY = SSL_DIR / "ca-key.pem"
CA_CERT = SSL_DIR / "ca.pem"
SERVER_KEY = SSL_DIR / "key.pem"
SERVER_CERT = SSL_DIR / "cert.pem"

commands_store = {}

def get_local_ips():
    ips = {"127.0.0.1", "localhost"}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            a = info[4][0]
            if ":" not in a:
                ips.add(a)
    except Exception:
        pass
    return sorted(list(ips))

def build_ca_and_server_cert(hosts):
    if CA_CERT.exists() and CA_KEY.exists() and SERVER_CERT.exists() and SERVER_KEY.exists():
        return
    key_ca = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"Local Dev CA")])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key_ca.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(days=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key_ca, hashes.SHA256())
    )
    with open(CA_KEY, "wb") as f:
        f.write(key_ca.private_bytes(encoding=serialization.Encoding.PEM,
                                     format=serialization.PrivateFormat.TraditionalOpenSSL,
                                     encryption_algorithm=serialization.NoEncryption()))
    with open(CA_CERT, "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"local-dev-server")])
    san_list = []
    for h in hosts:
        try:
            ip = ipaddress.ip_address(h)
            san_list.append(x509.IPAddress(ip))
        except Exception:
            san_list.append(x509.DNSName(h))
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(days=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
    )
    cert = cert_builder.sign(private_key=key_ca, algorithm=hashes.SHA256())
    with open(SERVER_KEY, "wb") as f:
        f.write(key.private_bytes(encoding=serialization.Encoding.PEM,
                                  format=serialization.PrivateFormat.TraditionalOpenSSL,
                                  encryption_algorithm=serialization.NoEncryption()))
    with open(SERVER_CERT, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

def is_windows_admin():
    if platform.system().lower() == "windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return False

def install_ca_windows(ca_path):
    try:
        command = f'Import-Certificate -FilePath "{ca_path}" -CertStoreLocation Cert:\CurrentUser\Root'
        subprocess.run(["powershell", "-Command", command], check=True, shell=True)
        return True
    except Exception:
        return False

def attempt_install_ca(ca_path):
    if platform.system().lower() == "windows":
        return install_ca_windows(ca_path)
    return False

hosts = get_local_ips()
if "192.168.0.105" not in hosts:
    hosts.append("192.168.0.105")
if "127.0.0.1" not in hosts:
    hosts.append("127.0.0.1")
if "localhost" not in hosts:
    hosts.append("localhost")
hosts = list(dict.fromkeys(hosts))

build_ca_and_server_cert(hosts)

installed = attempt_install_ca(CA_CERT)
if not installed:
    print("="*70)
    print("IMPORTANT: Please manually install the CA certificate")
    print(f"Certificate path: {CA_CERT}")
    print("1. Double-click the .pem file")
    print("2. Select 'Install Certificate'")
    print("3. Choose 'Current User'")
    print("4. Select 'Place all certificates in the following store'")
    print("5. Browse and select 'Trusted Root Certification Authorities'")
    print("6. Complete the wizard")
    print("="*70)

app = Flask(__name__)
CORS(app)
init_db()

@app.route("/")
def home():
    return "System Monitor Backend is running"

@app.route("/cert.pem")
def get_cert():
    return send_file(str(CA_CERT), mimetype="application/x-pem-file")

@app.route("/api/report", methods=["POST"])
def report_data():
    session = db_session()
    try:
        data = request.json
        mid = data.get("machine_id")
        system_info = data.get("system_info", {})
        state = data.get("state", {})
        metrics = data.get("metrics", {})
        disk_info = data.get("disk_info") or metrics.get("disks") or []
        ts = data.get("timestamp", int(time.time()))
        machine = session.query(Machine).filter_by(uuid=mid).first()
        if not machine:
            machine = Machine(uuid=mid)
            session.add(machine)
            session.commit()
        machine.hostname = system_info.get("hostname") or machine.hostname
        machine.os_platform = system_info.get("os_platform") or machine.os_platform
        machine.os_version = system_info.get("os_version") or machine.os_version
        machine.username = system_info.get("username") or machine.username
        try:
            machine.cpu_cores = int(system_info.get("cpu_cores") or 0)
        except:
            machine.cpu_cores = 0
        try:
            machine.memory_mb = int(system_info.get("memory_mb") or 0)
        except:
            machine.memory_mb = 0
        machine.last_seen = ts
        session.add(machine)
        session.commit()
        report = Report(
            machine_id=machine.id,
            timestamp=ts,
            disk_encryption=bool(state.get("disk_encryption")),
            os_updates=bool(state.get("os_updates")),
            antivirus=bool(state.get("antivirus")),
            sleep_settings=bool(state.get("sleep_settings")),
            cpu_usage=float(metrics.get("cpu_usage") or 0.0),
            memory_usage=float(metrics.get("memory_usage") or 0.0),
            disk_usage=float(metrics.get("disk_usage") or 0.0),
            raw=json.dumps(data),
            disk_info=json.dumps(disk_info),
        )
        session.add(report)
        session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/machines", methods=["GET"])
def get_machines():
    session = db_session()
    try:
        machines = session.query(Machine).all()
        result = []
        for machine in machines:
            last_report = session.query(Report).filter_by(machine_id=machine.id).order_by(Report.timestamp.desc()).first()
            if last_report:
                try:
                    disks = json.loads(last_report.disk_info) if last_report.disk_info else []
                except:
                    disks = []
                result.append({
                    "machine_id": machine.uuid,
                    "hostname": machine.hostname,
                    "os_platform": machine.os_platform,
                    "os_version": machine.os_version,
                    "username": machine.username,
                    "cpu_cores": machine.cpu_cores,
                    "memory_mb": machine.memory_mb,
                    "last_seen": last_report.timestamp,
                    "disk_encryption": last_report.disk_encryption,
                    "os_updates": last_report.os_updates,
                    "antivirus": last_report.antivirus,
                    "sleep_settings": last_report.sleep_settings,
                    "cpu_usage": last_report.cpu_usage,
                    "memory_usage": last_report.memory_usage,
                    "disk_usage": last_report.disk_usage,
                    "disk_info": disks
                })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/export", methods=["GET"])
def export_csv():
    session = db_session()
    try:
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow([
            'machine_id', 'hostname', 'os_platform', 'os_version', 'username',
            'cpu_cores', 'memory_mb', 'timestamp', 'disk_encryption', 'os_updates',
            'antivirus', 'sleep_settings', 'cpu_usage (%)', 'memory_usage (%)', 'disk_usage (%)', 'disk_info'
        ])
        reports = session.query(Report).order_by(Report.timestamp.desc()).all()
        for report in reports:
            machine = session.query(Machine).get(report.machine_id)
            disk_encryption = "Encrypted" if report.disk_encryption else "Unencrypted"
            os_updates = "Update Available" if report.os_updates else "Updated"
            antivirus = "Active" if report.antivirus else "Inactive"
            sleep_settings = "<=10 min" if report.sleep_settings else ">10 min"
            cw.writerow([
                machine.uuid if machine else "",
                machine.hostname if machine else "",
                machine.os_platform if machine else "",
                machine.os_version if machine else "",
                machine.username if machine else "",
                machine.cpu_cores if machine else "",
                machine.memory_mb if machine else "",
                report.timestamp,
                disk_encryption,
                os_updates,
                antivirus,
                sleep_settings,
                f"{report.cpu_usage:.2f} %",
                f"{report.memory_usage:.2f} %",
                f"{report.disk_usage:.2f} %",
                report.disk_info or ""
            ])
        output = io.BytesIO()
        output.write(si.getvalue().encode('utf-8'))
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='system_report.csv')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/commands/kill", methods=["POST"])
def create_kill_command():
    data = request.json or {}
    mid = data.get("machine_id")
    pid = data.get("pid")
    if not mid or not pid:
        return jsonify({"error": "missing"}), 400
    cid = str(uuid4())
    cmd = {"id": cid, "machine_id": mid, "action": "kill", "args": {"pid": str(pid)}, "created": int(time.time())}
    commands_store.setdefault(mid, []).append(cmd)
    return jsonify({"status": "ok", "id": cid}), 200

@app.route("/api/commands/<string:machine_id>", methods=["GET"])
def get_commands(machine_id):
    cmds = commands_store.get(machine_id, [])
    return jsonify(cmds), 200

@app.route("/api/commands/<string:cmd_id>/result", methods=["POST"])
def command_result(cmd_id):
    data = request.json or {}
    mid = data.get("machine_id")
    if mid in commands_store:
        commands_store[mid] = [c for c in commands_store[mid] if c.get("id") != cmd_id]
    return jsonify({"status": "ok"}), 200        

if __name__ == '__main__':
    if platform.system().lower() == "windows" and not is_windows_admin():
        print("!"*70)
        print("WARNING: Running without administrator privileges")
        print("HTTPS will work, but restart VS Code as admin if needed")
        print("!"*70)
    
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=(str(SERVER_CERT), str(SERVER_KEY)))











