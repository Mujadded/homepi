#!/bin/bash

# Install Python 3.11 using pyenv for Coral TPU support
# Debian Trixie doesn't have Python 3.11 in repos

set -e

echo "============================================"
echo "  Python 3.11 Setup via pyenv"
echo "============================================"
echo

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# 1. Install pyenv dependencies
print_info "Installing pyenv build dependencies..."
sudo apt-get update
sudo apt-get install -y \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev git

print_success "Dependencies installed"

# 2. Install pyenv
print_info "Installing pyenv..."
if [ ! -d "$HOME/.pyenv" ]; then
    curl https://pyenv.run | bash
    print_success "pyenv installed"
else
    print_success "pyenv already installed"
fi

# 3. Add pyenv to shell
print_info "Configuring pyenv in shell..."
if ! grep -q 'pyenv init' ~/.bashrc; then
    cat >> ~/.bashrc << 'PYENVRC'

# pyenv configuration
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
PYENVRC
    print_success "pyenv added to ~/.bashrc"
fi

# Load pyenv for this session
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# 4. Install Python 3.11
print_info "Installing Python 3.11.9 (this may take 10-15 minutes)..."
if ! pyenv versions | grep -q "3.11.9"; then
    pyenv install 3.11.9
    print_success "Python 3.11.9 installed"
else
    print_success "Python 3.11.9 already installed"
fi

# 5. Create venv with Python 3.11
print_info "Creating virtual environment with Python 3.11..."
cd ~/homepi

if [ -d "venv311" ]; then
    print_warning "Removing existing venv311..."
    rm -rf venv311
fi

pyenv local 3.11.9
python3.11 -m venv venv311
print_success "Virtual environment created"

# 6. Install packages
print_info "Installing Python packages..."
source venv311/bin/activate
pip install --upgrade pip

if [ -f "requirements-coral.txt" ]; then
    pip install -r requirements-coral.txt
else
    pip install Flask Flask-CORS APScheduler yt-dlp python-dotenv psutil mutagen
    pip install adafruit-circuitpython-ssd1306 adafruit-circuitpython-bme280 RPi.GPIO
    pip install pantilthat pycoral tflite-runtime pyserial python-telegram-bot numpy
fi

print_success "All packages installed"

# 7. Test import
print_info "Testing Coral TPU imports..."
python3.11 << 'TESTPY'
try:
    from pycoral.adapters import common
    print("✓ pycoral imported successfully")
except ImportError as e:
    print(f"⚠ {e}")
TESTPY

deactivate

# 8. Create activation script
cat > ~/homepi/activate-py311.sh << 'ACTIVATE'
#!/bin/bash
cd ~/homepi
source venv311/bin/activate
echo "✓ Python 3.11 environment activated"
python --version
ACTIVATE

chmod +x ~/homepi/activate-py311.sh
print_success "Created ~/homepi/activate-py311.sh"

# 9. Update service
if [ -f "/etc/systemd/system/homepi.service" ]; then
    sudo cp /etc/systemd/system/homepi.service /etc/systemd/system/homepi.service.bak
    sudo sed -i 's|WorkingDirectory=.*|WorkingDirectory=/home/'$USER'/homepi|g' /etc/systemd/system/homepi.service
    sudo sed -i 's|ExecStart=.*python.*|ExecStart=/home/'$USER'/homepi/venv311/bin/python3 app.py|g' /etc/systemd/system/homepi.service
    sudo systemctl daemon-reload
    print_success "Service updated"
fi

echo
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo
print_info "Usage:"
echo "  source ~/homepi/activate-py311.sh"
echo "  python3 test_security_modules.py"
echo
print_warning "Note: Open a new terminal or run 'source ~/.bashrc' for pyenv"

