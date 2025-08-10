#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/Library/SystemMonitor"
SCRIPT_NAME="system_utility.py"
PLIST_PATH="/Library/LaunchDaemons/com.systemmonitor.agent.plist"

# Auto-elevate with sudo
if [ "$(id -u)" -ne 0 ]; then
    echo "Requesting administrator privileges..."
    exec sudo -p "Password for installation: " "$0" "$@"
fi

echo "Installing SystemMonitor to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -f "./$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"
chmod 755 "$INSTALL_DIR/$SCRIPT_NAME"

# Find python3
PYTHON_BIN=""
for py in $(command -v python3 2>/dev/null) $(command -v python 2>/dev/null) /usr/local/bin/python3 /usr/bin/python3; do
    if [ -x "$py" ]; then
        PYTHON_BIN="$py"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python not found. Install python3 first."
    exit 1
fi

# Create LaunchDaemon plist
cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.systemmonitor.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>$INSTALL_DIR/$SCRIPT_NAME</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>/var/log/systemmonitor.out.log</string>
    <key>StandardErrorPath</key><string>/var/log/systemmonitor.err.log</string>
</dict>
</plist>
PLIST

chown root:wheel "$PLIST_PATH"
chmod 644 "$PLIST_PATH"

# Load the service
echo "Loading service..."
launchctl bootstrap system "$PLIST_PATH" 2>/dev/null || \
launchctl load -w "$PLIST_PATH" 2>/dev/null || true

echo "Success! Service installed and running"
echo "Logs: /var/log/systemmonitor.{out,err}.log"
