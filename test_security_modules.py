#!/usr/bin/env python3
"""
Security System Module Testing Script
Tests each security module individually before full integration
"""

import sys
import time
import os

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ {text}{RESET}")


def test_camera():
    """Test camera manager module"""
    print_header("Testing Camera Manager")
    
    try:
        import camera_manager
        print_success("Camera module imported")
        
        # Test initialization
        print_info("Initializing camera...")
        if camera_manager.init_camera():
            print_success("Camera initialized successfully")
            
            # Test frame capture
            print_info("Capturing test frame...")
            frame = camera_manager.get_frame()
            if frame is not None:
                print_success(f"Frame captured: {frame.shape}")
            else:
                print_error("Failed to capture frame")
                return False
            
            # Test snapshot
            print_info("Taking snapshot...")
            snapshot_path = camera_manager.take_snapshot()
            if snapshot_path and os.path.exists(snapshot_path):
                print_success(f"Snapshot saved: {snapshot_path}")
            else:
                print_error("Failed to save snapshot")
            
            # Test recording
            print_info("Testing 3-second video recording...")
            rec_path = camera_manager.start_recording()
            if rec_path:
                print_success(f"Recording started: {rec_path}")
                time.sleep(3)
                final_path = camera_manager.stop_recording()
                if final_path and os.path.exists(final_path):
                    print_success(f"Recording saved: {final_path}")
                else:
                    print_error("Recording file not found")
            else:
                print_error("Failed to start recording")
            
            # Cleanup
            camera_manager.stop_camera()
            print_success("Camera test completed")
            return True
        else:
            print_error("Camera initialization failed")
            return False
            
    except ImportError as e:
        print_error(f"Camera module not available: {e}")
        print_warning("Install picamera2: pip install picamera2")
        return False
    except Exception as e:
        print_error(f"Camera test failed: {e}")
        return False


def test_pantilt():
    """Test Pan-Tilt HAT controller"""
    print_header("Testing Pan-Tilt HAT Controller")
    
    try:
        import pantilt_controller
        print_success("Pan-Tilt module imported")
        
        # Test initialization
        print_info("Initializing Pan-Tilt HAT...")
        if pantilt_controller.init_pantilt():
            print_success("Pan-Tilt initialized successfully")
            print_info(f"Current position: {pantilt_controller.get_position()}")
            
            # Test movements
            print_info("Testing pan left (-30°)...")
            pantilt_controller.move_to(-30, 0, speed=5)
            time.sleep(1)
            print_success("Pan left complete")
            
            print_info("Testing pan right (30°)...")
            pantilt_controller.move_to(30, 0, speed=5)
            time.sleep(1)
            print_success("Pan right complete")
            
            print_info("Testing tilt up (-20°)...")
            pantilt_controller.move_to(0, -20, speed=5)
            time.sleep(1)
            print_success("Tilt up complete")
            
            print_info("Testing tilt down (20°)...")
            pantilt_controller.move_to(0, 20, speed=5)
            time.sleep(1)
            print_success("Tilt down complete")
            
            print_info("Returning to home position...")
            pantilt_controller.home()
            time.sleep(1)
            print_success("Home position reached")
            
            # Test patrol (optional)
            response = input("\nTest patrol mode for 5 seconds? (y/n): ")
            if response.lower() == 'y':
                print_info("Starting patrol mode...")
                pantilt_controller.start_patrol()
                time.sleep(5)
                pantilt_controller.stop_patrol()
                pantilt_controller.home()
                print_success("Patrol test complete")
            
            print_success("Pan-Tilt test completed")
            return True
        else:
            print_error("Pan-Tilt initialization failed")
            return False
            
    except ImportError as e:
        print_error(f"Pan-Tilt module not available: {e}")
        print_warning("Install pantilthat: pip install pantilthat")
        return False
    except Exception as e:
        print_error(f"Pan-Tilt test failed: {e}")
        return False


