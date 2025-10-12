# Jetson Orin Quick Start Guide

## Overview

Simple PyTorch-based inference server for your Jetson Orin. No Docker or ONNX Runtime needed!

## On Your Mac (copy files to Jetson)

```bash
# Copy inference server
scp jetson_inference_server.py kronos@192.168.0.105:~/homepi-inference/inference_server.py

# Copy setup script
scp jetson_setup.sh kronos@192.168.0.105:~/
```

## On Jetson Orin (SSH in)

### 1. Run Setup Script

```bash
cd ~
bash jetson_setup.sh
```

This will:
- Install PyTorch (if not already installed)
- Install Flask, OpenCV, numpy
- Create project directory
- Set up systemd service

### 2. Create Directory and Copy Server

```bash
mkdir -p ~/homepi-inference
# Then copy the file from Mac (see above)
```

Or manually create `~/homepi-inference/inference_server.py` and paste the code.

### 3. Test Server Manually

```bash
cd ~/homepi-inference
python3 inference_server.py
```

You should see:
```
==================================================
  HomePi AI Inference Server
==================================================

✓ CUDA available: Orin
✓ Model loaded successfully

Starting Flask server on http://0.0.0.0:5001
```

### 4. Test from Another Terminal

Open another SSH session or terminal:

```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "HomePi AI Inference",
  "backend": "pytorch",
  "model": "YOLOv5s",
  "device": "cuda",
  "model_loaded": true,
  "cuda_available": true
}
```

### 5. Test Detection (Optional)

Create a test image and send it:

```python
import base64
import requests
import json
from PIL import Image
import numpy as np

# Create test image
img = Image.new('RGB', (640, 480), color='blue')
img.save('test.jpg')

# Encode to base64
with open('test.jpg', 'rb') as f:
    b64_img = base64.b64encode(f.read()).decode('utf-8')

# Send to server
response = requests.post(
    'http://localhost:5001/detect',
    json={
        'image': b64_img,
        'threshold': 0.6,
        'classes': ['car', 'person']
    }
)

print(response.json())
```

### 6. Enable Auto-Start (Once Working)

```bash
sudo systemctl enable homepi-inference.service
sudo systemctl start homepi-inference.service
sudo systemctl status homepi-inference.service
```

### 7. View Logs

```bash
# Real-time logs
journalctl -u homepi-inference.service -f

# Recent logs
journalctl -u homepi-inference.service -n 100
```

## On Raspberry Pi (Test Connection)

```bash
cd ~/homepi

# Test connection
python3 object_detector.py

# When prompted, press Enter to use config.json URL (192.168.0.105:5001)
```

You should see:
```
✓ Remote AI service connected
  Service: HomePi AI Inference
  Model: YOLOv5s
  Device: cuda
```

## Troubleshooting

### PyTorch not found

```bash
pip3 install torch torchvision
```

### CUDA not available

Check CUDA installation:
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```

If False, check JetPack installation.

### Model download slow

First run downloads YOLOv5 model (~14MB). This happens automatically. Wait a few minutes.

### Port 5001 already in use

```bash
# Check what's using it
sudo lsof -i :5001

# Kill process
sudo kill -9 <PID>
```

### Firewall issues

```bash
sudo ufw allow 5001/tcp
sudo ufw reload
```

## Performance

Expected inference times on Jetson Orin:

- **With CUDA**: 10-20ms per frame
- **CPU only**: 50-100ms per frame

YOLOv5s is optimized for speed while maintaining good accuracy.

## Model Options

You can change the model in `inference_server.py`:

```python
# Line 63: Change model size
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Small (fastest)
model = torch.hub.load('ultralytics/yolov5', 'yolov5m')  # Medium
model = torch.hub.load('ultralytics/yolov5', 'yolov5l')  # Large
model = torch.hub.load('ultralytics/yolov5', 'yolov5x')  # Extra large
```

## Next Steps

1. ✅ Get server running on Jetson
2. ✅ Test from Raspberry Pi
3. ⏳ Test full security system on Pi
4. ⏳ Train custom car model (optional)

## Support

- Check logs: `journalctl -u homepi-inference.service -f`
- Test health: `curl http://192.168.0.105:5001/health`
- Restart: `sudo systemctl restart homepi-inference.service`

