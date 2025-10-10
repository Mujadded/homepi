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
current_brightness = 5  # Brightness level 1-8 (8 different levels)
showing_control_overlay = False
control_overlay_type = None  # 'brightness' or 'volume'
control_overlay_time = 0
control_value = 0

# Shared state from main app
playback_state = {
    'playing': False,
    'current_song': None,
    'position': 0,
    'duration': 0
}

schedules_data = []
sensor_data_ref = None
volume_callback = None  # Callback to set volume in main app


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
            display.rotation = 180  # Rotate display 180 degrees
            display.clear()
            # Set initial brightness (will be controlled by apply_brightness)
            
            print("✓ Sense HAT LED matrix initialized (8x8, rotated 180°)")
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
    """Screen 1: Hourglass showing actual countdown to next song"""
    global display
    
    next_schedule, countdown = get_next_schedule()
    display.clear()
    
    if next_schedule and countdown:
        import time
        
        # Parse countdown
        parts = countdown.split(':')
        if len(parts) >= 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            total_minutes = hours * 60 + minutes
            
            # Animate sand falling - pulsing effect
            pulse = (int(time.time() * 3) % 10) / 10.0
            
            # Hourglass outline
            outline = [
                [1,1,1,1,1,1,1,1],  # Top rim
                [0,1,1,1,1,1,1,0],  # Top funnel
                [0,0,1,1,1,1,0,0],
                [0,0,0,1,1,0,0,0],  # Narrow middle
                [0,0,1,1,1,1,0,0],
                [0,1,1,1,1,1,1,0],  # Bottom funnel
                [1,1,1,1,1,1,1,1],  # Bottom rim
                [0,0,0,0,0,0,0,0]
            ]
            
            # Calculate how full bottom chamber should be based on time remaining
            # More time = more sand in top, less time = more sand in bottom
            max_time = 120  # 2 hours max for scale
            time_ratio = min(1.0, total_minutes / max_time)
            
            # Bottom chamber sand level (inverted - less time = more sand)
            bottom_fill = int((1.0 - time_ratio) * 4)  # 0-4 rows of sand in bottom
            
            # Top chamber sand level
            top_fill = int(time_ratio * 3)  # 0-3 rows of sand in top
            
            # Color based on urgency
            if total_minutes < 10:
                sand_color = (255, 50, 0)  # Bright red - urgent!
                glow = int(pulse * 200)
                outline_color = (255, glow, 0)
            elif total_minutes < 30:
                sand_color = (255, 150, 0)  # Orange
                outline_color = (200, 150, 50)
            else:
                sand_color = (100, 200, 255)  # Blue - plenty of time
                outline_color = (50, 100, 150)
            
            # Draw hourglass outline
            for y in range(8):
                for x in range(8):
                    if outline[y][x]:
                        display.set_pixel(x, y, *outline_color)
            
            # Draw sand in top chamber (rows 1-2)
            if top_fill >= 1:
                for x in range(2, 6):
                    display.set_pixel(x, 1, *sand_color)
            if top_fill >= 2:
                for x in range(3, 5):
                    display.set_pixel(x, 2, *sand_color)
            
            # Draw sand falling through middle (animated)
            if int(time.time() * 2) % 2 == 0:
                display.set_pixel(3, 3, *sand_color)
                display.set_pixel(4, 3, *sand_color)
            
            # Draw sand in bottom chamber (rows 5-6)
            bottom_rows = [
                [(1,6), (2,6), (3,6), (4,6), (5,6), (6,6)],  # Bottom row
                [(2,5), (3,5), (4,5), (5,5)],  # Second from bottom
                [(2,5), (3,5), (4,5), (5,5)],  # Third from bottom
                [(3,4), (4,4)]  # Fourth from bottom
            ]
            
            for i in range(min(bottom_fill, len(bottom_rows))):
                for x, y in bottom_rows[i]:
                    display.set_pixel(x, y, *sand_color)
    else:
        # Checkmark - no schedules
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
    """Screen 2: Music visualizer + progress bar when playing"""
    global display, playback_state
    display.clear()
    
    if playback_state.get('playing'):
        import time
        
        # Get progress (position/duration)
        position = playback_state.get('position', 0)
        duration = playback_state.get('duration', 1)
        progress = min(1.0, position / duration) if duration > 0 else 0
        
        # Top 6 rows: Animated visualizer bars
        beat_time = time.time() * 4  # Animation speed
        
        for x in range(8):
            # Each column bounces at different frequency
            height = 3 + int(2 * abs(math.sin(beat_time + x * 0.7)))
            
            for y in range(6):
                if y >= (6 - height):
                    # Color gradient from bottom (green) to top (red)
                    if y >= 4:
                        display.set_pixel(x, y, 0, 200, 50)  # Green bottom
                    elif y >= 2:
                        display.set_pixel(x, y, 200, 200, 0)  # Yellow middle
                    else:
                        display.set_pixel(x, y, 255, 100, 0)  # Orange top
        
        # Row 7 (bottom): Progress bar
        progress_pixels = int(progress * 8)
        for x in range(8):
            if x < progress_pixels:
                display.set_pixel(x, 7, 0, 150, 255)  # Blue progress
            else:
                display.set_pixel(x, 7, 30, 30, 30)  # Dark gray remaining
    else:
        # Not playing - show pause icon
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


