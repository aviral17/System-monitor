#!/bin/bash
set -e

APP_NAME="SystemMonitor"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}.dmg"
INSTALL_DIR="/Applications"
SERVICE_DIR="/Library/LaunchDaemons"

TEMP_DIR=$(mktemp -d)
APP_DIR="$TEMP_DIR/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

cat > "$CONTENTS_DIR/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.$APP_NAME</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
</dict>
</plist>
EOF

cat > "$MACOS_DIR/launcher" <<EOF
#!/bin/bash
/usr/bin/python3 $INSTALL_DIR/$APP_NAME.app/Contents/Resources/system_utility.py
EOF
chmod +x "$MACOS_DIR/launcher"

cp "../system_utility.py" "$RESOURCES_DIR/"

cat > "$TEMP_DIR$SERVICE_DIR/com.example.$APP_NAME.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.example.$APP_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/$APP_NAME.app/Contents/MacOS/launcher</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/$APP_NAME.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/$APP_NAME.log</string>
</dict>
</plist>
EOF

cat > "$TEMP_DIR/INSTALL.txt" <<EOF
==== Installation Instructions ====

1. Double-click $DMG_NAME to mount it
2. Drag $APP_NAME.app to your Applications folder
3. Run in Terminal:
   sudo launchctl load $SERVICE_DIR/com.example.$APP_NAME.plist

To uninstall:
1. Run in Terminal:
   sudo launchctl unload $SERVICE_DIR/com.example.$APP_NAME.plist
2. Delete $APP_NAME.app from Applications
EOF

hdiutil create -volname "$APP_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_NAME"
rm -rf "$TEMP_DIR"
echo "Package built: $DMG_NAME"