#!/bin/bash

# Update yt-dlp to the latest version
# Run this if YouTube downloads are failing

echo "Updating yt-dlp to the latest version..."

if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: bash install.sh first"
    exit 1
fi

./venv/bin/pip install --upgrade yt-dlp

echo ""
echo "✅ yt-dlp updated successfully!"
echo ""
echo "YouTube frequently changes their API, so you may need to run this"
echo "script occasionally if downloads start failing."
echo ""

