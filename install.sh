#!/bin/bash

# HomePi Installation Script
# This script installs all dependencies and sets up the HomePi music scheduler

echo "======================================"
echo "  HomePi Music Scheduler Installer"
echo "======================================"
echo ""

# Check if running on Raspberry Pi or Linux
if [[ ! -f /etc/os-release ]]; then
    echo "Warning: This script is designed for Linux/Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo apt-get update

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt-get install -y python3-pip python3-dev python3-pygame ffmpeg

echo ""
echo "Step 3: Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Step 4: Creating necessary directories..."
mkdir -p songs
mkdir -p static

echo ""
echo "Step 5: Setting permissions..."
chmod +x app.py

echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "To start the application, run:"
echo "  python3 app.py"
echo ""
echo "Then open your browser and go to:"
echo "  http://localhost:5000"
echo ""
echo "To find your Raspberry Pi's IP address (for remote access):"
echo "  hostname -I"
echo ""
echo "For auto-start on boot, see the README.md file."
echo ""
echo "Enjoy your HomePi Music Scheduler!"
echo ""

