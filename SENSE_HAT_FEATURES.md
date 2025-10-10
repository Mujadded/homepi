# Sense HAT Features for HomePi

## Overview

The HomePi system now fully supports the Raspberry Pi Sense HAT with improved display visualizations and comprehensive sensor support.

## Display Improvements

### 1. Slower, More Readable Text
- **Scroll speed** changed from 0.05 to 0.08 (slower, easier to read)
- **Color-coded messages** for different states

### 2. Screen Rotation (Every 5 seconds)

#### Screen 1: Countdown Timer
- Shows time until next scheduled song
- **Hours remaining:** Shows "2h" in light blue
- **Minutes remaining:** Shows "45m" in green-blue
- **No schedule:** Shows a clock icon in dim white

#### Screen 2: Now Playing
- **When playing:** Green music note icon (8x8 pixel art)
- **When idle:** Clear/blank

#### Screen 3: Temperature & Humidity
- **Color-coded by temperature:**
  - Cold (<18°C): Blue text
  - Comfortable (18-25°C): Green text
  - Warm (>25°C): Orange/Red text
- **Format:** "22C 45%" (temperature and humidity)

#### Screen 4: Motion Visualization
- Real-time tilt detector using accelerometer
- Blue dot moves based on device orientation
- Gray center point for reference
- Tilt the Raspberry Pi to see the dot move!

## Sensor Data Available

### Environmental Sensors
- **Temperature** (°C)
- **Humidity** (%)
- **Atmospheric Pressure** (hPa)

### Motion Sensors
All available through the web interface and API:

#### 1. Orientation
- **Pitch:** Rotation around X-axis (forward/backward tilt)
- **Roll:** Rotation around Y-axis (left/right tilt)  
- **Yaw:** Rotation around Z-axis (compass direction)
- Units: Degrees (0-360°)

#### 2. Accelerometer
- **X, Y, Z acceleration**
- Measures gravity and movement
- Units: g (9.8 m/s²)
- Use cases:
  - Detect if device is moved
  - Measure vibration
  - Detect orientation

#### 3. Gyroscope
- **X, Y, Z angular velocity**
- Measures rotation speed
- Units: Degrees per second (°/s)
- Use cases:
  - Detect spinning
  - Measure rotation rate
  - Gaming controls

#### 4. Magnetometer/Compass
- **X, Y, Z magnetic field strength**
- Measures Earth's magnetic field
- Units: Microteslas (µT)
- Use cases:
  - Compass heading
  - Detect nearby magnets
  - Navigation

## Web Interface

### Main Pi HAT Status Card
Always visible at top of page:
- Countdown timer to next song (HH:MM:SS)
- Room temperature (color-coded)
- Room humidity
- Warning if HAT not detected

### Advanced Sensors Panel
Collapsible section showing:
- 📐 Orientation (Pitch, Roll, Yaw)
- ⚡ Accelerometer (X, Y, Z in g)
- 🔄 Gyroscope (X, Y, Z in °/s)
- 🧭 Compass (X, Y, Z in µT)

Updates every 30 seconds automatically.

## API Endpoint

### GET `/api/sensors`

Returns all Sense HAT sensor data:

```json
{
    "temperature": 22.5,
    "humidity": 45.3,
    "pressure": 1013.2,
    "orientation": {
        "pitch": 2.1,
        "roll": -1.5,
        "yaw": 178.3
    },
    "accelerometer": {
        "x": 0.012,
        "y": -0.003,
        "z": 0.998
    },
    "gyroscope": {
        "x": 0.125,
        "y": -0.087,
        "z": 0.045
    },
    "magnetometer": {
        "x": -12.5,
        "y": 45.2,
        "z": -23.8
    },
    "last_update": "2025-01-10T14:30:00",
    "sensor_available": true
}
```

## Potential Use Cases