def test_detector():
    """Test object detector with Coral TPU"""
    print_header("Testing Object Detector (Coral TPU)")
    
    try:
        import object_detector
        import numpy as np
        print_success("Object detector module imported")
        
        # Check for model file
        model_path = "models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
        if not os.path.exists(model_path):
            print_error(f"Model file not found: {model_path}")
            print_warning("Download model first:")
            print_warning("  mkdir -p models")
            print_warning("  cd models")
            print_warning("  wget https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite")
            return False
        
        # Test initialization
        print_info("Initializing Coral TPU detector...")
        if object_detector.init_detector(model_path):
            print_success("Detector initialized successfully")
            print_info(f"Status: {object_detector.get_status()}")
            
            # Create test image
            print_info("Creating test image...")
            test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            
            # Run detection
            print_info("Running object detection...")
            start_time = time.time()
            detections = object_detector.detect_objects(test_frame, threshold=0.5)
            inference_time = (time.time() - start_time) * 1000
            
            print_success(f"Detection completed in {inference_time:.1f}ms")
            print_info(f"Found {len(detections)} objects")
            
            for det in detections[:5]:  # Show first 5
                print(f"  - {det['class_name']}: {det['confidence']:.2f}")
            
            # Test filtering
            filtered = object_detector.filter_detections(detections, ['car', 'person'])
            print_info(f"Filtered to {len(filtered)} relevant objects")
            
            print_success("Detector test completed")
            return True
        else:
            print_error("Detector initialization failed")
            print_warning("Make sure:")
            print_warning("  1. Coral TPU is connected via USB")
            print_warning("  2. libedgetpu is installed")
            print_warning("  3. Model file exists")
            return False
            
    except ImportError as e:
        print_error(f"Detector module not available: {e}")
        print_warning("Install dependencies:")
        print_warning("  pip install pycoral tflite-runtime opencv-python")
        return False
    except Exception as e:
        print_error(f"Detector test failed: {e}")
        return False


def test_flipper():
    """Test Flipper Zero controller"""
    print_header("Testing Flipper Zero Controller")
    
    print_warning("⚠ This test will attempt to connect to Flipper Zero")
    print_warning("⚠ Make sure Flipper is connected via USB")
    
    response = input("\nContinue with Flipper test? (y/n): ")
    if response.lower() != 'y':
        print_warning("Flipper test skipped")
        return None
    
    try:
        import flipper_controller
        print_success("Flipper controller module imported")
        
        # Find Flipper port
        ports = ['/dev/ttyACM0', '/dev/ttyACM0', '/dev/ttyUSB0']
        print_info("Checking for Flipper on common ports...")
        
        connected = False
        for port in ports:
            if os.path.exists(port):
                print_info(f"Trying {port}...")
                if flipper_controller.init_flipper(port):
                    print_success(f"Flipper connected on {port}")
                    connected = True
                    break
        
        if not connected:
            print_error("Could not connect to Flipper Zero")
            print_warning("Check:")
            print_warning("  1. Flipper is connected via USB")
            print_warning("  2. Correct port (ls /dev/ttyACM*)")
            print_warning("  3. User in dialout group")
            return False
        
        # Test communication
        print_info("Testing communication...")
        response = flipper_controller.send_command("device_info", wait_response=True)
        if response:
            print_success("Flipper is responding")
            print(f"  Response: {response[:100]}...")
        else:
            print_error("Flipper not responding")
            return False
        
        # Test garage command (with warning)
        print_warning("\n⚠ Next test will send garage door signal!")
        print_warning("⚠ Only proceed if signal is recorded and safe to test")
        
        test_garage = input("\nTest garage command? (yes/no): ")
        if test_garage.lower() == 'yes':
            print_info("Sending garage door command...")
            if flipper_controller.open_garage():
                print_success("Garage command sent successfully")
            else:
                print_error("Garage command failed")
                print_warning("Make sure signal is recorded at:")
                print_warning("  /ext/subghz/garage_open.sub")
        
        # Cleanup
        flipper_controller.cleanup()
        print_success("Flipper test completed")
        return True
        
    except ImportError as e:
        print_error(f"Flipper module not available: {e}")
        print_warning("Install pyserial: pip install pyserial")
        return False
    except Exception as e:
        print_error(f"Flipper test failed: {e}")
        return False


