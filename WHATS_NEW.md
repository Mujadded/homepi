# 🎉 HomePi v2.0 - What's New

## Overview

Your HomePi music scheduler has been upgraded with **enterprise-grade reliability features** to ensure 24/7 operation. The system is now production-ready for always-on deployment.

---

## 🆕 New Features

### 1. 🐕 Watchdog Service - Auto-Recovery
**Never worry about crashes again!**

- Monitors HomePi every 60 seconds
- Automatically restarts if app stops responding
- Checks both service status and API health
- Logs all recovery attempts
- Maximum 3 retries before waiting for manual intervention

**What this means for you:**
- If the app crashes, it restarts automatically
- If the API hangs, it detects and restarts
- Your music schedules keep running even if something goes wrong

---

### 2. 💾 Automatic Backup System
**Your schedules are now safe!**

- **Daily backups** at 3:00 AM automatically
- Keeps **7 days** of backup history
- **One-click restore** from web interface
- **Manual backup** anytime you want
- Automatic cleanup of old backups

**What this means for you:**
- Never lose your carefully crafted schedules
- Experiment with confidence - you can always go back
- Easy disaster recovery

**Web Interface:**
- See all your backups with dates and file sizes
- Create backup with one click
- Restore any backup with one click

---

### 3. 📊 System Health Dashboard
**Know exactly what's happening!**

Real-time monitoring of:
- **CPU Usage** - See processor load
- **Memory Usage** - Track RAM consumption  
- **Disk Space** - Get warned before running out
- **Temperature** - Prevent overheating
- **Uptime** - How long system has been running
- **Bluetooth Status** - Is speaker connected?

**Color-coded indicators:**
- 🟢 **Green** = Healthy (< 80% threshold)
- 🟡 **Yellow** = Warning (80-99% threshold)
- 🔴 **Red** = Critical (> threshold)

**Smart warnings:**
- Alerts when metrics exceed safe thresholds
- Shows Bluetooth disconnection warnings
- One-click Bluetooth reconnect button

**What this means for you:**
- Spot problems before they cause issues
- Know when to free up disk space
- Monitor if Raspberry Pi is getting too hot
- See if Bluetooth speaker disconnected

---

### 4. 🔄 Bluetooth Auto-Connect
**Speaker always ready!**

- Automatically connects on boot
- Runs every 5 minutes to check connection
- Auto-reconnects if speaker disconnects
- Sets correct audio routing for PipeWire/PulseAudio
- Configures volume to 70% automatically

**What this means for you:**
- Plug in your Pi, and music just works
- If speaker turns off and back on, auto-reconnects
- No more manual Bluetooth setup after reboot

---

## 🎯 Automated Tasks

Your HomePi now runs these tasks automatically:

| Task | Frequency | What It Does |
|------|-----------|--------------|
| Health Check | Every 5 minutes | Checks all system metrics, auto-reconnects Bluetooth |
| Watchdog Check | Every 60 seconds | Ensures HomePi is responding, restarts if needed |
| Daily Backup | 3:00 AM | Creates backup of all schedules |
| Backup Cleanup | After each backup | Removes backups older than 7 days |
| Bluetooth Check | On boot + every 5 min | Connects speaker, maintains connection |

---

## 🌐 New Web Interface Features

### System Health Section (Top of page)
- 6 real-time metrics with visual indicators
- Color-coded health status
- Warning alerts that show up automatically
- Reconnect Bluetooth button

### Backup Management Section
- List of all backups with timestamps
- File size information
- "Create Backup Now" button
- "Restore" button for each backup
- Automatic daily backup info displayed

### Existing Features (Enhanced)
- All your music and schedule management
- Calendar view for schedules
- Per-schedule volume control
- Day-of-week selection
- YouTube download

---

## 📱 How to Use New Features

### View System Health
1. Open web interface
2. See **System Health** dashboard at the top
3. Check metrics are all green
4. If warnings appear, address them

### Create Backup
1. Scroll to **Backup Management** section
2. Click **Create Backup Now**
3. See new backup appear in list

### Restore Backup
1. Browse backup list
2. Find the backup you want
3. Click **Restore**
4. Confirm the action
5. Your schedules are restored!

### Reconnect Bluetooth
1. If Bluetooth shows as disconnected
2. Click **🔄 Reconnect Bluetooth** button
3. Wait 5 seconds
4. Check status updates to connected

---

## 🔧 System Services

Three new services are running in the background:

### 1. `homepi.service` (Main App)
- Your music scheduler
- Web interface
- Schedule management
- Music playback

### 2. `homepi-watchdog.service` (NEW)
- Monitors main app
- Auto-restarts on failure
- Logs recovery attempts
- View logs: `cat /tmp/homepi-watchdog.log`

### 3. `bluetooth-autoconnect.service` (NEW)
- Connects speaker on boot
- Maintains connection
- Auto-reconnects if needed
- View logs: `cat /tmp/bluetooth-autoconnect.log`

---

## 📈 Benefits for Always-On Operation

### Reliability
- **Automatic recovery** from crashes
- **Health monitoring** catches issues early
- **Watchdog** ensures continuous operation

### Data Safety
- **Daily backups** protect your work
- **7-day history** for disaster recovery
- **One-click restore** for quick fixes

### Visibility
- **Real-time metrics** show system status
- **Color-coded alerts** highlight problems
- **Bluetooth status** at a glance

### Automation
- **Bluetooth auto-connects** on boot
- **Schedules run** without intervention
- **Backups happen** automatically

---

## 🚀 Installation

**Super easy - just run:**

```bash
cd ~/homepi
bash upgrade.sh
```

That's it! The script will:
1. Install dependencies (psutil)
2. Setup watchdog service
3. Setup Bluetooth auto-connect
4. Restart services
5. Verify everything is running

---

## 📊 System Requirements

- **New dependency:** `psutil` (for system monitoring)
- **Disk space:** ~10MB for backups (very small)
- **RAM:** Same as before (~50MB)
- **CPU:** Minimal impact (<1% when idle)

---

## 🎊 What You Get

Before (v1.0):
- ✅ Music scheduling
- ✅ Web interface
- ✅ YouTube download

After (v2.0):
- ✅ Music scheduling
- ✅ Web interface
- ✅ YouTube download
- 🆕 **Auto-recovery from crashes**
- 🆕 **Daily automatic backups**
- 🆕 **System health monitoring**
- 🆕 **Bluetooth auto-connect**
- 🆕 **Visual health dashboard**
- 🆕 **Smart warnings**
- 🆕 **One-click backup/restore**

---

## 💡 Pro Tips

1. **Check health dashboard daily** - Spot issues before they're problems
2. **Create manual backups** before making big schedule changes
3. **Monitor temperature** in summer - consider cooling if needed
4. **Watch disk space** - clear old songs if running low
5. **Review watchdog logs** monthly - see if there are recurring issues

---

## 🎵 Your HomePi is Now Production-Ready!

With these new features, your Raspberry Pi can run 24/7 without babysitting. It will:
- Keep playing music on schedule
- Recover automatically from problems
- Protect your data with backups
- Alert you to potential issues
- Maintain Bluetooth connection

Enjoy your bulletproof music scheduler! 🎉

