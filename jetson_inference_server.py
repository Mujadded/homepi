"""
HomePi AI Inference Server for Nvidia Jetson Orin
Provides REST API for object detection using PyTorch YOLOv5
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

# Try to import torch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠ PyTorch not available")

# COCO class names (80 classes)
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
    'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush'
]

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global model state
model = None
model_loaded = False
device = 'cpu'


def load_model():
    """Load YOLOv5 model from torch hub"""
    global model, model_loaded, device
    
    if not TORCH_AVAILABLE:
        logger.error("PyTorch not available, cannot load model")
        return False
    
    try:
        logger.info("Loading YOLOv5s model from torch hub...")
        
        # Detect device
        if torch.cuda.is_available():
            device = 'cuda'
            logger.info(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            device = 'cpu'
            logger.warning("⚠ CUDA not available, using CPU")
        
        # Load YOLOv5 from torch hub
        # This will download the model on first run
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        model.to(device)
        model.eval()
        
        # Configure model
        model.conf = 0.6  # Default confidence threshold
        model.iou = 0.45  # NMS IOU threshold
        
        model_loaded = True
        logger.info("✓ YOLOv5s model loaded successfully")
        logger.info(f"  Device: {device}")
        logger.info(f"  Classes: {len(COCO_CLASSES)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        model_loaded = False
        return False


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


def run_inference(image, threshold=0.6, classes_filter=None):
    """
    Run inference on image
    
    Args:
        image: numpy array (RGB format)
        threshold: confidence threshold
        classes_filter: list of class names to keep (None = all)
    
    Returns:
        list of detections
    """
    global model, model_loaded
    
    if not model_loaded or model is None:
        logger.error("Model not loaded")
        return []
    
    try:
        # Set confidence threshold
        model.conf = threshold
        
        # Run inference
        start_time = time.time()
        
        with torch.no_grad():
            results = model(image)
        
        inference_time = (time.time() - start_time) * 1000
        
        # Process results
        detections = []
        
        # Get predictions (xyxy format)
        pred = results.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2, conf, class]
        
        # Get image dimensions
        img_height, img_width = image.shape[:2]
        
        for detection in pred:
            x1, y1, x2, y2, conf, cls = detection
            
            class_id = int(cls)
            class_name = COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else f'class_{class_id}'
            
            # Filter by class if specified
            if classes_filter and class_name not in classes_filter:
                continue
            
            # Normalize bbox to [0, 1]
            x1_norm = x1 / img_width
            y1_norm = y1 / img_height
            x2_norm = x2 / img_width
            y2_norm = y2 / img_height
            
            detections.append({
                'class_id': class_id,
                'class_name': class_name,
                'confidence': float(conf),
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'bbox_norm': [float(x1_norm), float(y1_norm), float(x2_norm), float(y2_norm)]
            })
        
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
        'backend': 'pytorch',
        'model': 'YOLOv5s',
        'device': device,
        'model_loaded': model_loaded,
        'cuda_available': torch.cuda.is_available() if TORCH_AVAILABLE else False
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
        
        # Get parameters
        threshold = data.get('threshold', 0.6)
        classes_filter = data.get('classes', None)
        
        # Run inference
        detections = run_inference(image, threshold, classes_filter)
        
        return jsonify({
            'success': True,
            'detections': detections,
            'count': len(detections)
        })
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("  HomePi AI Inference Server")
    print("=" * 50)
    print()
    
    # Check PyTorch
    if not TORCH_AVAILABLE:
        print("ERROR: PyTorch not installed")
        print("Install with: pip3 install torch torchvision")
        exit(1)
    
    # Check CUDA
    if torch.cuda.is_available():
        print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠ CUDA not available, using CPU (slower)")
    
    print()
    
    # Load model on startup
    if load_model():
        print("✓ Model loaded successfully")
        print()
        print("Starting Flask server on http://0.0.0.0:5001")
        print("Press Ctrl+C to stop")
        print()
        
        # Start Flask server
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,
            threaded=True
        )
    else:
        print("ERROR: Failed to load model")
        exit(1)

