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

# Shared frame buffer for streaming to multiple clients
frame_buffer = None
frame_buffer_lock = threading.Lock()
frame_timestamp = None
capture_thread = None
capture_thread_running = False

# Camera refresh management
refresh_lock = threading.Lock()
last_refresh_time = 0
REFRESH_COOLDOWN_SECONDS = 10  # Reduced from 30 to allow more frequent refreshes
STALE_FRAME_THRESHOLD = 0.5  # Refresh if frames are older than 0.5 seconds


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


def _continuous_capture():
    """Background thread that continuously captures frames for streaming"""
    global frame_buffer, frame_buffer_lock, capture_thread_running, camera, camera_enabled, frame_timestamp
    
    print("📹 Starting continuous capture thread")
    frame_count = 0
    
    # Wait for camera to be ready
    for i in range(50):  # Wait up to 5 seconds
        if camera and camera_enabled:
            break
        time.sleep(0.1)
    
    if not camera or not camera_enabled:
        print("❌ Camera not ready for continuous capture")
        return
    
    print("✓ Continuous capture thread ready")
    
    # Test first capture
    try:
        test_frame = camera.capture_array()
        print(f"✓ Test capture successful: {test_frame.shape}")
    except Exception as e:
        print(f"❌ Test capture failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    while capture_thread_running:
        try:
            if camera and camera_enabled:
                # Capture frame with timeout detection
                capture_start = time.time()
                try:
                    frame = camera.capture_array()
                    capture_duration = time.time() - capture_start
                    
                    # If capture took too long (> 100ms), something is wrong
                    if capture_duration > 0.1:
                        print(f"⚠️ Slow capture detected: {capture_duration:.3f}s (expected <0.1s)")
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            print(f"❌ Multiple slow captures ({consecutive_failures}), refreshing camera...")
                            consecutive_failures = 0
                            # Don't refresh here - let the health check handle it
                            time.sleep(0.1)
                            continue
                    else:
                        consecutive_failures = 0  # Reset on successful fast capture
                    
                    capture_time = time.time()
                    
                    # Update shared buffer
                    with frame_buffer_lock:
                        frame_buffer = frame.copy()
                        global frame_timestamp
                        frame_timestamp = capture_time
                    
                    frame_count += 1
                    if frame_count == 1:
                        print(f"✓ First frame captured: {frame.shape}")
                    if frame_count % 300 == 0:  # Log every 300 frames (~10 seconds)
                        print(f"📹 Captured {frame_count} frames")
                    
                    # Calculate sleep time to maintain 30 FPS, accounting for capture time
                    sleep_time = max(0.001, 0.033 - capture_duration)
                    time.sleep(sleep_time)
                except Exception as capture_error:
                    print(f"❌ Capture error: {capture_error}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        print(f"❌ Multiple capture failures ({consecutive_failures}), camera may need refresh")
                        consecutive_failures = 0
                    time.sleep(0.1)
            else:
                print("⚠ Camera became unavailable")
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Error in continuous capture: {e}")
            import traceback
            traceback.print_exc()
            consecutive_failures += 1
            time.sleep(0.1)
    
    print("📹 Continuous capture thread stopped")


def init_camera():
    """Initialize Picamera2 with configuration"""
    global camera, camera_enabled, camera_config, capture_thread, capture_thread_running, frame_timestamp
    
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
        global frame_timestamp
        frame_timestamp = None
        
        # Start continuous capture thread for streaming
        capture_thread_running = True
        capture_thread = threading.Thread(target=_continuous_capture, daemon=True)
        capture_thread.start()
        
        print("✓ Camera initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing camera: {e}")
        camera_enabled = False
        return False


def get_frame():
    """Get current frame from shared buffer (for detection and single captures)"""
    global frame_buffer, frame_buffer_lock
    
    if not camera_enabled:
        return None
    
    try:
        with frame_buffer_lock:
            if frame_buffer is not None:
                return frame_buffer.copy()
        return None
    except Exception as e:
        print(f"Error getting frame: {e}")
        return None


def get_latest_frame():
    """Get the most recently captured frame (non-blocking) - alias for get_frame()"""
    return get_frame()


def get_frame_for_streaming():
    """Get current frame from shared buffer for streaming (no copy needed)"""
    global frame_buffer, frame_buffer_lock
    
    if not camera_enabled:
        return None
    
    with frame_buffer_lock:
        return frame_buffer


def get_frame_timestamp():
    """Get timestamp of the most recently captured frame"""
    return frame_timestamp


def get_frame_age():
    """Return age of the most recent frame in seconds"""
    if frame_timestamp is None:
        return None
    return max(0.0, time.time() - frame_timestamp)


def refresh_camera(force=False, reason=None):
    """Restart camera capture without restarting entire service"""
    global last_refresh_time, frame_buffer, frame_timestamp
    message = f"Reason: {reason}" if reason else ""
    with refresh_lock:
        now = time.time()
        # Allow refresh if forced, or if cooldown has passed, or if it's been > 5 seconds (emergency)
        emergency = last_refresh_time and (now - last_refresh_time) > 5
        if not force and not emergency and last_refresh_time and now - last_refresh_time < REFRESH_COOLDOWN_SECONDS:
            elapsed = now - last_refresh_time
            print(f"🔁 Camera refresh skipped (last refresh {elapsed:.1f}s ago). {message}")
            return False
        
        print(f"🔄 Refreshing camera stream... {message}")
        try:
            # Stop camera completely
            stop_camera()
            
            # Additional cleanup - ensure buffers are cleared
            with frame_buffer_lock:
                frame_buffer = None
                frame_timestamp = None
            
            # Wait longer to ensure camera hardware is reset
            time.sleep(2)
            
            # Reinitialize camera
            success = init_camera()
            if success:
                last_refresh_time = time.time()
                print("✓ Camera stream refreshed")
            else:
                print("❌ Camera refresh failed during reinitialization")
            return success
        except Exception as e:
            print(f"❌ Error refreshing camera: {e}")
            import traceback
            traceback.print_exc()
            return False


def ensure_camera_fresh(max_stale_seconds=None, reason=None, force=False):
    """Ensure camera frames are fresh, refreshing camera if frames are stale"""
    if not camera_enabled:
        return False
    if max_stale_seconds is None:
        max_stale_seconds = STALE_FRAME_THRESHOLD
    
    age = get_frame_age()
    if age is None:
        # No frames captured yet - might be stuck
        print("⚠️ No frame timestamp available, camera may be stuck")
        return refresh_camera(force=force, reason=reason or "no frames detected")
    
    if age > max_stale_seconds:
        refresh_reason = reason or f"frames stale ({age:.2f}s old, threshold {max_stale_seconds}s)"
        return refresh_camera(force=force, reason=refresh_reason)
    return False


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
    global camera, camera_enabled, recording, capture_thread_running, capture_thread, frame_timestamp, frame_buffer
    
    # Stop capture thread
    if capture_thread_running:
        capture_thread_running = False
        if capture_thread:
            capture_thread.join(timeout=2)
    
    # Clear frame buffer
    with frame_buffer_lock:
        frame_buffer = None
        frame_timestamp = None
    
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
        finally:
            camera = None


def get_camera_status():
    """Get current camera status"""
    age = get_frame_age()
    timestamp = frame_timestamp
    last_frame_iso = datetime.fromtimestamp(timestamp).isoformat() if timestamp else None
    return {
        'enabled': camera_enabled,
        'recording': recording,
        'recording_file': current_recording_file,
        'resolution': camera_config.get('resolution', [1920, 1080]),
        'fps': camera_config.get('fps', 30),
        'frame_age': age,
        'last_frame_time': last_frame_iso
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

