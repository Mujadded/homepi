#!/bin/bash

# Complete switch from PipeWire to PulseAudio
# Fixes all conflicts and gets Bluetooth working

echo "🔧 Switching to PulseAudio (Complete)"
echo "═════════════════════════════════════"
echo ""

SPEAKER_MAC="41:42:9F:04:78:F1"

echo "Step 1: Stopping all audio services..."
# Stop PipeWire completely
systemctl --user stop pipewire.socket pipewire pipewire-pulse wireplumber 2>/dev/null || true
systemctl --user mask pipewire.socket pipewire pipewire-pulse wireplumber 2>/dev/null || true

# Kill any running instances
pkill -9 pipewire 2>/dev/null || true
pkill -9 wireplumber 2>/dev/null || true
pkill -9 pulseaudio 2>/dev/null || true

sleep 2

echo ""
echo "Step 2: Installing PulseAudio..."
sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth

echo ""
echo "Step 3: Removing PipeWire conflicts..."
sudo apt-get remove -y pipewire-pulse 2>/dev/null || true

echo ""
echo "Step 4: Configuring PulseAudio for Bluetooth..."

# Create PulseAudio config directory
mkdir -p ~/.config/pulse

# Enable Bluetooth modules
cat > ~/.config/pulse/default.pa << 'EOF'
.include /etc/pulse/default.pa

# Bluetooth support
load-module module-bluetooth-discover
load-module module-bluetooth-policy
load-module module-switch-on-connect
EOF

echo ""
echo "Step 5: Starting PulseAudio..."
# Make sure it's fully killed first
pulseaudio --kill 2>/dev/null || true
sleep 2

# Start in daemon mode
pulseaudio --start --log-target=syslog
sleep 3

# Check if it's running
if pulseaudio --check; then
    echo "✅ PulseAudio is running"
else
    echo "❌ PulseAudio failed to start"
    echo ""
    echo "Trying alternative method..."
    pulseaudio -D
    sleep 3
fi

echo ""
echo "Step 6: Restarting Bluetooth service..."
sudo systemctl restart bluetooth
sleep 2

echo ""
echo "Step 7: Connecting to speaker..."
bluetoothctl <<EOF
power on
agent on
default-agent
connect $SPEAKER_MAC
exit
EOF

sleep 5

echo ""
echo "Step 8: Checking for Bluetooth audio sink..."
echo ""

pactl list short sinks

BT_SINK=$(pactl list short sinks | grep bluez | awk '{print $2}' | head -1)

if [ -n "$BT_SINK" ]; then
    echo ""
    echo "✅ Bluetooth sink found: $BT_SINK"
    echo ""
    
    # Set as default
    pactl set-default-sink "$BT_SINK"
    pactl set-sink-volume "$BT_SINK" 70%
    pactl set-sink-mute "$BT_SINK" 0
    
    echo "✅ Bluetooth speaker set as default audio output"
    echo ""
    echo "🎵 Testing audio..."
    speaker-test -t wav -c 2 -l 1 2>/dev/null || aplay /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null || echo "Test sound not available"
    
    echo ""
    echo "════════════════════════════════════"
    echo "  ✅ SUCCESS!"
    echo "════════════════════════════════════"
    echo ""
    echo "Your Bluetooth speaker is now configured!"
    echo ""
    echo "Default sink: $BT_SINK"
    echo ""
    echo "Next steps:"
    echo "  1. cd ~/homepi"
    echo "  2. bash start.sh"
    echo ""
    echo "Audio will play through your Bluetooth speaker! 🎵"
    echo ""
    
    # Save for future
    echo "$SPEAKER_MAC" > ~/.homepi_bluetooth_speaker
    
else
    echo ""
    echo "❌ Bluetooth sink not found"
    echo ""
    echo "Debugging information:"
    echo ""
    echo "PulseAudio status:"
    pulseaudio --check && echo "  Running" || echo "  Not running"
    echo ""
    echo "Available sinks:"
    pactl list short sinks
    echo ""
    echo "Bluetooth connection:"
    bluetoothctl info $SPEAKER_MAC | grep "Connected"
    echo ""
    echo "Try manual connection:"
    echo "  bluetoothctl connect $SPEAKER_MAC"
    echo "  pactl list short sinks"
    echo ""
fi

