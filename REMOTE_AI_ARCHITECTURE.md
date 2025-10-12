# Remote AI Architecture

## Overview

The HomePi security system now uses a **remote AI inference architecture** instead of local Coral TPU processing. This provides better performance and flexibility.

## Architecture Diagram

```
┌──────────────────────────────────┐
│      Raspberry Pi 5              │
│                                  │
│  ┌────────────────────────────┐ │
│  │  Camera Module             │ │
│  │  (Capture frames)          │ │
│  └───────────┬────────────────┘ │
│              │                   │
│  ┌───────────▼────────────────┐ │
│  │  camera_manager.py         │ │
│  │  (Frame acquisition)       │ │
│  └───────────┬────────────────┘ │
│              │                   │
│  ┌───────────▼────────────────┐ │
│  │  object_detector.py        │ │
│  │  (Encode & send frame)     │ │
│  └───────────┬────────────────┘ │
│              │  HTTP API         │
│              │  (base64 JPEG)    │
└──────────────┼───────────────────┘
               │
               │ Network
               │
┌──────────────▼───────────────────┐
│      Nvidia Jetson Orin          │
│                                  │
│  ┌────────────────────────────┐ │
│  │  inference_server.py       │ │
│  │  (Flask API)               │ │
│  └───────────┬────────────────┘ │
│              │                   │
│  ┌───────────▼────────────────┐ │
│  │  YOLOv5 / Custom Model     │ │
│  │  (TensorRT/ONNX/PyTorch)   │ │
│  └───────────┬────────────────┘ │
│              │                   │
│  ┌───────────▼────────────────┐ │
│  │  GPU Inference             │ │
│  │  (CUDA acceleration)       │ │
│  └───────────┬────────────────┘ │
│              │                   │
│              │  Detections JSON  │
└──────────────┼───────────────────┘
               │
               │ Network
               │
┌──────────────▼───────────────────┐
│      Raspberry Pi 5              │
│                                  │
│  ┌────────────────────────────┐ │
│  │  security_manager.py       │ │
│  │  (Process detections)      │ │
│  └───────────┬────────────────┘ │
│              │                   │
│  ┌───────────▼────────────────┐ │
│  │  Pan-Tilt Tracking         │ │
│  │  Flipper Zero Control      │ │
│  │  Telegram Notifications    │ │
│  └────────────────────────────┘ │
└──────────────────────────────────┘
```

## Components

### Raspberry Pi Side

#### 1. `camera_manager.py`
- Captures frames from camera
- Provides frame buffer for detection
- Handles video recording

#### 2. `object_detector.py` (Modified)
- **Old**: Local Coral TPU inference
- **New**: HTTP client for remote inference
- Encodes frames to JPEG + base64
- Sends to Jetson via POST request
- Receives detection results

#### 3. `security_manager.py`
- Orchestrates detection loop
- Processes detection results
- Controls Pan-Tilt tracking
- Triggers Flipper Zero automation
- Sends Telegram notifications

#### 4. `pantilt_controller.py`
- Moves camera to track objects
- Follows detected cars/people

#### 5. `flipper_controller.py`
- Serial communication with Flipper Zero
- Triggers garage door opening

#### 6. `telegram_notifier.py`
- Sends alerts with photos/videos

### Jetson Orin Side

#### 1. `inference_server.py`
- Flask REST API server
- Receives base64-encoded images
- Runs object detection model
- Returns detection results (class, bbox, confidence)

#### 2. AI Model
- **Recommended**: YOLOv5 (fast, accurate)
- **Format**: ONNX or TensorRT engine
- **Input**: 640x640 RGB image
- **Output**: Class ID, bbox, confidence

## Data Flow

### 1. Detection Request

```json
POST http://jetson.local:5001/detect
{
  "image": "base64_encoded_jpeg_string",
  "threshold": 0.6,
  "classes": ["car", "person", "motorcycle"]
}
```

### 2. Detection Response

```json
{
  "success": true,
  "detections": [
    {
      "class_id": 2,
      "class_name": "car",
      "confidence": 0.87,
      "bbox_norm": [0.3, 0.2, 0.7, 0.8]
    }
  ],
  "count": 1
}
```

## Configuration

### Raspberry Pi `config.json`

