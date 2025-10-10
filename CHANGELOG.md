# HomePi Changelog - All Updates

This document contains ALL updates and features added to HomePi.

---

## 📦 Installation Quick Reference

### Files to Copy to Raspberry Pi:
```
✅ app.py
✅ static/index.html
✅ requirements.txt
✅ watchdog.sh
✅ homepi-watchdog.service
✅ setup-watchdog.sh
✅ bluetooth-autoconnect.sh
✅ bluetooth-autoconnect.service
✅ setup-bluetooth-autostart.sh
✅ upgrade.sh (optional - runs all setup)
```

### Quick Install:
```bash
cd ~/homepi

# Easy way (automated):
bash upgrade.sh

# Or manual way:
source venv/bin/activate
pip install psutil mutagen
bash setup-watchdog.sh
bash setup-bluetooth-autostart.sh
sudo systemctl restart homepi.service
```

---

## 🎉 All Features

### 1. ✅ Watchdog & Auto-Recovery
**What:** Automatically restarts HomePi if it crashes

**Features:**
- Checks every 60 seconds
- Auto-restarts if app stops
- Auto-restarts if API not responding
- Monitors Bluetooth connection
- Auto-reconnects Bluetooth if disconnected
- Logs to `/tmp/homepi-watchdog.log`

**Commands:**
```bash
sudo systemctl status homepi-watchdog.service
cat /tmp/homepi-watchdog.log
```

---

### 2. 💾 Automatic Backups
**What:** Daily backup of all schedules

**Features:**
- Runs at 3:00 AM daily
- Keeps last 7 days
- Manual backup button in web interface
- One-click restore
- Auto-cleanup of old backups

**Web Interface:**
- View all backups with dates
- "Create Backup Now" button
- "Restore" button for each backup

**Commands:**
```bash
ls ~/homepi/backups/
curl -X POST http://localhost:5000/api/backups/create
```

---

### 3. 📊 System Health Monitoring
**What:** Real-time system metrics dashboard

**Monitors:**
- CPU usage (warns >80%)
- Memory usage (warns >80%)
- Disk space (warns >90%)
- CPU temperature (warns >75°C)
- System uptime
- Bluetooth connection status

**Display:**
- Color-coded: 🟢 Green = OK, 🟡 Yellow = Warning, 🔴 Red = Critical
- Visual warnings section
- Reconnect Bluetooth button
- Auto-refreshes every 30 seconds

---

### 4. 🔁 Clear Repeat Mode Explanation
**What:** Clarified what "repeat" means

**Before:** Confusing checkbox  
**Now:** Clear explanation with warning

**Repeat OFF (default):** Song plays **once** and stops  
**Repeat ON:** Song **loops forever** until manually stopped

**Tip:** For most schedules, leave repeat OFF. Only use ON for alarm clocks.

---

### 5. ⏱️ Track Duration Display
**What:** Shows how long each song is

**Where:**
- Song list: `🎵 Song.mp3 • 3.5 MB • ⏱️ 3:24`
- Schedule list: Shows duration with each schedule
- Calendar view: Shows duration in timeline

**Benefits:**
- Plan schedules without overlaps
- Know exactly how long tracks are
- Spot potential conflicts

---

### 6. 📊 Live Playback Progress Bar
**What:** Real-time progress while playing

**Shows:**
- Current position in song (e.g., "1:32")
- Total duration (e.g., "3:24")
- Visual progress bar
- Playback volume control
- Updates every 2 seconds

**Display:**
```
Now Playing: Morning_Song.mp3
1:32 ████████████░░░░░░░░░ 3:24
Playback Volume: [████████] 70%
```

---

### 7. 🎯 Schedule End Time Display
**What:** Shows when each track will finish

**Format:** `07:00 → 07:03` (start → end)

**Special Cases:**
- Normal: `07:00 → 07:03` (green)
- Repeat: `07:00 → ♾️ Loops Forever` (orange)

**Benefits:**
- Instant conflict detection
- See exactly when tracks end
- Plan better spacing

**Examples:**
```
✅ Good: 07:00 → 07:03, then 07:10 → 07:13 (7-min gap)
❌ Bad:  07:00 → 07:06, then 07:03 → 07:06 (overlap!)
```

---

### 8. 🗑️ Cascade Delete
**What:** Deleting a song also deletes its schedules

**How It Works:**
1. Click delete on a song
2. If used in schedules, shows warning:
   ```
   ⚠️ WARNING: This will also delete 2 schedules:
   • Morning Alarm (07:00)
   • Weekend Wake Up (08:00)
   ```
3. You confirm or cancel
4. If confirmed: Song + all schedules deleted

**Benefits:**
- No orphaned schedules
- Clear warnings
- Can cancel if needed
- Everything stays in sync

---

### 9. 🔊 Per-Schedule Volume Control
**What:** Each schedule can have its own volume

**How:**
- Volume slider in schedule modal
- Default: 70%
- Set custom volume per schedule
- Shows in schedule list: `🔊 80%`

---

### 10. 📅 Day-of-Week Selection
**What:** Choose which days each schedule runs

**How:**
- Checkboxes for Mon-Sun in schedule modal
- Leave all unchecked = every day
- Select specific days = runs only those days
- Shows in schedule: `📅 MON, WED, FRI`

---

### 11. 📆 Calendar View
**What:** Visual timeline of your day

**Features:**
- Hour-by-hour view (00:00 - 23:00)
- Current hour highlighted
- Shows start → end times
- "Coming up!" alerts
- Past schedules grayed out
- Toggle between List/Calendar

---

### 12. 🔵 Bluetooth Auto-Connect
**What:** Speaker connects automatically on boot

**Features:**
- Runs on boot
- Checks every 5 minutes
- Auto-reconnects if disconnected
- Works with PulseAudio & PipeWire
- Logs to `/tmp/bluetooth-autoconnect.log`

