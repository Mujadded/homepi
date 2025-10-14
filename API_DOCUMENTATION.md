# HomePi API Documentation

## Project Overview

**HomePi** is a comprehensive Raspberry Pi-based home automation system that combines:
1. **Music Scheduler** - Schedule YouTube audio to play at specific times
2. **AI Security System** - Real-time object detection with Pan-Tilt camera tracking
3. **Environmental Monitoring** - Optional Sense HAT sensor integration

---

## Base URL

```
http://192.168.0.26:5000
```

Replace with your Raspberry Pi's IP address.

---

## Table of Contents

- [Music Scheduler API](#music-scheduler-api)
- [Security System API](#security-system-api)
- [Raspberry Pi I/O APIs (Jetson Integration)](#raspberry-pi-io-apis-jetson-integration)
  - [Patrol Mode APIs](#patrol-mode-apis)
- [System Health API](#system-health-api)
- [Sensor API](#sensor-api)
- [WebSocket Events](#websocket-events)

---

## Music Scheduler API

### Get All Schedules

```http
GET /api/schedules
```

**Response:**
```json
[
  {
    "id": "schedule_001",
    "name": "Morning Alarm",
    "url": "https://youtube.com/watch?v=...",
    "time": "07:00",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "enabled": true,
    "volume": 0.8
  }
]
```

### Create Schedule

```http
POST /api/schedules
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Evening Relaxation",
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "time": "18:30",
  "days": ["monday", "wednesday", "friday"],
  "enabled": true,
  "volume": 0.6
}
```

**Response:**
```json
{
  "success": true,
  "message": "Schedule created",
  "id": "schedule_002"
}
```

### Update Schedule

```http
PUT /api/schedules/{schedule_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "time": "19:00",
  "enabled": false
}
```

### Delete Schedule

```http
DELETE /api/schedules/{schedule_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Schedule deleted"
}
```

### Get Available Songs

```http
GET /api/songs
```

**Response:**
```json
[
  {
    "filename": "song1.mp3",
    "duration": 245.5,
    "size": 3932160
  }
]
```

### Playback Control

#### Get Playback Status

```http
GET /api/playback/status
```

**Response:**
```json
{
  "playing": true,
  "current_song": "song1.mp3",
  "volume": 0.8,
  "position": 45.2,
  "duration": 245.5
}
```

#### Play Song

```http
POST /api/playback/play
Content-Type: application/json
```

**Request Body:**
```json
{
  "song": "song1.mp3"
}
```

#### Stop Playback

```http
POST /api/playback/stop
```

#### Set Volume

```http
POST /api/playback/volume
Content-Type: application/json
```

**Request Body:**
```json
{
  "volume": 0.75
}
```

---

## Security System API

### Get Security Status

```http
GET /api/security/status
```

**Response:**
```json
{
  "enabled": true,
  "detection_running": true,
  "camera_enabled": true,
  "pantilt_enabled": true,
  "detector_enabled": true,
  "flipper_enabled": true,
  "telegram_enabled": true,
  "current_detections": 2,
  "tracking_target": true
}
```

### Enable Detection

```http
POST /api/security/enable
```

**Response:**
```json
{
  "success": true,
  "message": "Detection started"
}
```

### Disable Detection

```http
POST /api/security/disable
```

**Response:**
```json
{
  "success": true,
  "message": "Detection stopped"
}
```

### Get Recent Detections

```http
GET /api/security/detections?limit=20
```

**Query Parameters:**
- `limit` (optional): Number of detections to return (default: 20)

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2025-10-12T20:15:30",
    "object_type": "car",
    "confidence": 0.87,
    "car_id": "my_car",
    "action_taken": "garage_opened",
    "image_path": "detections/detection_20251012_201530.jpg",
    "bbox": [0.3, 0.2, 0.7, 0.8]
  },
  {
    "id": 2,
    "timestamp": "2025-10-12T20:18:45",
    "object_type": "person",
    "confidence": 0.92,
    "car_id": null,
    "action_taken": "notification_sent",
    "image_path": "detections/detection_20251012_201845.jpg",
    "bbox": [0.4, 0.3, 0.6, 0.9]
  }
]
```

### Get Detection Details

```http
GET /api/security/detections/{detection_id}
```

**Response:**
```json
{
  "id": 1,
  "timestamp": "2025-10-12T20:15:30",
  "object_type": "car",
  "confidence": 0.87,
  "car_id": "my_car",
  "action_taken": "garage_opened",
  "image_path": "detections/detection_20251012_201530.jpg",
  "video_path": "recordings/recording_20251012_201530.mp4",
  "bbox": [0.3, 0.2, 0.7, 0.8],
  "metadata": {
    "weather": "sunny",
    "temperature": 22.5
  }
}
```

### Live Camera Feed

```http
GET /api/security/live-feed
```

**Response:** MJPEG stream (multipart/x-mixed-replace)

**Usage in HTML:**
```html
<img src="http://192.168.0.26:5000/api/security/live-feed" alt="Live Feed">
```

### Pan-Tilt Control

#### Move Camera (Relative)

```http
POST /api/security/pantilt/move
Content-Type: application/json
```

**Request Body:**
```json
{
  "pan": 15,
  "tilt": -10,
  "speed": 5
}
```

- `pan`: Horizontal movement delta (-90 to +90, positive = right)
- `tilt`: Vertical movement delta (-90 to +90, positive = down)
- `speed`: Movement speed (1-10, higher = faster)

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

#### Move to Home Position

```http
POST /api/security/pantilt/home
```

**Response:**
```json
{
  "success": true,
  "position": {
    "pan": 0,
    "tilt": 0
  }
}
```

### Known Cars Management

#### Get Known Cars

```http
GET /api/security/cars
```

**Response:**
```json
[
  {
    "car_id": "my_car",
    "owner": "John Doe",
    "added_date": "2025-10-01T10:00:00"
  },
  {
    "car_id": "neighbor_car",
    "owner": "Jane Smith",
    "added_date": "2025-10-05T14:30:00"
  }
]
```

#### Add Known Car

```http
POST /api/security/cars
Content-Type: application/json
```

**Request Body:**
```json
{
  "car_id": "my_car",
  "owner": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Car added to known list"
}
```

#### Delete Known Car

```http
DELETE /api/security/cars/{car_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Car removed from known list"
}
```

### Training Data Upload

#### Upload Training Image

```http
POST /api/security/training/upload
Content-Type: multipart/form-data
```

**Form Data:**
- `image`: Image file (JPEG/PNG)
- `label`: Label identifier (e.g., "my_car", "dad", "mom")
- `category`: Category type ("car" or "person")

**Response:**
```json
{
  "success": true,
  "message": "Image saved for my_car",
  "filepath": "training_data/car/my_car/my_car_20251012_201530.jpg",
  "image_count": 15,
  "needs_more": true
}
```

#### Get Training Labels

```http
GET /api/security/training/labels
```

**Response:**
```json
{
  "cars": {
    "my_car": {
      "count": 45,
      "ready": false
    },
    "neighbor_car": {
      "count": 52,
      "ready": true
    }
  },
  "persons": {
    "dad": {
      "count": 60,
      "ready": true
    },
    "mom": {
      "count": 48,
      "ready": false
    }
  }
}
```

#### Train Model

```http
POST /api/security/training/train
Content-Type: application/json
```

**Request Body:**
```json
{
  "category": "car"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Training started",
  "note": "Training functionality coming soon. For now, use remote training on laptop.",
  "guide": "See TRAINING_GUIDE.md for instructions"
}
```

---

## System Health API

### Get System Health

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "uptime": 86400,
  "cpu_percent": 45.2,
  "memory_percent": 62.8,
  "disk_percent": 38.5,
  "temperature": 52.3,
  "schedules_count": 8,
  "last_backup": "2025-10-12T03:00:00",
  "security": {
    "enabled": true,
    "detection_running": true,
    "detections_today": 15
  }
}
```

### Get Backups

```http
GET /api/backups
```

**Response:**
```json
[
  {
    "filename": "schedules_20251012_030000.json",
    "date": "2025-10-12T03:00:00",
    "size": 2048
  }
]
```

### Create Manual Backup

```http
POST /api/backup
```

**Response:**
```json
{
  "success": true,
  "message": "Backup created",
  "filename": "schedules_20251012_203045.json"
}
```

---

## Sensor API

### Get Sensor Data

```http
GET /api/sensors
```

**Response:**
```json
{
  "enabled": true,
  "temperature": 22.5,
  "humidity": 45.2,
  "pressure": 1013.25,
  "orientation": {
    "pitch": 2.3,
    "roll": -1.5,
    "yaw": 0.8
  },
  "accelerometer": {
    "x": 0.02,
    "y": -0.01,
    "z": 9.81
  },
  "gyroscope": {
    "x": 0.1,
    "y": -0.2,
    "z": 0.05
  },
  "magnetometer": {
    "x": 23.5,
    "y": -12.3,
    "z": 45.6
  }
}
```

---

## Raspberry Pi I/O APIs (Jetson Integration)

**Note:** These APIs are designed for the Jetson Orin to control the Raspberry Pi's I/O devices. The Raspberry Pi operates in **I/O-only mode** where all AI processing is handled by the Jetson.

### Get Camera Frame

```http
GET /api/camera/frame
```

**Description:** Get a single camera frame for AI processing on Jetson.

**Response:**
```json
{
  "success": true,
  "frame": "base64_encoded_jpeg_string",
  "timestamp": "2025-10-12T20:15:30.123456"
}
```

**Usage Example:**
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

### Webhook: Receive Detection Results

```http
POST /api/webhook/detection
Content-Type: application/json
```

**Description:** Jetson sends detection results to Raspberry Pi for storage and action execution.

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
- `action`: Action to execute (open_garage, send_notification, null)
- `image_data`: Optional base64-encoded detection image

**Response:**
```json
{
  "success": true,
  "detection_id": 123,
  "message": "Detection processed"
}
```

**Actions Supported:**
- `open_garage`: Triggers Flipper Zero to open garage door
- `send_notification`: Sends Telegram notification (automatic if image_data provided)
- `null`: Store detection only, no action

### Pan-Tilt Command

```http
POST /api/pantilt/command
Content-Type: application/json
```

**Description:** Control Pan-Tilt HAT from Jetson for object tracking. Automatically interrupts patrol mode if active.

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

**Parameters:**
- `action`: "move" or "home"
- `pan`: Horizontal adjustment in degrees (positive = right)
- `tilt`: Vertical adjustment in degrees (positive = down)
- `speed`: Movement speed (1-10, higher = faster)

**Note:** Commands automatically interrupt patrol mode and resume after 5 seconds.

### Send Telegram Notification

```http
POST /api/telegram/send
Content-Type: application/json
```

**Description:** Send Telegram notification from Jetson.

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

**Note:** If `image_data` is provided in the webhook detection, Telegram notification is sent automatically.

### Trigger Flipper Zero Action

```http
POST /api/flipper/trigger
Content-Type: application/json
```

**Description:** Trigger Flipper Zero automation from Jetson.

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

**Actions Supported:**
- `garage_open`: Send garage door open signal

### Patrol Mode APIs

**Description:** Control automated Pan-Tilt patrol patterns with customizable positions and timing.

#### Start Patrol

```http
POST /api/pantilt/patrol/start
Content-Type: application/json
```

**Request Body:**
```json
{
  "speed": 7
}
```

**Response:**
```json
{
  "success": true,
  "message": "Patrol started",
  "status": {
    "active": true,
    "interrupted": false,
    "position_count": 4,
    "current_index": 0,
    "speed": 7,
    "resume_delay": 5,
    "direction": "forward"
  }
}
```

**Parameters:**
- `speed`: Movement speed between positions (1-10, higher = faster)

#### Stop Patrol

```http
POST /api/pantilt/patrol/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Patrol stopped"
}
```

#### Get Patrol Status

```http
GET /api/pantilt/patrol/status
```

**Response:**
```json
{
  "active": true,
  "interrupted": false,
  "position_count": 4,
  "current_index": 2,
  "speed": 5,
  "resume_delay": 5,
  "direction": "backward"
}
```

**Status Fields:**
- `active`: Whether patrol is currently running
- `interrupted`: Whether patrol is temporarily paused (auto-resumes)
- `position_count`: Number of saved patrol positions
- `current_index`: Current position in patrol sequence (null if inactive)
- `speed`: Current movement speed (1-10)
- `resume_delay`: Seconds to wait before resuming after interrupt
- `direction`: Current patrol direction ("forward" or "backward")

#### Get Patrol Positions

```http
GET /api/pantilt/patrol/positions
```

**Response:**
```json
{
  "positions": [
    {
      "id": 1,
      "pan": -45,
      "tilt": 0,
      "dwell_time": 10,
      "created_at": "2025-10-14T15:30:00"
    },
    {
      "id": 2,
      "pan": 0,
      "tilt": -20,
      "dwell_time": 5,
      "created_at": "2025-10-14T15:31:00"
    },
    {
      "id": 3,
      "pan": 45,
      "tilt": 0,
      "dwell_time": 8,
      "created_at": "2025-10-14T15:32:00"
    }
  ]
}
```

#### Add Patrol Position

```http
POST /api/pantilt/patrol/positions/add
Content-Type: application/json
```

**Description:** Save current Pan-Tilt position as a patrol waypoint.

**Request Body:**
```json
{
  "dwell_time": 15
}
```

**Response:**
```json
{
  "success": true,
  "position": {
    "id": 4,
    "pan": 30,
    "tilt": -10,
    "dwell_time": 15,
    "created_at": "2025-10-14T15:35:00"
  }
}
```

**Parameters:**
- `dwell_time`: How long to stay at this position in seconds (5-60)

#### Update Patrol Position

```http
PUT /api/pantilt/patrol/positions/{position_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "dwell_time": 20
}
```

**Response:**
```json
{
  "success": true,
  "message": "Position 4 updated"
}
```

#### Delete Patrol Position

```http
DELETE /api/pantilt/patrol/positions/{position_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Position 4 deleted"
}
```

**Patrol Behavior:**
- **Pattern**: Back-and-forth movement (1→2→3→2→1→2→3...)
- **Interrupts**: Manual controls and Jetson commands pause patrol
- **Auto-Resume**: Patrol resumes automatically after 5 seconds
- **Position Recording**: Use Pan-Tilt controls to move camera, then save position
- **Customizable**: Each position has individual dwell time (5-60 seconds)

---

## Jetson Orin APIs (Expected Implementation)

**Note:** These are the APIs your Jetson Orin project should implement for full integration.

### Health Check

```http
GET http://192.168.0.105:5001/status
```

**Expected Response:**
```json
{
  "status": "running",
  "model_loaded": true,
  "device": "cuda",
  "fps": 28.5,
  "detections_today": 45,
  "uptime": 86400
}
```

### Get Detection History

```http
GET http://192.168.0.105:5001/detections?limit=20
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2025-10-12T20:15:30",
    "object_type": "car",
    "confidence": 0.87,
    "car_id": "my_car",
    "action_taken": "garage_opened",
    "bbox": [0.3, 0.2, 0.7, 0.8]
  }
]
```

### Get Specific Detection

```http
GET http://192.168.0.105:5001/detections/{detection_id}
```

**Expected Response:**
```json
{
  "id": 1,
  "timestamp": "2025-10-12T20:15:30",
  "object_type": "car",
  "confidence": 0.87,
  "car_id": "my_car",
  "action_taken": "garage_opened",
  "bbox": [0.3, 0.2, 0.7, 0.8],
  "processing_time_ms": 45,
  "model_version": "yolov5s"
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error
- `503` - Service Unavailable (feature disabled)

---

## Authentication

Currently, the API does not require authentication. For production use, consider adding:
- API key authentication
- JWT tokens
- IP whitelisting
- HTTPS/TLS encryption

---

## Rate Limiting

No rate limiting is currently implemented. For production:
- Recommended: 100 requests per minute per IP
- Live feed: 1 concurrent connection per client

---

## CORS

CORS is enabled for all origins. Headers included:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

---

## Integration Examples

### Python

```python
import requests

BASE_URL = "http://192.168.0.26:5000"

# Get security status
response = requests.get(f"{BASE_URL}/api/security/status")
status = response.json()
print(f"Detection running: {status['detection_running']}")

# Get recent detections
detections = requests.get(f"{BASE_URL}/api/security/detections?limit=5").json()
for det in detections:
    print(f"{det['timestamp']}: {det['object_type']} ({det['confidence']:.2%})")

# Move camera
requests.post(f"{BASE_URL}/api/security/pantilt/move", json={
    "pan": 15,
    "tilt": -10,
    "speed": 5
})

# Patrol mode example
# Save current position for patrol
requests.post(f"{BASE_URL}/api/pantilt/patrol/positions/add", json={
    "dwell_time": 10
})

# Start patrol at speed 7
requests.post(f"{BASE_URL}/api/pantilt/patrol/start", json={
    "speed": 7
})

# Check patrol status
patrol_status = requests.get(f"{BASE_URL}/api/pantilt/patrol/status").json()
print(f"Patrol active: {patrol_status['active']}, Positions: {patrol_status['position_count']}")

# Stop patrol
requests.post(f"{BASE_URL}/api/pantilt/patrol/stop")
```

### JavaScript (Browser)

```javascript
const BASE_URL = "http://192.168.0.26:5000";

// Get security status
async function getSecurityStatus() {
  const response = await fetch(`${BASE_URL}/api/security/status`);
  const status = await response.json();
  console.log("Detection running:", status.detection_running);
}

// Get recent detections
async function getDetections() {
  const response = await fetch(`${BASE_URL}/api/security/detections?limit=5`);
  const detections = await response.json();
  detections.forEach(det => {
    console.log(`${det.timestamp}: ${det.object_type} (${(det.confidence * 100).toFixed(1)}%)`);
  });
}

// Move camera
async function moveCamera(pan, tilt) {
  await fetch(`${BASE_URL}/api/security/pantilt/move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pan, tilt, speed: 5 })
  });
}
```

### Node.js

```javascript
const axios = require('axios');

const BASE_URL = "http://192.168.0.26:5000";

// Get security status
async function getSecurityStatus() {
  const { data } = await axios.get(`${BASE_URL}/api/security/status`);
  console.log("Detection running:", data.detection_running);
}

// Upload training image
async function uploadTrainingImage(imagePath, label, category) {
  const FormData = require('form-data');
  const fs = require('fs');
  
  const form = new FormData();
  form.append('image', fs.createReadStream(imagePath));
  form.append('label', label);
  form.append('category', category);
  
  const { data } = await axios.post(
    `${BASE_URL}/api/security/training/upload`,
    form,
    { headers: form.getHeaders() }
  );
  
  console.log(`Uploaded: ${data.image_count} images for ${label}`);
}
```

### cURL

```bash
# Get security status
curl http://192.168.0.26:5000/api/security/status

# Get recent detections
curl http://192.168.0.26:5000/api/security/detections?limit=5

# Enable detection
curl -X POST http://192.168.0.26:5000/api/security/enable

# Move camera
curl -X POST http://192.168.0.26:5000/api/security/pantilt/move \
  -H "Content-Type: application/json" \
  -d '{"pan": 15, "tilt": -10, "speed": 5}'

# Add known car
curl -X POST http://192.168.0.26:5000/api/security/cars \
  -H "Content-Type: application/json" \
  -d '{"car_id": "my_car", "owner": "John Doe"}'

# Upload training image
curl -X POST http://192.168.0.26:5000/api/security/training/upload \
  -F "image=@/path/to/car.jpg" \
  -F "label=my_car" \
  -F "category=car"

# Patrol mode examples
# Save current position for patrol
curl -X POST http://192.168.0.26:5000/api/pantilt/patrol/positions/add \
  -H "Content-Type: application/json" \
  -d '{"dwell_time": 15}'

# Start patrol
curl -X POST http://192.168.0.26:5000/api/pantilt/patrol/start \
  -H "Content-Type: application/json" \
  -d '{"speed": 7}'

# Get patrol status
curl http://192.168.0.26:5000/api/pantilt/patrol/status

# Get patrol positions
curl http://192.168.0.26:5000/api/pantilt/patrol/positions

# Stop patrol
curl -X POST http://192.168.0.26:5000/api/pantilt/patrol/stop
```

---

## Architecture

### I/O Device Mode

HomePi operates in **I/O-only mode** where the Raspberry Pi handles all input/output operations while the Jetson Orin handles AI processing.

### Components

1. **Raspberry Pi 5** - I/O Device
   - Flask web server (port 5000)
   - Camera frame streaming
   - Pan-Tilt HAT control (commanded by Jetson)
   - Flipper Zero serial interface
   - Telegram bot integration
   - Local database (cache for web UI)
   - Web UI with live feed

2. **Nvidia Jetson Orin** - AI Processing Brain
   - Object detection (YOLOv5/Custom models)
   - Detection loop management
   - Decision making logic
   - Custom car/person recognition
   - Full detection database
   - HTTP client to control Raspberry Pi

3. **Flipper Zero** - Automation Device
   - Sub-GHz garage door control
   - USB serial connection to Raspberry Pi

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Jetson Orin                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Detection Loop:                                        │ │
│  │  1. GET /api/camera/frame → Raspberry Pi              │ │
│  │  2. Run AI detection                                    │ │
│  │  3. Analyze & decide actions                            │ │
│  │  4. POST /api/webhook/detection → Raspberry Pi        │ │
│  │  5. POST /api/pantilt/command (tracking)              │ │
│  └────────────────────────────────────────────────────────┘ │
│                  Full Detection Database                     │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP APIs ↓
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  I/O Operations:                                        │ │
│  │  • Stream camera frames                                 │ │
│  │  • Execute Pan-Tilt movements                           │ │
│  │  • Send Telegram notifications                          │ │
│  │  • Trigger Flipper Zero actions                         │ │
│  │  • Cache detections locally                             │ │
│  │  • Serve web UI                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│              Local Database (UI Cache)                       │
│                        ↓                                     │
│              ┌──────────────────────┐                       │
│              │  Telegram Bot        │                       │
│              │  Flipper Zero        │                       │
│              │  Pan-Tilt HAT        │                       │
│              │  Camera              │                       │
│              └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

**SQLite Database: `security.db`**

**Table: `detections`**
```sql
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    object_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    bbox TEXT,
    image_path TEXT,
    video_path TEXT,
    car_id TEXT,
    action_taken TEXT,
    metadata TEXT
);
```

**Table: `known_cars`**
```sql
CREATE TABLE known_cars (
    car_id TEXT PRIMARY KEY,
    owner TEXT,
    added_date TEXT NOT NULL
);
```

---

## Configuration

**File: `config.json`**

```json
{
  "music": {
    "enabled": true
  },
  "jetson": {
    "url": "http://192.168.0.105:5001",
    "webhook_enabled": true,
    "frame_streaming": true,
    "webhook_url": "http://192.168.0.26:5000/api/webhook/detection"
  },
  "security": {
    "enabled": true,
    "mode": "io_only",
    "local_detection": false,
    "camera": {
      "resolution": [1920, 1080],
      "fps": 30,
      "rotation": 0
    },
    "pantilt": {
      "pan_limits": [-90, 90],
      "tilt_limits": [-45, 45],
      "home_position": [0, 0],
      "tracking_enabled": true,
      "tracking_speed": 5,
      "patrol": {
        "default_speed": 5,
        "default_dwell_time": 10,
        "resume_delay": 5,
        "max_positions": 20
      }
    },
    "detection": {
      "remote_url": "http://192.168.0.105:5001",
      "confidence_threshold": 0.6,
      "detection_interval": 0.1,
      "classes_of_interest": ["car", "person", "motorcycle", "bicycle", "truck"]
    },
    "recording": {
      "clips_dir": "recordings",
      "clip_duration": 30,
      "keep_days": 30,
      "format": "mp4"
    },
    "automation": {
      "flipper_port": "/dev/ttyACM0",
      "garage_trigger": "my_car",
      "auto_open": true,
      "cooldown_seconds": 300
    },
    "notifications": {
      "telegram_enabled": true,
      "telegram_bot_token": "YOUR_BOT_TOKEN",
      "telegram_chat_id": "YOUR_CHAT_ID",
      "send_photo": true,
      "send_video": false,
      "notify_my_car": true,
      "notify_unknown_car": true,
      "notify_person": false
    }
  }
}
```

---

## Deployment

### Requirements

**Raspberry Pi:**
- Raspberry Pi 4/5 with 4GB+ RAM
- Raspberry Pi OS (Debian Bookworm/Trixie)
- Python 3.11+
- Camera Module v2/v3
- Pan-Tilt HAT (Pimoroni)
- Flipper Zero (optional)

**Jetson Orin:**
- Nvidia Jetson Orin Nano/NX
- JetPack 5.x
- Docker with NVIDIA Container Toolkit
- CUDA 11.4+

### Installation

```bash
# On Raspberry Pi
cd ~/homepi
./install.sh
sudo systemctl enable homepi.service
sudo systemctl start homepi.service

# On Jetson Orin
cd ~/homepi
./setup-jetson-docker.sh
docker-compose -f docker-compose.jetson.yml up -d
```

---

## Support & Documentation

- **Main README**: `README.md`
- **Jetson Integration**: `JETSON_INTEGRATION.md` (detailed guide for I/O mode)
- **API Documentation**: `API_DOCUMENTATION.md` (this file)
- **Security Setup**: `JETSON_SETUP.md`, `TESTING_GUIDE.md`
- **Training Guide**: `TRAINING_GUIDE.md`
- **Architecture**: `REMOTE_AI_ARCHITECTURE.md`
- **Implementation Status**: `IMPLEMENTATION_STATUS.md`

---

## License

MIT License - See LICENSE file for details

---

## Version

**Current Version:** 2.1.0  
**Last Updated:** October 14, 2025  
**API Version:** v1

**Latest Changes (v2.1.0):**
- ✅ Added Patrol Mode APIs for automated Pan-Tilt camera movement
- ✅ Customizable patrol positions with individual dwell times
- ✅ Back-and-forth patrol pattern with interrupt/resume capability
- ✅ Integration with Jetson commands for seamless tracking
- ✅ Removed training section from web UI (moved to Jetson)

