#!/usr/bin/env bash
set -euo pipefail

PLIST_PATH="/Library/LaunchDaemons/com.systemmonitor.agent.plist"
INSTALL_DIR="/Library/SystemMonitor"

# Auto-elevate with sudo
if [ "$(id -u)" -ne 0 ]; then
    echo "Requesting administrator privileges..."
    exec sudo -p "Password for uninstall: " "$0" "$@"
fi

echo "Stopping service..."
launchctl bootout system "$PLIST_PATH" 2>/dev/null || \
launchctl unload -w "$PLIST_PATH" 2>/dev/null || true

echo "Removing files..."
rm -f "$PLIST_PATH" 2>/dev/null || true
rm -rf "$INSTALL_DIR" 2>/dev/null || true

echo "SystemMonitor completely uninstalled"
