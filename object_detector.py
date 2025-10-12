"""
Object Detector for HomePi Security System
Uses Coral TPU EdgeTPU for real-time object detection
"""

import json
import time
import os
import numpy as np

# Coral TPU modules will be imported only when available
coral_available = False
try:
    from pycoral.adapters import common
    from pycoral.adapters import detect
    from pycoral.utils.edgetpu import make_interpreter
    coral_available = True
except ImportError as e:
    print(f"⚠ Coral TPU modules not available: {e}")

# CV2 for preprocessing
cv2_available = False
try:
    import cv2
    cv2_available = True
except ImportError:
    print("⚠ OpenCV not available")

# Global detector state
detector = None
detector_config = {}
detector_enabled = False
labels = {}


# COCO dataset labels (subset for common objects)
COCO_LABELS = {
    0: 'person',
    1: 'bicycle',
    2: 'car',
    3: 'motorcycle',
    4: 'airplane',
    5: 'bus',
    6: 'train',
    7: 'truck',
    8: 'boat',
    16: 'dog',
    17: 'cat',
    18: 'bird'
}


def load_config():
    """Load detection configuration from config.json"""
    global detector_config
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            detector_config = config.get('security', {}).get('detection', {})
            return detector_config
    except Exception as e:
        print(f"Error loading detector config: {e}")
        return {
            'model_path': 'models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite',
            'confidence_threshold': 0.6,
            'detection_interval': 0.1,
            'classes_of_interest': ['car', 'person', 'motorcycle', 'bicycle', 'truck']
        }


def load_labels(label_path=None):
    """Load label file for model"""
    global labels
    
    if label_path and os.path.exists(label_path):
        try:
            with open(label_path, 'r') as f:
                labels = {i: line.strip() for i, line in enumerate(f.readlines())}
            return labels
        except Exception as e:
            print(f"Error loading labels: {e}")
    
    # Use built-in COCO labels
    labels = COCO_LABELS
    return labels


def init_detector(model_path=None):
    """Initialize Coral TPU detector with TFLite model"""
    global detector, detector_enabled, detector_config, labels
    
    if not coral_available:
        print("Coral TPU modules not available")
        return False
    
    detector_config = load_config()
    
    if not model_path:
        model_path = detector_config.get('model_path', 'models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite')
    
    try:
        # Check if model exists
        if not os.path.exists(model_path):
            print(f"Model not found: {model_path}")
            print("Please download the model or run setup script")
            return False
        
        # Load interpreter on Edge TPU
        print(f"Loading model: {model_path}")
        detector = make_interpreter(model_path)
        detector.allocate_tensors()
        
        # Load labels
        label_path = model_path.replace('.tflite', '_labels.txt')
        load_labels(label_path if os.path.exists(label_path) else None)
        
        detector_enabled = True
        print(f"✓ Coral TPU detector initialized")
        print(f"  Model: {os.path.basename(model_path)}")
        print(f"  Labels: {len(labels)} classes")
        
        return True
        
    except Exception as e:
        print(f"Error initializing detector: {e}")
        detector_enabled = False
        return False


def preprocess_frame(frame, target_size=(300, 300)):
    """Preprocess frame for model input"""
    if not cv2_available:
        return None
    
    try:
        # Resize to model input size
        resized = cv2.resize(frame, target_size)
        
        # Convert RGB to BGR if needed (frame from camera is RGB)
        # Model expects RGB, so no conversion needed
        
        return resized
        
    except Exception as e:
        print(f"Error preprocessing frame: {e}")
        return None


