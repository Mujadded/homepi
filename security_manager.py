"""
Security Manager for HomePi
Main orchestration module for AI-powered security system
Coordinates camera, detection, tracking, recording, and automation
"""

import os
import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
import sqlite3

# Import security modules
import camera_manager
import pantilt_controller
import object_detector
import flipper_controller
import telegram_notifier

logger = logging.getLogger(__name__)

# Global state
security_enabled = False
detection_thread = None
detection_running = False
security_config = {}
db_conn = None

# Detection state
current_detections = []
tracking_target = None
last_my_car_time = 0
automation_cooldown = 300  # 5 minutes


def load_config():
    """Load security configuration"""
    global security_config, automation_cooldown
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            security_config = config.get('security', {})
            automation_cooldown = security_config.get('automation', {}).get('cooldown_seconds', 300)
            return security_config
    except Exception as e:
        logger.error(f"Error loading security config: {e}")
        return {}


def init_database():
    """Initialize SQLite database for detections"""
    global db_conn
    
    try:
        db_path = 'security.db'
        db_conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = db_conn.cursor()
        
        # Create detections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                object_type TEXT NOT NULL,
                car_id TEXT,
                confidence REAL,
                bbox TEXT,
                image_path TEXT,
                video_path TEXT,
                action_taken TEXT
            )
        ''')
        
        # Create known_cars table (for future car recognition)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS known_cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id TEXT UNIQUE NOT NULL,
                owner TEXT,
                features BLOB,
                added_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        db_conn.commit()
        logger.info("✓ Security database initialized")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


def init_security():
    """Initialize all security components"""
    global security_enabled, security_config
    
    logger.info("Initializing security system...")
    
    # Load configuration
    security_config = load_config()
    
    if not security_config.get('enabled', False):
        logger.info("Security system disabled in config")
        return False
    
    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database")
        return False
    
    # Initialize camera
    if not camera_manager.init_camera():
        logger.error("Failed to initialize camera")
        return False
    
    # Initialize Pan-Tilt HAT
    if not pantilt_controller.init_pantilt():
        logger.warning("Pan-Tilt HAT not available, tracking disabled")
    
    # Initialize object detector (remote inference)
    remote_url = security_config.get('detection', {}).get('remote_url')
    if not object_detector.init_detector(remote_url):
        logger.error("Failed to initialize object detector")
        return False
    
    # Initialize Flipper Zero (optional)
    flipper_port = security_config.get('automation', {}).get('flipper_port')
    if flipper_port:
        flipper_controller.init_flipper(flipper_port)
    
    # Initialize Telegram (optional)
    telegram_config = security_config.get('notifications', {})
    if telegram_config.get('telegram_enabled'):
        bot_token = telegram_config.get('telegram_bot_token')
        chat_id = telegram_config.get('telegram_chat_id')
        if bot_token and chat_id:
            telegram_notifier.init_telegram(bot_token, chat_id)
    
    # Create required directories
    Path('recordings').mkdir(exist_ok=True)
    Path('detections').mkdir(exist_ok=True)
    
    security_enabled = True
    logger.info("✓ Security system initialized")
    return True


def save_detection(detection_data):
    """Save detection to database"""
    global db_conn
    
    if not db_conn:
        return None
    
    try:
        cursor = db_conn.cursor()
        cursor.execute('''
            INSERT INTO detections 
            (object_type, car_id, confidence, bbox, image_path, video_path, action_taken)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            detection_data.get('object_type'),
            detection_data.get('car_id'),
            detection_data.get('confidence'),
            json.dumps(detection_data.get('bbox')),
            detection_data.get('image_path'),
            detection_data.get('video_path'),
            detection_data.get('action_taken')
        ))
        db_conn.commit()
        return cursor.lastrowid
        
    except Exception as e:
        logger.error(f"Error saving detection: {e}")
        return None


def get_recent_detections(limit=20):
    """Get recent detections from database"""
    global db_conn
    
    if not db_conn:
        return []
    
    try:
        cursor = db_conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, object_type, car_id, confidence, 
                   bbox, image_path, video_path, action_taken
            FROM detections
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        detections = []
        for row in cursor.fetchall():
            detections.append({
                'id': row[0],
                'timestamp': row[1],
                'object_type': row[2],
                'car_id': row[3],
                'confidence': row[4],
                'bbox': json.loads(row[5]) if row[5] else None,
                'image_path': row[6],
                'video_path': row[7],
                'action_taken': row[8]
            })
        
        return detections
        
    except Exception as e:
        logger.error(f"Error getting detections: {e}")
        return []


