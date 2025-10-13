"""
Flipper Zero Controller for HomePi Security System
Uses PyFlipper library for reliable Flipper Zero control
"""

import json
import time
import threading

# PyFlipper library
pyflipper_available = False
try:
    from pyflipper import PyFlipper
    pyflipper_available = True
except ImportError as e:
    print(f"⚠ PyFlipper module not available: {e}")
    print(f"   Install with: pip install pyflipper")

# Global Flipper state
flipper = None
flipper_config = {}
flipper_enabled = False
last_command_time = 0


def load_config():
    """Load Flipper configuration from config.json"""
    global flipper_config
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            flipper_config = config.get('security', {}).get('automation', {})
            return flipper_config
    except Exception as e:
        print(f"Error loading Flipper config: {e}")
        return {
            'flipper_port': '/dev/ttyACM1',
            'garage_trigger': 'my_car',
            'auto_open': True,
            'cooldown_seconds': 300
        }


def init_flipper(port=None):
    """
    Initialize PyFlipper connection to Flipper Zero
    
    Args:
        port: Serial port (e.g., /dev/ttyACM1)
    """
    global flipper, flipper_enabled, flipper_config
    
    if not pyflipper_available:
        print("PyFlipper module not available")
        print("Install with: pip install pyflipper")
        return False
    
    flipper_config = load_config()
    
    if not port:
        port = flipper_config.get('flipper_port', '/dev/ttyACM1')
    
    try:
        # Initialize PyFlipper
        flipper = PyFlipper(com=port)
        
        flipper_enabled = True
        print(f"✓ Flipper Zero connected on {port}")
        
        # Test connection by getting device info
        try:
            info = flipper.device_info.info()
            print(f"  Device: {info.get('hardware_name', 'Unknown')}")
            return True
        except:
            print("  Warning: Could not get device info, but connection established")
            return True
        
    except Exception as e:
        print(f"Error connecting to Flipper Zero: {e}")
        print(f"  Check that Flipper is connected to {port}")
        flipper_enabled = False
        return False


def open_garage():
    """
    Open garage door via Sub-GHz signal using PyFlipper
    
    This uses PyFlipper's tx_from_file method which is much more reliable
    than trying to control via CLI commands.
    """
    global last_command_time, flipper_config
    
    if not flipper_enabled:
        print("Flipper not enabled")
        return False
    
    # Check cooldown
    cooldown = flipper_config.get('cooldown_seconds', 300)
    if time.time() - last_command_time < cooldown:
        remaining = int(cooldown - (time.time() - last_command_time))
        print(f"Garage command on cooldown ({remaining}s remaining)")
        return False
    
    try:
        print("🚗 Opening garage door...")
        
        # Use PyFlipper's subghz.tx_from_file method
        # This directly transmits the .sub file - much more reliable!
        flipper.subghz.tx_from_file("/ext/subghz/garage.sub")
        
        print("✓ Garage door command sent")
        last_command_time = time.time()
        return True
        
    except Exception as e:
        print(f"Error opening garage: {e}")
        return False


def close_garage():
    """
    Close garage door via Sub-GHz signal
    Note: Most garage doors use the same signal for open/close (toggle)
    """
    # Most garage doors toggle, so just call open_garage
    return open_garage()


def trigger_garage():
    """
    Trigger garage (toggle open/close)
    Most garage doors use the same signal for both
    """
    return open_garage()


def is_enabled():
    """Check if Flipper Zero is enabled"""
    return flipper_enabled


def get_status():
    """Get Flipper connection status"""
    global flipper, flipper_enabled, last_command_time, flipper_config
    
    cooldown = flipper_config.get('cooldown_seconds', 300)
    time_since_last = time.time() - last_command_time if last_command_time > 0 else cooldown
    
    return {
        'enabled': flipper_enabled,
        'connected': flipper is not None,
        'port': flipper_config.get('flipper_port', '/dev/ttyACM1'),
        'auto_open': flipper_config.get('auto_open', True),
        'cooldown_seconds': cooldown,
        'ready': time_since_last >= cooldown
    }


def cleanup():
    """Close Flipper connection"""
    global flipper, flipper_enabled
    
    if flipper:
        try:
            # PyFlipper doesn't need explicit cleanup
            flipper_enabled = False
            print("Flipper Zero disconnected")
        except Exception as e:
            print(f"Error closing Flipper connection: {e}")


if __name__ == "__main__":
    # Test Flipper Zero functionality
    print("Testing Flipper Zero controller with PyFlipper...")
    print("\n⚠ NOTE: This will transmit /ext/subghz/garage.sub!")
    print("Make sure your garage signal is saved on Flipper at that location.")
    
    response = input("\nContinue with test? (yes/no): ")
    if response.lower() != 'yes':
        print("Test cancelled")
        exit(0)
    
    if init_flipper():
        print("\n✓ Flipper Zero initialized successfully")
        print(f"Status: {get_status()}")
        
        # Test garage command (with confirmation)
        print("\n⚠ WARNING: About to send garage door signal!")
        confirm = input("Send garage command? (yes/no): ")
        
        if confirm.lower() == 'yes':
            if open_garage():
                print("✓ Garage command successful")
            else:
                print("✗ Garage command failed")
        
        cleanup()
    else:
        print("\n✗ Flipper Zero initialization failed")
        print("\nTroubleshooting:")
        print("  1. Install PyFlipper: pip install pyflipper")
        print("  2. Check Flipper is connected via USB")
        print("  3. Check correct port (ls /dev/ttyACM*)")
        print("  4. Ensure Flipper is not connected to qFlipper")
        print("  5. Make sure garage.sub exists at /ext/subghz/garage.sub")