def detect_objects(frame, threshold=None):
    """
    Run object detection on frame
    
    Args:
        frame: Input image (numpy array, RGB format)
        threshold: Confidence threshold (0.0-1.0)
    
    Returns:
        List of detections: [
            {
                'class_id': int,
                'class_name': str,
                'confidence': float,
                'bbox': (x1, y1, x2, y2)
            },
            ...
        ]
    """
    global detector, detector_enabled, detector_config
    
    if not detector or not detector_enabled:
        return []
    
    if threshold is None:
        threshold = detector_config.get('confidence_threshold', 0.6)
    
    try:
        # Get input details
        input_details = detector.get_input_details()
        input_shape = input_details[0]['shape']
        
        # Expected input shape: [1, height, width, 3]
        target_height = input_shape[1]
        target_width = input_shape[2]
        
        # Preprocess frame
        processed = preprocess_frame(frame, (target_width, target_height))
        if processed is None:
            return []
        
        # Set input tensor
        common.set_input(detector, processed)
        
        # Run inference
        start_time = time.time()
        detector.invoke()
        inference_time = (time.time() - start_time) * 1000
        
        # Get detections
        detections = detect.get_objects(detector, threshold)
        
        # Process results
        results = []
        frame_height, frame_width = frame.shape[:2]
        
        for detection in detections:
            class_id = detection.id
            class_name = labels.get(class_id, f"class_{class_id}")
            confidence = detection.score
            
            # Get bounding box (normalized 0-1)
            bbox_norm = detection.bbox
            
            # Convert to pixel coordinates
            x1 = int(bbox_norm.xmin * frame_width)
            y1 = int(bbox_norm.ymin * frame_height)
            x2 = int(bbox_norm.xmax * frame_width)
            y2 = int(bbox_norm.ymax * frame_height)
            
            results.append({
                'class_id': class_id,
                'class_name': class_name,
                'confidence': float(confidence),
                'bbox': (x1, y1, x2, y2),
                'bbox_norm': (bbox_norm.xmin, bbox_norm.ymin, bbox_norm.xmax, bbox_norm.ymax)
            })
        
        # Print inference stats (debug)
        # print(f"Inference: {inference_time:.1f}ms, Detections: {len(results)}")
        
        return results
        
    except Exception as e:
        print(f"Error during detection: {e}")
        return []


def filter_detections(detections, classes_of_interest=None):
    """
    Filter detections by class names
    
    Args:
        detections: List of detection dicts
        classes_of_interest: List of class names to keep
    
    Returns:
        Filtered list of detections
    """
    if not classes_of_interest:
        classes_of_interest = detector_config.get('classes_of_interest', ['car', 'person'])
    
    filtered = [
        det for det in detections
        if det['class_name'] in classes_of_interest
    ]
    
    return filtered


def draw_detections(frame, detections):
    """Draw bounding boxes and labels on frame"""
    if not cv2_available:
        return frame
    
    # Make a copy to avoid modifying original
    annotated = frame.copy()
    
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        class_name = det['class_name']
        confidence = det['confidence']
        
        # Choose color based on class
        if 'car' in class_name or 'truck' in class_name:
            color = (0, 255, 0)  # Green for vehicles
        elif 'person' in class_name:
            color = (0, 0, 255)  # Red for people
        else:
            color = (255, 0, 0)  # Blue for others
        
        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        label = f"{class_name} {confidence:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        cv2.rectangle(annotated, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(annotated, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    return annotated


def is_enabled():
    """Check if detector is enabled"""
    return detector_enabled


def get_status():
    """Get detector status"""
    return {
        'enabled': detector_enabled,
        'model': os.path.basename(detector_config.get('model_path', '')),
        'threshold': detector_config.get('confidence_threshold', 0.6),
        'classes': detector_config.get('classes_of_interest', []),
        'labels_loaded': len(labels)
    }


if __name__ == "__main__":
    # Test detector
    print("Testing object detector...")
    
    if init_detector():
        print("Detector initialized successfully")
        print(f"Status: {get_status()}")
        
        # Create a test image
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        print("\nRunning test detection...")
        detections = detect_objects(test_frame)
        print(f"Detections: {len(detections)}")
        
        for det in detections:
            print(f"  - {det['class_name']}: {det['confidence']:.2f}")
    else:
        print("Detector initialization failed")
        print("Make sure:")
        print("  1. Coral TPU is connected via USB")
        print("  2. Model file exists in models/ directory")
        print("  3. libedgetpu is installed")

