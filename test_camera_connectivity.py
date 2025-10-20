#!/usr/bin/env python3
"""
Test script for camera connectivity check
This can be run manually to test the camera connectivity functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from homepi_watchdog import HomePiWatchdog

def test_camera_connectivity():
    """Test the camera connectivity check"""
    print("Testing HomePi Camera Connectivity Check")
    print("=" * 50)
    
    # Create watchdog instance
    watchdog = HomePiWatchdog()
    
    # Test camera connectivity
    print("1. Testing camera connectivity...")
    result = watchdog.check_camera_connectivity()
    print(f"   Camera connectivity: {'✅ PASS' if result else '❌ FAIL'}")
    
    if not result:
        print("\n2. Attempting to fix camera connectivity...")
        fix_result = watchdog.fix_camera_connectivity()
        print(f"   Fix attempt: {'✅ SUCCESS' if fix_result else '❌ FAILED'}")
        
        if fix_result:
            print("\n3. Re-testing camera connectivity after fix...")
            retest_result = watchdog.check_camera_connectivity()
            print(f"   Camera connectivity after fix: {'✅ PASS' if retest_result else '❌ FAIL'}")
    
    print("\n" + "=" * 50)
    print("Test completed")

if __name__ == "__main__":
    test_camera_connectivity()
