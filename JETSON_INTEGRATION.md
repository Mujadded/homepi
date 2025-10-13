# Jetson Orin Integration Guide

## Architecture Overview

HomePi has been refactored into an **I/O-only device** architecture where:

- **Raspberry Pi**: Handles all input/output operations (camera, Pan-Tilt, Telegram, Flipper, web UI)
- **Jetson Orin**: Handles all AI processing and detection logic

### Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Jetson Orin                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  AI Detection Loop:                                         │ │
│  │  1. Request frame from Pi                                   │ │
│  │  2. Run object detection (YOLOv5/Custom models)            │ │
│  │  3. Analyze results & decide actions                        │ │
│  │  4. Send detection + action to Pi webhook                   │ │
│  │  5. Control Pan-Tilt for tracking                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP APIs ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Raspberry Pi                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  I/O Operations:                                            │ │
│  │  • Serve camera frames (GET /api/camera/frame)             │ │
│  │  • Execute Pan-Tilt commands (POST /api/pantilt/command)   │ │
│  │  • Send Telegram notifications (POST /api/telegram/send)   │ │
│  │  • Trigger Flipper actions (POST /api/flipper/trigger)     │ │
│  │  • Store detections locally (POST /api/webhook/detection)  │ │
│  │  • Serve web UI with live feed                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Contract

### Raspberry Pi APIs (for Jetson to call)

#### 1. Get Camera Frame

**Endpoint:** `GET http://192.168.0.26:5000/api/camera/frame`

**Response:**
```json
{
  "success": true,
  "frame": "base64_encoded_jpeg_string",
  "timestamp": "2025-10-12T20:15:30.123456"
}
```

**Usage:**
```python
import requests
import base64
import numpy as np
import cv2

response = requests.get("http://192.168.0.26:5000/api/camera/frame")
data = response.json()

# Decode frame
frame_bytes = base64.b64decode(data['frame'])
frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
```

---

#### 2. Webhook: Receive Detection Results

**Endpoint:** `POST http://192.168.0.26:5000/api/webhook/detection`

**Request Body:**
```json
{
  "timestamp": "2025-10-12T20:15:30",
  "object_type": "car",
  "confidence": 0.87,
  "bbox": [0.3, 0.2, 0.7, 0.8],
  "car_id": "my_car",
  "action": "open_garage",
  "image_data": "base64_encoded_jpeg"
}
```

**Fields:**
- `timestamp`: ISO format timestamp
- `object_type`: Detected object class (car, person, etc.)
- `confidence`: Detection confidence (0.0 to 1.0)
- `bbox`: Normalized bounding box [x1, y1, x2, y2]
- `car_id`: Optional car identifier (from custom recognition)
- `action`: Action to execute (open_garage, send_notification, etc.)
- `image_data`: Optional base64-encoded detection image

**Response:**
```json
{
  "success": true,
  "detection_id": 123,
  "message": "Detection processed"
}
```

**Usage:**
```python
import requests
import base64

# Prepare detection data
detection = {
    "timestamp": "2025-10-12T20:15:30",
    "object_type": "car",
    "confidence": 0.87,
    "bbox": [0.3, 0.2, 0.7, 0.8],
    "car_id": "my_car",
    "action": "open_garage",
    "image_data": base64.b64encode(image_bytes).decode('utf-8')
}

# Send to Raspberry Pi
response = requests.post(
    "http://192.168.0.26:5000/api/webhook/detection",
    json=detection
)
```

---

#### 3. Pan-Tilt Control

**Endpoint:** `POST http://192.168.0.26:5000/api/pantilt/command`

**Request Body (Relative Movement):**
```json
{
  "action": "move",
  "pan": 15,
  "tilt": -10,
  "speed": 5
}
```

**Request Body (Home Position):**
```json
{
  "action": "home"
}
```

**Response:**
```json
{
  "success": true,
  "position": {
    "pan": 15,
    "tilt": -10
  }
}
```

**Usage:**
```python
# Track detected object
def track_object(bbox):
    # Calculate pan/tilt adjustments based on bbox position
    frame_center_x = 0.5
    frame_center_y = 0.5
    
    bbox_center_x = (bbox[0] + bbox[2]) / 2
    bbox_center_y = (bbox[1] + bbox[3]) / 2
    
    # Calculate error
    error_x = bbox_center_x - frame_center_x
    error_y = bbox_center_y - frame_center_y
    
    # Convert to pan/tilt adjustments (tune these gains)
    pan_adjustment = int(error_x * 30)  # degrees
    tilt_adjustment = int(error_y * 20)  # degrees
    
    # Send command
    requests.post(
        "http://192.168.0.26:5000/api/pantilt/command",
        json={
            "action": "move",
            "pan": pan_adjustment,
            "tilt": tilt_adjustment,
            "speed": 8
        }
    )
```

