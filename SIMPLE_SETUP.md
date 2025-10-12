# Simple Setup - Test Modules Without Coral TPU First

Since Python 3.13 doesn't support pycoral yet, let's test everything else first!

## Quick Setup (5 minutes)

```bash
cd ~/homepi

# 1. Install working Python packages
source venv/bin/activate
pip install -r requirements.txt

# 2. Create directories
mkdir -p models recordings detections

# 3. Reboot (for I2C and camera)
sudo reboot
```

## After Reboot - Test Modules

```bash
cd ~/homepi
source venv/bin/activate

# Test camera
python3 camera_manager.py

# Test Pan-Tilt HAT
python3 pantilt_controller.py

# Test Flipper Zero (if connected)
python3 flipper_controller.py

# Test Telegram (after configuring)
python3 telegram_notifier.py
```

## Configure Telegram (Optional)

1. Create bot with @BotFather on Telegram
2. Get your chat ID from @userinfobot
3. Edit `config.json`:

```json
"notifications": {
  "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
  "telegram_chat_id": "YOUR_CHAT_ID_HERE"
}
```

## What Works Now (Python 3.13)

✅ Camera Manager - Frame capture, recording, snapshots
✅ Pan-Tilt HAT - Servo control, tracking, patrol
✅ Flipper Zero - Serial communication, garage control
✅ Telegram - Notifications, photos, videos
✅ Music Scheduler - All existing features

## What Needs Python 3.11 (Later)

⏳ Object Detection - Coral TPU (pycoral)
⏳ Car Recognition - Custom models

## For Coral TPU Support (Optional - Do Later)

Two options when you're ready:

### Option A: Wait for pycoral Python 3.13 support
Check periodically: `pip search pycoral`

### Option B: Docker with Python 3.11
We can create a Docker container with Python 3.11 just for detection

### Option C: Separate Pi for Detection
Use another Pi with Python 3.11 just for AI detection

## Test Everything Else First!

Run the test script and skip the detector test:

```bash
python3 test_security_modules.py
```

Select tests 1-5 (skip #3 - Object Detector)

## Summary

You can build 90% of the security system right now:
- ✅ Camera working and recording
- ✅ Pan-Tilt tracking movement
- ✅ Flipper Zero garage automation
- ✅ Telegram notifications with photos
- ✅ Web interface controls

The only missing piece is AI object detection, which can be:
- Added later when pycoral supports Python 3.13
- Run in a separate container
- Or use a different detection method (motion detection, etc.)

**Let's test what we have first!**