def handle_detection(detections):
    """Process detection results and trigger actions"""
    global current_detections, tracking_target, last_my_car_time
    
    current_detections = detections
    
    if not detections:
        tracking_target = None
        return
    
    # Get detection config
    detection_config = security_config.get('detection', {})
    classes_of_interest = detection_config.get('classes_of_interest', ['car', 'person'])
    
    # Filter detections
    filtered = [d for d in detections if d['class_name'] in classes_of_interest]
    
    if not filtered:
        tracking_target = None
        return
    
    # Process each detection
    for detection in filtered:
        class_name = detection['class_name']
        confidence = detection['confidence']
        bbox = detection['bbox']
        
        logger.info(f"Detected: {class_name} ({confidence:.2f})")
        
        # Take snapshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_path = f"detections/{class_name}_{timestamp}.jpg"
        
        frame = camera_manager.get_frame()
        if frame is not None:
            camera_manager.save_frame(frame, snapshot_path)
        
        # Check if it's a car
        is_car = 'car' in class_name or 'truck' in class_name
        car_id = None
        
        if is_car:
            # TODO: Add car recognition here when implemented
            # For now, assume all cars are "unknown"
            car_id = "unknown_car"
        
        # Save to database
        detection_data = {
            'object_type': class_name,
            'car_id': car_id,
            'confidence': confidence,
            'bbox': bbox,
            'image_path': snapshot_path,
            'video_path': None,
            'action_taken': None
        }
        
        detection_id = save_detection(detection_data)
        
        # Send Telegram notification
        notification_config = security_config.get('notifications', {})
        if notification_config.get('telegram_enabled'):
            should_notify = (
                (class_name == 'person' and notification_config.get('notify_person', False)) or
                (is_car and car_id == 'my_car' and notification_config.get('notify_my_car', True)) or
                (is_car and car_id != 'my_car' and notification_config.get('notify_unknown_car', True))
            )
            
            if should_notify:
                message = f"🚨 Detected: {class_name}\n"
                message += f"Confidence: {confidence:.1%}\n"
                message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                if notification_config.get('send_photo') and os.path.exists(snapshot_path):
                    telegram_notifier.send_photo(snapshot_path, message)
                else:
                    telegram_notifier.send_notification(message)
        
        # Trigger automation for "my_car"
        if car_id == 'my_car':
            automation_config = security_config.get('automation', {})
            
            # Check cooldown
            current_time = time.time()
            if current_time - last_my_car_time > automation_cooldown:
                if automation_config.get('auto_open', False):
                    logger.info("🚗 My car detected! Opening garage...")
                    
                    if flipper_controller.is_enabled():
                        success = flipper_controller.open_garage()
                        
                        if success:
                            action_taken = "garage_opened"
                            last_my_car_time = current_time
                            
                            # Update database
                            if detection_id:
                                cursor = db_conn.cursor()
                                cursor.execute(
                                    'UPDATE detections SET action_taken = ? WHERE id = ?',
                                    (action_taken, detection_id)
                                )
                                db_conn.commit()
                            
                            # Send notification
                            telegram_notifier.send_notification("🚗 Garage door opened for your car!")
            else:
                logger.info("Garage automation on cooldown")
    
    # Update tracking target (track the first detection)
    if filtered and security_config.get('pantilt', {}).get('tracking_enabled', True):
        tracking_target = filtered[0]['bbox']
        track_object(tracking_target)


