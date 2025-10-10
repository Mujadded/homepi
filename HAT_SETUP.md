# Pi HAT Setup Guide

This guide explains how to set up and configure a Pi HAT with environmental sensors and OLED display for your HomePi Music Scheduler.

## Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Wiring Guide](#wiring-guide)
- [Installation](#installation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Customization](#customization)

## Hardware Requirements

### Recommended HAT Options

#### Option 1: Separate Modules (Most Flexible)
- **BME280** environmental sensor (temperature, humidity, pressure)
- **SSD1306 OLED display** (128x64 pixels, I2C)
- Both use I2C, easy to wire

**Pros:**
- Most flexible and affordable
- Easy to replace individual components
- Wide availability

**Cons:**
- Requires manual wiring

#### Option 2: Sense HAT (All-in-One)
- Complete environmental sensor suite
- 8x8 LED matrix (limited display)
- Gyroscope and accelerometer (not used)

**Pros:**
- Plug-and-play
- No wiring needed

**Cons:**
- More expensive
- 8x8 LED matrix has limited display capability compared to OLED

#### Option 3: Waveshare HATs
- Various combinations of displays and sensors
- Designed specifically for Raspberry Pi

## Wiring Guide

### I2C Pin Connections

Raspberry Pi GPIO Header has the following I2C pins:

```
Pin 1  (3.3V)     Pin 2  (5V)
Pin 3  (SDA)      Pin 4  (5V)
Pin 5  (SCL)      Pin 6  (GND)
...
```

### BME280 Sensor Wiring

| BME280 Pin | Raspberry Pi Pin | Description |
|------------|------------------|-------------|
| VCC        | Pin 1 (3.3V)     | Power       |
| GND        | Pin 6 (GND)      | Ground      |
| SCL        | Pin 5 (GPIO3)    | I2C Clock   |
| SDA        | Pin 3 (GPIO2)    | I2C Data    |

**Default I2C Address:** 0x76 or 0x77 (check your module)

### SSD1306 OLED Display Wiring

| SSD1306 Pin | Raspberry Pi Pin | Description |
|-------------|------------------|-------------|
| VCC         | Pin 1 (3.3V)     | Power       |
| GND         | Pin 6 (GND)      | Ground      |
| SCL         | Pin 5 (GPIO3)    | I2C Clock   |
| SDA         | Pin 3 (GPIO2)    | I2C Data    |

**Default I2C Address:** 0x3C or 0x3D

**Note:** Both devices share the same I2C bus (SDA and SCL), so you can wire them in parallel.

### Complete Wiring Diagram

```
Raspberry Pi GPIO Header
         ┌─────────────┐
3.3V ────┤ 1        2  ├──── 5V
SDA  ────┤ 3        4  ├──── 5V
SCL  ────┤ 5        6  ├──── GND
         └─────────────┘
           │   │    │
           │   │    └────────┐
           │   └─────────┐   │
           │             │   │
      ┌────┴────┐   ┌────┴───┴────┐
      │ BME280  │   │  SSD1306    │
      │ Sensor  │   │  Display    │
      └─────────┘   └─────────────┘
```

## Installation

### 1. Enable I2C

Run the automated setup script:

```bash
cd /path/to/homepi
chmod +x setup-hat.sh
./setup-hat.sh
```

Or manually enable I2C:

```bash
sudo raspi-config
```

Navigate to:
- **Interface Options** → **I2C** → **Enable**

Reboot:
```bash
sudo reboot
```

### 2. Verify I2C is Working

After reboot, check for I2C devices:

```bash
sudo i2cdetect -y 1
```

You should see addresses like:
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- 76 --
```

In this example:
- `3c` = SSD1306 OLED display
- `76` = BME280 sensor

### 3. Install Python Dependencies

Using pip:
```bash
pip3 install adafruit-circuitpython-ssd1306 adafruit-circuitpython-bme280 Pillow RPi.GPIO
```

Or using docker-compose (recommended):
```bash
docker-compose exec homepi pip install adafruit-circuitpython-ssd1306 adafruit-circuitpython-bme280 Pillow RPi.GPIO
```

### 4. Test Sensor

```bash
python3 sensor_manager.py
```

You should see:
```
✓ BME280 sensor initialized at address 0x76
Reading sensor data...
Temperature: 22.5°C
Humidity: 45.3%
Pressure: 1013.2 hPa
```

### 5. Test Display

```bash
python3 display_manager.py
```

The OLED display should light up and cycle through test screens.

### 6. Update Configuration

Edit `config.json` if your I2C addresses differ:

```json
{
    "display": {
        "enabled": true,
        "type": "ssd1306",
        "i2c_address": "0x3C",
        "width": 128,
        "height": 64,
        "rotation_interval": 5
    },
    "sensor": {
        "enabled": true,
        "type": "bme280",
        "i2c_address": "0x76",
        "read_interval": 30
    }
}
```

### 7. Restart HomePi Service

```bash
sudo systemctl restart homepi.service
```

Check logs:
```bash
sudo journalctl -u homepi.service -f
```

Look for:
```
🎩 Initializing Pi HAT...
✓ BME280 sensor initialized at address 0x76
✓ Environmental sensors active
✓ SSD1306 display initialized (128x64 at 0x3C)
✓ OLED display active
```

## Configuration

### Display Settings

- **enabled**: Enable/disable display (true/false)
- **type**: Display type (currently only "ssd1306")
- **i2c_address**: I2C address as hex string (e.g., "0x3C")
- **width**: Display width in pixels (128 or 64)
- **height**: Display height in pixels (64 or 32)
- **rotation_interval**: Seconds between screen rotations (default: 5)

### Sensor Settings

- **enabled**: Enable/disable sensor (true/false)
- **type**: Sensor type ("bme280" or "dht22")
- **i2c_address**: I2C address for BME280 (e.g., "0x76" or "0x77")
- **read_interval**: Seconds between sensor readings (default: 30)

## Troubleshooting

### I2C Not Detected

**Problem:** `sudo i2cdetect -y 1` shows no devices

**Solutions:**
1. Check wiring connections
2. Try `i2cdetect -y 0` (older Raspberry Pi models)
3. Verify I2C is enabled: `ls /dev/i2c*`
4. Reboot after enabling I2C

### Wrong I2C Address

**Problem:** Sensor/display not working with default address

**Solutions:**
1. Run `sudo i2cdetect -y 1` to find actual address
2. Update `config.json` with correct addresses
3. BME280 can be 0x76 or 0x77 (depends on SDO pin)
4. SSD1306 can be 0x3C or 0x3D

### Display Not Showing Anything

**Problem:** Display powers on but shows nothing

**Solutions:**
1. Check I2C address in config.json
2. Verify display dimensions (128x64 vs 128x32)
3. Try contrast adjustment in code
4. Test with: `python3 display_manager.py`

### Sensor Reading Errors

**Problem:** Sensor reads incorrect values or fails

**Solutions:**
1. Check I2C address matches your sensor
2. Verify power supply (3.3V for BME280)
3. Use shorter wires if possible (I2C issues with long wires)
4. Add pull-up resistors if needed (usually not required)

### Permission Denied Errors

**Problem:** `/dev/i2c-1: Permission denied`

**Solutions:**
1. Add user to i2c group: `sudo usermod -a -G i2c $USER`
2. Reboot or logout/login
3. Check permissions: `ls -l /dev/i2c-1`

### HAT Not Detected After Reboot

**Problem:** Works initially but fails after reboot

**Solutions:**
1. Verify I2C stays enabled after reboot
2. Check systemd service has proper permissions
3. Add I2C modules to /etc/modules if needed:
   ```bash
   echo "i2c-dev" | sudo tee -a /etc/modules
   ```

## Customization

### Changing Display Screens

Edit `display_manager.py` to customize what's shown:

```python
def display_loop():
    # Modify screen rotation
    if current_screen == 0:
        render_countdown_screen()  # Next schedule
    elif current_screen == 1:
        render_playing_screen()     # Now playing
    elif current_screen == 2:
        render_sensor_screen()      # Temp/humidity
    else:
        render_combined_screen()    # All info
```

### Adding More Sensors

To add additional sensors (e.g., DHT22):

1. Update `config.json`:
   ```json
   "sensor": {
       "type": "dht22",
       "gpio_pin": 4
   }
   ```

2. Install DHT library:
   ```bash
   pip3 install adafruit-circuitpython-dht
   ```

3. Code already supports DHT22 in `sensor_manager.py`

### Display Font Customization

Change fonts in `display_manager.py`:

```python
# Use different font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)

# Or use bitmap font
font = ImageFont.load_default()
```

### Changing Update Intervals

Modify intervals in `config.json`:

```json
{
    "display": {
        "rotation_interval": 3    // Faster screen rotation
    },
    "sensor": {
        "read_interval": 60       // Read every minute
    }
}
```

## Supported Hardware

### Tested Displays
- SSD1306 128x64 I2C OLED
- SSD1306 128x32 I2C OLED
- SH1106 128x64 I2C OLED (similar to SSD1306)

### Tested Sensors
- BME280 (temperature, humidity, pressure)
- DHT22 (temperature, humidity)
- DHT11 (temperature, humidity, lower accuracy)

## Web Interface

The Pi HAT data is displayed on the web interface at `http://your-pi-ip:5000`:

- **Pi HAT Status Card**: Shows countdown to next schedule, temperature, and humidity
- **System Status (collapsed)**: Shows additional sensor data with system metrics

The web page automatically updates sensor data every 30 seconds and countdown every second.

## Tips

1. **Power Supply**: Ensure your Pi has adequate power (2.5A minimum)
2. **Cable Length**: Keep I2C wires short (< 20cm) for reliability
3. **Pull-up Resistors**: Usually not needed, but use 4.7kΩ if you have issues
4. **Multiple Sensors**: You can connect multiple I2C devices as long as they have different addresses
5. **Testing**: Always test individual components before integrating

## Support

If you encounter issues:

1. Check the logs: `sudo journalctl -u homepi.service -f`
2. Test components individually with test scripts
3. Verify I2C connectivity with `i2cdetect`
4. Check wiring carefully
5. Consult datasheets for your specific modules

## References

- [Raspberry Pi I2C Documentation](https://www.raspberrypi.org/documentation/hardware/raspberrypi/i2c/)
- [BME280 Datasheet](https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/)
- [SSD1306 Datasheet](https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf)
- [Adafruit CircuitPython Libraries](https://circuitpython.org/libraries)

