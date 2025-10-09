# HomePi System Upgrade Guide

## New Features Added

### 1. Watchdog & Auto-Recovery ✅
- Automatically restarts HomePi if it crashes
- Monitors API health every 60 seconds
- Auto-reconnects if Bluetooth speaker disconnects

### 2. Automatic Backups ✅
- Daily backups at 3:00 AM
- Keeps backups for 7 days
- Manual backup/restore from web interface

### 3. System Health Monitoring ✅
- Real-time CPU, memory, disk usage
- Temperature monitoring
- Uptime tracking
- Bluetooth connection status
- Visual dashboard with color-coded warnings

## Installation Steps

### 1. Update Dependencies

```bash
cd ~/homepi

# Activate virtual environment
source venv/bin/activate

# Install new dependency
pip install psutil

# Or reinstall all requirements
pip install -r requirements.txt
```

### 2. Update Application Files

Copy these updated files to your Raspberry Pi:
- `app.py` (updated with health monitoring and backup functions)
- `static/index.html` (updated with health dashboard)
- `requirements.txt` (added psutil)

### 3. Setup Watchdog Service

```bash
# Make scripts executable
chmod +x watchdog.sh setup-watchdog.sh

# Install watchdog service
bash setup-watchdog.sh
```

### 4. Setup Bluetooth Auto-Connect (if using Bluetooth)

```bash
# Make scripts executable
chmod +x bluetooth-autoconnect.sh setup-bluetooth-autostart.sh

# Install auto-connect service
bash setup-bluetooth-autostart.sh
```

### 5. Restart Services

```bash
# Restart HomePi service
sudo systemctl restart homepi.service

# Check status
sudo systemctl status homepi.service
sudo systemctl status homepi-watchdog.service
sudo systemctl status bluetooth-autoconnect.service
```

## Verify Everything is Working

1. Open web interface: `http://<your-pi-ip>:5000`
2. Check the **System Health** section at the top
3. Verify all metrics are showing
4. Check **Backup Management** section
5. Create a test backup

## Troubleshooting

### Health metrics not showing

```bash
# Check if psutil is installed
source venv/bin/activate
python3 -c "import psutil; print('psutil OK')"

# If not, install it
pip install psutil
```

### Watchdog not running

```bash
# Check logs
cat /tmp/homepi-watchdog.log

# Restart watchdog
sudo systemctl restart homepi-watchdog.service

# Check status
sudo systemctl status homepi-watchdog.service
```

### Bluetooth not auto-connecting

```bash
# Check auto-connect logs
cat /tmp/bluetooth-autoconnect.log

# Test manually
bash bluetooth-autoconnect.sh

# Restart service
sudo systemctl restart bluetooth-autoconnect.service
```

### Backups not being created

```bash
# Check if backups directory exists
ls -la ~/homepi/backups/

# Create directory if missing
mkdir -p ~/homepi/backups

# Test manual backup via web interface
```

## What's Been Added

### Backend (app.py)
- `psutil` for system monitoring
- `get_system_health()` - Monitors CPU, memory, disk, temperature
- `check_bluetooth_connection()` - Checks Bluetooth status
- `auto_reconnect_bluetooth()` - Auto-reconnects Bluetooth
- `backup_schedules()` - Creates backups
- `restore_from_backup()` - Restores from backup
- `cleanup_old_backups()` - Removes backups older than 7 days
- New API endpoints:
  - `GET /api/health` - Get system health
  - `GET /api/backups` - List backups
  - `POST /api/backups/create` - Create backup
  - `POST /api/backups/restore` - Restore backup
  - `POST /api/bluetooth/reconnect` - Reconnect Bluetooth

### Frontend (index.html)
- System Health dashboard with real-time metrics
- Color-coded health indicators (green/yellow/red)
- Backup management interface
- Visual warnings for system issues
- Auto-refresh every 30 seconds

### System Services
- `homepi-watchdog.service` - Monitors and restarts HomePi
- `bluetooth-autoconnect.service` - Auto-connects Bluetooth on boot
- `watchdog.sh` - Watchdog monitoring script
- `bluetooth-autoconnect.sh` - Bluetooth connection script

## Benefits

1. **Reliability**: System automatically recovers from crashes
2. **Data Safety**: Daily backups protect your schedules
3. **Visibility**: Real-time monitoring of system health
4. **Automation**: Bluetooth auto-connects on boot
5. **Peace of Mind**: Always know your system status

## Automated Tasks

- **Health Check**: Every 5 minutes
- **Daily Backup**: 3:00 AM
- **Backup Cleanup**: Removes backups older than 7 days
- **Watchdog Check**: Every 60 seconds
- **Bluetooth Check**: Every 5 minutes (auto-reconnect if disconnected)

## Next Steps (Optional)

You can still add these features if needed:
- Fade-in/fade-out for songs
- Schedule templates
- Email notifications on errors
- Password protection
- API key authentication

