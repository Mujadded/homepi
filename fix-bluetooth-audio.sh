#!/bin/bash

# Fix Bluetooth Audio Routing
# Use this when Bluetooth is connected but no sound comes out

echo "🔊 Fixing Bluetooth Audio Routing..."
echo ""

# Check if PulseAudio is installed
if ! command -v pactl &> /dev/null; then
    echo "Installing PulseAudio..."
    sudo apt-get update
    sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth
fi

# Kill any existing PulseAudio instances
echo "1. Restarting PulseAudio..."
pulseaudio --kill 2>/dev/null || true
sleep 2

# Start PulseAudio
pulseaudio --start
sleep 3

# List available sinks
echo ""
echo "2. Available audio outputs:"
pactl list short sinks

echo ""
echo "3. Looking for Bluetooth speaker..."

# Find Bluetooth sink
BT_SINK=$(pactl list short sinks | grep bluez | awk '{print $2}' | head -1)

if [ -z "$BT_SINK" ]; then
    echo ""
    echo "❌ No Bluetooth audio sink found!"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Make sure your speaker is connected:"
    echo "   bluetoothctl info XX:XX:XX:XX:XX:XX"
    echo ""
    echo "2. Reconnect the speaker:"
    echo "   bluetoothctl connect XX:XX:XX:XX:XX:XX"
    echo ""
    echo "3. Check if A2DP profile is active:"
    echo "   pactl list cards"
    echo ""
    exit 1
fi

echo "✅ Found Bluetooth sink: $BT_SINK"

# Set as default sink
echo ""
echo "4. Setting Bluetooth speaker as default audio output..."
pactl set-default-sink "$BT_SINK"

# Set volume to 70%
echo "5. Setting volume to 70%..."
pactl set-sink-volume "$BT_SINK" 70%

# Check status
echo ""
echo "6. Current default sink:"
pactl info | grep "Default Sink"

echo ""
echo "✅ Audio routing configured!"
echo ""
echo "🎵 Testing audio..."
echo "You should hear a test sound from your Bluetooth speaker now..."
echo ""

# Test audio
speaker-test -t wav -c 2 -l 1 2>/dev/null || aplay /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null || echo "⚠️  Test sound not available, but routing is set up!"

echo ""
echo "🎉 Done! Audio should now play through your Bluetooth speaker."
echo ""
echo "If you still don't hear anything:"
echo "1. Check speaker volume (buttons on speaker)"
echo "2. Check speaker battery"
echo "3. Move speaker closer to Raspberry Pi"
echo "4. Run: bluetoothctl info XX:XX:XX:XX:XX:XX"
echo "   Make sure it says 'Connected: yes'"
echo ""

