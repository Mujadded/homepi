#!/bin/bash

# Bluetooth Auto-Connect Script
# Runs on boot to connect Bluetooth speaker and configure audio

SPEAKER_MAC="41:42:9F:04:78:F1"
LOG_FILE="/tmp/bluetooth-autoconnect.log"

echo "$(date): Starting Bluetooth auto-connect" >> "$LOG_FILE"

# Wait for system to be ready
sleep 10

# Ensure PulseAudio is running
if ! pulseaudio --check 2>/dev/null; then
    pulseaudio --start >> "$LOG_FILE" 2>&1
    sleep 3
fi

# Ensure Bluetooth service is running
systemctl is-active --quiet bluetooth || {
    sudo systemctl start bluetooth
    sleep 2
}

# Power on Bluetooth and connect
{
    echo "power on"
    sleep 2
    echo "connect $SPEAKER_MAC"
    sleep 5
    echo "exit"
} | bluetoothctl >> "$LOG_FILE" 2>&1

# Wait for audio sink to appear
sleep 3

# Find and set Bluetooth audio sink
BT_SINK=$(pactl list short sinks | grep bluez | awk '{print $2}' | head -1)

if [ -n "$BT_SINK" ]; then
    pactl set-default-sink "$BT_SINK" >> "$LOG_FILE" 2>&1
    pactl set-sink-volume "$BT_SINK" 70% >> "$LOG_FILE" 2>&1
    echo "$(date): Bluetooth audio configured successfully: $BT_SINK" >> "$LOG_FILE"
else
    echo "$(date): Bluetooth sink not found" >> "$LOG_FILE"
fi

echo "$(date): Auto-connect completed" >> "$LOG_FILE"

