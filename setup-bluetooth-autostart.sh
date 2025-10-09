#!/bin/bash

# Setup Bluetooth to auto-connect on boot

echo "🔧 Setting up Bluetooth Auto-Connect on Boot"
echo "════════════════════════════════════════════"
echo ""

SPEAKER_MAC="41:42:9F:04:78:F1"
CURRENT_USER=$(whoami)
HOME_DIR=$(eval echo ~$CURRENT_USER)

echo "User: $CURRENT_USER"
echo "Home: $HOME_DIR"
echo "Speaker MAC: $SPEAKER_MAC"
echo ""

# Update the MAC address in the script
echo "1. Updating Bluetooth auto-connect script..."
sed -i "s/SPEAKER_MAC=.*/SPEAKER_MAC=\"$SPEAKER_MAC\"/" bluetooth-autoconnect.sh
chmod +x bluetooth-autoconnect.sh

# Update service file with current user
echo "2. Creating systemd service..."
sed "s/User=mujadded/User=$CURRENT_USER/g; s/\/home\/mujadded/\/home\/$CURRENT_USER/g" bluetooth-autoconnect.service | sudo tee /etc/systemd/system/bluetooth-autoconnect.service > /dev/null

# Also ensure Bluetooth is set to auto-power-on
echo "3. Configuring Bluetooth to power on automatically..."
sudo mkdir -p /etc/bluetooth
if ! grep -q "AutoEnable=true" /etc/bluetooth/main.conf 2>/dev/null; then
    echo "" | sudo tee -a /etc/bluetooth/main.conf > /dev/null
    echo "[Policy]" | sudo tee -a /etc/bluetooth/main.conf > /dev/null
    echo "AutoEnable=true" | sudo tee -a /etc/bluetooth/main.conf > /dev/null
fi

# Trust the speaker so it auto-connects
echo "4. Trusting Bluetooth speaker..."
bluetoothctl trust "$SPEAKER_MAC" 2>/dev/null

# Enable the service
echo "5. Enabling auto-connect service..."
sudo systemctl daemon-reload
sudo systemctl enable bluetooth-autoconnect.service

echo ""
echo "✅ Setup complete!"
echo ""
echo "The Bluetooth speaker will now:"
echo "  ✓ Auto-connect on boot"
echo "  ✓ Auto-configure audio routing"
echo "  ✓ Set to 70% volume"
echo ""
echo "To test now:"
echo "  sudo systemctl start bluetooth-autoconnect.service"
echo ""
echo "Check status:"
echo "  sudo systemctl status bluetooth-autoconnect.service"
echo ""
echo "View logs:"
echo "  cat /tmp/bluetooth-autoconnect.log"
echo ""
echo "Reboot to test:"
echo "  sudo reboot"
echo ""

