# 🔊 Bluetooth Speaker Setup for Raspberry Pi

## Quick Setup Guide

### Step 1: Put Your Speaker in Pairing Mode
- Turn on your Bluetooth speaker
- Press and hold the Bluetooth/pairing button until it blinks
- Keep it close to the Raspberry Pi (within 3 feet)

### Step 2: Prepare Bluetooth (Important!)

First, make sure Bluetooth is ready:

```bash
# Unblock Bluetooth
sudo rfkill unblock bluetooth

# Restart Bluetooth service
sudo systemctl restart bluetooth

# Wait a few seconds
sleep 3
```

### Step 3: Connect via Command Line

```bash
# Start Bluetooth control
bluetoothctl

# Once in bluetoothctl prompt:
power on
agent on
default-agent
scan on

# Wait for your speaker to appear (look for its name)
# Note the MAC address (looks like: XX:XX:XX:XX:XX:XX)

# Once you see your speaker, stop scanning
scan off

# Pair with your speaker (replace XX:XX:XX:XX:XX:XX with actual MAC)
pair XX:XX:XX:XX:XX:XX

# Trust the device (so it auto-connects in future)
trust XX:XX:XX:XX:XX:XX

# Connect to the device
connect XX:XX:XX:XX:XX:XX

# Exit bluetoothctl
exit
```

### Step 4: Set Bluetooth as Default Audio Output

```bash
# Install required packages
sudo apt-get install pulseaudio pulseaudio-module-bluetooth

# Start PulseAudio
pulseaudio --start

# Set Bluetooth as default output
pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
# (Replace XX_XX_XX_XX_XX_XX with your speaker's MAC using underscores)
```

### Step 5: Test the Audio

```bash
# Test with speaker-test
speaker-test -t wav -c 2

# Or test with a sound file
aplay /usr/share/sounds/alsa/Front_Center.wav
```

---

## 🎯 Alternative Method: Using GUI

If you have desktop environment:

1. **Open Bluetooth Settings**
   ```bash
   sudo raspi-config
   # Navigate to: System Options → Boot / Auto Login
   # Select: Desktop or Desktop Autologin (if not already)
   ```

2. **Use Bluetooth Icon**
   - Click Bluetooth icon in taskbar (top-right)
   - Click "Add Device..."
   - Select your speaker from the list
   - Click "Pair"
   - Right-click Bluetooth icon → "Connect to Audio Device"

---

## 🔧 Automated Setup Script

I'll create a helper script for you:

```bash
# Save this as connect-bluetooth-speaker.sh
bash connect-bluetooth-speaker.sh
```

This will guide you through the process interactively.

---

## 🎛️ Setting Default Audio Output

### Check Available Audio Outputs

```bash
# List all audio sinks
pactl list short sinks

# You'll see something like:
# 0  alsa_output.platform-bcm2835_audio.analog-stereo  (3.5mm jack)
# 1  bluez_sink.AA_BB_CC_DD_EE_FF.a2dp_sink           (Bluetooth)
```

### Set Bluetooth as Default

```bash
# Method 1: Using pactl (temporary - until reboot)
pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink

# Method 2: Make it permanent
echo "set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink" >> ~/.config/pulse/default.pa
```

---

## 🔄 Auto-Connect on Boot

### Make Bluetooth Auto-Connect

```bash
# Edit Bluetooth service
sudo nano /etc/systemd/system/bt-agent.service
```

Add this content:
```ini
[Unit]
Description=Bluetooth Auth Agent
After=bluetooth.service
PartOf=bluetooth.service

[Service]
Type=simple
ExecStart=/usr/bin/bluetoothctl -- agent on
ExecStartPost=/usr/bin/bluetoothctl -- default-agent

[Install]
WantedBy=bluetooth.target
```

Enable it:
```bash
sudo systemctl enable bt-agent.service
sudo systemctl start bt-agent.service
```

---

## 📋 Complete Setup Script

Run this one-time setup:

```bash
#!/bin/bash
# Complete Bluetooth Audio Setup

echo "🔊 Bluetooth Speaker Setup for HomePi"
echo "====================================="
echo ""

# Install required packages
echo "Installing PulseAudio and Bluetooth modules..."
sudo apt-get update
sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth bluez

# Start Bluetooth service
echo "Starting Bluetooth service..."
sudo systemctl start bluetooth
sudo systemctl enable bluetooth

# Start PulseAudio
echo "Starting PulseAudio..."
pulseaudio --start

echo ""
echo "✅ Setup complete!"
echo ""
echo "Now run: bash connect-bluetooth-speaker.sh"
echo "to connect your speaker."
```

