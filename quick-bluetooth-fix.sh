#!/bin/bash

# Quick fix for already connected Bluetooth speaker
# Use this if speaker is connected but audio isn't working

echo "🔊 Quick Bluetooth Audio Fix"
echo "═══════════════════════════════"
echo ""

# Find connected Bluetooth speaker
SPEAKER_MAC=$(bluetoothctl devices Connected 2>/dev/null | grep "Device" | awk '{print $2}' | head -1)

if [ -z "$SPEAKER_MAC" ]; then
    echo "❌ No Bluetooth speaker connected!"
    echo ""
    echo "Please run: bash setup-bluetooth.sh"
    exit 1
fi

DEVICE_NAME=$(bluetoothctl info "$SPEAKER_MAC" | grep "Name:" | cut -d: -f2- | xargs)
echo "✅ Found connected speaker: $DEVICE_NAME"
echo "   MAC: $SPEAKER_MAC"
echo ""

# Detect audio system
if systemctl --user is-active --quiet pipewire-pulse 2>/dev/null; then
    AUDIO_SYSTEM="pipewire"
    echo "ℹ️  Audio System: PipeWire"
else
    AUDIO_SYSTEM="pulseaudio"
    echo "ℹ️  Audio System: PulseAudio"
fi

echo ""
echo "🔧 Configuring audio routing..."
echo ""

# Restart audio system
if [ "$AUDIO_SYSTEM" = "pipewire" ]; then
    systemctl --user restart pipewire pipewire-pulse wireplumber 2>/dev/null
    sleep 3
    
    # Set A2DP profile
    BT_CARD=$(pactl list cards short | grep bluez | awk '{print $2}' | head -1)
    if [ -n "$BT_CARD" ]; then
        echo "Setting A2DP profile..."
        pactl set-card-profile "$BT_CARD" a2dp-sink 2>/dev/null || pactl set-card-profile "$BT_CARD" a2dp_sink 2>/dev/null
        sleep 2
    fi
else
    pulseaudio --kill 2>/dev/null
    sleep 2
    pulseaudio --start
    sleep 2
fi

# Find and set Bluetooth sink
echo "Looking for Bluetooth audio sink..."
for i in {1..5}; do
    BT_SINK=$(pactl list short sinks | grep -i bluez | awk '{print $2}' | head -1)
    if [ -n "$BT_SINK" ]; then
        break
    fi
    echo "  Attempt $i/5..."
    sleep 1
done

if [ -z "$BT_SINK" ]; then
    echo "❌ Could not find Bluetooth audio sink"
    echo ""
    echo "Try:"
    echo "  1. Disconnect and reconnect: bluetoothctl disconnect $SPEAKER_MAC && bluetoothctl connect $SPEAKER_MAC"
    echo "  2. Run full setup: bash setup-bluetooth.sh"
    exit 1
fi

echo "✅ Found sink: $BT_SINK"
echo ""

# Set as default
pactl set-default-sink "$BT_SINK"
pactl set-sink-volume "$BT_SINK" 70%
pactl set-sink-mute "$BT_SINK" 0

echo "✅ Bluetooth speaker set as default audio output!"
echo ""
echo "🎵 Testing..."
speaker-test -t wav -c 2 -l 1 2>/dev/null || echo "Test completed"

echo ""
echo "✅ Done! Start HomePi: bash start.sh"
echo ""

