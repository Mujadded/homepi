#!/bin/bash

# HomePi Startup Script
# This script activates the virtual environment and starts the application

cd "$(dirname "$0")"

echo "Starting HomePi Music Scheduler..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: bash install.sh"
    exit 1
fi

# Activate virtual environment and start the app
source venv/bin/activate
python app.py

