#!/bin/bash

# Fix HomePi service for your user

echo "🔧 Fixing HomePi Service"
echo "════════════════════════"
echo ""

# Get current user
CURRENT_USER=$(whoami)
echo "Current user: $CURRENT_USER"
echo ""

# Stop the service if running
echo "Stopping service..."
sudo systemctl stop homepi.service

# Copy and update service file
echo "Updating service file..."
sed "s/User=pi/User=$CURRENT_USER/g; s/\/home\/pi/\/home\/$CURRENT_USER/g" homepi.service | sudo tee /etc/systemd/system/homepi.service

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable and start service
echo "Starting service..."
sudo systemctl enable homepi.service
sudo systemctl start homepi.service

echo ""
echo "Waiting for service to start..."
sleep 3

echo ""
echo "Service status:"
sudo systemctl status homepi.service --no-pager

echo ""
echo "✅ Done!"
echo ""
echo "Check if it's running:"
echo "  sudo systemctl status homepi.service"
echo ""
echo "View logs:"
echo "  sudo journalctl -u homepi.service -f"
echo ""
echo "Access web interface:"
echo "  http://$(hostname -I | awk '{print $1}'):5000"
echo ""

