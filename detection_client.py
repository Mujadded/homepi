"""
Detection Client - Wrapper to call Coral TPU detection service in Docker
Used by security_manager to run object detection
"""

import requests
import numpy as np
import base64
import io
from PIL import Image

# Detection service URL (Docker container)
DETECTION_SERVICE_URL = "http://localhost:5001"


def is_service_available():
    """Check if detection service is running"""
    try:
        response = requests.get(f"{DETECTION_SERVICE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def detect_objects(frame, threshold=0.6, classes_of_interest=None):
    """
    Run object detection on frame via Docker service
    
    Args:
        frame: numpy array (RGB format)
        threshold: confidence threshold
        classes_of_interest: list of class names to filter
    
    Returns:
        List of detections (same format as object_detector.py)
    """
    try:
        # Convert frame to base64
        image = Image.fromarray(frame)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Prepare request
        payload = {
            'image': image_b64,
            'threshold': threshold
        }
        
        if classes_of_interest:
            payload['classes'] = classes_of_interest
        
        # Call detection service
        response = requests.post(
            f"{DETECTION_SERVICE_URL}/detect",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('detections', [])
        else:
            print(f"Detection service error: {response.status_code}")
            return []
            
    except requests.exceptions.Timeout:
        print("Detection service timeout")
        return []
    except Exception as e:
        print(f"Detection client error: {e}")
        return []


def detect_objects_fast(frame, threshold=0.6):
    """
    Fast detection using raw bytes (no base64 encoding)
    Better for video streams
    """
    try:
        height, width = frame.shape[:2]
        
        # Send raw bytes
        response = requests.post(
            f"{DETECTION_SERVICE_URL}/detect_stream",
            data=frame.tobytes(),
            params={
                'width': width,
                'height': height,
                'threshold': threshold
            },
            headers={'Content-Type': 'application/octet-stream'},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('detections', [])
        else:
            return []
            
    except Exception as e:
        print(f"Fast detection error: {e}")
        return []


def get_detector_status():
    """Get detection service status"""
    try:
        response = requests.get(f"{DETECTION_SERVICE_URL}/status", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {'enabled': False}
    except:
        return {'enabled': False}


def filter_detections(detections, classes_of_interest):
    """Filter detections by class names (local filtering)"""
    return [
        det for det in detections
        if det['class_name'] in classes_of_interest
    ]


# For compatibility with object_detector.py interface
def init_detector(model_path=None):
    """Initialize detector (just check if service is available)"""
    if is_service_available():
        print("✓ Coral TPU detection service is available (Docker)")
        return True
    else:
        print("⚠ Coral TPU detection service not available")
        print("  Start with: docker-compose -f docker-compose.coral.yml up -d")
        return False


def is_enabled():
    """Check if detector is enabled"""
    return is_service_available()


if __name__ == "__main__":
    # Test detection client
    print("Testing Coral TPU Detection Client...")
    
    if init_detector():
        print("✓ Detection service is running")
        print(f"Status: {get_detector_status()}")
        
        # Test with random image
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        print("\nTesting detection...")
        detections = detect_objects(test_frame, threshold=0.5)
        print(f"Found {len(detections)} objects")
        
        for det in detections[:5]:
            print(f"  - {det['class_name']}: {det['confidence']:.2f}")
    else:
        print("✗ Detection service not running")
        print("\nTo start the service:")
        print("  docker-compose -f docker-compose.coral.yml up -d")

