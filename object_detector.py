"""
Object Detector Client for HomePi Security System
Sends frames to remote AI service (Nvidia Jetson Orin) for inference
"""

import json
import time
import os
import base64
import logging
import numpy as np
import requests
from io import BytesIO

# OpenCV for image encoding
cv2_available = False
try:
    import cv2
    cv2_available = True
except ImportError:
    print("⚠ OpenCV not available")

# PIL as fallback
PIL_available = False
try:
    from PIL import Image
    PIL_available = True
except ImportError:
    print("⚠ PIL not available")

logger = logging.getLogger(__name__)

# Global detector state
detector_enabled = False
detector_config = {}
remote_url = None
session = None


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
            'remote_url': 'http://jetson.local:5001',
            'confidence_threshold': 0.6,
            'detection_timeout': 5,
            'classes_of_interest': ['car', 'person', 'motorcycle', 'bicycle', 'truck']
        }


def init_detector(url=None):
    """
    Initialize connection to remote AI service
    
    Args:
        url: Remote inference server URL (e.g., 'http://jetson.local:5001')
    
    Returns:
        bool: True if initialized successfully
    """
    global detector_enabled, detector_config, remote_url, session
    
    detector_config = load_config()
    
    if not url:
        url = detector_config.get('remote_url', 'http://jetson.local:5001')
    
    remote_url = url.rstrip('/')
    
    try:
        # Create persistent session for better performance
        session = requests.Session()
        session.headers.update({'Content-Type': 'application/json'})
        
        # Test connection to remote service
        print(f"Connecting to remote AI service: {remote_url}")
        response = session.get(f"{remote_url}/health", timeout=5)
        
        if response.status_code == 200:
            info = response.json()
            print(f"✓ Remote AI service connected")
            print(f"  Service: {info.get('service', 'Unknown')}")
            print(f"  Model: {info.get('model', 'Unknown')}")
            print(f"  Device: {info.get('device', 'Unknown')}")
            detector_enabled = True
            return True
        else:
            print(f"Remote service returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"⚠ Could not connect to remote AI service at {remote_url}")
        print("  Make sure the Jetson Orin inference server is running")
        detector_enabled = False
        return False
    except Exception as e:
        print(f"Error initializing remote detector: {e}")
        detector_enabled = False
        return False


def encode_frame(frame, quality=85):
    """
    Encode frame to JPEG and base64 for transmission
    
    Args:
        frame: numpy array (RGB format)
        quality: JPEG quality (1-100)
    
    Returns:
        str: Base64 encoded JPEG string
    """
    if cv2_available:
        try:
            # Convert RGB to BGR for OpenCV
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Encode to JPEG
            success, buffer = cv2.imencode('.jpg', bgr_frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if success:
                # Encode to base64
                jpg_bytes = buffer.tobytes()
                b64_str = base64.b64encode(jpg_bytes).decode('utf-8')
                return b64_str
        except Exception as e:
            print(f"Error encoding frame with OpenCV: {e}")
    
    # Fallback to PIL
    if PIL_available:
        try:
            # Convert numpy to PIL Image
            pil_img = Image.fromarray(frame.astype('uint8'), 'RGB')
            
            # Encode to JPEG
            buffer = BytesIO()
            pil_img.save(buffer, format='JPEG', quality=quality)
            jpg_bytes = buffer.getvalue()
            
            # Encode to base64
            b64_str = base64.b64encode(jpg_bytes).decode('utf-8')
            return b64_str
        except Exception as e:
            print(f"Error encoding frame with PIL: {e}")
    
    return None


def detect_objects(frame, threshold=None):
    """
    Run object detection on frame using remote AI service
    
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
    global detector_enabled, detector_config, remote_url, session
    
    if not detector_enabled or not session:
        return []
    
    if threshold is None:
        threshold = detector_config.get('confidence_threshold', 0.6)
    
    try:
        # Encode frame
        b64_frame = encode_frame(frame, quality=85)
        if not b64_frame:
            print("Failed to encode frame")
            return []
        
        # Prepare request
        payload = {
            'image': b64_frame,
            'threshold': threshold,
            'classes': detector_config.get('classes_of_interest', [])
        }
        
        # Send to remote service
        timeout = detector_config.get('detection_timeout', 5)
        start_time = time.time()
        
        response = session.post(
            f"{remote_url}/detect",
            json=payload,
            timeout=timeout
        )
        
        inference_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            detections = result.get('detections', [])
            
            # Convert normalized bbox to pixel coordinates if needed
            frame_height, frame_width = frame.shape[:2]
            for det in detections:
                if 'bbox_norm' in det:
                    x1_norm, y1_norm, x2_norm, y2_norm = det['bbox_norm']
                    det['bbox'] = (
                        int(x1_norm * frame_width),
                        int(y1_norm * frame_height),
                        int(x2_norm * frame_width),
                        int(y2_norm * frame_height)
                    )
            
            # Debug logging
            if detections:
                logger.debug(f"Inference: {inference_time:.1f}ms, Detections: {len(detections)}")
            
            return detections
        else:
            print(f"Remote detection failed: {response.status_code}")
            return []
            
    except requests.exceptions.Timeout:
        print(f"Detection request timed out after {timeout}s")
        return []
    except requests.exceptions.ConnectionError:
        print("Lost connection to remote AI service")
        detector_enabled = False
        return []
    except Exception as e:
        print(f"Error during remote detection: {e}")
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
        'remote_url': remote_url,
        'threshold': detector_config.get('confidence_threshold', 0.6),
        'classes': detector_config.get('classes_of_interest', []),
        'timeout': detector_config.get('detection_timeout', 5)
    }


def cleanup():
    """Close session and cleanup"""
    global session, detector_enabled
    if session:
        session.close()
    detector_enabled = False


if __name__ == "__main__":
    # Test detector
    print("Testing remote object detector...")
    print("\nConfiguration:")
    print("  1. Make sure Jetson Orin inference server is running")
    print("  2. Update 'remote_url' in config.json")
    print("  3. Ensure network connectivity\n")
    
    # Allow user to input URL
    url = input("Enter Jetson Orin URL (or press Enter for config.json default): ").strip()
    if not url:
        url = None
    
    if init_detector(url):
        print("\nDetector initialized successfully")
        print(f"Status: {get_status()}")
        
        # Create a test image
        print("\nGenerating test image...")
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        print("Sending test detection request...")
        detections = detect_objects(test_frame)
        print(f"Detections: {len(detections)}")
        
        for det in detections:
            print(f"  - {det['class_name']}: {det['confidence']:.2f}")
        
        cleanup()
    else:
        print("\nDetector initialization failed")
        print("Make sure:")
        print("  1. Jetson Orin inference server is running")
        print("  2. Network connection to Jetson is working")
        print("  3. Remote URL is correct in config.json")
