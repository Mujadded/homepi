"""
Display Manager for Pi HAT OLED Display
Handles SSD1306 OLED display showing song info, countdown, and sensor data
"""

import os
import json
import time
import math
import threading
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# Global display variables
display = None
display_config = {}
current_screen = 0
display_enabled = False

# Shared state from main app
playback_state = {
    'playing': False,
    'current_song': None,
    'position': 0,
    'duration': 0
}

schedules_data = []
sensor_data_ref = None


def load_config():
    """Load display configuration from config.json"""
    global display_config
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            display_config = config.get('display', {})
    else:
        display_config = {
            'enabled': True,
            'type': 'ssd1306',
            'i2c_address': '0x3C',
            'width': 128,
            'height': 64,
            'rotation_interval': 5
        }
    return display_config


def init_display():
    """Initialize the display (SSD1306 OLED or Sense HAT LED matrix)"""
    global display, display_enabled, display_config
    
    display_config = load_config()
    
    if not display_config.get('enabled', True):
        print("Display disabled in config")
        return False
    
    display_type = display_config.get('type', 'ssd1306')
    
    try:
        if display_type == 'sense_hat':
            # Initialize Sense HAT LED matrix
            from sense_hat import SenseHat
            
            display = SenseHat()
            display.low_light = True  # Reduce brightness
            display.clear()
            
            print("✓ Sense HAT LED matrix initialized (8x8)")
            display_enabled = True
            return True
            
        elif display_type == 'ssd1306':
            import board
            import adafruit_ssd1306
            
            # Initialize I2C
            i2c = board.I2C()
            
            # Get display dimensions
            width = display_config.get('width', 128)
            height = display_config.get('height', 64)
            i2c_addr = int(display_config.get('i2c_address', '0x3C'), 16)
            
            # Initialize display
            display = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=i2c_addr)
            
            # Clear display
            display.fill(0)
            display.show()
            
            print(f"✓ SSD1306 display initialized ({width}x{height} at {display_config.get('i2c_address')})")
            display_enabled = True
            return True
        
    except ImportError as e:
        print(f"⚠ Display libraries not installed: {e}")
        print("  For Sense HAT: pip install sense-hat")
        print("  For SSD1306: pip install adafruit-circuitpython-ssd1306 Pillow")
        return False
    except Exception as e:
        print(f"⚠ Could not initialize display: {e}")
        return False


def get_next_schedule():
    """Calculate time until next scheduled song"""
    global schedules_data
    
    if not schedules_data:
        return None, None
    
    now = datetime.now()
    current_time = now.hour * 60 + now.minute
    current_day = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][now.weekday()]
    
    next_schedule = None
    min_diff = float('inf')
    
    for schedule in schedules_data:
        if not schedule.get('enabled', True):
            continue
        
        sched_time = schedule['hour'] * 60 + schedule['minute']
        days_of_week = schedule.get('days_of_week', [])
        
        # Check if schedule applies today
        if days_of_week and current_day not in days_of_week:
            continue
        
        # Only consider future times today
        if sched_time > current_time:
            diff = sched_time - current_time
            if diff < min_diff:
                min_diff = diff
                next_schedule = schedule
    
    if next_schedule:
        hours = min_diff // 60
        minutes = min_diff % 60
        return next_schedule, f"{hours:02d}:{minutes:02d}"
    
    return None, None


def render_countdown_screen(draw, width, height):
    """Render countdown to next schedule"""
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    next_schedule, countdown = get_next_schedule()
    
    if next_schedule:
        # Draw title
        draw.text((2, 2), "NEXT SCHEDULE:", font=font_small, fill=255)
        
        # Draw schedule name (truncate if needed)
        name = next_schedule['name']
        if len(name) > 15:
            name = name[:15] + "..."
        draw.text((2, 16), name, font=font_small, fill=255)
        
        # Draw countdown timer
        draw.text((2, 32), countdown, font=font_large, fill=255)
        
        # Draw scheduled time
        time_str = f"{next_schedule['hour']:02d}:{next_schedule['minute']:02d}"
        draw.text((2, 54), f"@ {time_str}", font=font_small, fill=255)
    else:
        draw.text((2, 24), "No schedules", font=font_small, fill=255)
        draw.text((2, 38), "upcoming", font=font_small, fill=255)


