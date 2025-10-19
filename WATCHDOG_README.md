# HomePi Watchdog System

A comprehensive monitoring and auto-recovery system for your HomePi setup that automatically detects and fixes common issues.

## 🛡️ **What It Does**

The HomePi Watchdog continuously monitors your system and automatically:

- **Service Health**: Monitors HomePi service and restarts if crashed
- **Network Issues**: Detects network problems and restarts networking
- **Bluetooth Problems**: Fixes Bluetooth connectivity issues
- **System Resources**: Monitors CPU, memory, and disk usage
- **Auto-Recovery**: Restarts services, fixes network, and reboots if needed
- **Smart Logging**: Maintains detailed logs with rotation

## 🚀 **Quick Installation**

```bash
# Make the installation script executable
chmod +x install-watchdog.sh

# Run the installation (as root)
sudo bash install-watchdog.sh
```

## 📋 **Manual Installation**

1. **Install Python dependencies**:
   ```bash
   pip3 install psutil requests
   ```

2. **Copy watchdog files**:
   ```bash
   sudo cp homepi_watchdog.py /usr/local/bin/
   sudo cp homepi-watchdog.service /etc/systemd/system/
   sudo chmod +x /usr/local/bin/homepi_watchdog.py
   ```

3. **Enable and start the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable homepi-watchdog.service
   sudo systemctl start homepi-watchdog.service
   ```

## 🔧 **Configuration**

Edit `watchdog_config.json` to customize behavior:

```json
{
  "watchdog": {
    "check_interval": 30,        // Check every 30 seconds
    "max_failures": 3,           // Max failures before action
    "enable_system_reboot": true // Allow system reboot as last resort
  },
  "auto_fix": {
    "enable_service_restart": true,
    "enable_network_fix": true,
    "enable_bluetooth_fix": true
  }
}
```

## 📊 **Monitoring Commands**

```bash
# Check watchdog status
sudo systemctl status homepi-watchdog.service

# View real-time logs
sudo journalctl -u homepi-watchdog.service -f

# Check HomePi service status
sudo systemctl status homepi.service

# View system logs
sudo journalctl -u homepi.service -f

# Check all HomePi services
sudo systemctl status homepi* --no-pager
```

## 🔍 **What Gets Monitored**

### **Service Health**
- HomePi Flask application responding
- Service status (active/inactive)
- Port 5000 accessibility

### **Network Connectivity**
- Internet connectivity (Google, Cloudflare)
- Ethernet interface status
- DNS resolution

### **Bluetooth Status**
- Bluetooth service running
- HCI devices available
- Audio device connectivity

### **System Resources**
- CPU usage (alerts if >90%)
- Memory usage (alerts if >90%)
- Disk space (alerts if >90%)

## 🛠️ **Auto-Fix Actions**

### **Service Issues**
1. Restart HomePi service
2. Wait 30 seconds
3. Verify service is responding

### **Network Issues**
1. Restart networking service
2. Bring down/up network interface
3. Flush DNS cache
4. Test connectivity

### **Bluetooth Issues**
1. Restart Bluetooth service
2. Reset HCI devices
3. Run Bluetooth fix script
4. Verify audio devices

### **System Reboot** (Last Resort)
1. Only after 3 consecutive failures
2. Rate limited (max 2 reboots per hour)
3. Creates reboot flag file
4. Graceful shutdown with 1-minute delay

## 📝 **Logging**

Logs are stored in `/var/log/homepi-watchdog.log` with automatic rotation:

- **Daily rotation** with 7-day retention
- **Compression** of old logs
- **Size limit** of 10MB per file
- **Structured logging** with timestamps

## 🚨 **Troubleshooting**

### **Watchdog Not Starting**
```bash
# Check service status
sudo systemctl status homepi-watchdog.service

# Check logs for errors
sudo journalctl -u homepi-watchdog.service --no-pager

# Restart service
sudo systemctl restart homepi-watchdog.service
```

### **Service Keeps Restarting**
```bash
# Check HomePi service logs
sudo journalctl -u homepi.service --no-pager

# Check system resources
htop
df -h
free -h

# Check network
ping 8.8.8.8
ip addr show
```

### **Network Issues Persist**
```bash
# Check network interface
ip link show eth0

# Restart networking manually
sudo systemctl restart networking

# Check routing
ip route show
```

## 🔧 **Advanced Usage**

### **Run Enhanced Startup Script**
```bash
# Full system startup with fixes
sudo bash startup-enhanced.sh

# Check status only
sudo bash startup-enhanced.sh status

# Restart services
sudo bash startup-enhanced.sh restart

# View logs
sudo bash startup-enhanced.sh logs
```

### **Manual Service Management**
```bash
# Start watchdog
sudo systemctl start homepi-watchdog.service

# Stop watchdog
sudo systemctl stop homepi-watchdog.service

# Restart watchdog
sudo systemctl restart homepi-watchdog.service

# Disable watchdog
sudo systemctl disable homepi-watchdog.service
```

## 📈 **Monitoring Dashboard**

The watchdog integrates with your existing HomePi web interface. Check the System Status section for:

- Service health indicators
- Last check time
- Failure count
- Auto-fix actions taken

## ⚙️ **Customization**

### **Add Custom Checks**
Edit `homepi_watchdog.py` and add new check methods:

```python
def check_custom_service(self):
    """Check your custom service"""
    # Your custom logic here
    return True
```

### **Modify Fix Actions**
Update the `attempt_fixes()` method to include your custom fixes:

```python
def attempt_fixes(self, failed_checks):
    fixes_applied = []
    
    # Your custom fixes here
    if not failed_checks.get('custom_check', True):
        if self.fix_custom_issue():
            fixes_applied.append('custom_fix')
    
    return fixes_applied
```

## 🆘 **Emergency Recovery**

If the system becomes completely unresponsive:

1. **Physical access**: Connect monitor/keyboard
2. **Check logs**: `journalctl -u homepi-watchdog.service`
3. **Manual restart**: `sudo systemctl restart homepi.service`
4. **Full reboot**: `sudo reboot`
5. **Check SD card**: May need replacement if corrupted

## 📞 **Support**

For issues with the watchdog system:

1. Check the logs first: `sudo journalctl -u homepi-watchdog.service -f`
2. Verify configuration: `cat watchdog_config.json`
3. Test individual components manually
4. Check system resources and network connectivity

The watchdog is designed to be self-healing, but if it's not working, the underlying system issue may need manual intervention.
