#!/bin/bash

# HomePi Security System Setup Script
# Installs dependencies and configures hardware for security system

set -e

echo "============================================"
echo "  HomePi Security System Setup"
echo "============================================"
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    print_warning "Not running on Raspberry Pi - some features may not work"
fi

# Detect Python environment
if [ -d "venv" ]; then
    print_info "Using virtual environment"
    PYTHON_CMD="./venv/bin/python3"
    PIP_CMD="./venv/bin/pip"
elif [ -f "docker-compose.yml" ]; then
    print_info "Using Docker environment"
    PYTHON_CMD="docker-compose exec -T homepi python3"
    PIP_CMD="docker-compose exec -T homepi pip"
else
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

# 1. System Dependencies
echo
print_info "Installing system dependencies..."

sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-numpy \
    libcap-dev \
    libopenblas-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff6 \
    v4l-utils \
    i2c-tools \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    python3-opencv \
    python3-picamera2

print_success "System dependencies installed"

# 2. Enable I2C for Pan-Tilt HAT
echo
print_info "Enabling I2C for Pan-Tilt HAT..."

if ! grep -q "dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
    print_success "I2C enabled (reboot required)"
else
    print_success "I2C already enabled"
fi

# Add user to i2c group
sudo usermod -a -G i2c $USER

# 3. Enable Camera
echo
print_info "Configuring camera..."

if ! grep -q "camera_auto_detect=1" /boot/config.txt; then
    echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
    print_success "Camera enabled (reboot required)"
else
    print_success "Camera already enabled"
fi

# 4. Add user to dialout group for Flipper Zero
echo
print_info "Configuring serial port access for Flipper Zero..."
sudo usermod -a -G dialout $USER
print_success "Serial port access configured"

# 5. Install Python Dependencies
echo
print_info "Installing Python dependencies..."

if [ "$PIP_CMD" = "pip3" ]; then
    print_warning "Installing system-wide (use virtual environment for production)"
    $PIP_CMD install --break-system-packages -r requirements.txt || $PIP_CMD install -r requirements.txt
else
    $PIP_CMD install -r requirements.txt
fi

print_success "Python dependencies installed"

# 6. Create Required Directories
echo
print_info "Creating required directories..."

mkdir -p recordings
mkdir -p detections
mkdir -p backups

print_success "Directories created"

# 7. Test Hardware
echo
print_info "Testing hardware connections..."

# Test I2C
if command -v i2cdetect &> /dev/null; then
    print_info "Scanning I2C bus..."
    i2cdetect -y 1 > /tmp/i2c_scan.txt 2>&1 || true
    if grep -q "48\|60" /tmp/i2c_scan.txt; then
        print_success "Pan-Tilt HAT detected on I2C"
    else
        print_warning "Pan-Tilt HAT not detected - check connections"
    fi
fi

# Test Camera
if command -v libcamera-hello &> /dev/null; then
    print_info "Testing camera..."
    if timeout 2 libcamera-hello --list-cameras 2>&1 | grep -q "Available cameras"; then
        print_success "Camera detected"
    else
        print_warning "Camera not detected - check connections"
    fi
fi

# Test Flipper Zero
if ls /dev/ttyACM* &> /dev/null; then
    print_success "Serial device detected (possibly Flipper Zero)"
else
    print_warning "No serial devices detected"
fi

# 8. Summary
echo
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo
print_info "Summary:"
echo "  ✓ System dependencies installed"
echo "  ✓ I2C enabled for Pan-Tilt HAT"
echo "  ✓ Camera enabled"
echo "  ✓ Serial access configured"
echo "  ✓ Python dependencies installed"
echo "  ✓ Directories created"
echo

print_warning "IMPORTANT: Reboot required for some changes to take effect"
echo
print_info "Next steps:"
echo "  1. Reboot: sudo reboot"
echo "  2. Set up Jetson Orin AI inference server (see JETSON_SETUP.md)"
echo "  3. Configure Jetson URL in config.json (detection.remote_url)"
echo "  4. Configure Telegram in config.json (bot_token and chat_id)"
echo "  5. Record garage signal on Flipper Zero to /ext/subghz/garage_open.sub"
echo "  6. Test modules: python3 test_security_modules.py"
echo "  7. Start service: sudo systemctl restart homepi.service"
echo

read -p "Reboot now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Rebooting..."
    sudo reboot
else
    print_info "Remember to reboot before using the security system"
fi
