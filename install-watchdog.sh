#!/bin/bash
# HomePi Watchdog Installation Script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}HomePi Watchdog Installation${NC}"
echo "================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Usage: sudo bash install-watchdog.sh"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOMEPI_DIR="$SCRIPT_DIR"

echo -e "${YELLOW}Installing HomePi Watchdog...${NC}"

# Make scripts executable
chmod +x "$HOMEPI_DIR/startup-enhanced.sh"
chmod +x "$HOMEPI_DIR/homepi_watchdog.py"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --upgrade psutil requests

# Install systemd service
echo "Installing systemd service..."
cp "$HOMEPI_DIR/homepi-watchdog.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable homepi-watchdog.service

# Create log directory
mkdir -p /var/log
touch /var/log/homepi-watchdog.log
chmod 644 /var/log/homepi-watchdog.log

# Setup logrotate
cat > /etc/logrotate.d/homepi-watchdog << 'EOF'
/var/log/homepi-watchdog.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

echo -e "${GREEN}Installation completed!${NC}"
echo ""
echo "To start the watchdog:"
echo "  sudo systemctl start homepi-watchdog.service"
echo ""
echo "To check status:"
echo "  sudo systemctl status homepi-watchdog.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u homepi-watchdog.service -f"
echo ""
echo "To run the enhanced startup script:"
echo "  sudo bash startup-enhanced.sh"
echo ""
echo -e "${YELLOW}The watchdog will automatically:${NC}"
echo "• Monitor HomePi service health"
echo "• Check network connectivity"
echo "• Fix Bluetooth issues"
echo "• Restart services when needed"
echo "• Reboot system as last resort"
echo ""
echo -e "${GREEN}Watchdog is ready to protect your HomePi!${NC}"
