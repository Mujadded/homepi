"""
Pan-Tilt Patrol Controller for HomePi Security System
Manages customizable patrol patterns with position recording and auto-resume after interrupts
"""

import json
import time
import threading
from datetime import datetime

# Import pantilt controller
import pantilt_controller

# Global patrol state
patrol_positions = []  # List of {id, pan, tilt, dwell_time, created_at}
patrol_active = False
patrol_thread = None
patrol_speed = 5  # Default speed (1-10)
current_position_index = 0
patrol_direction = 1  # 1 = forward, -1 = backward (for back-and-forth)
interrupted = False
interrupt_resume_timer = None
interrupt_resume_delay = 5  # seconds to wait before resuming after interrupt

# File to persist patrol positions
POSITIONS_FILE = "patrol_positions.json"


def load_positions():
    """Load patrol positions from file"""
    global patrol_positions
    
    try:
        with open(POSITIONS_FILE, 'r') as f:
            patrol_positions = json.load(f)
            print(f"✓ Loaded {len(patrol_positions)} patrol positions")
            return True
    except FileNotFoundError:
        patrol_positions = []
        print("No saved patrol positions found")
        return False
    except Exception as e:
        print(f"Error loading patrol positions: {e}")
        patrol_positions = []
        return False


def save_positions():
    """Save patrol positions to file"""
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(patrol_positions, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving patrol positions: {e}")
        return False


def add_position(pan, tilt, dwell_time=10):
    """
    Add a new patrol position
    
    Args:
        pan: Pan angle
        tilt: Tilt angle
        dwell_time: How long to stay at this position (seconds)
    
    Returns:
        dict: The created position object
    """
    global patrol_positions
    
    # Generate unique ID
    position_id = len(patrol_positions) + 1
    if patrol_positions:
        position_id = max(p['id'] for p in patrol_positions) + 1
    
    position = {
        'id': position_id,
        'pan': pan,
        'tilt': tilt,
        'dwell_time': dwell_time,
        'created_at': datetime.now().isoformat()
    }
    
    patrol_positions.append(position)
    save_positions()
    
    print(f"✓ Added patrol position {position_id}: pan={pan}, tilt={tilt}, dwell={dwell_time}s")
    return position


def delete_position(position_id):
    """Delete a patrol position by ID"""
    global patrol_positions
    
    patrol_positions = [p for p in patrol_positions if p['id'] != position_id]
    save_positions()
    print(f"✓ Deleted patrol position {position_id}")
    return True


def update_position(position_id, dwell_time):
    """Update the dwell time for a position"""
    global patrol_positions
    
    for pos in patrol_positions:
        if pos['id'] == position_id:
            pos['dwell_time'] = dwell_time
            save_positions()
            print(f"✓ Updated patrol position {position_id}: dwell={dwell_time}s")
            return True
    
    return False


def get_positions():
    """Get all patrol positions"""
    return patrol_positions


def clear_all_positions():
    """Clear all patrol positions"""
    global patrol_positions
    patrol_positions = []
    save_positions()
    print("✓ Cleared all patrol positions")
    return True


def patrol_loop():
    """
    Main patrol loop - moves through positions in back-and-forth pattern
    Pattern: 1→2→3→2→1→2→3→2→1...
    """
    global patrol_active, current_position_index, patrol_direction, interrupted
    
    print("🚶 Patrol loop started")
    
    while patrol_active:
        # Wait if interrupted
        if interrupted:
            time.sleep(0.5)
            continue
        
        # Check if we have positions
        if not patrol_positions:
            print("⚠ No patrol positions defined, stopping patrol")
            patrol_active = False
            break
        
        # Get current position
        pos = patrol_positions[current_position_index]
        
        # Move to position
        print(f"📍 Moving to position {pos['id']}: pan={pos['pan']}, tilt={pos['tilt']}")
        pantilt_controller.move_to(pos['pan'], pos['tilt'], speed=patrol_speed)
        
        # Dwell at position
        dwell_time = pos['dwell_time']
        print(f"⏱ Dwelling for {dwell_time}s")
        
        # Sleep in small increments to allow for quick stop
        for _ in range(int(dwell_time * 10)):
            if not patrol_active or interrupted:
                break
            time.sleep(0.1)
        
        # Calculate next position (back-and-forth pattern)
        next_index = current_position_index + patrol_direction
        
        # Check if we need to reverse direction
        if next_index >= len(patrol_positions):
            # Reached the end, go backwards
            patrol_direction = -1
            next_index = len(patrol_positions) - 2
            if next_index < 0:
                next_index = 0
        elif next_index < 0:
            # Reached the beginning, go forwards
            patrol_direction = 1
            next_index = 1
            if next_index >= len(patrol_positions):
                next_index = 0
        
        current_position_index = next_index
    
    print("🛑 Patrol loop stopped")


def start_patrol(speed=5):
    """
    Start patrol mode
    
    Args:
        speed: Movement speed (1-10)
    """
    global patrol_active, patrol_thread, patrol_speed, current_position_index, patrol_direction
    
    if not pantilt_controller.is_enabled():
        print("⚠ Pan-Tilt not enabled")
        return False
    
    if not patrol_positions:
        print("⚠ No patrol positions defined")
        return False
    
    if patrol_active:
        print("⚠ Patrol already active")
        return True
    
    # Set speed
    patrol_speed = max(1, min(10, speed))
    
    # Reset to start
    current_position_index = 0
    patrol_direction = 1
    interrupted = False
    
    # Start patrol thread
    patrol_active = True
    patrol_thread = threading.Thread(target=patrol_loop, daemon=True, name="PatrolLoop")
    patrol_thread.start()
    
    print(f"✓ Patrol started with {len(patrol_positions)} positions at speed {patrol_speed}")
    return True


def stop_patrol():
    """Stop patrol mode"""
    global patrol_active, interrupted
    
    if not patrol_active:
        return False
    
    patrol_active = False
    interrupted = False
    
    # Cancel any pending resume timer
    if interrupt_resume_timer:
        interrupt_resume_timer.cancel()
    
    print("✓ Patrol stopped")
    return True


def interrupt_patrol():
    """
    Temporarily interrupt patrol (called when Jetson sends a command)
    Will auto-resume after interrupt_resume_delay seconds
    """
    global interrupted, interrupt_resume_timer
    
    if not patrol_active:
        return False
    
    print(f"⏸ Patrol interrupted, will resume in {interrupt_resume_delay}s")
    interrupted = True
    
    # Cancel any existing timer
    if interrupt_resume_timer:
        interrupt_resume_timer.cancel()
    
    # Schedule resume
    interrupt_resume_timer = threading.Timer(interrupt_resume_delay, resume_patrol)
    interrupt_resume_timer.daemon = True
    interrupt_resume_timer.start()
    
    return True


def resume_patrol():
    """Resume patrol after interrupt"""
    global interrupted
    
    if patrol_active and interrupted:
        print("▶ Resuming patrol")
        interrupted = False


def set_resume_delay(seconds):
    """Set the delay before auto-resuming patrol after interrupt"""
    global interrupt_resume_delay
    interrupt_resume_delay = max(1, min(60, seconds))
    print(f"✓ Interrupt resume delay set to {interrupt_resume_delay}s")


def is_active():
    """Check if patrol is currently active"""
    return patrol_active


def is_interrupted():
    """Check if patrol is currently interrupted"""
    return interrupted


def get_status():
    """Get current patrol status"""
    return {
        'active': patrol_active,
        'interrupted': interrupted,
        'position_count': len(patrol_positions),
        'current_index': current_position_index if patrol_active else None,
        'speed': patrol_speed,
        'resume_delay': interrupt_resume_delay,
        'direction': 'forward' if patrol_direction == 1 else 'backward'
    }


def init_patrol():
    """Initialize patrol system"""
    load_positions()
    print("✓ Patrol system initialized")
    return True


def cleanup():
    """Cleanup patrol resources"""
    stop_patrol()
    print("✓ Patrol cleanup complete")


if __name__ == "__main__":
    # Test patrol functionality
    print("Testing Patrol System...")
    
    init_patrol()
    
    # Add some test positions
    add_position(-45, 0, 5)
    add_position(0, -20, 3)
    add_position(45, 0, 5)
    add_position(0, 20, 3)
    
    print("\nStarting patrol...")
    start_patrol(speed=7)
    
    time.sleep(30)
    
    print("\nInterrupting patrol...")
    interrupt_patrol()
    
    time.sleep(10)
    
    print("\nStopping patrol...")
    stop_patrol()
    
    cleanup()

