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
    libatlas-base-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff5 \
    v4l-utils \
    i2c-tools \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good

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

# 4. Install Coral TPU Libraries
echo
print_info "Installing Coral TPU libraries..."

# Check if libedgetpu is already installed
if ! dpkg -l | grep -q libedgetpu1; then
    print_info "Adding Coral repository..."
    echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
    sudo apt-get update
    
    print_info "Installing libedgetpu (standard version)..."
    sudo apt-get install -y libedgetpu1-std
    print_success "Coral TPU libraries installed"
else
    print_success "Coral TPU libraries already installed"
fi

# Add udev rules for Coral TPU
if [ ! -f /etc/udev/rules.d/99-edgetpu-accelerator.rules ]; then
    print_info "Adding Coral TPU udev rules..."
    echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1a6e", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/99-edgetpu-accelerator.rules
    echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="18d1", GROUP="plugdev"' | sudo tee -a /etc/udev/rules.d/99-edgetpu-accelerator.rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    print_success "Coral TPU udev rules added"
fi

# Add user to plugdev group
sudo usermod -a -G plugdev $USER

# 5. Add user to dialout group for Flipper Zero
echo
print_info "Configuring serial port access for Flipper Zero..."
sudo usermod -a -G dialout $USER
print_success "Serial port access configured"

# 6. Install Python Dependencies
echo
print_info "Installing Python dependencies..."

if [ "$PIP_CMD" = "pip3" ]; then
    print_warning "Installing system-wide (use virtual environment for production)"
    $PIP_CMD install --break-system-packages -r requirements.txt || $PIP_CMD install -r requirements.txt
else
    $PIP_CMD install -r requirements.txt
fi

print_success "Python dependencies installed"

# 7. Create Required Directories
echo
print_info "Creating required directories..."

mkdir -p models
mkdir -p recordings
mkdir -p detections
mkdir -p backups

print_success "Directories created"

# 8. Download Detection Model
echo
print_info "Downloading object detection model..."

MODEL_FILE="models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
if [ ! -f "$MODEL_FILE" ]; then
    cd models
    wget -q --show-progress https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
    wget -q --show-progress https://github.com/google-coral/test_data/raw/master/coco_labels.txt
    cd ..
    print_success "Detection model downloaded"
else
    print_success "Detection model already exists"
fi

# 9. Test Hardware
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

# Test Coral TPU
if lsusb | grep -q "Global Unichip\|Google Inc."; then
    print_success "Coral TPU detected on USB"
else
    print_warning "Coral TPU not detected - check USB connection"
fi

# Test Flipper Zero
if ls /dev/ttyACM* &> /dev/null; then
    print_success "Serial device detected (possibly Flipper Zero)"
else
    print_warning "No serial devices detected"
fi

# 10. Summary
echo
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo
print_info "Summary:"
echo "  ✓ System dependencies installed"
echo "  ✓ I2C enabled for Pan-Tilt HAT"
echo "  ✓ Camera enabled"
echo "  ✓ Coral TPU libraries installed"
echo "  ✓ Serial access configured"
echo "  ✓ Python dependencies installed"
echo "  ✓ Directories created"
echo "  ✓ Detection model downloaded"
echo

print_warning "IMPORTANT: Reboot required for some changes to take effect"
echo
print_info "Next steps:"
echo "  1. Reboot: sudo reboot"
echo "  2. Configure Telegram in config.json (bot_token and chat_id)"
echo "  3. Record garage signal on Flipper Zero to /ext/subghz/garage_open.sub"
echo "  4. Test modules: python3 test_security_modules.py"
echo "  5. Start service: sudo systemctl restart homepi.service"
echo

read -p "Reboot now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Rebooting..."
    sudo reboot
else
    print_info "Remember to reboot before using the security system"
fi