def render_playing_screen(draw, width, height):
    """Render currently playing song with progress"""
    try:
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except:
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    if playback_state.get('playing') and playback_state.get('current_song'):
        # Draw "NOW PLAYING"
        draw.text((2, 2), "NOW PLAYING:", font=font_tiny, fill=255)
        
        # Draw song name (truncate if needed)
        song = playback_state['current_song']
        if len(song) > 20:
            song = song[:20] + "..."
        draw.text((2, 14), song, font=font_small, fill=255)
        
        # Draw progress bar
        if playback_state.get('duration', 0) > 0:
            position = playback_state.get('position', 0)
            duration = playback_state['duration']
            progress = min(position / duration, 1.0)
            
            # Progress bar
            bar_width = width - 8
            bar_height = 8
            bar_x = 4
            bar_y = 40
            
            # Background
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], outline=255, fill=0)
            
            # Filled portion
            if progress > 0:
                fill_width = int(bar_width * progress)
                draw.rectangle([bar_x + 1, bar_y + 1, bar_x + fill_width, bar_y + bar_height - 1], fill=255)
            
            # Time display
            pos_min = int(position // 60)
            pos_sec = int(position % 60)
            dur_min = int(duration // 60)
            dur_sec = int(duration % 60)
            time_str = f"{pos_min}:{pos_sec:02d} / {dur_min}:{dur_sec:02d}"
            draw.text((4, 52), time_str, font=font_tiny, fill=255)
    else:
        # Idle screen
        draw.text((20, 24), "♪ IDLE ♪", font=font_small, fill=255)


def render_sensor_screen(draw, width, height):
    """Render temperature and humidity"""
    global sensor_data_ref
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    if sensor_data_ref and sensor_data_ref.get('sensor_available'):
        # Draw temperature
        temp = sensor_data_ref.get('temperature')
        if temp is not None:
            draw.text((2, 2), "Temperature:", font=font_small, fill=255)
            draw.text((2, 16), f"{temp:.1f}°C", font=font_large, fill=255)
        
        # Draw humidity
        humidity = sensor_data_ref.get('humidity')
        if humidity is not None:
            draw.text((2, 38), "Humidity:", font=font_small, fill=255)
            draw.text((2, 50), f"{humidity:.1f}%", font=font_large, fill=255)
    else:
        draw.text((2, 24), "No sensor data", font=font_small, fill=255)


def render_combined_screen(draw, width, height):
    """Render all info in one compact view"""
    try:
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except:
        font_tiny = ImageFont.load_default()
    
    y_pos = 2
    
    # Current time
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%m/%d")
    draw.text((2, y_pos), f"{time_str} {date_str}", font=font_tiny, fill=255)
    y_pos += 12
    
    # Playing status
    if playback_state.get('playing'):
        song = playback_state['current_song']
        if len(song) > 18:
            song = song[:18] + "..."
        draw.text((2, y_pos), f"♪ {song}", font=font_tiny, fill=255)
    else:
        draw.text((2, y_pos), "♪ Idle", font=font_tiny, fill=255)
    y_pos += 12
    
    # Next schedule
    next_schedule, countdown = get_next_schedule()
    if next_schedule:
        name = next_schedule['name']
        if len(name) > 12:
            name = name[:12] + "..."
        draw.text((2, y_pos), f"Next: {name}", font=font_tiny, fill=255)
        y_pos += 10
        draw.text((2, y_pos), f"In: {countdown}", font=font_tiny, fill=255)
    else:
        draw.text((2, y_pos), "Next: None", font=font_tiny, fill=255)
    y_pos += 12
    
    # Sensor data
    if sensor_data_ref and sensor_data_ref.get('sensor_available'):
        temp = sensor_data_ref.get('temperature')
        humidity = sensor_data_ref.get('humidity')
        if temp and humidity:
            draw.text((2, y_pos), f"Env: {temp:.1f}°C {humidity:.0f}%", font=font_tiny, fill=255)


def render_sense_hat_countdown():
    """Render countdown on Sense HAT with visual hourglass animation"""
    global display
    
    next_schedule, countdown = get_next_schedule()
    display.clear()
    
    if next_schedule and countdown:
        # Visual hourglass filling up over time
        import time
        
        # Parse countdown
        parts = countdown.split(':')
        if len(parts) >= 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            total_minutes = hours * 60 + minutes
            
            # Calculate fill level (0-8 pixels)
            if total_minutes > 60:
                fill_level = 2  # Many hours = mostly empty
            elif total_minutes > 30:
                fill_level = 4  # Half hour
            elif total_minutes > 10:
                fill_level = 6  # Close
            else:
                fill_level = 8  # Very close!
            
            # Draw hourglass shape
            hourglass = [
                [1,1,1,1,1,1,1,1],  # Top
                [0,1,1,1,1,1,1,0],
                [0,0,1,1,1,1,0,0],
                [0,0,0,1,1,0,0,0],  # Narrow middle
                [0,0,1,1,1,1,0,0],
                [0,1,1,1,1,1,1,0],
                [1,1,1,1,1,1,1,1],  # Bottom
                [1,1,1,1,1,1,1,1]
            ]
            
            # Color based on urgency
            if total_minutes < 10:
                color = (255, 0, 0)  # Red - urgent!
            elif total_minutes < 30:
                color = (255, 200, 0)  # Orange
            else:
                color = (0, 200, 255)  # Blue - plenty of time
            
            # Draw hourglass and fill from bottom
            for y in range(8):
                for x in range(8):
                    if hourglass[y][x]:
                        # Fill from bottom up
                        if y >= (8 - fill_level):
                            display.set_pixel(x, y, *color)
                        else:
                            # Empty part - dim outline
                            display.set_pixel(x, y, color[0]//4, color[1]//4, color[2]//4)
    else:
        # Checkmark - no schedules today
        checkmark = [
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,1,0],
            [0,0,0,0,0,1,1,0],
            [0,0,0,0,1,1,0,0],
            [1,0,0,1,1,0,0,0],
            [1,1,1,1,0,0,0,0],
            [0,1,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0]
        ]
        for y in range(8):
            for x in range(8):
                if checkmark[y][x]:
                    display.set_pixel(x, y, 0, 255, 0)


def render_sense_hat_playing():
    """Render playing status on Sense HAT with clean visual icons"""
    global display
    display.clear()
    
    if playback_state.get('playing'):
        # Pulsing music note
        import time
        pulse = int(abs(math.sin(time.time() * 3)) * 255)
        
        # Music note icon
        music_note = [
            [0,0,0,0,0,1,1,0],
            [0,0,0,0,0,1,1,0],
            [0,0,0,0,0,1,1,0],
            [0,0,0,0,0,1,1,0],
            [0,1,1,0,0,1,1,0],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [0,1,1,0,0,1,1,0]
        ]
        
        for y in range(8):
            for x in range(8):
                if music_note[y][x]:
                    # Pulsing green
                    display.set_pixel(x, y, 0, pulse, 0)
    else:
        # Pause symbol
        pause_icon = [
            [0,0,0,0,0,0,0,0],
            [0,1,1,0,0,1,1,0],
            [0,1,1,0,0,1,1,0],
            [0,1,1,0,0,1,1,0],
            [0,1,1,0,0,1,1,0],
            [0,1,1,0,0,1,1,0],
            [0,1,1,0,0,1,1,0],
            [0,0,0,0,0,0,0,0]
        ]
        
        for y in range(8):
            for x in range(8):
                if pause_icon[y][x]:
                    display.set_pixel(x, y, 100, 100, 100)


def render_sense_hat_sensor():
    """Render sensor data on Sense HAT with animated temperature gauge"""
    global display, sensor_data_ref
    
    if sensor_data_ref and sensor_data_ref.get('sensor_available'):
        temp = sensor_data_ref.get('temperature')
        humidity = sensor_data_ref.get('humidity')
        
        if temp:
            display.clear()
            
            # Temperature bar graph (left side)
            temp_height = int((temp - 10) / 30 * 7)  # Map 10-40°C to 0-7 pixels
            temp_height = max(0, min(7, temp_height))
            
            for y in range(8):
                if y >= (7 - temp_height):
                    # Color changes with temperature
                    if temp < 18:
                        display.set_pixel(0, y, 0, 0, 255)  # Cold = blue
                        display.set_pixel(1, y, 0, 100, 255)
                    elif temp < 25:
                        display.set_pixel(0, y, 0, 255, 0)  # Comfortable = green
                        display.set_pixel(1, y, 100, 255, 0)
                    else:
                        display.set_pixel(0, y, 255, 0, 0)  # Hot = red
                        display.set_pixel(1, y, 255, 100, 0)
            
            # Humidity bar graph (right side)
            humidity_height = int(humidity / 100 * 7)
            for y in range(8):
                if y >= (7 - humidity_height):
                    # Blue gradient for humidity
                    display.set_pixel(7, y, 0, 150, 255)
                    display.set_pixel(6, y, 50, 200, 255)
            
            # Center decoration - pulsing dot
            import time
            pulse = int(abs(math.sin(time.time() * 2)) * 255)
            display.set_pixel(4, 3, pulse, pulse, pulse)
            display.set_pixel(4, 4, pulse, pulse, pulse)
    else:
        display.clear()


def render_sense_hat_idle():
    """Render idle screen - simple heart pulse"""
    global display
    import time
    display.clear()
    
    # Pulsing heart
    pulse = int(abs(math.sin(time.time() * 2)) * 255)
    
    heart = [
        [0,0,1,1,0,1,1,0],
        [0,1,1,1,1,1,1,1],
        [0,1,1,1,1,1,1,1],
        [0,1,1,1,1,1,1,1],
        [0,0,1,1,1,1,1,0],
        [0,0,0,1,1,1,0,0],
        [0,0,0,0,1,0,0,0],
        [0,0,0,0,0,0,0,0]
    ]
    
    for y in range(8):
        for x in range(8):
            if heart[y][x]:
                display.set_pixel(x, y, pulse, 0, pulse // 2)


def update_display():
    """Update the display with current screen"""
    global display, current_screen, display_config
    
    if not display or not display_enabled:
        return
    
    display_type = display_config.get('type', 'ssd1306')
    
    try:
        if display_type == 'sense_hat':
            # Sense HAT LED matrix (8x8) - simple visualizations
            if current_screen == 0:
                render_sense_hat_countdown()
            elif current_screen == 1:
                render_sense_hat_playing()
            elif current_screen == 2:
                render_sense_hat_sensor()
            else:
                render_sense_hat_idle()
        
        elif display_type == 'ssd1306':
            # Create image for OLED
            width = display_config.get('width', 128)
            height = display_config.get('height', 64)
            image = Image.new('1', (width, height))
            draw = ImageDraw.Draw(image)
            
            # Render current screen (rotate through 4 screens)
            if current_screen == 0:
                render_countdown_screen(draw, width, height)
            elif current_screen == 1:
                render_playing_screen(draw, width, height)
            elif current_screen == 2:
                render_sensor_screen(draw, width, height)
            else:
                render_combined_screen(draw, width, height)
            
            # Display image
            display.image(image)
            display.show()
    except Exception as e:
        print(f"Display update error: {e}")


def display_loop():
    """Main display thread loop"""
    global current_screen, display_config
    
    rotation_interval = display_config.get('rotation_interval', 5)
    update_interval = 1  # Update every second
    rotation_counter = 0
    
    print(f"Starting display loop (rotating every {rotation_interval} seconds)...")
    
    while True:
        try:
            update_display()
            rotation_counter += update_interval
            
            # Rotate screens
            if rotation_counter >= rotation_interval:
                current_screen = (current_screen + 1) % 4
                rotation_counter = 0
        except Exception as e:
            print(f"Display loop error: {e}")
        
        time.sleep(update_interval)


def start_display_thread(schedules, sensor_data_dict):
    """Start the display update thread"""
    global schedules_data, sensor_data_ref
    
    schedules_data = schedules
    sensor_data_ref = sensor_data_dict
    
    if not init_display():
        print("⚠ Display not available - running without OLED display")
        return None
    
    thread = threading.Thread(target=display_loop, daemon=True, name="DisplayThread")
    thread.start()
    print("✓ Display thread started")
    return thread


def update_playback_state(playing=None, current_song=None, position=None, duration=None):
    """Update playback state for display"""
    global playback_state
    
    if playing is not None:
        playback_state['playing'] = playing
    if current_song is not None:
        playback_state['current_song'] = current_song
    if position is not None:
        playback_state['position'] = position
    if duration is not None:
        playback_state['duration'] = duration


def update_schedules(schedules):
    """Update schedules data for display"""
    global schedules_data
    schedules_data = schedules


if __name__ == "__main__":
    # Test the display
    print("Testing display...")
    if init_display():
        print("Display initialized, testing screens...")
        
        # Test data
        update_playback_state(playing=True, current_song="Test Song.mp3", position=30, duration=180)
        schedules_data = [
            {'id': 1, 'name': 'Morning Alarm', 'hour': 8, 'minute': 0, 'enabled': True}
        ]
        sensor_data_ref = {'temperature': 22.5, 'humidity': 45.0, 'sensor_available': True}
        
        # Cycle through screens
        for i in range(4):
            current_screen = i
            print(f"Showing screen {i}...")
            update_display()
            time.sleep(3)
        
        print("Test complete")
    else:
        print("Failed to initialize display")

