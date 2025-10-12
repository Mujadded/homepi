# Jetson Orin AI Inference Server Setup

This guide covers setting up a remote AI inference server on your Nvidia Jetson Orin for HomePi security system.

## Architecture

```
┌─────────────────┐      HTTP API       ┌──────────────────┐
│  Raspberry Pi   │ ───────────────────> │  Jetson Orin     │
│  (Camera +      │  (base64 image)      │  (AI Inference)  │
│   Pan-Tilt)     │ <─────────────────── │                  │
└─────────────────┘  (detections JSON)   └──────────────────┘
```

**Benefits:**
- Jetson Orin has more powerful GPU (much faster inference)
- Can run larger, more accurate models
- Raspberry Pi stays lightweight (just camera + servo control)
- Easy to upgrade models without touching Raspberry Pi

---

## Part 1: Jetson Orin Setup

### 1. Install JetPack SDK

On your Jetson Orin:

```bash
# Check JetPack version
sudo apt-cache show nvidia-jetpack

# Update system
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install Dependencies

```bash
# Python and pip
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-opencv \
    libopencv-dev

# Deep learning frameworks
sudo apt-get install -y \
    nvidia-tensorrt \
    python3-libnvinfer \
    python3-libnvinfer-dev

# Flask for API server
pip3 install flask flask-cors numpy pillow
```

### 3. Install PyTorch (optional, for custom models)

```bash
# For JetPack 5.x
wget https://nvidia.box.com/shared/static/url_to_torch.whl
pip3 install torch-*.whl

# Verify
python3 -c "import torch; print(torch.cuda.is_available())"
```

### 4. Install ONNX Runtime (recommended)

```bash
# ONNX Runtime with TensorRT backend
pip3 install onnxruntime-gpu

# Verify
python3 -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

---

## Part 2: Inference Server Code

Create a directory on Jetson for the inference server:

```bash
mkdir ~/homepi-inference
cd ~/homepi-inference
```

### File: `inference_server.py`

```python
"""
HomePi AI Inference Server for Nvidia Jetson Orin
Provides REST API for object detection
"""

import os
import time
import base64
import json
import logging
from io import BytesIO

import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

# Choose your inference backend
BACKEND = 'tensorrt'  # Options: 'tensorrt', 'onnx', 'pytorch'

# Load model based on backend
if BACKEND == 'tensorrt':
    # TODO: Implement TensorRT engine loading
    import tensorrt as trt
    
elif BACKEND == 'onnx':
    import onnxruntime as ort
    
elif BACKEND == 'pytorch':
    import torch

# COCO class names
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench'
    # ... (add all 80 classes)
]

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global model state
model = None
model_loaded = False


def load_model():
    """Load object detection model"""
    global model, model_loaded
    
    logger.info(f"Loading model with {BACKEND} backend...")
    
    if BACKEND == 'onnx':
        # Example: YOLOv5 ONNX model
        model_path = 'models/yolov5s.onnx'
        
        providers = ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
        model = ort.InferenceSession(model_path, providers=providers)
        
        logger.info(f"Model loaded with providers: {model.get_providers()}")
        
    elif BACKEND == 'pytorch':
        # Example: Load pre-trained model
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
        model.cuda()  # Move to GPU
        model.eval()
        
    model_loaded = True
    logger.info("Model loaded successfully")


def decode_image(b64_string):
    """Decode base64 image to numpy array"""
    try:
        # Decode base64
        img_bytes = base64.b64decode(b64_string)
        
        # Load with PIL
        pil_img = Image.open(BytesIO(img_bytes))
        
        # Convert to numpy RGB
        img_array = np.array(pil_img)
        
        # Ensure RGB format
        if len(img_array.shape) == 2:  # Grayscale
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif img_array.shape[2] == 4:  # RGBA
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
        return img_array
        
    except Exception as e:
        logger.error(f"Error decoding image: {e}")
        return None


def preprocess(image):
    """Preprocess image for model input"""
    # Resize to model input size (e.g., 640x640 for YOLOv5)
    input_size = (640, 640)
    resized = cv2.resize(image, input_size)
    
    # Normalize to [0, 1]
    normalized = resized.astype(np.float32) / 255.0
    
    # Transpose to CHW format and add batch dimension
    input_tensor = np.transpose(normalized, (2, 0, 1))[np.newaxis, ...]
    
    return input_tensor


def postprocess(outputs, original_shape, threshold=0.6):
    """Post-process model outputs to get detections"""
    detections = []
    
    # This depends on your model output format
    # Example for YOLOv5 output: [batch, num_predictions, 85]
    # 85 = x, y, w, h, confidence, class_scores (80 classes)
    
    for output in outputs[0]:  # Iterate over predictions
        confidence = output[4]
        
        if confidence < threshold:
            continue
        
        # Get class with highest score
        class_scores = output[5:]
        class_id = np.argmax(class_scores)
        class_confidence = class_scores[class_id]
        
        if class_confidence < threshold:
            continue
        
        # Get bounding box (center format)
        x_center, y_center, width, height = output[:4]
        
        # Convert to corner format and normalize
        x1 = (x_center - width / 2) / 640
        y1 = (y_center - height / 2) / 640
        x2 = (x_center + width / 2) / 640
        y2 = (y_center + height / 2) / 640
        
        # Clip to [0, 1]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(1, x2), min(1, y2)
        
        detections.append({
            'class_id': int(class_id),
            'class_name': COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else f'class_{class_id}',
            'confidence': float(confidence * class_confidence),
            'bbox_norm': (x1, y1, x2, y2)
        })
    
    return detections


def run_inference(image, threshold=0.6):
    """Run inference on image"""
    global model, model_loaded
    
    if not model_loaded:
        return []
    
    try:
        # Preprocess
        input_tensor = preprocess(image)
        
        # Run inference
        start_time = time.time()
        
        if BACKEND == 'onnx':
            input_name = model.get_inputs()[0].name
            outputs = model.run(None, {input_name: input_tensor})
        elif BACKEND == 'pytorch':
            with torch.no_grad():
                results = model(image)
                outputs = results.xyxy[0].cpu().numpy()
        
        inference_time = (time.time() - start_time) * 1000
        
        # Post-process
        detections = postprocess(outputs, image.shape, threshold)
        
        logger.info(f"Inference: {inference_time:.1f}ms, Detections: {len(detections)}")
        
        return detections
        
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return []


# ============================================
# Flask Routes
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'HomePi AI Inference',
        'backend': BACKEND,
        'model': 'YOLOv5s' if BACKEND == 'pytorch' else 'Custom',
        'device': 'Nvidia Jetson Orin',
        'model_loaded': model_loaded
    })


@app.route('/detect', methods=['POST'])
def detect():
    """Object detection endpoint"""
    try:
        data = request.json
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode image
        image = decode_image(data['image'])
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        # Get threshold and classes filter
        threshold = data.get('threshold', 0.6)
        classes_filter = data.get('classes', [])
        
        # Run inference
        detections = run_inference(image, threshold)
        
        # Filter by class if specified
        if classes_filter:
            detections = [d for d in detections if d['class_name'] in classes_filter]
        
        return jsonify({
            'success': True,
            'detections': detections,
            'count': len(detections)
        })
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Load model on startup
    load_model()
    
    # Start Flask server
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )
```