def track_object(bbox):
    """Track object with Pan-Tilt HAT"""
    if not pantilt_controller.is_enabled():
        return
    
    try:
        # Get frame dimensions
        frame = camera_manager.get_frame()
        if frame is None:
            return
        
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate object center
        x1, y1, x2, y2 = bbox
        obj_center_x = (x1 + x2) / 2
        obj_center_y = (y1 + y2) / 2
        
        # Calculate frame center
        frame_center_x = frame_width / 2
        frame_center_y = frame_height / 2
        
        # Calculate error (how far object is from center)
        error_x = obj_center_x - frame_center_x
        error_y = obj_center_y - frame_center_y
        
        # Convert to pan/tilt adjustments (proportional control)
        # Normalize to -1 to 1, then scale
        pan_adjust = (error_x / frame_width) * 20  # Max 20 degrees adjustment
        tilt_adjust = -(error_y / frame_height) * 20  # Negative because Y is inverted
        
        # Get current position
        current_pos = pantilt_controller.get_position()
        
        # Calculate new position
        new_pan = current_pos['pan'] + pan_adjust
        new_tilt = current_pos['tilt'] + tilt_adjust
        
        # Move to new position
        tracking_speed = security_config.get('pantilt', {}).get('tracking_speed', 5)
        pantilt_controller.move_to(new_pan, new_tilt, tracking_speed)
        
    except Exception as e:
        logger.error(f"Error tracking object: {e}")


def detection_loop():
    """Main detection loop running in separate thread"""
    global detection_running, tracking_target
    
    logger.info("Detection loop started")
    detection_interval = security_config.get('detection', {}).get('detection_interval', 0.1)
    
    while detection_running:
        try:
            # Get current frame
            frame = camera_manager.get_frame()
            
            if frame is None:
                time.sleep(detection_interval)
                continue
            
            # Run object detection
            detections = object_detector.detect_objects(frame)
            
            # Process detections
            if detections:
                handle_detection(detections)
            else:
                # No detections, reset tracking
                tracking_target = None
            
            # Sleep for detection interval
            time.sleep(detection_interval)
            
        except Exception as e:
            logger.error(f"Error in detection loop: {e}")
            time.sleep(1)
    
    logger.info("Detection loop stopped")


def start_detection():
    """Start detection thread"""
    global detection_thread, detection_running, security_enabled
    
    if not security_enabled:
        logger.error("Security system not initialized")
        return False
    
    if detection_running:
        logger.warning("Detection already running")
        return False
    
    detection_running = True
    detection_thread = threading.Thread(target=detection_loop, daemon=True)
    detection_thread.start()
    
    logger.info("✓ Detection started")
    return True


def stop_detection():
    """Stop detection thread"""
    global detection_running, detection_thread
    
    if not detection_running:
        return False
    
    detection_running = False
    
    if detection_thread:
        detection_thread.join(timeout=5)
    
    logger.info("Detection stopped")
    return True


def get_status():
    """Get security system status"""
    return {
        'enabled': security_enabled,
        'detection_running': detection_running,
        'camera_enabled': camera_manager.is_enabled(),
        'pantilt_enabled': pantilt_controller.is_enabled(),
        'detector_enabled': object_detector.is_enabled(),
        'flipper_enabled': flipper_controller.is_enabled(),
        'telegram_enabled': telegram_notifier.is_enabled(),
        'current_detections': len(current_detections),
        'tracking_target': tracking_target is not None
    }


def cleanup():
    """Cleanup security system"""
    global detection_running, db_conn
    
    logger.info("Cleaning up security system...")
    
    # Stop detection
    stop_detection()
    
    # Cleanup components
    camera_manager.cleanup()
    pantilt_controller.cleanup()
    object_detector.cleanup()
    flipper_controller.cleanup()
    telegram_notifier.cleanup()
    
    # Close database
    if db_conn:
        db_conn.close()
    
    logger.info("Security system cleanup complete")


if __name__ == "__main__":
    # Test security manager
    logging.basicConfig(level=logging.INFO)
    
    print("Testing security manager...")
    
    if init_security():
        print("✓ Security system initialized")
        print(f"Status: {get_status()}")
        
        # Start detection
        if start_detection():
            print("✓ Detection started")
            print("Running for 10 seconds...")
            time.sleep(10)
            
            # Show recent detections
            detections = get_recent_detections(5)
            print(f"\nRecent detections: {len(detections)}")
            for det in detections:
                print(f"  - {det['object_type']} ({det['confidence']:.2f}) at {det['timestamp']}")
            
            stop_detection()
        
        cleanup()
    else:
        print("✗ Security system initialization failed")

