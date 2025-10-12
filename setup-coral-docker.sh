#!/bin/bash

# Setup Coral TPU Detection with Docker
# Uses Python 3.11 in container for pycoral compatibility

set -e

echo "============================================"
echo "  Coral TPU Docker Setup"
echo "============================================"
echo

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# 1. Install Docker
print_info "Checking Docker installation..."

if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker installed"
    print_warning "You need to log out and back in for Docker group to take effect"
else
    print_success "Docker already installed"
fi

# 2. Install Docker Compose
print_info "Checking Docker Compose..."

if ! command -v docker-compose &> /dev/null; then
    print_info "Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose already installed"
fi

# 3. Add user to docker group (if not already)
if ! groups | grep -q docker; then
    print_info "Adding user to docker group..."
    sudo usermod -aG docker $USER
    print_warning "Log out and back in for group changes"
fi

# 4. Create models directory
print_info "Creating models directory..."
mkdir -p ~/homepi/models
cd ~/homepi

# 5. Download detection model
MODEL_FILE="models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
if [ ! -f "$MODEL_FILE" ]; then
    print_info "Downloading object detection model..."
    cd models
    wget -q --show-progress https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
    cd ..
    print_success "Model downloaded"
else
    print_success "Model already exists"
fi

# 6. Install requests package in main venv (for detection_client)
print_info "Installing detection client dependencies..."
source venv/bin/activate
pip install requests Pillow
deactivate
print_success "Client dependencies installed"

# 7. Build Docker image
print_info "Building Coral TPU Docker image (this may take 5-10 minutes)..."
docker-compose -f docker-compose.coral.yml build
print_success "Docker image built"

# 8. Test Coral TPU access
print_info "Checking Coral TPU USB connection..."
if lsusb | grep -q "Global Unichip\|Google Inc."; then
    print_success "Coral TPU detected on USB"
else
    print_warning "Coral TPU not detected - check USB connection"
fi

# 9. Start the service
print_info "Starting Coral TPU detection service..."
docker-compose -f docker-compose.coral.yml up -d
print_success "Service started"

# Wait for service to be ready
print_info "Waiting for service to initialize..."
sleep 5

# 10. Test the service
print_info "Testing detection service..."
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    print_success "Detection service is running!"
else
    print_warning "Service health check failed - check logs:"
    print_info "  docker-compose -f docker-compose.coral.yml logs"
fi

echo
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo
print_info "Summary:"
echo "  ✓ Docker installed"
echo "  ✓ Coral TPU image built"
echo "  ✓ Detection service running on port 5001"
echo "  ✓ Detection client ready"
echo
print_info "Usage:"
echo "  # Test detection client"
echo "  python3 detection_client.py"
echo
echo "  # View service logs"
echo "  docker-compose -f docker-compose.coral.yml logs -f"
echo
echo "  # Stop service"
echo "  docker-compose -f docker-compose.coral.yml down"
echo
echo "  # Restart service"
echo "  docker-compose -f docker-compose.coral.yml restart"
echo
print_info "The main HomePi app will automatically use Docker detection"
echo "when security_manager detects the service is running."
echo

