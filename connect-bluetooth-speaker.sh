#!/bin/bash

# Bluetooth Speaker Connection Script for HomePi
# This script helps you easily connect your Bluetooth speaker

echo "🔊 Bluetooth Speaker Connection Helper"
echo "======================================="
echo ""

# Check if Bluetooth is available
if ! command -v bluetoothctl &> /dev/null; then
    echo "❌ bluetoothctl not found!"
    echo "Installing Bluetooth packages..."
    sudo apt-get update
    sudo apt-get install -y bluetooth bluez
fi

# Check if PulseAudio is installed
if ! command -v pactl &> /dev/null; then
    echo "❌ PulseAudio not found!"
    echo "Installing PulseAudio..."
    sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth
fi

# Unblock and start Bluetooth service
echo "Preparing Bluetooth..."
sudo rfkill unblock bluetooth
sleep 1
sudo systemctl restart bluetooth
sleep 2

# Start PulseAudio if not running
if ! pulseaudio --check; then
    echo "Starting PulseAudio..."
    pulseaudio --start
fi

echo ""
echo "📋 Instructions:"
echo "1. Put your Bluetooth speaker in PAIRING MODE now"
echo "2. Make sure it's within 3 feet of the Raspberry Pi"
echo "3. Press Enter when ready..."
read -r

echo ""
echo "🔍 Scanning for Bluetooth devices..."
echo "This will take about 10 seconds..."
echo ""

# Create a temporary file for bluetoothctl commands
TMP_FILE=$(mktemp)
cat > "$TMP_FILE" << 'EOF'
power on
agent on
default-agent
scan on
EOF

# Start scanning in background
timeout 12s bluetoothctl < "$TMP_FILE" > /tmp/bt_scan.log 2>&1 &
SCAN_PID=$!

# Wait for scan to complete
sleep 12

# Stop scanning
echo "scan off" | bluetoothctl > /dev/null 2>&1

# Parse the scan results
echo "📱 Found Bluetooth devices:"
echo ""
grep "Device" /tmp/bt_scan.log | grep -v "not available" | nl
echo ""

# Ask user to select device
echo "Enter the number of your speaker (or 'q' to quit): "
read -r SELECTION

if [ "$SELECTION" = "q" ]; then
    echo "Cancelled."
    rm -f "$TMP_FILE" /tmp/bt_scan.log
    exit 0
fi

# Get the MAC address of selected device
MAC_ADDRESS=$(grep "Device" /tmp/bt_scan.log | grep -v "not available" | sed -n "${SELECTION}p" | awk '{print $2}')

if [ -z "$MAC_ADDRESS" ]; then
    echo "❌ Invalid selection"
    rm -f "$TMP_FILE" /tmp/bt_scan.log
    exit 1
fi

echo ""
echo "🔗 Connecting to: $MAC_ADDRESS"
echo ""

# Connect to the device
cat > "$TMP_FILE" << EOF
pair $MAC_ADDRESS
trust $MAC_ADDRESS
connect $MAC_ADDRESS
exit
EOF

bluetoothctl < "$TMP_FILE"

# Wait a moment for connection
sleep 3

# Check if connected
if bluetoothctl info "$MAC_ADDRESS" | grep -q "Connected: yes"; then
    echo ""
    echo "✅ Successfully connected!"
    echo ""
    
    # Get the PulseAudio sink name
    echo "Setting up audio routing..."
    sleep 2
    
    # Convert MAC for PulseAudio (replace : with _)
    PA_MAC=$(echo "$MAC_ADDRESS" | tr ':' '_')
    SINK_NAME="bluez_sink.${PA_MAC}.a2dp_sink"
    
    # Try to set as default sink
    if pactl set-default-sink "$SINK_NAME" 2>/dev/null; then
        echo "✅ Bluetooth speaker set as default audio output"
        
        # Set volume to 70%
        pactl set-sink-volume "$SINK_NAME" 70%
        echo "🔊 Volume set to 70%"
    else
        echo "⚠️  Audio routing may need manual configuration"
        echo "Run this command manually:"
        echo "  pactl set-default-sink $SINK_NAME"
    fi
    
    echo ""
    echo "🎵 Testing audio..."
    echo "You should hear a test sound from your Bluetooth speaker..."
    speaker-test -t wav -c 2 -l 1 2>/dev/null || echo "⚠️  speaker-test not available"
    
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "Your Bluetooth speaker is now connected and ready to use with HomePi!"
    echo ""
    echo "💡 To reconnect in the future, run:"
    echo "   bluetoothctl connect $MAC_ADDRESS"
    echo ""
    echo "💡 To set as default audio:"
    echo "   pactl set-default-sink $SINK_NAME"
    echo ""
    
    # Save the MAC address for future reference
    echo "$MAC_ADDRESS" > ~/.homepi_bluetooth_speaker
    echo "📝 Speaker MAC saved to ~/.homepi_bluetooth_speaker"
    
else
    echo ""
    echo "❌ Failed to connect"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Make sure speaker is still in pairing mode"
    echo "2. Try moving speaker closer to Raspberry Pi"
    echo "3. Restart speaker and try again"
    echo "4. Check if speaker is already paired with another device"
fi

# Cleanup
rm -f "$TMP_FILE" /tmp/bt_scan.log

echo ""
echo "Done! You can now start HomePi:"
echo "  bash start.sh"
echo ""

