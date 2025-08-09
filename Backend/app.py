from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from database import init_db, db_session, Machine, Report
import csv
import io
import json
import time
import subprocess
import os

app = Flask(__name__)
CORS(app)
init_db()

# Auto-generate SSL certs if missing
if not os.path.exists("cert.pem") or not os.path.exists("key.pem"):
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:4096", "-nodes",
        "-keyout", "key.pem", "-out", "cert.pem", "-days", "365",
        "-subj", "/CN=localhost"
    ], check=True)

@app.route('/')
def home():
    return "System Monitor Backend is running"

# @app.route('/api/report', methods=['POST'])
# def report_data():
#     session = db_session()
#     try:
#         data = request.json
#         mid = data.get('machine_id')
#         system_info = data.get('system_info', {})
#         state = data.get('state', {})
#         metrics = data.get('metrics', {})
#         disk_info = data.get('disk_info') or metrics.get('disks') or []
#         ts = data.get('timestamp', int(time.time()))
#         print("Received report from", mid)
#         print("Disk info received:")
#         try:
#             print(json.dumps(disk_info, indent=2))
#         except Exception:
#             print(disk_info)
#         machine = session.query(Machine).filter_by(uuid=mid).first()
#         if not machine:
#             machine = Machine(uuid=mid)
#             session.add(machine)
#             session.commit()
#         machine.hostname = system_info.get('hostname') or machine.hostname
#         machine.os_platform = system_info.get('os_platform') or machine.os_platform
#         machine.os_version = system_info.get('os_version') or machine.os_version
#         machine.username = system_info.get('username') or machine.username
#         try:
#             machine.cpu_cores = int(system_info.get('cpu_cores') or 0)
#         except:
#             machine.cpu_cores = 0
#         try:
#             machine.memory_mb = int(system_info.get('memory_mb') or 0)
#         except:
#             machine.memory_mb = 0
#         machine.last_seen = ts
#         session.add(machine)
#         session.commit()
#         report = Report(
#             machine_id=machine.id,
#             timestamp=ts,
#             disk_encryption=bool(state.get('disk_encryption')),
#             os_updates=bool(state.get('os_updates')),
#             antivirus=bool(state.get('antivirus')),
#             sleep_settings=bool(state.get('sleep_settings')),
#             cpu_usage=float(metrics.get('cpu_usage') or 0.0),
#             memory_usage=float(metrics.get('memory_usage') or 0.0),
#             disk_usage=float(metrics.get('disk_usage') or 0.0),
#             raw=json.dumps(data),
#             disk_info=json.dumps(disk_info)
#         )
#         session.add(report)
#         session.commit()
#         return jsonify({"status": "success"}), 200
#     except Exception as e:
#         session.rollback()
#         return jsonify({"error": str(e)}), 500
#     finally:
#         session.close()


@app.route('/cert.pem')
def get_cert():
    return send_file('cert.pem', mimetype='application/x-pem-file')

@app.route('/api/report', methods=['POST'])
def report_data():
    session = db_session()
    try:
        data = request.json
        mid = data.get('machine_id')
        system_info = data.get('system_info', {})
        state = data.get('state', {})
        metrics = data.get('metrics', {})
        disk_info = data.get('disk_info') or metrics.get('disks') or []
        ts = data.get('timestamp', int(time.time()))
        
        print("Received report from", mid)
        print("Disk info received:")
        try:
            print(json.dumps(disk_info, indent=2))
        except Exception:
            print(disk_info)
            
        machine = session.query(Machine).filter_by(uuid=mid).first()
        if not machine:
            machine = Machine(uuid=mid)
            session.add(machine)
            session.commit()
            
        machine.hostname = system_info.get('hostname') or machine.hostname
        machine.os_platform = system_info.get('os_platform') or machine.os_platform
        machine.os_version = system_info.get('os_version') or machine.os_version
        machine.username = system_info.get('username') or machine.username
        try:
            machine.cpu_cores = int(system_info.get('cpu_cores') or 0)
        except:
            machine.cpu_cores = 0
        try:
            machine.memory_mb = int(system_info.get('memory_mb') or 0)
        except:
            machine.memory_mb = 0
        machine.last_seen = ts
        session.add(machine)
        session.commit()
        
        report = Report(
            machine_id=machine.id,
            timestamp=ts,
            disk_encryption=bool(state.get('disk_encryption')),
            os_updates=bool(state.get('os_updates')),
            antivirus=bool(state.get('antivirus')),
            sleep_settings=bool(state.get('sleep_settings')),
            cpu_usage=float(metrics.get('cpu_usage') or 0.0),
            memory_usage=float(metrics.get('memory_usage') or 0.0),
            disk_usage=float(metrics.get('disk_usage') or 0.0),
            raw=json.dumps(data),
            disk_info=json.dumps(disk_info)
        )
        session.add(report)
        session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()    

# @app.route('/api/machines', methods=['GET'])
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


@app.route('/api/machines', methods=['GET'])
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


# @app.route('/api/export', methods=['GET'])
# def export_csv():
#     session = db_session()
#     try:
#         si = io.StringIO()
#         cw = csv.writer(si)
#         cw.writerow([
#             'machine_id', 'hostname', 'os_platform', 'os_version', 'username',
#             'cpu_cores', 'memory_mb', 'timestamp', 'disk_encryption', 'os_updates',
#             'antivirus', 'sleep_settings', 'cpu_usage', 'memory_usage', 'disk_usage', 'disk_info'
#         ])
#         reports = session.query(Report).order_by(Report.timestamp.desc()).all()
#         for report in reports:
#             machine = session.query(Machine).get(report.machine_id)
#             cw.writerow([
#                 machine.uuid if machine else "",
#                 machine.hostname if machine else "",
#                 machine.os_platform if machine else "",
#                 machine.os_version if machine else "",
#                 machine.username if machine else "",
#                 machine.cpu_cores if machine else "",
#                 machine.memory_mb if machine else "",
#                 report.timestamp,
#                 report.disk_encryption,
#                 report.os_updates,
#                 report.antivirus,
#                 report.sleep_settings,
#                 report.cpu_usage,
#                 report.memory_usage,
#                 report.disk_usage,
#                 report.disk_info or ""
#             ])
#         output = io.BytesIO()
#         output.write(si.getvalue().encode('utf-8'))
#         output.seek(0)
#         return send_file(
#             output,
#             mimetype='text/csv',
#             as_attachment=True,
#             download_name='system_report.csv'
#         )
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         session.close()


@app.route('/api/export', methods=['GET'])
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
            
            # Convert booleans to human-readable statuses
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
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='system_report.csv'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('cert.pem', 'key.pem')) # ssl_context ---> HTTPS secured HTTP server
    app.run(host='192.168.0.105', port=5000, debug=True, ssl_context=('cert.pem', 'key.pem')) # ssl_context ---> HTTPS secured HTTP server