def render_sense_hat_temperature():
    """Screen 3: Heart colored by temperature (blue=cold, red=hot)"""
    global display, sensor_data_ref
    display.clear()
    
    if sensor_data_ref and sensor_data_ref.get('sensor_available'):
        temp = sensor_data_ref.get('temperature')
        
        if temp:
            import time
            pulse = int(abs(math.sin(time.time() * 2)) * 128) + 127
            
            # Heart shape
            heart = [
                [0,1,1,0,0,1,1,0],
                [1,1,1,1,1,1,1,1],
                [1,1,1,1,1,1,1,1],
                [1,1,1,1,1,1,1,1],
                [0,1,1,1,1,1,1,0],
                [0,0,1,1,1,1,0,0],
                [0,0,0,1,1,0,0,0],
                [0,0,0,0,0,0,0,0]
            ]
            
            # Temperature-based color
            if temp < 16:
                # Very cold - bright blue
                heart_color = (0, 100, pulse)
            elif temp < 18:
                # Cold - light blue
                heart_color = (0, pulse // 2, pulse)
            elif temp < 22:
                # Cool - cyan
                heart_color = (0, pulse, pulse)
            elif temp < 26:
                # Comfortable - green/yellow
                heart_color = (pulse // 2, pulse, 0)
            elif temp < 28:
                # Warm - orange
                heart_color = (pulse, pulse // 2, 0)
            else:
                # Hot - red
                heart_color = (pulse, 0, 0)
            
            # Draw pulsing heart
            for y in range(8):
                for x in range(8):
                    if heart[y][x]:
                        display.set_pixel(x, y, *heart_color)
    else:
        display.clear()


def render_sense_hat_humidity():
    """Screen 4: Water droplet filling up based on humidity"""
    global display, sensor_data_ref
    display.clear()
    
    if sensor_data_ref and sensor_data_ref.get('sensor_available'):
        humidity = sensor_data_ref.get('humidity')
        
        if humidity:
            # Droplet shape with fill levels (bottom to top)
            droplet = [
                [0,0,0,1,1,0,0,0],  # Row 0 (top point)
                [0,0,1,1,1,1,0,0],  # Row 1
                [0,1,1,1,1,1,1,0],  # Row 2
                [0,1,1,1,1,1,1,0],  # Row 3
                [1,1,1,1,1,1,1,1],  # Row 4
                [1,1,1,1,1,1,1,1],  # Row 5
                [0,1,1,1,1,1,1,0],  # Row 6
                [0,0,1,1,1,1,0,0]   # Row 7 (bottom)
            ]
            
            # Calculate fill level (0-8 based on humidity 0-100%)
            fill_level = int((humidity / 100) * 8)
            
            # Draw droplet with fill
            for y in range(8):
                for x in range(8):
                    if droplet[y][x]:
                        # Fill from bottom up
                        if y >= (8 - fill_level):
                            # Filled part - bright blue
                            display.set_pixel(x, y, 0, 150, 255)
                        else:
                            # Empty part - dim outline
                            display.set_pixel(x, y, 0, 30, 60)
    else:
        display.clear()




def apply_brightness():
    """Apply current brightness level to display by dimming all pixels"""
    global display, current_brightness
    
    if not display or not display_enabled:
        return
    
    display_type = display_config.get('type', 'ssd1306')
    if display_type != 'sense_hat':
        return
    
    # Get current pixels
    pixels = display.get_pixels()
    
    # Calculate brightness multiplier (1-8 maps to 0.1-1.0)
    brightness_multiplier = current_brightness / 8.0
    
    # Apply brightness to all pixels
    new_pixels = []
    for pixel in pixels:
        r, g, b = pixel
        new_r = int(r * brightness_multiplier)
        new_g = int(g * brightness_multiplier)
        new_b = int(b * brightness_multiplier)
        new_pixels.append((new_r, new_g, new_b))
    
    display.set_pixels(new_pixels)


def render_brightness_overlay(brightness_level):
    """Show brightness control overlay with sun icon"""
    global display
    display.clear()
    
    # Sun icon in center
    sun = [
        [0,0,0,1,1,0,0,0],
        [0,1,0,1,1,0,1,0],
        [0,0,1,1,1,1,0,0],
        [1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1],
        [0,0,1,1,1,1,0,0],
        [0,1,0,1,1,0,1,0],
        [0,0,0,1,1,0,0,0]
    ]
    
    # Draw sun - brightness affects the sun brightness
    sun_brightness = int((brightness_level / 8) * 255)
    for y in range(7):  # Don't draw on bottom row
        for x in range(8):
            if sun[y][x]:
                display.set_pixel(x, y, sun_brightness, sun_brightness, 0)
    
    # Bottom row shows level (1-8 pixels)
    for x in range(8):
        if x < brightness_level:
            display.set_pixel(x, 7, 255, 200, 0)


def render_volume_overlay(volume_percent):
    """Show volume control overlay with speaker icon"""
    global display
    display.clear()
    
    # Speaker icon
    speaker = [
        [0,0,0,0,1,0,0,1],
        [0,0,1,0,1,0,1,0],
        [0,1,1,1,1,1,0,0],
        [0,1,1,1,1,1,1,0],
        [0,1,1,1,1,1,1,0],
        [0,1,1,1,1,1,0,0],
        [0,0,1,0,1,0,1,0],
        [0,0,0,0,1,0,0,1]
    ]
    
    # Draw speaker
    for y in range(8):
        for x in range(8):
            if speaker[y][x]:
                display.set_pixel(x, y, 0, 200, 255)
    
    # Right column shows volume level
    level_pixels = int((volume_percent / 100) * 8)
    for y in range(8):
        if y >= (8 - level_pixels):
            display.set_pixel(7, y, 0, 255, 0)


def handle_joystick_events():
    """Handle joystick input for brightness and volume control"""
    global display, current_brightness, showing_control_overlay, control_overlay_type
    global control_overlay_time, control_value, volume_callback
    
    if not display or not display_enabled:
        return
    
    display_type = display_config.get('type', 'ssd1306')
    if display_type != 'sense_hat':
        return
    
    try:
        from sense_hat import SenseHat, ACTION_PRESSED
        
        # Check joystick events
        for event in display.stick.get_events():
            if event.action == ACTION_PRESSED:
                # UP/DOWN = Brightness control (8 levels: 1-8)
                if event.direction == "up":
                    # Increase brightness
                    current_brightness = min(8, current_brightness + 1)
                    
                    showing_control_overlay = True
                    control_overlay_type = 'brightness'
                    control_overlay_time = time.time()
                    control_value = current_brightness
                    
                elif event.direction == "down":
                    # Decrease brightness
                    current_brightness = max(1, current_brightness - 1)
                    
                    showing_control_overlay = True
                    control_overlay_type = 'brightness'
                    control_overlay_time = time.time()
                    control_value = current_brightness
                
                # LEFT/RIGHT = Volume control
                elif event.direction == "left":
                    # Decrease volume
                    if volume_callback:
                        current_vol = volume_callback('get')
                        new_vol = max(0, current_vol - 10)
                        volume_callback('set', new_vol)
                        
                        showing_control_overlay = True
                        control_overlay_type = 'volume'
                        control_overlay_time = time.time()
                        control_value = new_vol
                
                elif event.direction == "right":
                    # Increase volume
                    if volume_callback:
                        current_vol = volume_callback('get')
                        new_vol = min(100, current_vol + 10)
                        volume_callback('set', new_vol)
                        
                        showing_control_overlay = True
                        control_overlay_type = 'volume'
                        control_overlay_time = time.time()
                        control_value = new_vol
                
                # MIDDLE = Dismiss overlay immediately
                elif event.direction == "middle":
                    showing_control_overlay = False
    
    except Exception as e:
        pass  # Joystick not available or error


def update_display():
    """Update the display with current screen"""
    global display, current_screen, display_config, showing_control_overlay
    global control_overlay_type, control_overlay_time, control_value
    
    if not display or not display_enabled:
        return
    
    display_type = display_config.get('type', 'ssd1306')
    
    try:
        # Check for joystick input
        handle_joystick_events()
        
        # Show control overlay if active (for 2 seconds)
        if showing_control_overlay and time.time() - control_overlay_time < 2:
            if control_overlay_type == 'brightness':
                render_brightness_overlay(control_value)
            elif control_overlay_type == 'volume':
                render_volume_overlay(control_value)
            return  # Don't show normal screens while overlay is active
        else:
            showing_control_overlay = False
        
        if display_type == 'sense_hat':
            # Sense HAT LED matrix (8x8) - 4 functional screens
            if current_screen == 0:
                render_sense_hat_countdown()  # Hourglass countdown
            elif current_screen == 1:
                render_sense_hat_playing()  # Visualizer + progress
            elif current_screen == 2:
                render_sense_hat_temperature()  # Heart colored by temp
            else:
                render_sense_hat_humidity()  # Droplet filled by humidity
            
            # Apply brightness adjustment to rendered screen
            apply_brightness()
        
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


def set_volume_callback(callback):
    """Set callback function for volume control from main app"""
    global volume_callback
    volume_callback = callback


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