**Commands:**
```bash
sudo systemctl status bluetooth-autoconnect.service
cat /tmp/bluetooth-autoconnect.log
```

---

## 🎮 Better User Interface

### Clearer Button Labels:
- ~~"Play"~~ → **"▶️ Play Once"**
- ~~"Play & Repeat"~~ → **"🔁 Loop"**

### Two Volume Controls:
- **Default Volume:** For all new playbacks
- **Playback Volume:** For currently playing song

### Song List Shows:
```
🎵 Song.mp3
3.5 MB • ⏱️ 3:24
[▶️ Play Once] [🔁 Loop] [🗑️]
```

### Schedule List Shows:
```
Morning Alarm
✅ Active

07:00 → 07:03 • 🎵 Song.mp3 • ⏱️ 3:24 • 🔊 80% • 📅 MON, WED, FRI
```

---

## 🔧 Technical Improvements

### Backend (app.py):
- Added `psutil` for system monitoring
- Added `mutagen` for audio duration detection
- Playback progress tracking
- Health monitoring functions
- Backup/restore functions
- Cascade delete logic
- Enhanced error handling

### Frontend (index.html):
- Health dashboard with real-time metrics
- Backup management interface
- Progress bar with time display
- End time calculations
- Cascade delete warnings
- Calendar timeline view
- Better mobile responsiveness

### System Services:
- `homepi-watchdog.service` - Monitors main app
- `bluetooth-autoconnect.service` - Handles Bluetooth
- Automated daily backup at 3 AM
- Health check every 5 minutes

---

## 📊 Automated Tasks

| Task | Frequency | Purpose |
|------|-----------|---------|
| Health Check | Every 5 min | Monitor system + Bluetooth |
| Watchdog | Every 60 sec | Check if app is responding |
| Daily Backup | 3:00 AM | Backup all schedules |
| Backup Cleanup | After backup | Remove backups >7 days |
| Bluetooth Check | On boot + every 5 min | Maintain speaker connection |

---

## 💡 Usage Tips

### For Daily Schedules:
✅ Leave repeat **OFF**  
✅ Check track durations  
✅ Space schedules 1-2 min apart  
✅ Use per-schedule volumes  
✅ Select specific days if needed

### For Alarms:
✅ Enable repeat if you want loop  
✅ Test volume first  
✅ Make sure you can reach Stop button

### Avoiding Conflicts:
✅ Look at end times (`→`)  
✅ Check for overlaps  
✅ Leave gaps between schedules  
✅ Use calendar view for visual check

### Deleting Songs:
⚠️ Read the warning message  
⚠️ See which schedules will be deleted  
⚠️ Can cancel if you change mind

---

## 🐛 Troubleshooting

### Health metrics not showing:
```bash
source ~/homepi/venv/bin/activate
pip install psutil
sudo systemctl restart homepi.service
```

### Track durations show "Unknown":
```bash
pip install mutagen
sudo systemctl restart homepi.service
```

### Watchdog not running:
```bash
cat /tmp/homepi-watchdog.log
sudo systemctl restart homepi-watchdog.service
```

### Bluetooth not auto-connecting:
```bash
cat /tmp/bluetooth-autoconnect.log
bash setup-bluetooth-autostart.sh
```

### Progress bar not moving:
- Song might not have duration metadata
- Still plays normally, just can't show progress

---

## 📈 Before & After Comparison

| Feature | Before | After |
|---------|--------|-------|
| **Crashes** | Manual restart | Auto-recovery |
| **Backups** | Manual | Automatic daily |
| **Monitoring** | None | Full dashboard |
| **Repeat Mode** | Confusing | Clear explanation |
| **Track Length** | Unknown | Shown everywhere |
| **Playback Progress** | None | Live progress bar |
| **Schedule End Time** | Hidden | Clearly shown |
| **Delete Song** | Breaks schedules | Auto-cleanup |
| **Volume** | Global only | Per-schedule |
| **Days** | Every day | Selectable |
| **View** | List only | List + Calendar |
| **Bluetooth** | Manual | Auto-connect |

---

## 🎯 System Requirements

**Dependencies:**
- Python 3.7+
- Flask 3.0.0
- APScheduler 3.10.4
- pygame (system package)
- psutil 5.9.6
- mutagen 1.47.0
- yt-dlp (latest)

**Disk Space:**
- App: ~50 MB
- Backups: ~10 MB (for 7 days)
- Songs: Varies

**RAM:**
- Idle: ~50 MB
- Playing: ~100 MB

**CPU:**
- Idle: <1%
- Playing: 2-5%

---

## 🚀 Quick Start for New Users

1. **Install:**
   ```bash
   bash install.sh
   bash upgrade.sh
   ```

2. **Setup Bluetooth:**
   ```bash
   bash setup-bluetooth.sh
   ```

3. **Access Web Interface:**
   ```
   http://<raspberry-pi-ip>:5000
   ```

4. **Add Songs:**
   - Upload or download from YouTube

5. **Create Schedules:**
   - Set time, choose song, select days
   - Leave repeat OFF for normal schedules

6. **Monitor:**
   - Check health dashboard
   - View calendar timeline
   - Watch for warnings

---

## 📝 Summary

HomePi is now a **production-ready, always-on music scheduler** with:

✅ Enterprise-grade reliability (watchdog, auto-recovery)  
✅ Data safety (automatic backups)  
✅ System monitoring (health dashboard)  
✅ Smart scheduling (durations, end times, conflict detection)  
✅ User-friendly (clear UI, warnings, feedback)  
✅ Maintenance-free (auto-connects, auto-cleans)

Your Raspberry Pi can now run 24/7 playing music on schedule without any babysitting! 🎉

