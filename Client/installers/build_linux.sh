#!/bin/bash
set -e

APP_NAME="system-monitor"
VERSION="1.0.0"
INSTALL_DIR="/usr/local/bin"
SERVICE_DIR="/etc/systemd/system"

TEMP_DIR=$(mktemp -d)

mkdir -p "$TEMP_DIR/DEBIAN"
mkdir -p "$TEMP_DIR$INSTALL_DIR"
mkdir -p "$TEMP_DIR$SERVICE_DIR"

cp "../system_utility.py" "$TEMP_DIR$INSTALL_DIR/$APP_NAME"
chmod +x "$TEMP_DIR$INSTALL_DIR/$APP_NAME"

cat > "$TEMP_DIR$SERVICE_DIR/$APP_NAME.service" <<EOF
[Unit]
Description=System Monitor
After=network.target

[Service]
ExecStart=$INSTALL_DIR/$APP_NAME
Restart=always
RestartSec=60
User=root

[Install]
WantedBy=multi-user.target
EOF

cat > "$TEMP_DIR/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $VERSION
Section: base
Priority: optional
Architecture: all
Maintainer: Support <support@example.com>
Description: System monitoring utility
Depends: python3, python3-psutil, python3-requests
EOF

cat > "$TEMP_DIR/DEBIAN/postinst" <<EOF
#!/bin/bash
systemctl daemon-reload
systemctl enable $APP_NAME.service
systemctl start $APP_NAME.service
echo "Service started! Check status with: systemctl status $APP_NAME"
EOF
chmod +x "$TEMP_DIR/DEBIAN/postinst"

cat > "$TEMP_DIR/DEBIAN/prerm" <<EOF
#!/bin/bash
systemctl stop $APP_NAME.service
systemctl disable $APP_NAME.service
EOF
chmod +x "$TEMP_DIR/DEBIAN/prerm"

dpkg-deb --build "$TEMP_DIR" "${APP_NAME}_${VERSION}.deb"
rm -rf "$TEMP_DIR"
echo "Package built: ${APP_NAME}_${VERSION}.deb"
echo "Install with: sudo dpkg -i ${APP_NAME}_${VERSION}.deb"