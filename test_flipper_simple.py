#!/usr/bin/env python3
"""
Simple Flipper Zero test - minimal code to debug serial communication
"""

import serial
import time

print("=" * 50)
print("Simple Flipper Test")
print("=" * 50)

try:
    # Connect to Flipper
    print("\n1. Connecting to Flipper on /dev/ttyACM0...")
    flipper = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
    time.sleep(2)
    print("   ✓ Connected")
    
    # Clear buffers
    print("\n2. Clearing buffers...")
    flipper.reset_input_buffer()
    flipper.reset_output_buffer()
    print("   ✓ Buffers cleared")
    
    # Test 1: Send help command
    print("\n3. Testing communication with 'help' command...")
    flipper.write(b"help\n")
    flipper.flush()
    time.sleep(1)
    
    if flipper.in_waiting > 0:
        response = flipper.read(flipper.in_waiting).decode('utf-8', errors='ignore')
        print(f"   Response received ({len(response)} bytes):")
        print(f"   {response[:200]}...")
    else:
        print("   ✗ No response received")
    
    # Test 2: Send input command
    print("\n4. Testing 'input send ok press' command...")
    print("   ⚠ Make sure Sub-GHz app is open with garage.sub loaded!")
    input("   Press Enter when ready...")
    
    flipper.reset_input_buffer()
    flipper.reset_output_buffer()
    
    command = "input send ok press\n"
    print(f"   Sending: {command.strip()}")
    flipper.write(command.encode('utf-8'))
    flipper.flush()
    time.sleep(1)
    
    if flipper.in_waiting > 0:
        response = flipper.read(flipper.in_waiting).decode('utf-8', errors='ignore')
        print(f"   Response: {response}")
    else:
        print("   No response")
    
    print("\n5. Waiting 10 seconds (watch Flipper screen)...")
    time.sleep(10)
    
    print("\n6. Sending 'input send ok release' command...")
    command = "input send ok release\n"
    print(f"   Sending: {command.strip()}")
    flipper.write(command.encode('utf-8'))
    flipper.flush()
    time.sleep(1)
    
    if flipper.in_waiting > 0:
        response = flipper.read(flipper.in_waiting).decode('utf-8', errors='ignore')
        print(f"   Response: {response}")
    else:
        print("   No response")
    
    print("\n7. Closing connection...")
    flipper.close()
    print("   ✓ Done")
    
    print("\n" + "=" * 50)
    print("Did the garage open? (y/n)")
    print("=" * 50)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

