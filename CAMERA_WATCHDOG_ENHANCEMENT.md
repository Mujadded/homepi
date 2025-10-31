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

### 3. Automatic Camera Refresh (No Service Restart Required)
- Camera manager tracks frame timestamps and exposes frame age
- `camera_manager.refresh_camera()` restarts Picamera2 in-process (60s cooldown by default)
- App-level health monitor auto-refreshes if frames are older than 1.5 seconds
- Live-feed endpoint self-heals by triggering a refresh when it sees stale frames
- Watchdog prefers the refresh API before falling back to service/network restarts

### 4. Manual Camera Refresh Endpoint
- `POST /api/security/camera/refresh` refreshes the stream without restarting HomePi
- Accepts optional JSON payload: `{ "force": true, "reason": "manual" }`
- Respects refresh cooldown unless `force` is specified

### 5. Enhanced Configuration
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

### 6. Integration with Health Checks
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

4. **`app.py`**
   - Health check now runs every minute and refreshes the camera when frames are stale
   - Added `/api/security/camera/refresh` endpoint for manual refresh requests

5. **`camera_manager.py`**
   - Tracks frame timestamps and exposes frame age in status responses
    - Provides `refresh_camera()` and `ensure_camera_fresh()` helpers with cooldown handling
    - Resets Picamera2 in-process to clear lag without restarting the whole service

## How It Works

### Detection
1. Watchdog runs every 30 seconds (configurable)
2. Camera manager updates frame timestamps on every capture
3. App health monitor (every minute) checks frame age and camera availability
4. Live-feed generator double-checks frame freshness per client session
5. If external access fails or frames become stale → trigger refresh/fix attempts

### Fix Process
1. **Camera Refresh**: `camera_manager.refresh_camera()` (stop & reinit Picamera2 in-place)
2. **Service Restart**: `systemctl restart homepi.service` (fallback if refresh skipped/fails)
3. **Interface Restart**: `ip link set {interface} down/up`
4. **Firewall Check**: `iptables -I INPUT -p tcp --dport 5000 -j ACCEPT`
5. Re-tests connectivity after each fix attempt

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

Trigger a manual camera refresh via API:
```bash
curl -X POST http://192.168.0.26:5000/api/security/camera/refresh \
     -H 'Content-Type: application/json' \
     -d '{"reason": "manual refresh test"}'
```

## Benefits

1. **Automatic Recovery**: No manual intervention needed when camera connectivity fails
2. **Krono Compatibility**: Ensures Krono can always access the camera feed
3. **Stream Stability**: Detects stale buffers and refreshes the camera without restarting HomePi
4. **Network Resilience**: Handles WiFi/Ethernet connectivity issues
5. **Firewall Protection**: Automatically fixes port blocking issues
6. **Configurable**: Easy to adjust test endpoints, fix methods, and refresh thresholds

## Configuration Options

- `enable_camera_fix`: Enable/disable camera fixes
- `test_endpoints`: Which API endpoints to test
- `fix_methods`: Which fix methods to try
- `test_timeout`: Timeout for connectivity tests
- `check_interval`: How often to run checks (default: 30 seconds)

This enhancement ensures that the HomePi camera feed remains accessible to Krono screen monitor, automatically fixing the connectivity issues that were previously resolved manually.
