"""
Pan-Tilt HAT Controller for HomePi Security System
Controls Pimoroni Pan-Tilt HAT servos for camera positioning and tracking
"""

import json
import time
import threading
import math

# Pan-Tilt HAT will be imported only when available
pantilt_available = False
try:
    import pantilthat
    pantilt_available = True
except ImportError as e:
    print(f"⚠ Pan-Tilt HAT not available: {e}")

# Global state
pantilt_config = {}
pantilt_enabled = False
current_pan = 0
current_tilt = 0
patrol_thread = None
patrol_active = False
tracking_active = False


def load_config():
    """Load Pan-Tilt configuration from config.json"""
    global pantilt_config
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            pantilt_config = config.get('security', {}).get('pantilt', {})
            return pantilt_config
    except Exception as e:
        print(f"Error loading pan-tilt config: {e}")
        return {
            'pan_limits': [-90, 90],
            'tilt_limits': [-45, 45],
            'home_position': [0, 0],
            'patrol_enabled': False,
            'tracking_enabled': True,
            'patrol_speed': 2,
            'tracking_speed': 5
        }


def init_pantilt():
    """Initialize Pan-Tilt HAT"""
    global pantilt_enabled, pantilt_config, current_pan, current_tilt
    
    if not pantilt_available:
        print("Pan-Tilt HAT not available")
        return False
    
    pantilt_config = load_config()
    
    try:
        # Initialize servos
        pantilthat.pan(0)
        pantilthat.tilt(0)
        
        current_pan = 0
        current_tilt = 0
        pantilt_enabled = True
        
        print("✓ Pan-Tilt HAT initialized")
        
        # Move to home position
        home_pos = pantilt_config.get('home_position', [0, 0])
        move_to(home_pos[0], home_pos[1])
        
        return True
        
    except Exception as e:
        print(f"Error initializing Pan-Tilt HAT: {e}")
        pantilt_enabled = False
        return False


def move_to(pan, tilt, speed=5):
    """
    Move to specified pan/tilt position with speed control
    
    Args:
        pan: Pan angle (-90 to +90)
        tilt: Tilt angle (-90 to +90)
        speed: Movement speed (1-10, higher is faster)
    """
    global current_pan, current_tilt, pantilt_enabled
    
    if not pantilt_enabled:
        return False
    
    try:
        # Clamp values to limits
        pan_limits = pantilt_config.get('pan_limits', [-90, 90])
        tilt_limits = pantilt_config.get('tilt_limits', [-45, 45])
        
        pan = max(pan_limits[0], min(pan_limits[1], pan))
        tilt = max(tilt_limits[0], min(tilt_limits[1], tilt))
        
        # Calculate steps for smooth movement
        steps = max(abs(pan - current_pan), abs(tilt - current_tilt))
        steps = int(steps / speed) if steps > speed else 1
        
        if steps > 1:
            # Smooth movement
            for i in range(steps + 1):
                progress = i / steps
                intermediate_pan = current_pan + (pan - current_pan) * progress
                intermediate_tilt = current_tilt + (tilt - current_tilt) * progress
                
                pantilthat.pan(int(intermediate_pan))
                pantilthat.tilt(int(intermediate_tilt))
                time.sleep(0.02)
        else:
            # Direct movement
            pantilthat.pan(int(pan))
            pantilthat.tilt(int(tilt))
        
        current_pan = pan
        current_tilt = tilt
        return True
        
    except Exception as e:
        print(f"Error moving Pan-Tilt: {e}")
        return False


def home():
    """Return to home position"""
    home_pos = pantilt_config.get('home_position', [0, 0])
    print(f"Moving to home position: {home_pos}")
    return move_to(home_pos[0], home_pos[1], speed=3)


def get_position():
    """Get current pan/tilt position"""
    return {'pan': current_pan, 'tilt': current_tilt}


def patrol_loop():
    """Patrol/sweep pattern in background thread"""
    global patrol_active, current_pan, current_tilt
    
    patrol_speed = pantilt_config.get('patrol_speed', 2)
    pan_limits = pantilt_config.get('pan_limits', [-90, 90])
    
    # Patrol pattern: sweep left to right
    while patrol_active:
        if not tracking_active:
            # Sweep right
            for pan in range(int(current_pan), pan_limits[1], patrol_speed):
                if not patrol_active or tracking_active:
                    break
                move_to(pan, 0, speed=1)
                time.sleep(0.1)
            
            # Sweep left
            for pan in range(int(current_pan), pan_limits[0], -patrol_speed):
                if not patrol_active or tracking_active:
                    break
                move_to(pan, 0, speed=1)
                time.sleep(0.1)
        else:
            time.sleep(0.5)