```json
{
  "security": {
    "detection": {
      "remote_url": "http://192.168.1.100:5001",
      "confidence_threshold": 0.6,
      "detection_interval": 0.1,
      "detection_timeout": 5,
      "classes_of_interest": ["car", "person", "motorcycle"]
    }
  }
}
```

### Jetson Orin `inference_server.py`

```python
# Backend selection
BACKEND = 'tensorrt'  # or 'onnx', 'pytorch'

# Model path
model_path = 'models/yolov5s.onnx'

# Server settings
app.run(host='0.0.0.0', port=5001)
```

## Benefits of Remote Architecture

### 1. **Performance**
- Jetson Orin GPU >> Coral TPU
- Can run larger, more accurate models
- Faster inference (10-20ms vs 50-100ms)

### 2. **Flexibility**
- Easy to swap models without touching Pi
- Can upgrade Jetson independently
- Test models on laptop before deploying

### 3. **Scalability**
- One Jetson can serve multiple cameras
- Pi stays lightweight (only camera + servos)
- Can add more Pis without adding compute

### 4. **Custom Models**
- Easy to train custom car recognition
- Use PyTorch/TensorFlow directly on Jetson
- No Coral TPU constraints

### 5. **Python 3.13 Compatibility**
- No Coral TPU library issues
- Raspberry Pi can use latest Python
- Jetson uses stable Python 3.8-3.11

## Network Requirements

### Bandwidth

- Frame size: ~100-200 KB (JPEG compressed)
- Detection rate: 10 FPS
- Bandwidth needed: ~2 Mbps
- **Recommendation**: Wired Gigabit Ethernet

### Latency

- Encoding: 10-20ms
- Network transfer: 5-10ms (local network)
- Inference: 10-20ms (TensorRT)
- Decoding response: <1ms
- **Total**: 25-50ms (plenty fast for tracking)

### Reliability

- Use persistent HTTP session (keep-alive)
- Implement retry logic on connection loss
- Fallback: disable tracking, continue recording

## Setup Steps

### 1. Raspberry Pi

```bash
cd ~/homepi
sudo bash setup-security.sh
# Configure config.json with Jetson URL
```

### 2. Jetson Orin

```bash
# Follow JETSON_SETUP.md
mkdir ~/homepi-inference
cd ~/homepi-inference
# Copy inference_server.py
pip3 install -r requirements.txt
python3 inference_server.py
```

### 3. Test Connection

```bash
# On Raspberry Pi
cd ~/homepi
python3 object_detector.py
```

### 4. Configure Systemd (both machines)

Raspberry Pi: `homepi.service` (already exists)
Jetson Orin: `homepi-inference.service` (create new)

## Troubleshooting

### Connection Failed

```bash
# Check Jetson is reachable
ping jetson.local

# Check port is open
telnet jetson.local 5001

# Check firewall
sudo ufw status
```

### Slow Detection

```bash
# Use smaller model (yolov5s instead of yolov5m)
# Reduce input resolution (416x416 instead of 640x640)
# Use TensorRT engine instead of ONNX
```

### Out of Memory (Jetson)

```bash
# Monitor memory
tegrastats

# Use FP16 or INT8 quantization
# Reduce batch size
```

## Future Enhancements

### 1. **Multiple Cameras**
- Batch detection requests
- Round-robin load balancing

### 2. **Model Zoo**
- Face recognition model
- License plate reader (ALPR)
- Custom car classifier

### 3. **Edge Computing**
- Run lightweight model on Pi for pre-filtering
- Only send promising frames to Jetson

### 4. **Cloud Integration**
- Fallback to cloud API (AWS Rekognition, Google Vision)
- Long-term storage on S3/GCS

## Files Changed

- ✅ `object_detector.py` - Rewritten for HTTP client
- ✅ `config.json` - Updated detection config
- ✅ `requirements.txt` - Removed Coral TPU, added requests
- ✅ `setup-security.sh` - Removed Coral TPU setup
- ✅ Deleted: Coral Docker files
- ✅ Created: `JETSON_SETUP.md`
- ✅ Created: `REMOTE_AI_ARCHITECTURE.md`

## Summary

The remote AI architecture provides a **production-ready, scalable, and high-performance** solution for HomePi security system. Raspberry Pi handles hardware (camera, servos, sensors) while Jetson Orin handles the heavy AI compute.

