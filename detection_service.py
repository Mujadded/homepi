"""
Detection Service API for Coral TPU
Runs in Docker container with Python 3.11
Main app calls this via HTTP to run object detection
"""

from flask import Flask, request, jsonify
import object_detector
import numpy as np
import base64
import io
from PIL import Image

app = Flask(__name__)

# Initialize detector on startup
print("Initializing Coral TPU detector...")
if not object_detector.init_detector():
    print("Warning: Detector initialization failed, will retry on first request")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'detector_enabled': object_detector.is_enabled(),
        'detector_info': object_detector.get_status()
    })

@app.route('/detect', methods=['POST'])
def detect():
    """
    Run object detection on uploaded image
    
    Request body:
    {
        "image": "base64_encoded_image",
        "threshold": 0.6,  // optional
        "classes": ["car", "person"]  // optional
    }
    
    Response:
    {
        "detections": [
            {
                "class_id": 2,
                "class_name": "car",
                "confidence": 0.87,
                "bbox": [x1, y1, x2, y2],
                "bbox_norm": [xmin, ymin, xmax, ymax]
            }
        ],
        "count": 1,
        "inference_time_ms": 15.3
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        image_data = base64.b64decode(data['image'])
        image = Image.open(io.BytesIO(image_data))
        frame = np.array(image)
        
        # Get optional parameters
        threshold = data.get('threshold', 0.6)
        classes_of_interest = data.get('classes', None)
        
        # Run detection
        detections = object_detector.detect_objects(frame, threshold=threshold)
        
        # Filter by classes if specified
        if classes_of_interest:
            detections = object_detector.filter_detections(detections, classes_of_interest)
        
        return jsonify({
            'detections': detections,
            'count': len(detections),
            'image_size': frame.shape[:2]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/detect_stream', methods=['POST'])
def detect_stream():
    """
    Run detection on raw image bytes (faster for video streams)
    Expects raw RGB numpy array as bytes
    """
    try:
        # Get image dimensions from query params
        width = int(request.args.get('width', 1920))
        height = int(request.args.get('height', 1080))
        threshold = float(request.args.get('threshold', 0.6))
        
        # Read raw bytes
        image_bytes = request.data
        
        # Reconstruct numpy array
        frame = np.frombuffer(image_bytes, dtype=np.uint8).reshape((height, width, 3))
        
        # Run detection
        detections = object_detector.detect_objects(frame, threshold=threshold)
        
        return jsonify({
            'detections': detections,
            'count': len(detections)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/status', methods=['GET'])
def status():
    """Get detector status"""
    return jsonify(object_detector.get_status())


if __name__ == '__main__':
    print("Starting Coral TPU Detection Service...")
    print("Listening on http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)