---

#### 4. Send Telegram Notification

**Endpoint:** `POST http://192.168.0.26:5000/api/telegram/send`

**Request Body:**
```json
{
  "message": "🚗 Car detected in driveway",
  "image_data": "base64_encoded_jpeg",
  "chat_id": "optional_chat_id"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification sent"
}
```

---

#### 5. Trigger Flipper Zero Action

**Endpoint:** `POST http://192.168.0.26:5000/api/flipper/trigger`

**Request Body:**
```json
{
  "action": "garage_open"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Garage command sent"
}
```

---

### Jetson Orin APIs (to be implemented)

These are the APIs your Jetson project should implement:

#### 1. Health Check

**Endpoint:** `GET http://192.168.0.105:5001/status`

**Response:**
```json
{
  "status": "running",
  "model_loaded": true,
  "device": "cuda",
  "fps": 28.5,
  "detections_today": 45
}
```

---

#### 2. Detection History

**Endpoint:** `GET http://192.168.0.105:5001/detections?limit=20`

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2025-10-12T20:15:30",
    "object_type": "car",
    "confidence": 0.87,
    "car_id": "my_car",
    "action_taken": "garage_opened"
  }
]
```

---

## Detection Loop Implementation (Jetson)

Here's a sample detection loop for your Jetson project:

```python
import requests
import base64
import numpy as np
import cv2
import time
from datetime import datetime

# Configuration
PI_URL = "http://192.168.0.26:5000"
DETECTION_INTERVAL = 0.1  # seconds
CONFIDENCE_THRESHOLD = 0.6

def get_frame_from_pi():
    """Get camera frame from Raspberry Pi"""
    try:
        response = requests.get(f"{PI_URL}/api/camera/frame", timeout=5)
        data = response.json()
        
        if data.get('success'):
            # Decode frame
            frame_bytes = base64.b64decode(data['frame'])
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            return frame
    except Exception as e:
        print(f"Error getting frame: {e}")
    
    return None


def send_detection_to_pi(detection_data):
    """Send detection results to Raspberry Pi"""
    try:
        response = requests.post(
            f"{PI_URL}/api/webhook/detection",
            json=detection_data,
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"Error sending detection: {e}")
        return None


def track_object(bbox):
    """Send Pan-Tilt command to track object"""
    frame_center_x = 0.5
    frame_center_y = 0.5
    
    bbox_center_x = (bbox[0] + bbox[2]) / 2
    bbox_center_y = (bbox[1] + bbox[3]) / 2
    
    error_x = bbox_center_x - frame_center_x
    error_y = bbox_center_y - frame_center_y
    
    # Only adjust if error is significant
    if abs(error_x) > 0.1 or abs(error_y) > 0.1:
        pan_adjustment = int(error_x * 30)
        tilt_adjustment = int(error_y * 20)
        
        try:
            requests.post(
                f"{PI_URL}/api/pantilt/command",
                json={
                    "action": "move",
                    "pan": pan_adjustment,
                    "tilt": tilt_adjustment,
                    "speed": 8
                },
                timeout=5
            )
        except Exception as e:
            print(f"Error tracking: {e}")


def detection_loop(model):
    """Main detection loop"""
    print("Starting detection loop...")
    
    while True:
        try:
            # Get frame from Pi
            frame = get_frame_from_pi()
            if frame is None:
                time.sleep(1)
                continue
            
            # Run detection
            results = model(frame)
            
            # Process detections
            for detection in results:
                if detection['confidence'] < CONFIDENCE_THRESHOLD:
                    continue
                
                object_type = detection['class_name']
                confidence = detection['confidence']
                bbox = detection['bbox']  # [x1, y1, x2, y2] normalized
                
                print(f"Detected: {object_type} ({confidence:.2%})")
                
                # Determine action
                action = None
                car_id = None
                
                if object_type == 'car':
                    # Run custom car recognition here
                    car_id = recognize_car(frame, bbox)
                    
                    if car_id == 'my_car':
                        action = 'open_garage'
                
                # Encode detection image
                _, jpeg = cv2.imencode('.jpg', frame)
                image_data = base64.b64encode(jpeg.tobytes()).decode('utf-8')
                
                # Send to Pi
                detection_data = {
                    'timestamp': datetime.now().isoformat(),
                    'object_type': object_type,
                    'confidence': confidence,
                    'bbox': bbox,
                    'car_id': car_id,
                    'action': action,
                    'image_data': image_data
                }
                
                send_detection_to_pi(detection_data)
                
                # Track object
                track_object(bbox)
            
            # Rate limiting
            time.sleep(DETECTION_INTERVAL)
            
        except KeyboardInterrupt:
            print("\nStopping detection loop...")
            break
        except Exception as e:
            print(f"Error in detection loop: {e}")
            time.sleep(1)


