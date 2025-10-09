# 🎵 PipeWire Bluetooth Audio Setup

## Your Raspberry Pi Uses PipeWire

Modern Raspberry Pi OS uses **PipeWire** instead of PulseAudio. PipeWire is newer and more advanced, but the setup is slightly different.

---

## ✅ Quick Fix for PipeWire + Bluetooth

### Step 1: Install PipeWire Components

```bash
# Install PipeWire with PulseAudio compatibility
sudo apt-get update
sudo apt-get install -y pipewire pipewire-pulse wireplumber
```

### Step 2: Connect Your Bluetooth Speaker

```bash
bluetoothctl
power on
agent on
default-agent
scan on

# Wait for your speaker, note the MAC address
scan off

# Connect (replace with your MAC)
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```

### Step 3: Set A2DP Profile

This is the key step for PipeWire:

```bash
# List Bluetooth cards
pactl list cards short

# You should see something like: bluez_card.XX_XX_XX_XX_XX_XX

# Set the A2DP profile (high quality audio)
pactl set-card-profile bluez_card.XX_XX_XX_XX_XX_XX a2dp-sink

# Wait a moment
sleep 2

# Now check sinks
pactl list short sinks

# You should now see: bluez_sink.XX_XX_XX_XX_XX_XX
```

### Step 4: Set as Default Output

```bash
# Set Bluetooth as default (use the sink name from above)
pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX

# Set volume
pactl set-sink-volume @DEFAULT_SINK@ 70%

# Test
speaker-test -t wav -c 2 -l 1
```

---

## 🚀 Automated Script (Recommended!)

Use the automated fix script:

```bash
cd ~/homepi
bash fix-bluetooth-pipewire.sh
```

This script will:
1. ✅ Detect PipeWire
2. ✅ Install required components
3. ✅ Find your Bluetooth speaker
4. ✅ Set A2DP profile automatically
5. ✅ Configure audio routing
6. ✅ Test the audio

---

## 🔍 Understanding PipeWire

### What is PipeWire?
PipeWire is a modern replacement for PulseAudio. It provides:
- Better Bluetooth support
- Lower latency
- Better multi-device handling
- PulseAudio compatibility layer

### How HomePi Works with PipeWire
1. PipeWire provides `pipewire-pulse` (PulseAudio compatibility)
2. `pactl` commands work the same way
3. pygame uses SDL which talks to PulseAudio API
4. PipeWire's compatibility layer handles it all

---

## 🔧 Troubleshooting PipeWire + Bluetooth

### No Bluetooth Sink After Connecting?

**The issue:** Speaker is connected but no audio sink appears.

**The fix:** Set the A2DP profile manually:

```bash
# 1. Find your Bluetooth card
pactl list cards short

# Output example:
# 5  bluez_card.41_42_9F_04_78_F1  module-bluez5-device.c

# 2. Get detailed info
pactl list cards | grep -A 50 bluez

# Look for available profiles (should show a2dp-sink or a2dp_sink)

# 3. Set the A2DP profile
pactl set-card-profile bluez_card.41_42_9F_04_78_F1 a2dp-sink

# 4. Check sinks again
pactl list short sinks

# Should now show the Bluetooth sink!
```

### Sink Appears Then Disappears?

```bash
# Restart PipeWire services
systemctl --user restart pipewire pipewire-pulse wireplumber
sleep 3

# Reconnect speaker
bluetoothctl connect XX:XX:XX:XX:XX:XX
sleep 2

# Set profile
pactl set-card-profile bluez_card.XX_XX_XX_XX_XX_XX a2dp-sink
```

### Audio Stuttering or Cutting Out?

```bash
# Increase Bluetooth MTU size
sudo nano /etc/bluetooth/main.conf

# Add these under [General]:
[General]
FastConnectable = true
MultiProfile = multiple
ReconnectAttempts=7
ReconnectIntervals=1,2,4,8,16,32,64

# Restart Bluetooth
sudo systemctl restart bluetooth
```

### Check PipeWire Status

```bash
# Check if PipeWire is running
systemctl --user status pipewire
systemctl --user status pipewire-pulse
systemctl --user status wireplumber

# If not running, start them
systemctl --user start pipewire pipewire-pulse wireplumber
```

---

## 🎯 Complete Working Example

Here's a complete sequence that works:

```bash
# 1. Make sure packages are installed
sudo apt-get install -y pipewire pipewire-pulse wireplumber

# 2. Restart PipeWire
systemctl --user restart pipewire pipewire-pulse wireplumber
sleep 3

# 3. Connect Bluetooth speaker
bluetoothctl connect 41:42:9F:04:78:F1  # Your MAC
sleep 3

# 4. Set A2DP profile
pactl set-card-profile bluez_card.41_42_9F_04_78_F1 a2dp-sink
sleep 2

# 5. Set as default
pactl set-default-sink bluez_sink.41_42_9F_04_78_F1

# 6. Set volume
pactl set-sink-volume @DEFAULT_SINK@ 70%

# 7. Test
speaker-test -t wav -c 2 -l 1

# 8. Start HomePi
cd ~/homepi
bash start.sh
```

---

## 💡 Key Differences: PipeWire vs PulseAudio

| Aspect | PulseAudio | PipeWire |
|--------|-----------|----------|
| Command | `pulseaudio --start` | Runs as systemd service |
| Control | `pactl` commands | Same `pactl` commands |
| Bluetooth | Works | Better support |
| Profile | Auto-switches | Need to set A2DP manually |
| Latency | Higher | Lower |

---

## 🎵 Why Set A2DP Profile?

**A2DP** = Advanced Audio Distribution Profile
- High quality audio streaming
- Stereo sound
- Better bitrate

**Without A2DP:**
- Speaker connects but no audio sink appears
- Can't route audio to it

**With A2DP:**
- Audio sink appears: `bluez_sink.XX_XX_XX_XX_XX_XX`
- Can set as default output
- HomePi can play through it

---

## 📝 Summary

For PipeWire + Bluetooth:
1. ✅ Connect speaker with bluetoothctl
2. ✅ **Set A2DP profile** (this is the key!)
3. ✅ Set sink as default
4. ✅ Start HomePi

The `fix-bluetooth-pipewire.sh` script does all this automatically!

---

**Your HomePi will now work perfectly with Bluetooth on PipeWire!** 🎉

