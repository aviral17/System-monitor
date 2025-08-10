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
