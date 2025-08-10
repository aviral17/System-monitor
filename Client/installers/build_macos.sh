#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SystemMonitor"
VERSION="1.0.0"
OUTPUT_DIR="dist"
INSTALL_DIR="$APP_NAME"

# Check dependencies
if ! command -v zip &>/dev/null; then
    echo "ERROR: zip command not found. Install with: brew install zip"
    exit 1
fi

# Fix permission issues by controlling ownership
rm -rf "$OUTPUT_DIR" || sudo rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/$INSTALL_DIR"
chmod 755 "$OUTPUT_DIR"

# Copy python script with explicit permissions
SOURCE_SCRIPT="../system_utility.py"
[ -f "$SOURCE_SCRIPT" ] || SOURCE_SCRIPT="./system_utility.py"
cp -f "$SOURCE_SCRIPT" "$OUTPUT_DIR/$INSTALL_DIR/"
chmod 644 "$OUTPUT_DIR/$INSTALL_DIR/system_utility.py"

# Create installer script
cat > "$OUTPUT_DIR/$INSTALL_DIR/install.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/Library/SystemMonitor"
SCRIPT_NAME="system_utility.py"
PLIST_PATH="/Library/LaunchDaemons/com.systemmonitor.agent.plist"

if [[ $EUID -ne 0 ]]; then
    exec sudo "$0" "$@"
fi

echo "Installing SystemMonitor to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -f "./$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"
chmod 755 "$INSTALL_DIR/$SCRIPT_NAME"

# Find python3 reliably
PYTHON_BIN=""
for candidate in /usr/local/bin/python3 /usr/bin/python3 python3 python; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python not found. Install python3"
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

# Load daemon
launchctl bootstrap system "$PLIST_PATH" 2>/dev/null || launchctl load -w "$PLIST_PATH"

echo "Success! Daemon installed and loaded"
echo "Check logs: tail -f /var/log/systemmonitor.{out,err}.log"
SH
chmod 755 "$OUTPUT_DIR/$INSTALL_DIR/install.sh"

# Create uninstaller
cat > "$OUTPUT_DIR/$INSTALL_DIR/uninstall.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

PLIST_PATH="/Library/LaunchDaemons/com.systemmonitor.agent.plist"
INSTALL_DIR="/Library/SystemMonitor"

if [[ $EUID -ne 0 ]]; then
    exec sudo "$0" "$@"
fi

echo "Unloading daemon..."
launchctl bootout system "$PLIST_PATH" 2>/dev/null || \
launchctl unload -w "$PLIST_PATH" 2>/dev/null || true

rm -f "$PLIST_PATH"
rm -rf "$INSTALL_DIR"

echo "SystemMonitor completely uninstalled"
SH
chmod 755 "$OUTPUT_DIR/$INSTALL_DIR/uninstall.sh"

# Create zip package
(cd "$OUTPUT_DIR" && zip -r "${APP_NAME}-${VERSION}-macos.zip" "$INSTALL_DIR")

echo "Build successful: $OUTPUT_DIR/${APP_NAME}-${VERSION}-macos.zip"