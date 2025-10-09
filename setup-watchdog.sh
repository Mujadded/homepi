#!/bin/bash

# Setup Watchdog Service

echo "🐕 Setting up HomePi Watchdog Service"
echo "════════════════════════════════════════"
echo ""

CURRENT_USER=$(whoami)

# Make watchdog script executable
chmod +x watchdog.sh

# Update service file with current user
echo "Creating watchdog service..."
sed "s/User=mujadded/User=$CURRENT_USER/g; s/\/home\/mujadded/\/home\/$CURRENT_USER/g" homepi-watchdog.service | sudo tee /etc/systemd/system/homepi-watchdog.service > /dev/null

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the watchdog
sudo systemctl enable homepi-watchdog.service
sudo systemctl start homepi-watchdog.service

echo ""
echo "✅ Watchdog service installed!"
echo ""
echo "The watchdog will:"
echo "  ✓ Check HomePi every 60 seconds"
echo "  ✓ Auto-restart if service stops"
echo "  ✓ Auto-restart if API not responding"
echo "  ✓ Log all actions to /tmp/homepi-watchdog.log"
echo ""
echo "Commands:"
echo "  Status:  sudo systemctl status homepi-watchdog"
echo "  Logs:    cat /tmp/homepi-watchdog.log"
echo "  Stop:    sudo systemctl stop homepi-watchdog"
echo ""