### Current Implementation
1. **Environment monitoring** - Track room temperature and humidity
2. **Schedule countdown** - Visual countdown on LED matrix
3. **Motion detection** - Tilt visualization on idle screen
4. **Music visualization** - Icons showing playback state

### Future Ideas

#### 1. Gesture Controls
- Shake to skip song
- Tilt left/right for volume
- Flip upside down to stop

#### 2. Interactive Alarm
- Keep playing until device is shaken
- Snooze by tilting
- Disable by specific orientation

#### 3. Environmental Alerts
- Flash LED if too hot/cold
- Humidity warnings
- Air quality monitoring (with additional sensors)

#### 4. Motion-Triggered Actions
- Auto-pause when device moves
- Start playlist when picked up
- Location-based schedules using compass

#### 5. LED Visualizations
- Audio spectrum analyzer on 8x8 matrix
- Scrolling song lyrics
- Weather icons
- Custom patterns based on time of day

#### 6. Gaming Features
- Use as game controller
- Balance challenges
- Orientation puzzles
- Motion-based music mixing

## Configuration

Edit `config.json`:

```json
{
    "display": {
        "enabled": true,
        "type": "sense_hat",
        "rotation_interval": 5
    },
    "sensor": {
        "enabled": true,
        "type": "sense_hat",
        "read_interval": 30
    }
}
```

**Options:**
- `rotation_interval`: Seconds between LED screen changes (default: 5)
- `read_interval`: Seconds between sensor readings (default: 30)

## Tips

### Calibrating the Compass
For accurate compass readings:
```python
from sense_hat import SenseHat
sense = SenseHat()
sense.set_imu_config(True, True, True)  # Enable compass, gyro, accel
```

### Reducing LED Brightness
The LED matrix can be bright. Use:
```python
sense.low_light = True  # Already set in code
# Or manually:
sense.set_pixels([[...]], redraw=False)
```

### Motion Detection Threshold
To detect significant movement:
```python
# Check if total acceleration > threshold
accel = sensor_data['accelerometer']
total = (accel['x']**2 + accel['y']**2 + accel['z']**2)**0.5
if abs(total - 1.0) > 0.1:  # Moved!
    print("Device is moving!")
```

## Troubleshooting

### LED Matrix Too Bright
- Already set to `low_light = True`
- Can be adjusted further in code if needed

### Text Scrolling Too Fast/Slow
- Edit `scroll_speed` parameter in `display_manager.py`
- Current: 0.08 (good balance)
- Slower: increase to 0.1 or 0.12
- Faster: decrease to 0.05

### Motion Sensors Not Working
1. Check Sense HAT is properly seated
2. Restart the service
3. Verify in logs: `sudo journalctl -u homepi.service -f`
4. Look for "Sense HAT initialized"

### Orientation Seems Wrong
- The Sense HAT must be right-side up
- Pitch/Roll/Yaw are relative to how it's mounted
- Can be calibrated if needed

## Performance

- **Sensor reads:** Every 30 seconds (configurable)
- **Display updates:** Every 1 second
- **CPU impact:** ~1-2% additional
- **No impact on audio playback**

## Resources

- [Sense HAT Documentation](https://pythonhosted.org/sense-hat/)
- [Sense HAT Projects](https://projects.raspberrypi.org/en/projects/getting-started-with-the-sense-hat)
- [IMU Data Explained](https://learn.adafruit.com/adafruit-sensorlab-gyroscope-calibration)

## Summary

Your Sense HAT is now fully integrated with:
- ✅ Improved LED display with icons and slower text
- ✅ Temperature, humidity, pressure sensors
- ✅ Motion sensors (accelerometer, gyroscope, magnetometer)
- ✅ Real-time tilt visualization
- ✅ Countdown timer with color coding
- ✅ Web interface showing all sensor data
- ✅ API access to all sensors
- ✅ Graceful degradation if HAT disconnected

The system provides a rich foundation for future interactive features!

