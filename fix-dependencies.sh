#!/bin/bash
# Quick fix for Python dependencies on Raspberry Pi

echo "🔧 Installing Python dependencies for HomePi Watchdog"
echo "====================================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root"
    echo "Usage: sudo bash fix-dependencies.sh"
    exit 1
fi

echo "📦 Updating package list..."
apt-get update -qq

echo "📦 Installing system packages..."
apt-get install -y python3-psutil python3-requests curl wget htop

# Check if packages were installed successfully
if python3 -c "import psutil, requests" 2>/dev/null; then
    echo "✅ Python dependencies installed successfully via apt"
else
    echo "⚠️  Some packages not available via apt, trying pip..."
    pip3 install --break-system-packages psutil requests
fi

# Verify installation
echo "🔍 Verifying installation..."
if python3 -c "import psutil, requests; print('✅ All dependencies available')" 2>/dev/null; then
    echo ""
    echo "🎉 Installation successful!"
    echo ""
    echo "Now you can run:"
    echo "  sudo bash install-watchdog.sh"
    echo ""
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
