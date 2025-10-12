#!/bin/bash

# HomePi Jetson Docker Setup
# Easy setup for inference server using NVIDIA PyTorch container

set -e

echo "============================================"
echo "  HomePi Jetson Docker Setup"
echo "============================================"
echo

# 1. Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io
    echo "✓ Docker installed"
else
    echo "✓ Docker already installed"
fi

# 2. Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing docker-compose..."
    sudo apt-get install -y docker-compose
    echo "✓ docker-compose installed"
else
    echo "✓ docker-compose already installed"
fi

# 3. Add user to docker group
echo "👤 Adding user to docker group..."
sudo usermod -aG docker $USER
echo "✓ User added to docker group"

# 4. Check NVIDIA Container Toolkit
if ! dpkg -l | grep -q nvidia-container-toolkit; then
    echo "📦 Installing NVIDIA Container Toolkit..."
    
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    
    echo "✓ NVIDIA Container Toolkit installed"
else
    echo "✓ NVIDIA Container Toolkit already installed"
fi

# 5. Enable Docker to start on boot
echo "🔧 Enabling Docker auto-start..."
sudo systemctl enable docker
echo "✓ Docker will start on boot"

# 6. Create project directory
if [ ! -d "$HOME/homepi" ]; then
    echo "📁 Creating project directory..."
    mkdir -p $HOME/homepi
else
    echo "✓ Project directory exists"
fi

# 7. Test Docker
echo ""
echo "🧪 Testing Docker..."
if docker ps &> /dev/null; then
    echo "✓ Docker is working"
else
    echo "⚠ Docker not accessible - you may need to log out and back in"
    echo "  Or run: newgrp docker"
fi

# 8. Test NVIDIA runtime
echo ""
echo "🧪 Testing NVIDIA runtime..."
if docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA runtime is working"
else
    echo "⚠ NVIDIA runtime test failed - check installation"
fi

# 9. Summary
echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Copy files from Mac to Jetson:"
echo "   scp docker-compose.jetson.yml kronos@192.168.0.105:~/homepi/docker-compose.yml"
echo "   scp jetson_inference_server.py kronos@192.168.0.105:~/homepi/"
echo ""
echo "2. Pull NVIDIA PyTorch image (one-time, ~8GB):"
echo "   cd ~/homepi"
echo "   docker pull nvcr.io/nvidia/pytorch:24.09-py3"
echo ""
echo "3. Start inference server:"
echo "   docker-compose up -d"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Test from Raspberry Pi:"
echo "   python3 object_detector.py"
echo ""

# Check if we need to log out
if ! groups | grep -q docker; then
    echo "⚠ IMPORTANT: Log out and back in for docker group to take effect"
    echo "  Or run: newgrp docker"
    echo ""
fi

