#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SystemMonitor"
VERSION="1.0.0"
OUTPUT_DIR="dist"
INSTALL_DIR="$APP_NAME"

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/$INSTALL_DIR"

# copy the python script
cp -f ../system_utility.py "$OUTPUT_DIR/$INSTALL_DIR/" || cp -f ./system_utility.py "$OUTPUT_DIR/$INSTALL_DIR/"

# installer that will run ON THE TARGET (requires sudo)
cat > "$OUTPUT_DIR/$INSTALL_DIR/install.sh" <<'SH'
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
SH

chmod +x "$OUTPUT_DIR/$INSTALL_DIR/install.sh"

# uninstall script for target
cat > "$OUTPUT_DIR/$INSTALL_DIR/uninstall.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="systemmonitor"
INSTALL_DIR="/opt/SystemMonitor"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root: sudo ./uninstall.sh"
  exit 1
fi

echo "Stopping and removing service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true
systemctl daemon-reload
rm -f "$SERVICE_FILE"

echo "Removing installation directory..."
rm -rf "$INSTALL_DIR"

echo "Uninstalled."
SH

chmod +x "$OUTPUT_DIR/$INSTALL_DIR/uninstall.sh"

# pack
tar -C "$OUTPUT_DIR" -czf "$OUTPUT_DIR/${APP_NAME}-${VERSION}-linux.tar.gz" "$INSTALL_DIR"

echo "Built: $OUTPUT_DIR/${APP_NAME}-${VERSION}-linux.tar.gz"
