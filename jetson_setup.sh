#!/bin/bash

# HomePi Jetson Orin Setup Script
# Sets up AI inference server on Jetson

set -e

echo "============================================"
echo "  HomePi Jetson Inference Setup"
echo "============================================"
echo

# Check if running on Jetson
if ! command -v jetson_release &> /dev/null; then
    echo "⚠ Warning: This doesn't appear to be a Jetson device"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Update system
echo "📦 Updating system packages..."
sudo apt-get update

# 2. Install Python dependencies
echo "🐍 Installing Python packages..."
sudo apt-get install -y python3-pip python3-dev

# 3. Install PyTorch (check if already installed)
if python3 -c "import torch" 2>/dev/null; then
    echo "✓ PyTorch already installed"
    python3 -c "import torch; print(f'  Version: {torch.__version__}')"
    python3 -c "import torch; print(f'  CUDA: {torch.cuda.is_available()}')"
else
    echo "📥 Installing PyTorch for Jetson..."
    echo "⚠ This may take a few minutes..."
    
    # For JetPack 5.x and 6.x, PyTorch is available via pip
    pip3 install torch torchvision
    
    echo "✓ PyTorch installed"
fi

# 4. Install other dependencies
echo "📦 Installing Flask and dependencies..."
pip3 install flask flask-cors numpy opencv-python pillow

# 5. Create project directory
if [ ! -d "$HOME/homepi-inference" ]; then
    echo "📁 Creating project directory..."
    mkdir -p $HOME/homepi-inference
    cd $HOME/homepi-inference
else
    echo "✓ Project directory exists"
    cd $HOME/homepi-inference
fi

# 6. Copy inference server if it doesn't exist
if [ ! -f "inference_server.py" ]; then
    echo "⚠ Please copy jetson_inference_server.py to $HOME/homepi-inference/inference_server.py"
    echo "  You can use scp or copy it manually"
fi

# 7. Test imports
echo ""
echo "🧪 Testing imports..."
python3 -c "import torch; print('✓ torch')" || echo "✗ torch failed"
python3 -c "import torchvision; print('✓ torchvision')" || echo "✗ torchvision failed"
python3 -c "import flask; print('✓ flask')" || echo "✗ flask failed"
python3 -c "import cv2; print('✓ opencv')" || echo "✗ opencv failed"
python3 -c "import numpy; print('✓ numpy')" || echo "✗ numpy failed"

# 8. Create systemd service
echo ""
echo "🔧 Creating systemd service..."

cat > /tmp/homepi-inference.service << 'EOF'
[Unit]
Description=HomePi AI Inference Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/homepi-inference
ExecStart=/usr/bin/python3 $HOME/homepi-inference/inference_server.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Replace $USER and $HOME in the service file
sed -i "s/\$USER/$USER/g" /tmp/homepi-inference.service
sed -i "s|\$HOME|$HOME|g" /tmp/homepi-inference.service

sudo mv /tmp/homepi-inference.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "✓ Systemd service created"

# 9. Summary
echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Copy inference server code:"
echo "   scp jetson_inference_server.py jetson@192.168.0.105:~/homepi-inference/inference_server.py"
echo ""
echo "2. Test the server manually:"
echo "   cd ~/homepi-inference"
echo "   python3 inference_server.py"
echo ""
echo "3. If it works, enable auto-start:"
echo "   sudo systemctl enable homepi-inference.service"
echo "   sudo systemctl start homepi-inference.service"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status homepi-inference.service"
echo ""
echo "5. View logs:"
echo "   journalctl -u homepi-inference.service -f"
echo ""
echo "Server will run on: http://0.0.0.0:5001"
echo ""