def test_telegram():
    """Test Telegram notifier"""
    print_header("Testing Telegram Notifier")
    
    print_info("Telegram requires bot token and chat ID")
    print_info("Get token from @BotFather")
    print_info("Get chat ID from @userinfobot")
    
    # Check config
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
            telegram_config = config.get('security', {}).get('notifications', {})
            bot_token = telegram_config.get('telegram_bot_token', '')
            chat_id = telegram_config.get('telegram_chat_id', '')
    except:
        bot_token = ''
        chat_id = ''
    
    if not bot_token or not chat_id:
        print_warning("Telegram not configured in config.json")
        
        response = input("\nEnter credentials manually? (y/n): ")
        if response.lower() != 'y':
            print_warning("Telegram test skipped")
            return None
        
        bot_token = input("Enter bot token: ").strip()
        chat_id = input("Enter chat ID: ").strip()
        
        if not bot_token or not chat_id:
            print_error("Invalid credentials")
            return False
    
    try:
        import telegram_notifier
        print_success("Telegram module imported")
        
        # Initialize
        print_info("Initializing Telegram bot...")
        if telegram_notifier.init_telegram(bot_token, chat_id):
            print_success("Telegram bot initialized")
            print_info(f"Status: {telegram_notifier.get_status()}")
            
            # Test text message
            print_info("Sending test notification...")
            if telegram_notifier.send_notification("🧪 Test notification from HomePi Security testing script!"):
                print_success("Test notification sent")
            else:
                print_error("Failed to send notification")
            
            # Test photo (if test image exists)
            test_photo = "detections/snapshot_*.jpg"
            import glob
            photos = glob.glob(test_photo)
            if photos:
                print_info(f"Sending test photo: {photos[0]}")
                if telegram_notifier.send_photo(photos[0], "📸 Test photo from HomePi"):
                    print_success("Test photo sent")
                else:
                    print_error("Failed to send photo")
            
            telegram_notifier.cleanup()
            print_success("Telegram test completed")
            print_info("Check your Telegram app for messages!")
            return True
        else:
            print_error("Telegram initialization failed")
            return False
            
    except ImportError as e:
        print_error(f"Telegram module not available: {e}")
        print_warning("Install python-telegram-bot: pip install python-telegram-bot")
        return False
    except Exception as e:
        print_error(f"Telegram test failed: {e}")
        return False


def main():
    """Run all tests"""
    print_header("HomePi Security System - Module Testing")
    
    print_info("This script will test each security module individually")
    print_info("Make sure hardware is connected before testing")
    print()
    
    results = {}
    
    # Test menu
    tests = {
        '1': ('Camera Manager', test_camera),
        '2': ('Pan-Tilt HAT', test_pantilt),
        '3': ('Object Detector (Coral TPU)', test_detector),
        '4': ('Flipper Zero', test_flipper),
        '5': ('Telegram Notifier', test_telegram)
    }
    
    while True:
        print("\n" + "="*60)
        print("Select test to run:")
        print("="*60)
        for key, (name, _) in tests.items():
            status = results.get(name, 'Not tested')
            if status == True:
                status = f"{GREEN}✓ Passed{RESET}"
            elif status == False:
                status = f"{RED}✗ Failed{RESET}"
            elif status is None:
                status = f"{YELLOW}⊝ Skipped{RESET}"
            else:
                status = f"{BLUE}⋯ Not tested{RESET}"
            print(f"  {key}. {name:<30} {status}")
        print(f"  6. Run all tests")
        print(f"  0. Exit")
        print("="*60)
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            break
        elif choice == '6':
            # Run all tests
            for name, test_func in tests.values():
                result = test_func()
                results[name] = result
                if result is not False:  # Continue even if skipped
                    continue
        elif choice in tests:
            name, test_func = tests[choice]
            result = test_func()
            results[name] = result
        else:
            print_error("Invalid choice")
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for r in results.values() if r == True)
    failed = sum(1 for r in results.values() if r == False)
    skipped = sum(1 for r in results.values() if r is None)
    total = len(results)
    
    for name, result in results.items():
        if result == True:
            print_success(f"{name}: PASSED")
        elif result == False:
            print_error(f"{name}: FAILED")
        elif result is None:
            print_warning(f"{name}: SKIPPED")
    
    print()
    print(f"Total: {total} | {GREEN}Passed: {passed}{RESET} | {RED}Failed: {failed}{RESET} | {YELLOW}Skipped: {skipped}{RESET}")
    
    if failed > 0:
        print()
        print_warning("Some tests failed. Check hardware connections and dependencies.")
    elif passed == total and total > 0:
        print()
        print_success("All tests passed! Ready for integration.")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Testing interrupted by user{RESET}")
        sys.exit(0)

