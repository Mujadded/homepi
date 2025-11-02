# HomePi Watchdog Status API

## Overview

New API endpoint to monitor HomePi availability and watchdog service status from external systems like Jetson Orin.

## Endpoint

```
GET http://192.168.0.26:5000/api/watchdog/status
```

## Response Format

```json
{
  "homepi_online": true,
  "timestamp": "2025-10-20T21:15:30.123456",
  "service_status": {
    "homepi_service": {
      "active": true,
      "status": "active"
    }
  },
  "watchdog_status": {
    "watchdog_service": {
      "active": true,
      "status": "active"
    }
  },
  "health_checks": {
    "service": true,
    "app": true,
    "network": true,
    "camera": true,
    "bluetooth": true,
    "resources": true,
    "current": {
      "camera_enabled": true,
      "camera_frame_age": 0.033,
      "bluetooth_connected": true,
      "cpu_percent": 15.2,
      "memory_percent": 45.3,
      "disk_percent": 62.1,
      "warnings": []
    }
  }
}
```

## Response Fields

### `homepi_online` (boolean)
- `true`: HomePi is online and responding
- `false`: HomePi is down or unreachable

### `timestamp` (string)
ISO 8601 formatted timestamp of when the status was generated.

### `service_status`
Status of critical services:
- `homepi_service`: Main HomePi application service
  - `active`: Service is running
  - `status`: systemd status (active/inactive/unknown)
  - `error`: Error message if status check failed

### `watchdog_status`
Status of watchdog service:
- `watchdog_service`: HomePi watchdog service
  - `active`: Watchdog is running
  - `status`: systemd status (active/inactive/unknown)
  - `error`: Error message if status check failed

### `health_checks`
Latest health check results from watchdog:
- `service`: HomePi service is running
- `app`: Flask app responding to health checks
- `network`: Network connectivity working
- `camera`: Camera feed accessible externally
- `bluetooth`: Bluetooth speaker connected
- `resources`: CPU/memory/disk within limits
- `current`: Real-time system metrics
  - `camera_enabled`: Camera is initialized
  - `camera_frame_age`: Age of most recent frame (seconds)
  - `bluetooth_connected`: Bluetooth speaker status
  - `cpu_percent`: Current CPU usage
  - `memory_percent`: Current memory usage
  - `disk_percent`: Current disk usage
  - `warnings`: Array of any active warnings

## Error Response

If HomePi is completely down:
```json
{
  "homepi_online": false,
  "timestamp": "2025-10-20T21:15:30.123456",
  "error": "Connection failed"
}
```

## Usage Examples

### Check if HomePi is online (from Jetson)

```bash
curl http://192.168.0.26:5000/api/watchdog/status
```

### Python monitoring script

```python
import requests
import json
from datetime import datetime

def check_homepi_status():
    try:
        response = requests.get('http://192.168.0.26:5000/api/watchdog/status', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"HomePi Status: {'✅ ONLINE' if data['homepi_online'] else '❌ OFFLINE'}")
            print(f"Timestamp: {data['timestamp']}")
            
            # Service status
            if data.get('service_status', {}).get('homepi_service', {}).get('active'):
                print("✅ HomePi service: Running")
            else:
                print("❌ HomePi service: Down")
            
            # Watchdog status
            if data.get('watchdog_status', {}).get('watchdog_service', {}).get('active'):
                print("✅ Watchdog service: Running")
            else:
                print("❌ Watchdog service: Down")
            
            # Health checks
            if 'health_checks' in data:
                checks = data['health_checks']
                print(f"\nHealth Checks:")
                print(f"  Service: {'✅' if checks.get('service') else '❌'}")
                print(f"  App: {'✅' if checks.get('app') else '❌'}")
                print(f"  Network: {'✅' if checks.get('network') else '❌'}")
                print(f"  Camera: {'✅' if checks.get('camera') else '❌'}")
                print(f"  Bluetooth: {'✅' if checks.get('bluetooth') else '❌'}")
                print(f"  Resources: {'✅' if checks.get('resources') else '❌'}")
                
                # Current metrics
                if 'current' in checks:
                    current = checks['current']
                    print(f"\nCurrent Metrics:")
                    print(f"  CPU: {current.get('cpu_percent', 0):.1f}%")
                    print(f"  Memory: {current.get('memory_percent', 0):.1f}%")
                    print(f"  Disk: {current.get('disk_percent', 0):.1f}%")
                    print(f"  Camera frame age: {current.get('camera_frame_age', 0):.3f}s")
                    
                    if current.get('warnings'):
                        print(f"\n⚠️  Warnings: {', '.join(current['warnings'])}")
            
            return data['homepi_online']
        else:
            print(f"❌ HomePi returned error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ HomePi is unreachable: {e}")
        return False

if __name__ == "__main__":
    status = check_homepi_status()
    exit(0 if status else 1)
```

### Notification integration for Jetson

```python
import requests
import time
from telegram_notifier import send_notification  # Your notification function

def monitor_homepi(interval_seconds=60):
    """Monitor HomePi and send notifications if issues detected"""
    last_status = None
    
    while True:
        try:
            response = requests.get('http://192.168.0.26:5000/api/watchdog/status', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if HomePi went offline
                if last_status is True and not data['homepi_online']:
                    send_notification("🚨 HomePi is offline!")
                
                # Check if HomePi came back online
                if last_status is False and data['homepi_online']:
                    send_notification("✅ HomePi is back online")
                
                # Check for health issues
                if data['homepi_online']:
                    checks = data.get('health_checks', {})
                    if isinstance(checks, dict):
                        # Check if any health check is failing
                        failed = [k for k, v in checks.items() 
                                if k != 'current' and v is False]
                        
                        if failed:
                            send_notification(
                                f"⚠️ HomePi health issues: {', '.join(failed)}"
                            )
                
                last_status = data['homepi_online']
                
        except requests.exceptions.RequestException:
            if last_status is not False:
                send_notification("🚨 Cannot reach HomePi!")
                last_status = False
        
        time.sleep(interval_seconds)

if __name__ == "__main__":
    monitor_homepi(interval_seconds=60)
```

## Benefits

1. **Remote Monitoring**: Jetson can check HomePi status without SSH access
2. **Automated Notifications**: Detect when HomePi goes offline or has issues
3. **Service Health**: Monitor all critical services and resources
4. **Real-time Metrics**: Get current CPU, memory, disk, camera, and Bluetooth status
5. **Historical Context**: See latest watchdog health check results

## Testing

Test the endpoint locally:

```bash
# From HomePi
curl http://localhost:5000/api/watchdog/status | jq

# From Jetson or any device on network
curl http://192.168.0.26:5000/api/watchdog/status | jq
```

## Integration with Jetson

Add to your Jetson monitoring script:

```python
import subprocess

def is_homepi_healthy():
    """Quick check if HomePi is healthy"""
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://192.168.0.26:5000/api/watchdog/status'],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            return data.get('homepi_online', False)
    except:
        pass
    return False
```

## Troubleshooting

If the endpoint returns errors:

1. **HomePi service not running**: Check `sudo systemctl status homepi.service`
2. **Permission denied on log file**: Ensure `/var/log/homepi-watchdog.log` is readable
3. **Timeout issues**: Check network connectivity between Jetson and HomePi
4. **Missing health checks**: Watchdog may not have run yet (wait 30 seconds)

## Related Endpoints

- `GET /api/health` - General system health metrics
- `GET /api/security/status` - Security system specific status
- `POST /api/security/camera/refresh` - Manually refresh camera stream
