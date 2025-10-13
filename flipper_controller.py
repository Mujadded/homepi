"""
Flipper Zero Controller for HomePi Security System
Serial communication with Flipper Zero for garage automation
"""

import json
import time
import threading

# Serial communication
serial_available = False
try:
    import serial
    serial_available = True
except ImportError as e:
    print(f"⚠ Serial module not available: {e}")

# Global Flipper state
flipper = None
flipper_config = {}
flipper_enabled = False
flipper_lock = threading.Lock()
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


def init_flipper(port=None, baudrate=115200, timeout=2):
    """
    Initialize serial connection to Flipper Zero
    
    Args:
        port: Serial port (e.g., /dev/ttyACM1)
        baudrate: Baud rate for serial communication
        timeout: Read timeout in seconds
    """
    global flipper, flipper_enabled, flipper_config
    
    if not serial_available:
        print("Serial module not available")
        return False
    
    flipper_config = load_config()
    
    if not port:
        port = flipper_config.get('flipper_port', '/dev/ttyACM1')
    
    try:
        flipper = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            write_timeout=timeout
        )
        
        # Wait for connection
        time.sleep(2)
        
        # Flush buffers
        flipper.reset_input_buffer()
        flipper.reset_output_buffer()
        
        flipper_enabled = True
        print(f"✓ Flipper Zero connected on {port}")
        
        # Test connection
        if test_connection():
            return True
        else:
            print("Flipper connected but not responding")
            return False
        
    except serial.SerialException as e:
        print(f"Error connecting to Flipper Zero: {e}")
        print(f"  Check that Flipper is connected to {port}")
        flipper_enabled = False
        return False
    except Exception as e:
        print(f"Unexpected error initializing Flipper: {e}")
        flipper_enabled = False
        return False


def send_command(command, wait_response=True, timeout=5):
    """
    Send command to Flipper Zero
    
    Args:
        command: Command string to send
        wait_response: Wait for response
        timeout: Response timeout in seconds
    
    Returns:
        Response string or None
    """
    global flipper, flipper_lock
    
    if not flipper or not flipper_enabled:
        print("Flipper not connected")
        return None
    
    try:
        with flipper_lock:
            # Clear buffers
            flipper.reset_input_buffer()
            flipper.reset_output_buffer()
            
            # Send command (add newline if not present)
            if not command.endswith('\n'):
                command += '\n'
            
            flipper.write(command.encode('utf-8'))
            flipper.flush()
            
            if wait_response:
                # Wait for response
                start_time = time.time()
                response = b''
                
                while (time.time() - start_time) < timeout:
                    if flipper.in_waiting > 0:
                        chunk = flipper.read(flipper.in_waiting)
                        response += chunk
                        
                        # Check if response is complete (ends with prompt)
                        if b'>:' in response or b'$' in response:
                            break
                    time.sleep(0.1)
                
                return response.decode('utf-8', errors='ignore').strip()
            
            return "OK"
        
    except Exception as e:
        print(f"Error sending command to Flipper: {e}")
        return None


def test_connection():
    """Test if Flipper is responding"""
    try:
        # Send simple command
        response = send_command("help", wait_response=True, timeout=3)
        if response and len(response) > 0:
            print("Flipper Zero is responding")
            return True
        return False
    except:
        return False


def open_garage():
    """
    Open garage door via Sub-GHz signal
    Requires garage signal to be pre-recorded on Flipper at /ext/subghz/garage.sub
    
    Uses the loader to start Sub-GHz app with the file
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
        
        # Method 1: Try using loader to open Sub-GHz app with file
        # This is more reliable across firmware versions
        loader_cmd = "loader open SubGhz /ext/subghz/garage.sub"
        print(f"Opening Sub-GHz app: {loader_cmd}")
        response = send_command(loader_cmd, wait_response=True, timeout=5)
        
        if response and "error" in response.lower() and "fail" in response.lower():
            print(f"Loader method failed: {response}")
            print("Trying alternative method...")
            
            # Method 2: Try direct subghz commands (older firmware)
            load_cmd = "subghz load /ext/subghz/garage.sub"
            response = send_command(load_cmd, wait_response=True, timeout=5)
            
            if not response or "error" in response.lower() or "fail" in response.lower():
                print(f"Failed to load signal: {response}")
                return False
            
            # Transmit
            tx_cmd = "subghz tx"
            response = send_command(tx_cmd, wait_response=True, timeout=10)
            
            if not response or "error" in response.lower() or "fail" in response.lower():
                print(f"Failed to transmit: {response}")
                return False
        else:
            # Loader opened successfully, now we need to trigger transmission
            # Wait a moment for the app to fully load
            time.sleep(1)
            
            # Send input event to HOLD OK button (Sub-GHz requires long press to transmit)
            print("Triggering transmission (holding OK button for 10 seconds)...")
            send_command("input send long ok", wait_response=False, timeout=1)
            
            # Wait for the long press transmission to complete (10+ seconds)
            time.sleep(12)
        
        # Close the app (to return to CLI)
        print("Closing Sub-GHz app...")
        send_command("loader close", wait_response=False, timeout=1)
        
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
        'connected': flipper is not None and flipper.is_open if flipper else False,
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
            flipper.close()
            flipper_enabled = False
            print("Flipper Zero disconnected")
        except Exception as e:
            print(f"Error closing Flipper connection: {e}")


if __name__ == "__main__":
    # Test Flipper Zero functionality
    print("Testing Flipper Zero controller...")
    print("\n⚠ NOTE: This will attempt to send garage door signal!")
    print("\nMake sure your garage signal is saved on Flipper at:")
    print("  /ext/subghz/garage.sub")
    print("\nTo save your garage signal:")
    print("  1. Go to Sub-GHz app on Flipper")
    print("  2. Read your garage remote signal")
    print("  3. Save it as 'garage' (will be saved to /ext/subghz/garage.sub)")
    
    response = input("\nContinue with test? (yes/no): ")
    if response.lower() != 'yes':
        print("Test cancelled")
        exit(0)
    
    if init_flipper():
        print("\n✓ Flipper Zero initialized successfully")
        print(f"Status: {get_status()}")
        
        # Test connection
        print("\nTesting communication...")
        response = send_command("device_info")
        if response:
            print(f"Response: {response[:100]}...")  # First 100 chars
        
        # Test garage command (with confirmation)
        print("\n⚠ WARNING: About to send garage door signal!")
        print("This will load and transmit /ext/subghz/garage.sub")
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
        print("  1. Check Flipper is connected via USB")
        print("  2. Check correct port (ls /dev/ttyACM*)")
        print("  3. Check user has permission (add to dialout group)")
        print("  4. Ensure Flipper is not connected to qFlipper")
        print("  5. Make sure garage.sub exists at /ext/subghz/garage.sub")

