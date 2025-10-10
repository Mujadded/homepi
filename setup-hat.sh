#!/bin/bash

# Setup script for Pi HAT with environmental sensors and OLED display
# This script enables I2C and installs required dependencies

set -e

echo "========================================="
echo "HomePi HAT Setup"
echo "========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Enable I2C
echo "📟 Enabling I2C interface..."
if command -v raspi-config &> /dev/null; then
    sudo raspi-config nonint do_i2c 0
    echo "✓ I2C enabled"
else
    echo "⚠️  raspi-config not found - please enable I2C manually"
    echo "   Run: sudo raspi-config"
    echo "   Then: Interface Options -> I2C -> Enable"
fi

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip i2c-tools libjpeg-dev zlib1g-dev

# Check if I2C is working
echo ""
echo "🔍 Checking I2C devices..."
if command -v i2cdetect &> /dev/null; then
    echo "Running i2cdetect -y 1 (this will show connected I2C devices):"
    sudo i2cdetect -y 1
    echo ""
    echo "Look for addresses like:"
    echo "  0x3C or 0x3D = SSD1306 OLED display"
    echo "  0x76 or 0x77 = BME280 sensor"
    echo ""
else
    echo "⚠️  i2c-tools not installed properly"
fi

# Install Python packages using docker-compose (if available)
echo "📚 Installing Python packages..."
if [ -f "docker-compose.yml" ]; then
    echo "Using docker-compose to install packages..."
    docker-compose exec homepi pip install adafruit-circuitpython-ssd1306 adafruit-circuitpython-bme280 Pillow RPi.GPIO
else
    echo "Using pip to install packages..."
    pip3 install adafruit-circuitpython-ssd1306 adafruit-circuitpython-bme280 Pillow RPi.GPIO
fi

# Test sensor connection
echo ""
echo "🧪 Testing sensor connection..."
python3 sensor_manager.py || echo "⚠️  Sensor test failed - check wiring and I2C address in config.json"

# Test display connection
echo ""
echo "🖥️  Testing display connection..."
python3 display_manager.py || echo "⚠️  Display test failed - check wiring and I2C address in config.json"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Check config.json and adjust I2C addresses if needed"
echo "2. Restart the HomePi service:"
echo "   sudo systemctl restart homepi.service"
echo "3. Check the logs:"
echo "   sudo journalctl -u homepi.service -f"
echo ""
echo "If sensors/display don't work:"
echo "- Verify I2C addresses with: sudo i2cdetect -y 1"
echo "- Check wiring (see HAT_SETUP.md)"
echo "- Update config.json with correct addresses"
echo ""

