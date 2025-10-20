# HomePi Camera Connectivity Watchdog Enhancement

## Overview

Enhanced the HomePi watchdog service to automatically detect and fix camera connectivity issues that prevent Krono from accessing the MJPEG live feed.

## Problem Solved

The original issue was that Krono screen monitor couldn't connect to HomePi camera feed at `http://192.168.0.26:5000/api/security/live-feed`. The watchdog now includes:

1. **External connectivity testing** - Tests camera endpoints from the device's external IP (not just localhost)
2. **Automatic fixes** - Restarts service, network interfaces, and checks firewall rules
3. **Configuration-driven** - Uses `watchdog_config.json` for customizable settings

## Key Features Added

### 1. Camera Connectivity Check (`check_camera_connectivity()`)
- Gets device's external IP address dynamically
- Tests camera endpoints from external perspective:
  - `/api/security/status`
  - `/api/security/live-feed`
- Uses configurable timeout settings
- Properly detects when external access fails (even if localhost works)

### 2. Camera Connectivity Fix (`fix_camera_connectivity()`)
- **Service Restart**: Restarts homepi.service to refresh network bindings
- **Interface Restart**: Restarts network interface (WiFi/Ethernet) to fix connectivity
- **Firewall Check**: Checks and fixes iptables rules blocking port 5000
- Configurable fix methods via `watchdog_config.json`

### 3. Enhanced Configuration
Added camera section to `watchdog_config.json`:
```json
{
  "camera": {
    "enable_external_test": true,
    "test_endpoints": [
      "/api/security/status",
      "/api/security/live-feed"
    ],
    "fix_methods": [
      "service_restart",
      "interface_restart", 
      "firewall_check"
    ],
    "test_timeout": 10
  }
}
```

### 4. Integration with Health Checks
- Added `camera` check to `perform_health_check()`
- Prioritizes camera fixes in `attempt_fixes()` (critical for Krono)
- Logs detailed debug information for troubleshooting

## Files Modified

1. **`homepi_watchdog.py`**
   - Added `check_camera_connectivity()` method
   - Added `fix_camera_connectivity()` method
   - Enhanced `load_watchdog_config()` to load from JSON
   - Updated health checks and fix attempts

2. **`watchdog_config.json`**
   - Added `enable_camera_fix: true` to auto_fix section
   - Added camera configuration section
   - Configurable test endpoints and fix methods

3. **`test_camera_connectivity.py`** (new)
   - Manual test script for camera connectivity
   - Can be run to verify functionality

## How It Works

### Detection
1. Watchdog runs every 30 seconds (configurable)
2. Gets device IP: `hostname -I | awk '{print $1}'`
3. Tests external endpoints: `http://{device_ip}:5000/api/security/status`
4. If external access fails → triggers fix attempts

### Fix Process
1. **Service Restart**: `systemctl restart homepi.service`
2. **Interface Restart**: `ip link set {interface} down/up`
3. **Firewall Check**: `iptables -I INPUT -p tcp --dport 5000 -j ACCEPT`
4. Re-tests connectivity after each fix attempt

### Logging
- Debug logs show device IP and endpoint tests
- Info logs show fix attempts and results
- Warning logs show when fixes fail

## Testing

Run the test script manually:
```bash
cd /home/mujadded/homepi
python3 test_camera_connectivity.py
```

## Benefits

1. **Automatic Recovery**: No manual intervention needed when camera connectivity fails
2. **Krono Compatibility**: Ensures Krono can always access the camera feed
3. **Network Resilience**: Handles WiFi/Ethernet connectivity issues
4. **Firewall Protection**: Automatically fixes port blocking issues
5. **Configurable**: Easy to adjust test endpoints and fix methods

## Configuration Options

- `enable_camera_fix`: Enable/disable camera fixes
- `test_endpoints`: Which API endpoints to test
- `fix_methods`: Which fix methods to try
- `test_timeout`: Timeout for connectivity tests
- `check_interval`: How often to run checks (default: 30 seconds)

This enhancement ensures that the HomePi camera feed remains accessible to Krono screen monitor, automatically fixing the connectivity issues that were previously resolved manually.
