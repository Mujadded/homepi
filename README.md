# HomePi - Raspberry Pi Music Scheduler

A beautiful, modern web-based music scheduler for Raspberry Pi that allows you to play specific songs at particular times of the day with repeat functionality.

## ✨ Features

### Music Scheduler
- 🎵 **Song Management**: Upload songs or download from YouTube
- ⏰ **Scheduling**: Schedule songs to play at specific times daily
- 🔁 **Repeat Mode**: Option to repeat songs continuously when scheduled time is reached
- 🎚️ **Volume Control**: Adjust playback volume via web interface
- 🌐 **Web Interface**: Beautiful, responsive web UI for managing everything
- 📱 **Mobile Friendly**: Works on phones, tablets, and desktops
- 🎩 **Pi HAT Support**: Optional OLED display and environmental sensors (temperature, humidity)
- ⏱️ **Countdown Display**: See time remaining until next scheduled song
- 📊 **System Monitoring**: CPU, memory, disk, temperature, and Bluetooth status

### AI Security System (Optional)
- 🎥 **Camera Surveillance**: Monitor outside with Pi Camera + Pan-Tilt HAT
- 🤖 **AI Object Detection**: Powered by remote Nvidia Jetson Orin inference
- 🚗 **Custom Car Recognition**: Train model to detect your specific car
- 📹 **Video Recording**: Automatic recording of detection events
- 🔔 **Telegram Alerts**: Instant notifications with photos/videos
- 🏠 **Garage Automation**: Auto-open via Flipper Zero when your car is detected
- 🎯 **Object Tracking**: Pan-Tilt follows detected cars and people
- 💾 **Detection Database**: SQLite database of all events

## Requirements

- Raspberry Pi (any model with audio output)
- Python 3.7 or higher
- Internet connection (for YouTube downloads)
- Audio output (3.5mm jack, HDMI, or USB speaker)

## Installation

### 1. Clone or download this project

```bash
cd /home/pi
git clone <your-repo-url> homepi
cd homepi
```

### 2. Install system dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-pygame ffmpeg
```

### 3. Install Python dependencies

```bash
pip3 install -r requirements.txt
```

### 4. Create necessary directories

```bash
mkdir -p songs
```

## Configuration

The application uses the following default settings:
- **Port**: 5000
- **Songs Directory**: `./songs`
- **Schedules File**: `./schedules.json`
- **Default Volume**: 70%

## Usage

### Start the Application

**Option 1: Using the start script (recommended)**
```bash
bash start.sh
```

**Option 2: Using virtual environment**
```bash
source venv/bin/activate
python app.py
```

**Option 3: Direct command**
```bash
./venv/bin/python app.py
```

The server will start on `http://0.0.0.0:5000`

### Access the Web Interface

On the same Raspberry Pi:
```
http://localhost:5000
```

From another device on the same network:
```
http://<raspberry-pi-ip>:5000
```

To find your Raspberry Pi's IP address:
```bash
hostname -I
```

### Managing Songs

#### Upload Songs
1. Click "Upload Song" button
2. Select an audio file (MP3, WAV, OGG, M4A)
3. Click Upload

#### Download from YouTube
1. Click "Download from YouTube" button
2. Paste a YouTube URL
3. Click Download (this may take a minute)

#### Delete Songs
- Click the trash icon (🗑️) next to any song

### Creating Schedules

1. Click "Add Schedule" button
2. Enter a name for the schedule
3. Select a song from the dropdown
4. Set the hour (0-23) and minute (0-59)
5. Check "Repeat continuously" if you want the song to loop
6. Check "Enabled" to activate the schedule
7. Click "Save Schedule"

### Playback Controls

- **Play**: Play a song immediately
- **Play & Repeat**: Play a song and loop it continuously
- **Pause**: Pause current playback
- **Resume**: Resume paused playback
- **Stop**: Stop all playback
- **Volume**: Use the slider to adjust volume (0-100%)

## 🔐 Security System Setup (Optional)

HomePi can be extended with an AI-powered security system. See detailed guides:

- **[REMOTE_AI_ARCHITECTURE.md](REMOTE_AI_ARCHITECTURE.md)** - System architecture overview
- **[JETSON_SETUP.md](JETSON_SETUP.md)** - Setting up Jetson Orin inference server
- **[MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)** - Migration guide and setup steps

### Quick Setup

1. **Install security components on Raspberry Pi:**
   ```bash
   sudo bash setup-security.sh
   ```

2. **Set up Jetson Orin inference server** (follow JETSON_SETUP.md)

3. **Configure in `config.json`:**
   ```json
   {
     "security": {
       "enabled": true,
       "detection": {
         "remote_url": "http://jetson-ip:5001"
       }
     }
   }
   ```

4. **Test modules:**
   ```bash
   python3 test_security_modules.py
   ```

### Hardware Required

- Pi Camera Module (v2 or v3)
- Pimoroni Pan-Tilt HAT
- Flipper Zero (for garage automation)
- Nvidia Jetson Orin (for AI inference)

## 🎩 Pi HAT Support (Optional)

HomePi supports optional Pi HAT hardware for enhanced functionality:

### Features

- **OLED Display**: Shows now playing, next schedule countdown, temperature/humidity
- **Environmental Sensors**: Monitor room temperature and humidity (BME280 or DHT22)
- **Countdown Timer**: Physical display of time until next scheduled song
- **Rotating Screens**: Display automatically cycles through information

### Supported Hardware

- **SSD1306 OLED Display** (128x64 or 128x32, I2C)
- **BME280 Sensor** (temperature, humidity, pressure, I2C)
- **DHT22 Sensor** (temperature, humidity, GPIO)
- **Sense HAT** (all-in-one solution)

