#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SystemMonitor"
VERSION="1.0.0"
OUTPUT_DIR="dist"
INSTALL_DIR="$APP_NAME"

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/$INSTALL_DIR"

# copy python script (try parent dir then current)
cp -f ../system_utility.py "$OUTPUT_DIR/$INSTALL_DIR/" || cp -f ./system_utility.py "$OUTPUT_DIR/$INSTALL_DIR/"

# installer for macOS target (to be run as sudo)
cat > "$OUTPUT_DIR/$INSTALL_DIR/install.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

# This script installs the monitor as a system LaunchDaemon (requires sudo)
INSTALL_DIR="/Library/SystemMonitor"
SCRIPT_NAME="system_utility.py"
PLIST_PATH="/Library/LaunchDaemons/com.systemmonitor.agent.plist"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root: sudo ./install.sh"
  exit 1
fi

echo "Installing SystemMonitor to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp -f "./$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"
chmod 755 "$INSTALL_DIR/$SCRIPT_NAME"

# Find python3
PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python || true)"
fi
if [ -z "$PYTHON_BIN" ]; then
  echo "Python not found. Install python3 (Homebrew or system)."
  exit 1
fi

# Optional: remove stored machine_id if you want fresh install
# rm -f /Library/SystemMonitor/machine_id

# create LaunchDaemon plist
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

# load the daemon
launchctl bootstrap system "$PLIST_PATH" 2>/dev/null || launchctl load -w "$PLIST_PATH"

echo "LaunchDaemon installed and loaded."
echo "Check logs: tail -f /var/log/systemmonitor.out.log"
SH

chmod +x "$OUTPUT_DIR/$INSTALL_DIR/install.sh"

# uninstall script
cat > "$OUTPUT_DIR/$INSTALL_DIR/uninstall.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

PLIST_PATH="/Library/LaunchDaemons/com.systemmonitor.agent.plist"
INSTALL_DIR="/Library/SystemMonitor"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root: sudo ./uninstall.sh"
  exit 1
fi

echo "Unloading daemon..."
launchctl bootout system "$PLIST_PATH" 2>/dev/null || launchctl unload -w "$PLIST_PATH" 2>/dev/null || true

rm -f "$PLIST_PATH"
rm -rf "$INSTALL_DIR"

echo "Uninstalled SystemMonitor."
SH

chmod +x "$OUTPUT_DIR/$INSTALL_DIR/uninstall.sh"

# pack zip
cd "$OUTPUT_DIR"
zip -r "${APP_NAME}-${VERSION}-macos.zip" "$INSTALL_DIR" > /dev/null
cd - >/dev/null

echo "Built: $OUTPUT_DIR/${APP_NAME}-${VERSION}-macos.zip"
