#!/bin/bash

# Setup Python 3.11 for Coral TPU support
# Python 3.13 doesn't support pycoral/tflite-runtime yet

set -e

echo "============================================"
echo "  Python 3.11 Setup for Coral TPU"
echo "============================================"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Install Python 3.11
print_info "Installing Python 3.11..."

if ! command -v python3.11 &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
    print_success "Python 3.11 installed"
else
    print_success "Python 3.11 already installed"
fi

# 2. Create Python 3.11 virtual environment
print_info "Creating Python 3.11 virtual environment..."

cd ~/homepi

if [ -d "venv311" ]; then
    print_warning "venv311 already exists, removing old one..."
    rm -rf venv311
fi

python3.11 -m venv venv311
print_success "Virtual environment created: venv311"

# 3. Activate and install packages
print_info "Installing Python packages in venv311..."

source venv311/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install from requirements-coral.txt (includes pycoral)
if [ -f "requirements-coral.txt" ]; then
    pip install -r requirements-coral.txt
    print_success "All packages installed including Coral TPU support"
else
    print_warning "requirements-coral.txt not found, installing manually..."
    pip install Flask Flask-CORS APScheduler yt-dlp python-dotenv psutil mutagen
    pip install adafruit-circuitpython-ssd1306 adafruit-circuitpython-bme280 RPi.GPIO
    pip install pantilthat pycoral tflite-runtime pyserial python-telegram-bot numpy
    print_success "Packages installed"
fi

# 4. Test Coral TPU availability
print_info "Testing Coral TPU availability..."

python3.11 << 'EOF'
try:
    from pycoral.adapters import common
    from pycoral.adapters import detect
    from pycoral.utils.edgetpu import make_interpreter
    print("✓ Coral TPU libraries imported successfully")
except ImportError as e:
    print(f"⚠ Warning: {e}")
    print("  This is OK if Coral TPU is not connected yet")
EOF

deactivate

# 5. Create activation script
print_info "Creating activation script..."

cat > activate-venv311.sh << 'ACTIVATESCRIPT'
#!/bin/bash
# Activate Python 3.11 environment for Coral TPU
source ~/homepi/venv311/bin/activate
echo "✓ Python 3.11 venv activated (Coral TPU support)"
echo "Python version: $(python --version)"
ACTIVATESCRIPT

chmod +x activate-venv311.sh
print_success "Created activate-venv311.sh"

# 6. Update homepi.service to use Python 3.11
print_info "Updating systemd service to use Python 3.11..."

if [ -f "/etc/systemd/system/homepi.service" ]; then
    # Backup original
    sudo cp /etc/systemd/system/homepi.service /etc/systemd/system/homepi.service.bak
    
    # Update ExecStart to use venv311
    sudo sed -i 's|venv/bin/python3|venv311/bin/python3|g' /etc/systemd/system/homepi.service
    
    sudo systemctl daemon-reload
    print_success "Service updated to use Python 3.11"
else
    print_warning "homepi.service not found, will need manual update"
fi

echo
echo "============================================"
echo "  Python 3.11 Setup Complete!"
echo "============================================"
echo
print_info "Summary:"
echo "  ✓ Python 3.11 installed"
echo "  ✓ Virtual environment created: ~/homepi/venv311"
echo "  ✓ All packages installed (including Coral TPU)"
echo "  ✓ Activation script created"
echo "  ✓ Service updated"
echo
print_info "Usage:"
echo "  1. Activate venv: source ~/homepi/activate-venv311.sh"
echo "  2. Or use directly: ~/homepi/venv311/bin/python3"
echo "  3. Test modules: python3 test_security_modules.py"
echo "  4. Restart service: sudo systemctl restart homepi.service"
echo

