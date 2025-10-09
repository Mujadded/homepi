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
    echo "Restarting PipeWire..."
    systemctl --user restart pipewire pipewire-pulse wireplumber 2>/dev/null
    sleep 3
    
    # Convert MAC address for card name (: to _)
    CARD_MAC=$(echo "$SPEAKER_MAC" | tr ':' '_')
    BT_CARD="bluez_card.$CARD_MAC"
    
    echo "Looking for Bluetooth card: $BT_CARD"
    
    # Check if card exists
    if pactl list cards short | grep -q "$BT_CARD"; then
        echo "✅ Card found!"
        echo ""
        echo "Setting A2DP profile (high-quality audio)..."
        
        # Try both profile name formats
        if pactl set-card-profile "$BT_CARD" a2dp-sink 2>/dev/null; then
            echo "✅ A2DP profile set (a2dp-sink)"
        elif pactl set-card-profile "$BT_CARD" a2dp_sink 2>/dev/null; then
            echo "✅ A2DP profile set (a2dp_sink)"
        else
            echo "⚠️  Could not set A2DP profile"
            echo ""
            echo "Available profiles:"
            pactl list cards | grep -A 20 "$BT_CARD" | grep "Profiles:" -A 10
        fi
        
        sleep 3
    else
        echo "⚠️  Card not found yet"
        echo ""
        echo "Available cards:"
        pactl list cards short
        echo ""
        echo "Trying to reconnect speaker..."
        bluetoothctl disconnect "$SPEAKER_MAC"
        sleep 2
        bluetoothctl connect "$SPEAKER_MAC"
        sleep 5
        
        # Try again
        if pactl list cards short | grep -q "bluez"; then
            BT_CARD=$(pactl list cards short | grep bluez | awk '{print $2}' | head -1)
            echo "✅ Card found: $BT_CARD"
            pactl set-card-profile "$BT_CARD" a2dp-sink 2>/dev/null || pactl set-card-profile "$BT_CARD" a2dp_sink 2>/dev/null
            sleep 2
        fi
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
    echo "Debugging information:"
    echo ""
    echo "Cards:"
    pactl list cards short
    echo ""
    echo "Sinks:"
    pactl list short sinks
    echo ""
    
    if [ "$AUDIO_SYSTEM" = "pipewire" ]; then
        echo "For PipeWire, you need to set A2DP profile manually:"
        echo ""
        CARD_MAC=$(echo "$SPEAKER_MAC" | tr ':' '_')
        echo "  pactl set-card-profile bluez_card.$CARD_MAC a2dp-sink"
        echo ""
    fi
    
    echo "Or run full setup:"
    echo "  bash setup-bluetooth.sh"
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

