#!/bin/bash

# Fix Bluetooth Audio with PipeWire
# Modern Raspberry Pi OS uses PipeWire instead of PulseAudio

echo "🔊 Fixing Bluetooth Audio with PipeWire..."
echo ""

# Check what audio system is running
if systemctl --user is-active --quiet pipewire; then
    echo "✅ PipeWire is running"
    AUDIO_SYSTEM="pipewire"
elif pulseaudio --check 2>/dev/null; then
    echo "✅ PulseAudio is running"
    AUDIO_SYSTEM="pulseaudio"
else
    echo "⚠️  No audio system detected"
    AUDIO_SYSTEM="none"
fi

echo ""
echo "Audio System: $AUDIO_SYSTEM"
echo ""

# Install PipeWire PulseAudio compatibility if needed
if [ "$AUDIO_SYSTEM" = "pipewire" ]; then
    echo "1. Ensuring PipeWire PulseAudio compatibility..."
    sudo apt-get install -y pipewire-pulse wireplumber
    
    # Restart PipeWire
    echo "2. Restarting PipeWire..."
    systemctl --user restart pipewire pipewire-pulse wireplumber
    sleep 3
fi

# Use pactl (works with both PulseAudio and PipeWire)
echo "3. Looking for audio sinks..."
pactl list short sinks

echo ""
echo "4. Looking for Bluetooth speaker..."

# Find Bluetooth sink (works with PipeWire too)
BT_SINK=$(pactl list short sinks | grep -i "bluez" | awk '{print $2}' | head -1)

if [ -z "$BT_SINK" ]; then
    echo ""
    echo "❌ No Bluetooth audio sink found!"
    echo ""
    echo "Let's check your Bluetooth connection..."
    echo ""
    
    # Check connected Bluetooth devices
    echo "Connected Bluetooth devices:"
    bluetoothctl devices | while read -r line; do
        MAC=$(echo "$line" | awk '{print $2}')
        NAME=$(echo "$line" | cut -d' ' -f3-)
        if bluetoothctl info "$MAC" | grep -q "Connected: yes"; then
            echo "  ✅ $NAME ($MAC) - Connected"
            
            # Try to get the card info
            CARD=$(pactl list cards short | grep -i bluez | awk '{print $2}')
            if [ -n "$CARD" ]; then
                echo "     Card found: $CARD"
                echo "     Setting A2DP profile..."
                pactl set-card-profile "$CARD" a2dp-sink 2>/dev/null || pactl set-card-profile "$CARD" a2dp_sink 2>/dev/null
                sleep 2
            fi
        else
            echo "  ❌ $NAME ($MAC) - Not connected"
        fi
    done
    
    echo ""
    echo "Checking for sinks again..."
    BT_SINK=$(pactl list short sinks | grep -i "bluez" | awk '{print $2}' | head -1)
fi

if [ -z "$BT_SINK" ]; then
    echo ""
    echo "❌ Still no Bluetooth sink found!"
    echo ""
    echo "Manual troubleshooting:"
    echo ""
    echo "1. Make sure speaker is connected:"
    echo "   bluetoothctl"
    echo "   connect XX:XX:XX:XX:XX:XX"
    echo "   exit"
    echo ""
    echo "2. List all cards:"
    echo "   pactl list cards"
    echo ""
    echo "3. Set A2DP profile manually:"
    echo "   pactl set-card-profile bluez_card.XX_XX_XX_XX_XX_XX a2dp-sink"
    echo ""
    exit 1
fi

echo "✅ Found Bluetooth sink: $BT_SINK"

# Set as default
echo ""
echo "5. Setting Bluetooth speaker as default audio output..."
pactl set-default-sink "$BT_SINK"

# Set volume
echo "6. Setting volume to 70%..."
pactl set-sink-volume "$BT_SINK" 70%

# Unmute if muted
pactl set-sink-mute "$BT_SINK" 0

echo ""
echo "7. Current audio configuration:"
pactl info | grep "Default Sink"

echo ""
echo "✅ Audio routing configured!"
echo ""

# Test audio
echo "🎵 Testing audio..."
echo "You should hear a test sound from your Bluetooth speaker..."
echo ""

# Try different test methods
if command -v speaker-test &> /dev/null; then
    speaker-test -t wav -c 2 -l 1 2>/dev/null
elif [ -f /usr/share/sounds/alsa/Front_Center.wav ]; then
    aplay /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null
else
    echo "⚠️  No test sound available, but routing is configured!"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Current default sink: $BT_SINK"
echo ""
echo "If you heard the test sound, you're all set! 🎵"
echo ""
echo "Now restart HomePi:"
echo "  bash start.sh"
echo ""

