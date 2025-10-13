"""
Camera Manager for HomePi Security System
Handles Picamera2 operations including frame capture, video recording, and snapshots
"""

import os
import threading
import time
import json
from datetime import datetime
from pathlib import Path

# Camera will be imported only when available
camera_available = False
try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import FileOutput
    import numpy as np
    camera_available = True
except ImportError as e:
    print(f"⚠ Camera modules not available: {e}")

# Global camera instance
camera = None
camera_config = {}
camera_enabled = False
recording = False
current_recording_file = None
frame_lock = threading.Lock()
latest_frame = None


def load_config():
    """Load camera configuration from config.json"""
    global camera_config
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            camera_config = config.get('security', {}).get('camera', {})
            return camera_config
    except Exception as e:
        print(f"Error loading camera config: {e}")
        return {
            'resolution': [1920, 1080],
            'fps': 30,
            'rotation': 0
        }


def init_camera():
    """Initialize Picamera2 with configuration"""
    global camera, camera_enabled, camera_config
    
    if not camera_available:
        print("Camera modules not available")
        return False
    
    camera_config = load_config()
    
    try:
        camera = Picamera2()
        
        # Configure camera
        config = camera.create_preview_configuration(
            main={"size": tuple(camera_config.get('resolution', [1920, 1080])), "format": "RGB888"},
            lores={"size": (640, 480), "format": "YUV420"},
            display="lores"
        )
        
        camera.configure(config)
        
        # Set rotation if specified
        rotation = camera_config.get('rotation', 0)
        if rotation:
            camera.transform = {'rotation': rotation}
        
        camera.start()
        time.sleep(2)  # Allow camera to warm up
        
        camera_enabled = True
        print("✓ Camera initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing camera: {e}")
        camera_enabled = False
        return False


def get_frame():
    """Get current frame from camera for detection"""
    global latest_frame, frame_lock
    
    if not camera or not camera_enabled:
        return None
    
    try:
        with frame_lock:
            frame = camera.capture_array()
            latest_frame = frame.copy()
            return latest_frame
    except Exception as e:
        print(f"Error capturing frame: {e}")
        return None


def get_latest_frame():
    """Get the most recently captured frame (non-blocking)"""
    global latest_frame, frame_lock
    
    with frame_lock:
        if latest_frame is not None:
            return latest_frame.copy()
    return None


def get_single_frame_encoded():
    """
    Get single frame as base64-encoded JPEG for Jetson processing
    Returns base64 string or None
    """
    import base64
    
    frame = get_frame()
    if frame is None:
        return None
    
    try:
        import cv2
        # Convert RGB to BGR for OpenCV
        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Encode frame to JPEG
        _, jpeg = cv2.imencode('.jpg', bgr_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # Convert to base64
        encoded = base64.b64encode(jpeg.tobytes()).decode('utf-8')
        return encoded
        
    except Exception as e:
        print(f"Error encoding frame: {e}")
        return None


def start_recording(filename=None):
    """Start recording video to file"""
    global recording, current_recording_file, camera
    
    if not camera or not camera_enabled:
        print("Camera not available for recording")
        return False
    
    if recording:
        print("Already recording")
        return False
    
    try:
        # Create recordings directory
        rec_dir = camera_config.get('clips_dir', 'recordings')
        os.makedirs(rec_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.h264"
        
        filepath = os.path.join(rec_dir, filename)
        current_recording_file = filepath
        
        # Start recording
        encoder = H264Encoder(bitrate=10000000)
        output = FileOutput(filepath)
        camera.start_recording(encoder, output)
        
        recording = True
        print(f"✓ Recording started: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error starting recording: {e}")
        recording = False
        return False


def stop_recording():
    """Stop current video recording"""
    global recording, current_recording_file, camera
    
    if not recording:
        print("Not currently recording")
        return None
    
    try:
        camera.stop_recording()
        filepath = current_recording_file
        recording = False
        current_recording_file = None
        print(f"✓ Recording stopped: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error stopping recording: {e}")
        return None


def take_snapshot(filename=None, directory='detections'):
    """Capture and save a single frame as image"""
    global camera
    
    if not camera or not camera_enabled:
        print("Camera not available for snapshot")
        return None
    
    try:
        # Create directory
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.jpg"
        
        filepath = os.path.join(directory, filename)
        
        # Capture and save
        frame = camera.capture_array()
        
        # Convert RGB to BGR for OpenCV
        try:
            import cv2
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filepath, frame_bgr)
        except:
            # Fallback to PIL if OpenCV not available
            from PIL import Image
            img = Image.fromarray(frame)
            img.save(filepath)
        
        print(f"✓ Snapshot saved: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error taking snapshot: {e}")
        return None


def is_recording():
    """Check if currently recording"""
    return recording


def is_enabled():
    """Check if camera is enabled and ready"""
    return camera_enabled


def stop_camera():
    """Stop camera and cleanup"""
    global camera, camera_enabled, recording
    
    if recording:
        stop_recording()
    
    if camera:
        try:
            camera.stop()
            camera.close()
            camera_enabled = False
            print("Camera stopped")
        except Exception as e:
            print(f"Error stopping camera: {e}")


def get_camera_status():
    """Get current camera status"""
    return {
        'enabled': camera_enabled,
        'recording': recording,
        'recording_file': current_recording_file,
        'resolution': camera_config.get('resolution', [1920, 1080]),
        'fps': camera_config.get('fps', 30)
    }


if __name__ == "__main__":
    # Test camera functionality
    print("Testing camera manager...")
    
    if init_camera():
        print("Camera initialized successfully")
        
        # Test frame capture
        frame = get_frame()
        if frame is not None:
            print(f"Captured frame: {frame.shape}")
        
        # Test snapshot
        snapshot_path = take_snapshot()
        if snapshot_path:
            print(f"Snapshot saved: {snapshot_path}")
        
        # Test recording
        print("Starting 5-second recording test...")
        rec_path = start_recording()
        if rec_path:
            time.sleep(5)
            final_path = stop_recording()
            print(f"Recording saved: {final_path}")
        
        stop_camera()
    else:
        print("Camera initialization failed")

