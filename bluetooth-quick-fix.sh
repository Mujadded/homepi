#!/bin/bash

# Quick fix for Bluetooth "NotReady" error

echo "🔧 Fixing Bluetooth NotReady Error..."
echo ""

# Unblock Bluetooth (in case it's soft-blocked)
echo "1. Unblocking Bluetooth..."
sudo rfkill unblock bluetooth
sleep 2

# Restart Bluetooth service
echo "2. Restarting Bluetooth service..."
sudo systemctl restart bluetooth
sleep 3

# Power on the Bluetooth adapter
echo "3. Powering on Bluetooth adapter..."
echo -e "power on\nquit" | bluetoothctl

# Check status
echo ""
echo "4. Checking Bluetooth status..."
sudo systemctl status bluetooth --no-pager | head -5

echo ""
echo "5. Checking if Bluetooth is powered on..."
bluetoothctl show | grep "Powered"

echo ""
echo "✅ Bluetooth should now be ready!"
echo ""
echo "Try scanning again:"
echo "  bluetoothctl"
echo "  power on"
echo "  scan on"
echo ""

