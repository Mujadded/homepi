"""
Sensor Manager for Pi HAT Environmental Monitoring
Handles temperature and humidity sensor readings (BME280/DHT22)
"""

import os
import json
import time
import threading
from datetime import datetime

# Global sensor data storage
sensor_data = {
    'temperature': None,
    'humidity': None,
    'pressure': None,
    'last_update': None,
    'sensor_available': False
}

# Sensor instance
sensor = None
sensor_type = None
config = {}

def load_config():
    """Load configuration from config.json"""
    global config
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {
            'sensor': {
                'enabled': True,
                'type': 'bme280',
                'i2c_address': '0x76',
                'read_interval': 30
            }
        }
    return config.get('sensor', {})


def init_sensor():
    """Initialize the environmental sensor (BME280, DHT22, or Sense HAT)"""
    global sensor, sensor_type, sensor_data
    
    sensor_config = load_config()
    
    if not sensor_config.get('enabled', True):
        print("Sensor disabled in config")
        return False
    
    sensor_type = sensor_config.get('type', 'bme280')
    
    try:
        if sensor_type == 'sense_hat':
            # Try to initialize Sense HAT
            from sense_hat import SenseHat
            
            sensor = SenseHat()
            print("✓ Sense HAT initialized")
            sensor_data['sensor_available'] = True
            return True
            
        elif sensor_type == 'bme280':
            # Try to initialize BME280
            import board
            import adafruit_bme280.advanced as adafruit_bme280
            
            i2c = board.I2C()
            i2c_addr = int(sensor_config.get('i2c_address', '0x76'), 16)
            sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=i2c_addr)
            
            # Set oversampling for better accuracy
            sensor.sea_level_pressure = 1013.25
            sensor.mode = adafruit_bme280.MODE_NORMAL
            sensor.standby_period = adafruit_bme280.STANDBY_TC_500
            sensor.iir_filter = adafruit_bme280.IIR_FILTER_X16
            sensor.overscan_pressure = adafruit_bme280.OVERSCAN_X16
            sensor.overscan_humidity = adafruit_bme280.OVERSCAN_X1
            sensor.overscan_temperature = adafruit_bme280.OVERSCAN_X2
            
            print(f"✓ BME280 sensor initialized at address {sensor_config.get('i2c_address')}")
            sensor_data['sensor_available'] = True
            return True
            
        elif sensor_type == 'dht22':
            # Try to initialize DHT22
            import board
            import adafruit_dht
            
            sensor = adafruit_dht.DHT22(board.D4)  # GPIO4 by default
            print("✓ DHT22 sensor initialized on GPIO4")
            sensor_data['sensor_available'] = True
            return True
        
        else:
            print(f"Unknown sensor type: {sensor_type}")
            return False
            
    except ImportError as e:
        print(f"⚠ Sensor libraries not installed: {e}")
        print("  Run: pip install adafruit-circuitpython-bme280 adafruit-circuitpython-dht")
        return False
    except Exception as e:
        print(f"⚠ Could not initialize sensor: {e}")
        print("  Make sure I2C is enabled: sudo raspi-config")
        return False


def read_temperature():
    """Read temperature from sensor in Celsius"""
    global sensor, sensor_type, sensor_data
    
    if sensor is None:
        return None
    
    try:
        if sensor_type == 'sense_hat':
            temp = sensor.get_temperature()
        elif sensor_type == 'bme280':
            temp = sensor.temperature
        elif sensor_type == 'dht22':
            temp = sensor.temperature
        else:
            return None
        
        sensor_data['temperature'] = round(temp, 1)
        return sensor_data['temperature']
    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None


def read_humidity():
    """Read humidity from sensor as percentage"""
    global sensor, sensor_type, sensor_data
    
    if sensor is None:
        return None
    
    try:
        if sensor_type == 'sense_hat':
            humidity = sensor.get_humidity()
        elif sensor_type == 'bme280':
            humidity = sensor.humidity
        elif sensor_type == 'dht22':
            humidity = sensor.humidity
        else:
            return None
        
        sensor_data['humidity'] = round(humidity, 1)
        return sensor_data['humidity']
    except Exception as e:
        print(f"Error reading humidity: {e}")
        return None


def read_pressure():
    """Read atmospheric pressure from sensor in hPa"""
    global sensor, sensor_type, sensor_data
    
    if sensor is None:
        return None
    
    try:
        if sensor_type == 'sense_hat':
            pressure = sensor.get_pressure()
        elif sensor_type == 'bme280':
            pressure = sensor.pressure
        else:
            return None
        
        sensor_data['pressure'] = round(pressure, 1)
        return sensor_data['pressure']
    except Exception as e:
        print(f"Error reading pressure: {e}")
        return None


def read_all_sensors():
    """Read all sensor values and update global data"""
    global sensor_data
    
    if sensor is None:
        return sensor_data
    
    try:
        temp = read_temperature()
        humidity = read_humidity()
        pressure = read_pressure()
        
        if temp is not None or humidity is not None:
            sensor_data['last_update'] = datetime.now().isoformat()
            sensor_data['sensor_available'] = True
        
        return sensor_data
    except Exception as e:
        print(f"Error reading sensors: {e}")
        sensor_data['sensor_available'] = False
        return sensor_data


def sensor_loop():
    """Background thread loop to continuously read sensor data"""
    global sensor_data
    
    sensor_config = load_config()
    read_interval = sensor_config.get('read_interval', 30)
    
    print(f"Starting sensor loop (reading every {read_interval} seconds)...")
    
    while True:
        try:
            read_all_sensors()
            
            if sensor_data['sensor_available'] and sensor_data['temperature'] is not None:
                print(f"Sensors: {sensor_data['temperature']}°C, {sensor_data['humidity']}% RH" + 
                      (f", {sensor_data['pressure']} hPa" if sensor_data['pressure'] else ""))
        except Exception as e:
            print(f"Sensor loop error: {e}")
        
        time.sleep(read_interval)


def start_sensor_thread():
    """Start the sensor reading thread"""
    if not init_sensor():
        print("⚠ Sensor not available - running without environmental monitoring")
        return None
    
    thread = threading.Thread(target=sensor_loop, daemon=True, name="SensorThread")
    thread.start()
    print("✓ Sensor thread started")
    return thread


def get_sensor_data():
    """Get current sensor data (for API endpoint)"""
    return sensor_data.copy()


if __name__ == "__main__":
    # Test the sensor
    print("Testing sensor...")
    if init_sensor():
        print("Reading sensor data...")
        data = read_all_sensors()
        print(f"Temperature: {data['temperature']}°C")
        print(f"Humidity: {data['humidity']}%")
        if data['pressure']:
            print(f"Pressure: {data['pressure']} hPa")
    else:
        print("Failed to initialize sensor")

