#!/bin/bash
# Debug script for Bluetooth detection issues

echo "🔍 Bluetooth Detection Debug Script"
echo "=================================="
echo ""

echo "1. Checking Bluetooth service status..."
systemctl is-active bluetooth
echo ""

echo "2. Checking HCI device status..."
hciconfig hci0
echo ""

echo "3. Checking PulseAudio runtime path..."
ls -la /run/user/1000/pulse*
echo ""

echo "4. Testing pactl command as root..."
pactl list short sinks | grep bluez || echo "No bluez sinks found as root"
echo ""

echo "5. Testing pactl command as user..."
sudo -u mujadded bash -c 'export PULSE_RUNTIME_PATH=/run/user/1000/pulse && pactl list short sinks | grep bluez' || echo "No bluez sinks found as user"
echo ""

echo "6. Testing full command with RUNNING check..."
sudo -u mujadded bash -c 'export PULSE_RUNTIME_PATH=/run/user/1000/pulse && pactl list short sinks | grep bluez | grep RUNNING' || echo "No RUNNING bluez sinks found"
echo ""

echo "7. Checking all sinks as user..."
sudo -u mujadded bash -c 'export PULSE_RUNTIME_PATH=/run/user/1000/pulse && pactl list short sinks'
echo ""

echo "8. Checking PulseAudio process..."
ps aux | grep pulse
echo ""

echo "9. Checking user environment..."
sudo -u mujadded env | grep PULSE
echo ""

echo "✅ Debug complete!"
