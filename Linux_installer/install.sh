#!/usr/bin/env bash
set -euo pipefail

# Target install script (run as root)
INSTALL_DIR="/opt/SystemMonitor"
SCRIPT_NAME="system_utility.py"
SERVICE_NAME="systemmonitor"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root: sudo ./install.sh"
  exit 1
fi

echo "Installing SystemMonitor to $INSTALL_DIR ..."

mkdir -p "$INSTALL_DIR"
cp -f "./$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"
chmod 755 "$INSTALL_DIR/$SCRIPT_NAME"

# Find python3 executable
PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python || true)"
fi
if [ -z "$PYTHON_BIN" ]; then
  echo "Python not found. Please install python3."
  exit 1
fi

# Optional: remove saved machine_id so that re-install creates a new machine entry
# Uncomment below if you want a fresh machine id on reinstall
# rm -f /var/lib/SystemMonitor/machine_id
# rm -f /opt/SystemMonitor/machine_id

# write systemd unit
cat > "$SERVICE_FILE" <<UNIT
[Unit]
Description=SystemMonitor background reporter
After=network.target

[Service]
Type=simple
ExecStart=$PYTHON_BIN $INSTALL_DIR/$SCRIPT_NAME
WorkingDirectory=$INSTALL_DIR
Restart=on-failure
RestartSec=5
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

# reload and enable/start
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

echo "Service $SERVICE_NAME installed and started."
echo "Use: systemctl status $SERVICE_NAME"
echo "Logs: journalctl -u $SERVICE_NAME -f"