### Quick Setup

1. Connect your Pi HAT hardware (see [HAT_SETUP.md](HAT_SETUP.md) for wiring)

2. Run the setup script:
   ```bash
   chmod +x setup-hat.sh
   ./setup-hat.sh
   ```

3. Configure your hardware in `config.json`:
   ```json
   {
       "display": {
           "enabled": true,
           "type": "ssd1306",
           "i2c_address": "0x3C",
           "width": 128,
           "height": 64,
           "rotation_interval": 5
       },
       "sensor": {
           "enabled": true,
           "type": "bme280",
           "i2c_address": "0x76",
           "read_interval": 30
       }
   }
   ```

4. Restart the service:
   ```bash
   sudo systemctl restart homepi.service
   ```

### Verify I2C Devices

Check connected I2C devices:
```bash
sudo i2cdetect -y 1
```

Look for:
- `0x3C` or `0x3D` = SSD1306 OLED display
- `0x76` or `0x77` = BME280 sensor

### Web Interface Integration

The sensor data and countdown are automatically displayed on the web interface at the top of the page, showing:
- Real-time countdown to next scheduled song
- Current room temperature
- Current room humidity
- Warning if HAT is not detected

For detailed setup instructions, wiring diagrams, and troubleshooting, see **[HAT_SETUP.md](HAT_SETUP.md)**.

## Running at Startup (Auto-start)

To make the application start automatically when your Raspberry Pi boots:

### Method 1: Using systemd (Recommended)

1. Create a service file:

```bash
sudo nano /etc/systemd/system/homepi.service
```

2. Add the following content:

```ini
[Unit]
Description=HomePi Music Scheduler
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/homepi
Environment="DISPLAY=:0"
ExecStart=/usr/bin/python3 /home/pi/homepi/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable homepi.service
sudo systemctl start homepi.service
```

4. Check status:

```bash
sudo systemctl status homepi.service
```

### Method 2: Using crontab

```bash
crontab -e
```

Add this line:
```
@reboot sleep 30 && cd /home/pi/homepi && /usr/bin/python3 app.py &
```

## Bluetooth Speaker Setup

### Initial Setup

To use a Bluetooth speaker with HomePi:

```bash
# Run the all-in-one setup script
bash setup-bluetooth.sh
```

This script handles everything automatically:
- Detects PulseAudio or PipeWire
- Scans and connects to your speaker
- Configures audio routing
- Tests the audio
- Creates quick reconnect script

### Auto-Connect on Boot

To make Bluetooth auto-connect after reboot:

```bash
# Setup auto-connect service
bash setup-bluetooth-autostart.sh

# Test it
sudo reboot
```

See also: [BLUETOOTH_SETUP.md](BLUETOOTH_SETUP.md) | [PIPEWIRE_BLUETOOTH.md](PIPEWIRE_BLUETOOTH.md)

## Troubleshooting

### No audio output

**For 3.5mm Jack / HDMI:**
1. Check audio configuration:
```bash
sudo raspi-config
# Navigate to System Options -> Audio and select your output
```

2. Test audio:
```bash
speaker-test -t wav -c 2
```

**For Bluetooth Speaker:**
1. Check if connected:
```bash
bluetoothctl info XX:XX:XX:XX:XX:XX
```

2. Set as default audio:
```bash
pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
```

3. Restart HomePi after connecting speaker

### Cannot access web interface from other devices

1. Check if the server is running:
```bash
ps aux | grep app.py
```

2. Check firewall settings (if any):
```bash
sudo ufw status
```

3. Ensure you're using the correct IP address:
```bash
hostname -I
```

### YouTube download fails (403 Forbidden)

YouTube frequently changes their API. Update yt-dlp:

```bash
# Easy way - use the update script
bash update-ytdlp.sh

# Or manually
./venv/bin/pip install --upgrade yt-dlp

# Then restart the app
```

If still failing:
```bash
# Check ffmpeg is installed
ffmpeg -version

# Make sure you're using a valid YouTube URL
# Try a different video
```

### Scheduled songs not playing

1. Check the logs when running the app
2. Verify the song file exists in the `songs` directory
3. Ensure the schedule is enabled
4. Check system time is correct:
```bash
date
```

## File Structure

```
homepi/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── .gitignore         # Git ignore rules
├── songs/             # Directory for audio files (created automatically)
├── schedules.json     # Schedule storage (created automatically)
└── static/
    └── index.html     # Web interface
```

## API Endpoints

The application provides a REST API:

### Songs
- `GET /api/songs` - List all songs
- `POST /api/songs/upload` - Upload a song
- `DELETE /api/songs/<filename>` - Delete a song
- `POST /api/songs/youtube` - Download from YouTube

### Schedules
- `GET /api/schedules` - List all schedules
- `POST /api/schedules` - Create a schedule
- `PUT /api/schedules/<id>` - Update a schedule
- `DELETE /api/schedules/<id>` - Delete a schedule

### Playback
- `POST /api/playback/play` - Play a song
- `POST /api/playback/stop` - Stop playback
- `POST /api/playback/pause` - Pause playback
- `POST /api/playback/resume` - Resume playback
- `POST /api/playback/volume` - Set volume
- `GET /api/playback/status` - Get playback status

## Security Notes

- This application is designed for local network use
- No authentication is implemented by default
- Do not expose directly to the internet without adding security measures
- Consider using a reverse proxy (nginx) with authentication for remote access

## License

MIT License - Feel free to modify and use as you wish!

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Support

For issues and questions, please create an issue on the project repository.

---

Made with ❤️ for Raspberry Pi enthusiasts