---

## 🎵 Testing HomePi with Bluetooth Speaker

After connecting your speaker:

```bash
# Start HomePi
cd ~/homepi
bash start.sh

# Open web interface
# Try playing a song
# Audio should come from your Bluetooth speaker!
```

---

## 🔍 Troubleshooting

### "NotReady" Error When Scanning?

```bash
# Quick fix - run this script
bash bluetooth-quick-fix.sh

# Or manually:
# 1. Unblock Bluetooth
sudo rfkill unblock bluetooth

# 2. Restart Bluetooth service
sudo systemctl restart bluetooth

# 3. Wait a few seconds, then try again
sleep 3
bluetoothctl

# In bluetoothctl:
power on
scan on
```

### Speaker Not Found During Scan?

```bash
# Restart Bluetooth service
sudo systemctl restart bluetooth

# Make sure speaker is in pairing mode
# Try scanning again
```

### Audio Not Coming from Speaker? (Most Common Issue!)

This is usually because audio routing isn't set up. **Use the fix script:**

```bash
# Automatic fix - run this!
bash fix-bluetooth-audio.sh
```

**Or fix manually:**

```bash
# 1. Install/restart PulseAudio
sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth
pulseaudio --kill
sleep 2
pulseaudio --start
sleep 3

# 2. Find your Bluetooth audio sink
pactl list short sinks

# Look for a line like: bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink

# 3. Set it as default (replace with your sink name)
pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink

# 4. Set volume
pactl set-sink-volume @DEFAULT_SINK@ 70%

# 5. Test
speaker-test -t wav -c 2 -l 1
```

**If sink not found:**
```bash
# Disconnect and reconnect speaker
bluetoothctl disconnect XX:XX:XX:XX:XX:XX
sleep 2
bluetoothctl connect XX:XX:XX:XX:XX:XX
sleep 5

# Try finding sink again
pactl list short sinks
```

### Connection Drops?

```bash
# Increase Bluetooth power
sudo hciconfig hci0 class 0x200428

# Edit Bluetooth config
sudo nano /etc/bluetooth/main.conf

# Add/modify these lines:
[General]
DiscoverableTimeout = 0
PairableTimeout = 0
```

### No Sound in HomePi?

**Quick fix:**
```bash
# Run the audio fix script
bash fix-bluetooth-audio.sh

# Then restart HomePi
cd ~/homepi
bash start.sh
```

**Manual fix:**
```bash
# 1. Make sure PulseAudio is running
pulseaudio --kill
sleep 2
pulseaudio --start
sleep 3

# 2. Set Bluetooth as default
pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink

# 3. Restart HomePi
cd ~/homepi
# Stop current instance (Ctrl+C)
bash start.sh
```

**Check pygame audio:**
```bash
# pygame needs SDL audio env variable for PulseAudio
export SDL_AUDIODRIVER=pulseaudio
bash start.sh
```

---

## 🎯 Quick Commands Reference

```bash
# Connect to speaker
bluetoothctl connect XX:XX:XX:XX:XX:XX

# Disconnect speaker
bluetoothctl disconnect XX:XX:XX:XX:XX:XX

# Check connection status
bluetoothctl info XX:XX:XX:XX:XX:XX

# List paired devices
bluetoothctl paired-devices

# Set volume
pactl set-sink-volume @DEFAULT_SINK@ 70%
```

---

## 💡 Tips

1. **Keep Speaker Close**: During pairing, keep speaker within 3 feet
2. **Battery Level**: Check speaker battery before long sessions
3. **Auto-reconnect**: Once trusted, speaker should auto-connect on boot
4. **Volume Control**: Use both speaker's volume and web interface volume
5. **Range**: Bluetooth typically works up to 30 feet without obstacles

---

## 🔋 Power Saving

If you want to disable Bluetooth when not needed:

```bash
# Disable Bluetooth
sudo rfkill block bluetooth

# Enable Bluetooth
sudo rfkill unblock bluetooth
```

---

## 📱 Multiple Speakers?

You can pair multiple speakers, but only one can be active at a time:

```bash
# Switch between speakers
bluetoothctl disconnect XX:XX:XX:XX:XX:XX  # Disconnect current
bluetoothctl connect YY:YY:YY:YY:YY:YY    # Connect to another
```

---

**Your HomePi is now ready for Bluetooth audio!** 🎉

For more help, see the troubleshooting section or check Raspberry Pi Bluetooth documentation.

