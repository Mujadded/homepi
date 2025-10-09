# 🚀 Quick Start Guide

## Get HomePi Running in 5 Minutes!

### Step 1: Transfer to Raspberry Pi
```bash
# Option 1: Clone from git (if you've pushed it)
git clone <your-repo-url> homepi
cd homepi

# Option 2: Copy files directly
scp -r homepi pi@raspberrypi.local:~/
```

### Step 2: Install Dependencies
```bash
cd homepi
bash install.sh
```

This will:
- Update system packages
- Install Python, pygame, and ffmpeg
- Install Python requirements
- Create necessary directories
- Set permissions

### Step 3: Start the Application

**Option 1: Using the start script (easiest)**
```bash
bash start.sh
```

**Option 2: Using virtual environment directly**
```bash
source venv/bin/activate
python app.py
```

**Option 3: Direct command**
```bash
./venv/bin/python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

### Step 4: Open in Browser

**On the Raspberry Pi:**
```
http://localhost:5000
```

**From another device:**
```
http://<raspberry-pi-ip>:5000
```

Find your Pi's IP:
```bash
hostname -I
```

---

## 🎉 You're Done!

You should now see a beautiful, modern interface with:
- 🎮 Playback controls
- 🎵 Song management
- ⏰ Schedule management
- 🔊 Volume control

---

## Quick Tutorial

### Add Your First Song

**Method 1: Upload**
1. Click "📤 Upload Song"
2. Choose an audio file (MP3, WAV, etc.)
3. Click Upload

**Method 2: YouTube**
1. Click "📥 Download from YouTube"
2. Paste a YouTube URL
3. Click Download (wait ~1 minute)

### Create Your First Schedule

1. Click "➕ Add Schedule"
2. Enter a name (e.g., "Morning Alarm")
3. Select your song
4. Set the time (hour: 8, minute: 0 for 8:00 AM)
5. Check "Repeat continuously" if you want it to loop
6. Make sure "Enabled" is checked
7. Click "Save Schedule"

### Test Playback

1. Find a song in the "Songs" section
2. Click "▶️ Play" to test
3. Use the volume slider to adjust
4. Click "⏹️ Stop" when done

---

## Auto-Start on Boot (Optional)

To make HomePi start automatically when your Pi boots:

```bash
sudo cp homepi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable homepi.service
sudo systemctl start homepi.service
```

Check status:
```bash
sudo systemctl status homepi.service
```

Stop service:
```bash
sudo systemctl stop homepi.service
```

---

## Common Issues & Fixes

### 🔇 No Audio?

**For 3.5mm Jack / HDMI:**
```bash
# Configure audio output
sudo raspi-config
# Navigate to: System Options → Audio → Select your output

# Test audio
speaker-test -t wav -c 2
```

**For Bluetooth Speaker:**
```bash
# All-in-one setup (easiest!)
bash setup-bluetooth.sh

# Then start HomePi
bash start.sh
```

The script handles everything: scanning, pairing, connecting, and audio routing.

See [BLUETOOTH_SETUP.md](BLUETOOTH_SETUP.md) or [PIPEWIRE_BLUETOOTH.md](PIPEWIRE_BLUETOOTH.md) for details.

### 🌐 Can't Access from Other Devices?
```bash
# Check if server is running
ps aux | grep app.py

# Verify IP address
hostname -I

# Check firewall (if any)
sudo ufw status
```

### 📥 YouTube Download Fails (403 Forbidden)?

YouTube changes their API frequently. Update yt-dlp:

```bash
# Use the update script
bash update-ytdlp.sh

# Or manually
./venv/bin/pip install --upgrade yt-dlp

# Restart the app
```

**Note:** YouTube blocking is common. yt-dlp usually releases fixes within days.

### ⏰ Schedule Not Working?
- Verify the schedule is enabled (green "Active" badge)
- Check the song file exists
- Verify system time is correct: `date`
- Check logs when running `python3 app.py`

---

## Tips & Tricks

### 🎵 Supported Audio Formats
- MP3 (most common)
- WAV (lossless)
- OGG (open format)
- M4A (AAC format)

### ⏰ Time Format
- Use 24-hour format
- Hour: 0-23 (0 = midnight, 12 = noon, 23 = 11 PM)
- Minute: 0-59

### 🔁 Repeat Mode
- When enabled, song plays on loop continuously
- Continues until you click Stop
- Perfect for alarms or background music

### 📱 Mobile Access
- The interface is fully responsive
- Works great on phones and tablets
- Add to home screen for app-like experience

### 🔊 Volume Tips
- Set volume via web interface
- Changes apply immediately
- Volume persists across songs
- Range: 0-100%

---

## File Locations

```
homepi/
├── app.py              # Main application
├── songs/              # Your audio files
├── schedules.json      # Schedule data
└── static/
    └── index.html      # Web interface
```

---

## Need Help?

1. Check the full [README.md](README.md) for detailed documentation
2. See [FEATURES.md](FEATURES.md) for interface details
3. Review [DESIGN.md](DESIGN.md) for technical details
4. Create an issue on GitHub (if applicable)

---

## Enjoy Your HomePi! 🎉

Now you can:
- ⏰ Wake up to your favorite songs
- 🕌 Schedule prayer call sounds
- 🎵 Automate background music
- 🔔 Create hourly chimes
- 🎶 And much more!

**Happy Scheduling!** 🚀