if __name__ == "__main__":
    # Load your detection model
    from ultralytics import YOLO
    model = YOLO('yolov5s.pt')
    
    # Start detection
    detection_loop(model)
```

---

## Database Synchronization

Both systems maintain their own databases:

### Raspberry Pi Database
- **Purpose**: Local cache for web UI display
- **Location**: `security.db` on Raspberry Pi
- **Tables**: `detections`, `known_cars`
- **Populated by**: Jetson webhook calls

### Jetson Orin Database
- **Purpose**: Full detection history and analytics
- **Location**: Your Jetson project
- **Tables**: Your design
- **Populated by**: Detection loop

### Synchronization Strategy

1. **Real-time**: Jetson pushes detections to Pi via webhook
2. **Periodic**: Pi can query Jetson for full history if needed
3. **Conflict Resolution**: Jetson is source of truth

---

## Error Handling

### Retry Logic

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session():
    """Create session with retry logic"""
    session = requests.Session()
    
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session

# Use in detection loop
session = create_session()
response = session.get(f"{PI_URL}/api/camera/frame", timeout=5)
```

### Fallback Behavior

- **Frame request fails**: Wait 1 second, retry
- **Webhook fails**: Log locally, continue detection
- **Pan-Tilt fails**: Log error, continue detection
- **Telegram fails**: Log error, continue detection

---

## Configuration

### Raspberry Pi (`config.json`)

```json
{
  "jetson": {
    "url": "http://192.168.0.105:5001",
    "webhook_enabled": true,
    "frame_streaming": true,
    "webhook_url": "http://192.168.0.26:5000/api/webhook/detection"
  },
  "security": {
    "enabled": true,
    "mode": "io_only",
    "local_detection": false
  }
}
```

### Jetson Orin (your config)

```json
{
  "raspberry_pi": {
    "url": "http://192.168.0.26:5000",
    "frame_endpoint": "/api/camera/frame",
    "webhook_endpoint": "/api/webhook/detection"
  },
  "detection": {
    "model": "yolov5s",
    "confidence_threshold": 0.6,
    "detection_interval": 0.1,
    "classes_of_interest": ["car", "person", "motorcycle"]
  }
}
```

---

## Testing

### Test Camera Frame Endpoint

```bash
curl http://192.168.0.26:5000/api/camera/frame | jq .
```

### Test Webhook

```bash
curl -X POST http://192.168.0.26:5000/api/webhook/detection \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-10-12T20:15:30",
    "object_type": "car",
    "confidence": 0.87,
    "bbox": [0.3, 0.2, 0.7, 0.8],
    "car_id": "test_car",
    "action": null
  }'
```

### Test Pan-Tilt

```bash
curl -X POST http://192.168.0.26:5000/api/pantilt/command \
  -H "Content-Type: application/json" \
  -d '{"action": "move", "pan": 10, "tilt": -5, "speed": 5}'
```

### Test Telegram

```bash
curl -X POST http://192.168.0.26:5000/api/telegram/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Test notification from Jetson"}'
```

---

## Performance Considerations

### Bandwidth

- **Frame size**: ~50-100 KB per frame (JPEG quality 85)
- **Frame rate**: 10 FPS = ~500 KB/s to 1 MB/s
- **Network**: Gigabit Ethernet recommended

### Latency

- **Frame request**: ~20-50 ms
- **Detection**: ~30-100 ms (depends on model)
- **Webhook**: ~10-30 ms
- **Total loop**: ~100-200 ms (5-10 FPS achievable)

### Optimization

1. **Reduce frame resolution** for detection (640x480 instead of 1920x1080)
2. **Lower JPEG quality** (70 instead of 85)
3. **Skip frames** if detection is slow
4. **Use HTTP keep-alive** connections
5. **Batch multiple detections** in one webhook call

---

## Troubleshooting

### Issue: Frame request timeout

**Solution:** Check network connection, increase timeout, reduce frame size

### Issue: Webhook fails with 503

**Solution:** Ensure security system is initialized on Pi

### Issue: Pan-Tilt doesn't move

**Solution:** Check Pan-Tilt HAT connection, verify `pantilt_enabled` in status

### Issue: Telegram not sending

**Solution:** Verify bot token and chat ID in Pi's `config.json`

---

## Next Steps

1. Implement detection loop on Jetson Orin
2. Test frame streaming performance
3. Implement custom car recognition
4. Add detection analytics dashboard
5. Optimize for real-time performance

---

## Support

For issues or questions:
- Check `API_DOCUMENTATION.md` for full API reference
- Review logs: `sudo journalctl -u homepi.service -f`
- Test individual endpoints with curl
- Verify network connectivity between Pi and Jetson

