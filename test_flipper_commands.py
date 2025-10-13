#!/usr/bin/env python3
"""
Test all possible Flipper Zero commands to see what actually works
"""

import serial
import time

def send_and_wait(flipper, command, wait_time=2):
    """Send command and wait for response"""
    flipper.reset_input_buffer()
    flipper.reset_output_buffer()
    
    print(f"\n→ Sending: {command}")
    flipper.write(f"{command}\n".encode('utf-8'))
    flipper.flush()
    time.sleep(wait_time)
    
    if flipper.in_waiting > 0:
        response = flipper.read(flipper.in_waiting).decode('utf-8', errors='ignore')
        print(f"← Response ({len(response)} bytes):")
        print(response[:500])  # First 500 chars
        return response
    else:
        print("← No response")
        return ""

print("=" * 60)
print("Flipper Zero Command Test")
print("=" * 60)

try:
    flipper = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
    time.sleep(2)
    print("✓ Connected to Flipper\n")
    
    # Test 1: Help
    print("\n" + "=" * 60)
    print("TEST 1: Help command")
    print("=" * 60)
    send_and_wait(flipper, "help", 2)
    
    # Test 2: Device info
    print("\n" + "=" * 60)
    print("TEST 2: Device info")
    print("=" * 60)
    send_and_wait(flipper, "device_info", 2)
    
    # Test 3: Storage list
    print("\n" + "=" * 60)
    print("TEST 3: List Sub-GHz files")
    print("=" * 60)
    send_and_wait(flipper, "storage list /ext/subghz/", 3)
    
    # Test 4: Storage stat
    print("\n" + "=" * 60)
    print("TEST 4: Check garage.sub file")
    print("=" * 60)
    send_and_wait(flipper, "storage stat /ext/subghz/garage.sub", 2)
    
    # Test 5: Loader list
    print("\n" + "=" * 60)
    print("TEST 5: List available apps")
    print("=" * 60)
    send_and_wait(flipper, "loader list", 2)
    
    # Test 6: Try opening Sub-GHz app
    print("\n" + "=" * 60)
    print("TEST 6: Try opening Sub-GHz app")
    print("=" * 60)
    print("⚠ Watch Flipper screen!")
    send_and_wait(flipper, "loader open SubGhz /ext/subghz/garage.sub", 3)
    
    input("\nDid the Sub-GHz app open on Flipper? Press Enter to continue...")
    
    # Test 7: Input commands
    print("\n" + "=" * 60)
    print("TEST 7: Try input commands")
    print("=" * 60)
    print("⚠ Watch Flipper screen!")
    send_and_wait(flipper, "input send ok press", 1)
    time.sleep(3)
    send_and_wait(flipper, "input send ok release", 1)
    
    input("\nDid you see any button press on Flipper? Press Enter to continue...")
    
    # Test 8: Close app
    print("\n" + "=" * 60)
    print("TEST 8: Close app")
    print("=" * 60)
    send_and_wait(flipper, "loader close", 2)
    
    flipper.close()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    print("\nPlease report:")
    print("1. Which commands showed actual responses (not just echo)?")
    print("2. Did the Sub-GHz app open?")
    print("3. Did you see any button presses?")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