### File: `requirements.txt`

```
Flask==3.0.0
Flask-CORS==4.0.0
numpy
opencv-python
Pillow
onnxruntime-gpu  # or onnxruntime for CPU
```

---

## Part 3: Download Models

### Option 1: YOLOv5 (Recommended for Speed)

```bash
# Download YOLOv5 ONNX model
cd ~/homepi-inference
mkdir models
cd models

# Small model (fast, good for real-time)
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.onnx

# Or medium model (slower, more accurate)
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.onnx
```

### Option 2: PyTorch Model (Easiest)

```python
# No download needed, PyTorch Hub handles it
import torch
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
```

---

## Part 4: Run the Server

### Start Server

```bash
cd ~/homepi-inference
python3 inference_server.py
```

Server will start on `http://0.0.0.0:5001`

### Test Server

```bash
# From Jetson or Raspberry Pi
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "HomePi AI Inference",
  "backend": "onnx",
  "model": "YOLOv5s",
  "device": "Nvidia Jetson Orin",
  "model_loaded": true
}
```

---

## Part 5: Auto-Start on Boot

Create systemd service on Jetson:

```bash
sudo nano /etc/systemd/system/homepi-inference.service
```

```ini
[Unit]
Description=HomePi AI Inference Server
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/homepi-inference
ExecStart=/usr/bin/python3 /home/jetson/homepi-inference/inference_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable homepi-inference.service
sudo systemctl start homepi-inference.service
sudo systemctl status homepi-inference.service
```

---

## Part 6: Raspberry Pi Configuration

Update `config.json` on Raspberry Pi:

```json
{
  "security": {
    "detection": {
      "remote_url": "http://jetson.local:5001",
      "confidence_threshold": 0.6,
      "detection_timeout": 5,
      "classes_of_interest": ["car", "person", "motorcycle"]
    }
  }
}
```

Replace `jetson.local` with:
- Hostname (if mDNS works)
- IP address (e.g., `192.168.1.100`)
- Domain name (if you have DNS)

---

## Part 7: Test Connection

On Raspberry Pi:

```bash
cd ~/homepi
python3 object_detector.py
```

Follow prompts to test remote connection.

---

## Network Tips

### Static IP for Jetson (Recommended)

Edit `/etc/netplan/*.yaml`:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

Apply:
```bash
sudo netplan apply
```

### Firewall

Allow port 5001:

```bash
sudo ufw allow 5001/tcp
sudo ufw reload
```

---

## Performance Optimization

### 1. Use TensorRT Engine

Convert ONNX to TensorRT for maximum speed:

```bash
/usr/src/tensorrt/bin/trtexec \
    --onnx=yolov5s.onnx \
    --saveEngine=yolov5s.engine \
    --fp16  # or --int8 for even faster
```

### 2. Batch Processing

If multiple cameras, modify server to accept batch requests.

### 3. Model Quantization

Use INT8 quantization for 2-3x speedup with minimal accuracy loss.

---

## Troubleshooting

### Jetson not reachable

```bash
# Check network
ping jetson.local

# Check service
ssh jetson@jetson.local
sudo systemctl status homepi-inference.service
```

### Slow inference

```bash
# Check GPU usage
tegrastats

# Monitor CUDA
nvidia-smi

# Use smaller model (yolov5s instead of yolov5m)
```

### Out of memory

```bash
# Reduce model size or input resolution
# Edit inference_server.py, change input_size to (416, 416)
```

---

## Custom Car Recognition

To detect your specific car:

1. Collect 100+ images of your car
2. Fine-tune YOLOv5 on your dataset
3. Export to ONNX
4. Replace model on Jetson
5. Update class names in `inference_server.py`

Guide: https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data

---

## Summary

Your setup:
- **Raspberry Pi**: Camera, Pan-Tilt HAT, Flipper Zero, Web UI
- **Jetson Orin**: AI inference server (object detection)
- **Communication**: HTTP API with base64 image transfer

This architecture is scalable and keeps your Raspberry Pi lightweight!