def start_patrol():
    """Start patrol/sweep mode"""
    global patrol_active, patrol_thread
    
    if not pantilt_enabled:
        return False
    
    if patrol_active:
        print("Patrol already active")
        return True
    
    patrol_active = True
    patrol_thread = threading.Thread(target=patrol_loop, daemon=True, name="PatrolThread")
    patrol_thread.start()
    print("✓ Patrol mode started")
    return True


def stop_patrol():
    """Stop patrol mode"""
    global patrol_active
    
    if patrol_active:
        patrol_active = False
        print("Patrol mode stopped")
        return True
    return False


def track_object(bbox, frame_width=1920, frame_height=1080):
    """
    Track detected object by centering camera on its bounding box
    
    Args:
        bbox: Bounding box (x1, y1, x2, y2)
        frame_width: Width of camera frame
        frame_height: Height of camera frame
    """
    global tracking_active, current_pan, current_tilt
    
    if not pantilt_enabled:
        return False
    
    tracking_active = True
    
    try:
        # Calculate object center
        x1, y1, x2, y2 = bbox
        obj_center_x = (x1 + x2) / 2
        obj_center_y = (y1 + y2) / 2
        
        # Calculate frame center
        frame_center_x = frame_width / 2
        frame_center_y = frame_height / 2
        
        # Calculate offset from center (normalized -1 to 1)
        offset_x = (obj_center_x - frame_center_x) / frame_center_x
        offset_y = (obj_center_y - frame_center_y) / frame_center_y
        
        # Deadzone - don't move if object is close to center
        deadzone = 0.1
        if abs(offset_x) < deadzone and abs(offset_y) < deadzone:
            return True
        
        # Calculate pan/tilt adjustments
        # Scale offset to angle adjustment (max 30 degrees per frame)
        tracking_speed = pantilt_config.get('tracking_speed', 5)
        pan_adjustment = offset_x * tracking_speed
        tilt_adjustment = -offset_y * tracking_speed  # Invert Y axis
        
        # Apply adjustments
        new_pan = current_pan + pan_adjustment
        new_tilt = current_tilt + tilt_adjustment
        
        # Move to new position
        return move_to(new_pan, new_tilt, speed=10)
        
    except Exception as e:
        print(f"Error tracking object: {e}")
        return False
    finally:
        tracking_active = False


def stop_tracking():
    """Stop tracking mode"""
    global tracking_active
    tracking_active = False
    return True


def is_enabled():
    """Check if Pan-Tilt is enabled"""
    return pantilt_enabled


def is_patrol_active():
    """Check if patrol mode is active"""
    return patrol_active


def is_tracking_active():
    """Check if tracking is active"""
    return tracking_active


def get_status():
    """Get current Pan-Tilt status"""
    return {
        'enabled': pantilt_enabled,
        'patrol_active': patrol_active,
        'tracking_active': tracking_active,
        'position': {'pan': current_pan, 'tilt': current_tilt},
        'limits': {
            'pan': pantilt_config.get('pan_limits', [-90, 90]),
            'tilt': pantilt_config.get('tilt_limits', [-45, 45])
        }
    }


def cleanup():
    """Stop all operations and cleanup"""
    global patrol_active, tracking_active
    
    stop_patrol()
    stop_tracking()
    
    if pantilt_enabled:
        home()
        print("Pan-Tilt cleanup complete")


if __name__ == "__main__":
    # Test Pan-Tilt functionality
    print("Testing Pan-Tilt HAT...")
    
    if init_pantilt():
        print("Pan-Tilt initialized successfully")
        print(f"Current position: {get_position()}")
        
        # Test movements
        print("\nTesting pan left...")
        move_to(-45, 0)
        time.sleep(1)
        
        print("Testing pan right...")
        move_to(45, 0)
        time.sleep(1)
        
        print("Testing tilt up...")
        move_to(0, -30)
        time.sleep(1)
        
        print("Testing tilt down...")
        move_to(0, 30)
        time.sleep(1)
        
        print("Returning home...")
        home()
        time.sleep(1)
        
        # Test patrol
        print("\nTesting patrol mode for 10 seconds...")
        start_patrol()
        time.sleep(10)
        stop_patrol()
        
        home()
        cleanup()
    else:
        print("Pan-Tilt initialization failed")

