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

# Make sure audio system is running (PulseAudio or PipeWire)
if systemctl --user is-active --quiet pipewire-pulse; then
    # PipeWire with PulseAudio compatibility is running
    echo "Using PipeWire audio system"
    export SDL_AUDIODRIVER=pulseaudio
elif command -v pulseaudio &> /dev/null; then
    # Start PulseAudio if needed
    if ! pulseaudio --check 2>/dev/null; then
        echo "Starting PulseAudio..."
        pulseaudio --start
        sleep 2
    fi
    export SDL_AUDIODRIVER=pulseaudio
else
    # Fallback
    export SDL_AUDIODRIVER=pulseaudio
fi

# Activate virtual environment and start the app
source venv/bin/activate
python app.py

