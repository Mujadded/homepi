#!/bin/bash

# Complete fix for PipeWire + Bluetooth on Raspberry Pi
# Addresses the issue where Bluetooth cards don't appear in PipeWire

echo "🔧 Complete PipeWire + Bluetooth Fix"
echo "════════════════════════════════════"
echo ""

SPEAKER_MAC="41:42:9F:04:78:F1"


echo "✅ WirePlumber Bluetooth config created"

echo ""
echo "Step 3: Restarting audio services..."
systemctl --user daemon-reload
systemctl --user restart pipewire pipewire-pulse wireplumber
sleep 5

echo ""
echo "Step 4: Checking Bluetooth service..."
sudo systemctl restart bluetooth
sleep 2

echo ""
echo "Step 5: Connecting to speaker..."
bluetoothctl <<EOF
power on
connect $SPEAKER_MAC
exit
EOF

sleep 5

echo ""
echo "Step 6: Checking for Bluetooth card..."
echo ""
pactl list cards short

echo ""
BT_CARD=$(pactl list cards short | grep bluez | awk '{print $2}')

if [ -z "$BT_CARD" ]; then
    echo "❌ Bluetooth card still not appearing"
    echo ""
    echo "This is a known issue with PipeWire on Raspberry Pi."
    echo ""
    echo "WORKAROUND: Install PulseAudio instead"
    echo ""
    read -p "Would you like to switch to PulseAudio? (y/n): " SWITCH
    
    if [ "$SWITCH" = "y" ] || [ "$SWITCH" = "Y" ]; then
        echo ""
        echo "Installing PulseAudio..."
        sudo apt-get remove -y pipewire-pulse
        sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth
        
        # Disable PipeWire services
        systemctl --user mask pipewire-pulse
        systemctl --user stop pipewire pipewire-pulse wireplumber
        
        # Start PulseAudio
        pulseaudio --kill 2>/dev/null
        sleep 2
        pulseaudio --start
        sleep 3
        
        echo ""
        echo "✅ Switched to PulseAudio"
        echo ""
        echo "Now reconnecting speaker..."
        bluetoothctl connect $SPEAKER_MAC
        sleep 3
        
        # Check for sink
        BT_SINK=$(pactl list short sinks | grep bluez | awk '{print $2}')
        if [ -n "$BT_SINK" ]; then
            echo "✅ Bluetooth sink found: $BT_SINK"
            pactl set-default-sink "$BT_SINK"
            pactl set-sink-volume "$BT_SINK" 70%
            echo ""
            echo "🎵 Testing audio..."
            speaker-test -t wav -c 2 -l 1 2>/dev/null
            echo ""
            echo "✅ Done! Audio should work now."
            echo ""
            echo "Start HomePi: bash start.sh"
        else
            echo "❌ Still no sink. Check Bluetooth connection."
        fi
    fi
else
    echo "✅ Bluetooth card found: $BT_CARD"
    echo ""
    echo "Setting A2DP profile..."
    pactl set-card-profile "$BT_CARD" a2dp-sink || pactl set-card-profile "$BT_CARD" a2dp_sink
    sleep 2
    
    BT_SINK=$(pactl list short sinks | grep bluez | awk '{print $2}')
    if [ -n "$BT_SINK" ]; then
        echo "✅ Bluetooth sink found: $BT_SINK"
        pactl set-default-sink "$BT_SINK"
        pactl set-sink-volume "$BT_SINK" 70%
        echo ""
        echo "🎵 Testing audio..."
        speaker-test -t wav -c 2 -l 1 2>/dev/null
        echo ""
        echo "✅ Done! Start HomePi: bash start.sh"
    else
        echo "❌ Sink still not appearing"
    fi
fi

echo ""

