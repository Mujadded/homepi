#!/bin/bash

# HomePi Upgrade Script
# Installs all new reliability features

echo "╔════════════════════════════════════════╗"
echo "║   HomePi Reliability Upgrade v2.0      ║"
echo "╚════════════════════════════════════════╝"
echo ""

CURRENT_USER=$(whoami)
HOME_DIR=$(eval echo ~$CURRENT_USER)
PROJECT_DIR="$HOME_DIR/homepi"

cd "$PROJECT_DIR" || exit 1

echo "📦 Step 1: Installing dependencies..."
echo "──────────────────────────────────────"
source venv/bin/activate
pip install psutil
echo "✅ Dependencies installed"
echo ""

echo "🐕 Step 2: Setting up Watchdog service..."
echo "──────────────────────────────────────"
chmod +x watchdog.sh setup-watchdog.sh
bash setup-watchdog.sh
echo ""

echo "🔊 Step 3: Setting up Bluetooth auto-connect..."
echo "──────────────────────────────────────"
chmod +x bluetooth-autoconnect.sh setup-bluetooth-autostart.sh
bash setup-bluetooth-autostart.sh
echo ""

echo "🔄 Step 4: Restarting services..."
echo "──────────────────────────────────────"
sudo systemctl restart homepi.service
sleep 3
echo ""

echo "✅ Step 5: Verifying installation..."
echo "──────────────────────────────────────"
echo ""

if systemctl is-active --quiet homepi.service; then
    echo "✅ HomePi service: Running"
else
    echo "❌ HomePi service: Not running"
fi

if systemctl is-active --quiet homepi-watchdog.service; then
    echo "✅ Watchdog service: Running"
else
    echo "❌ Watchdog service: Not running"
fi

if systemctl is-active --quiet bluetooth-autoconnect.service; then
    echo "✅ Bluetooth auto-connect: Running"
else
    echo "⚠️  Bluetooth auto-connect: Not running (may be OK if not using Bluetooth)"
fi

echo ""
echo "╔════════════════════════════════════════╗"
echo "║        Upgrade Complete! 🎉            ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Your HomePi now has:"
echo "  ✓ Auto-restart on crashes"
echo "  ✓ Daily automatic backups (3 AM)"
echo "  ✓ System health monitoring"
echo "  ✓ Bluetooth auto-reconnect"
echo ""
echo "Access your HomePi at:"
echo "  http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "View logs:"
echo "  sudo journalctl -u homepi.service -f"
echo "  cat /tmp/homepi-watchdog.log"
echo "  cat /tmp/bluetooth-autoconnect.log"
echo ""
echo "System status:"
echo "  sudo systemctl status homepi.service"
echo "  sudo systemctl status homepi-watchdog.service"
echo "  sudo systemctl status bluetooth-autoconnect.service"
echo ""

