# Security System Testing Guide

## Overview

This guide will help you test each security module individually before full integration.

## Prerequisites

### Hardware Checklist
- [ ] Raspberry Pi 4 (connected and powered)
- [ ] Pimoroni Pan-Tilt HAT (installed on GPIO)
- [ ] Raspberry Pi Camera Module (connected to camera port)
- [ ] Google Coral USB Accelerator (plugged into USB port)
- [ ] Flipper Zero (connected via USB with garage signal recorded)

### Software Requirements
- [ ] Raspberry Pi OS installed
- [ ] Python 3.9+ installed
- [ ] Git repository cloned to `/home/user/homepi`

## Step 1: Run Setup Script

On your Raspberry Pi, run the setup script to install all dependencies:

```bash
cd ~/homepi
sudo bash setup-security.sh
```

This will:
- Install system dependencies
- Enable I2C and camera
- Install Coral TPU libraries
- Install Python packages
- Download detection model
- Test hardware connections

**⚠️ REBOOT REQUIRED** after setup completes!

```bash
sudo reboot
```

## Step 2: Test Individual Modules

After reboot, run the testing script:

```bash
cd ~/homepi
python3 test_security_modules.py
```

### Interactive Testing Menu

The script provides an interactive menu to test each module:

```
Select test to run:
1. Camera Manager
2. Pan-Tilt HAT
3. Object Detector (Coral TPU)
4. Flipper Zero
5. Telegram Notifier
6. Run all tests
0. Exit
```

## Module Testing Details

### Test 1: Camera Manager

**What it tests:**
- Camera initialization
- Frame capture
- Snapshot saving
- Video recording (3 seconds)

**Expected output:**
```
✓ Camera initialized successfully
✓ Frame captured: (1080, 1920, 3)
✓ Snapshot saved: detections/snapshot_20241012_143022.jpg
✓ Recording started: recordings/recording_20241012_143025.h264
✓ Recording saved: recordings/recording_20241012_143028.h264
```

**Troubleshooting:**
- **Error: "Camera module not available"**
  - Check camera cable connection
  - Ensure camera enabled in `/boot/config.txt`
  - Run `libcamera-hello --list-cameras`

- **Error: "Failed to capture frame"**
  - Camera may be in use by another process
  - Restart: `sudo systemctl restart homepi`

### Test 2: Pan-Tilt HAT

**What it tests:**
- Servo initialization
- Pan left/right movements
- Tilt up/down movements
- Home position return
- Optional: Patrol mode

**Expected output:**
```
✓ Pan-Tilt initialized successfully
ℹ Current position: {'pan': 0, 'tilt': 0}
✓ Pan left complete
✓ Pan right complete
✓ Tilt up complete
✓ Tilt down complete
✓ Home position reached
```

**Troubleshooting:**
- **Error: "Pan-Tilt HAT not available"**
  - Check HAT is properly seated on GPIO pins
  - Run `i2cdetect -y 1` to verify I2C devices
  - Should see address `0x15` (PCA9685)

- **Servos not moving:**
  - Check power supply (HAT needs 5V, 2A+)
  - Verify servos connected to correct channels
  - Check servo cables not reversed

### Test 3: Object Detector (Coral TPU)

**What it tests:**
- Coral TPU initialization
- Model loading
- Inference speed
- Object detection on test image
- Detection filtering

**Expected output:**
```
✓ Detector initialized successfully
✓ Detection completed in 15.3ms
ℹ Found 3 objects
  - person: 0.89
  - car: 0.76
  - bicycle: 0.62
```

**Troubleshooting:**
- **Error: "Model file not found"**
  - Run setup script to download model
  - Or manually: `cd models && wget https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite`

- **Error: "Coral TPU not available"**
  - Check USB connection: `lsusb | grep Google`
  - Reinstall libraries: `sudo apt-get install --reinstall libedgetpu1-std`
  - Try different USB port

- **Slow inference (>50ms):**
  - Model may not be compiled for EdgeTPU
  - Check filename ends with `_edgetpu.tflite`
  - CPU fallback mode (slow but works)

### Test 4: Flipper Zero

**What it tests:**
- USB serial connection
- Command sending
- Device communication
- Optional: Garage door signal

**Expected output:**
```
✓ Flipper connected on /dev/ttyACM1
✓ Flipper is responding
✓ Garage command sent successfully
```

**Troubleshooting:**
- **Error: "Could not connect to Flipper Zero"**
  - Check USB connection
  - Verify port: `ls /dev/ttyACM*`
  - Check permissions: `sudo usermod -a -G dialout $USER`
  - Log out and back in for group changes

- **Flipper not responding:**
  - Disconnect qFlipper if running
  - Restart Flipper: Hold ← + ↓ for 10 seconds
  - Try different USB cable

- **Garage command failed:**
  - Ensure signal recorded to `/ext/subghz/garage_open.sub`
  - Test signal manually in Flipper app first
  - Check signal file path in command

### Test 5: Telegram Notifier

**What it tests:**
- Bot initialization
- Text message sending
- Photo sending
- Connection to Telegram API

**Setup required:**
1. Create bot with [@BotFather](https://t.me/BotFather)
   - Send `/newbot`
   - Choose name and username
   - Copy bot token

2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
   - Start chat
   - Copy your ID

3. Add to `config.json`:
   ```json
   "notifications": {
     "telegram_enabled": true,
     "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
     "telegram_chat_id": "YOUR_CHAT_ID_HERE"
   }
   ```

**Expected output:**
```
✓ Telegram bot initialized
✓ Test notification sent
✓ Test photo sent
ℹ Check your Telegram app for messages!
```

**Troubleshooting:**
- **Error: "Telegram not configured"**
  - Add credentials to `config.json`
  - Or enter manually when prompted

- **Error: "Bot initialization failed"**
  - Verify bot token is correct
  - Check internet connection
  - Try sending test message to bot first

- **No messages received:**
  - Verify chat ID is correct
  - Start conversation with bot first
  - Check bot is not blocked

## Step 3: Verify All Tests Pass

After testing all modules, verify results:

```
Test Summary
============
✓ Camera Manager: PASSED
✓ Pan-Tilt HAT: PASSED
✓ Object Detector (Coral TPU): PASSED
✓ Flipper Zero: PASSED
✓ Telegram Notifier: PASSED

Total: 5 | Passed: 5 | Failed: 0 | Skipped: 0

All tests passed! Ready for integration.
```

## Common Issues

### Permission Errors

If you get permission errors:

```bash
# Add user to required groups
sudo usermod -a -G video $USER
sudo usermod -a -G i2c $USER
sudo usermod -a -G dialout $USER
sudo usermod -a -G plugdev $USER

# Log out and back in for changes to take effect
```

### Module Import Errors

If Python modules can't be imported:

```bash
# Check virtual environment
source venv/bin/activate

# Or reinstall dependencies
pip install -r requirements.txt
```

### Hardware Not Detected

```bash
# Check camera
libcamera-hello --list-cameras

# Check I2C devices
i2cdetect -y 1

# Check USB devices
lsusb

# Check serial ports
ls -l /dev/ttyACM*
```

## Next Steps

Once all tests pass:

1. **Configure Telegram** (if not done):
   - Add bot token and chat ID to `config.json`

2. **Record Garage Signal** (if not done):
   - Use Flipper to read garage door remote
   - Save to `/ext/subghz/garage_open.sub`

3. **Test Full Integration**:
   - Continue to next phase: security_manager.py
   - Run complete detection pipeline
   - Test automation flow

4. **Train Car Model** (optional):
   - Follow training guide on laptop
   - Transfer model to Pi
   - Test car recognition

## Support

If tests fail:

1. Check hardware connections
2. Review troubleshooting section
3. Check logs: `sudo journalctl -u homepi.service -f`
4. Verify all dependencies installed
5. Ensure proper permissions

## Hardware Status Checklist

Before proceeding, verify:

- [ ] Camera: Captures frames successfully
- [ ] Pan-Tilt: Moves in all directions smoothly
- [ ] Coral TPU: Inference under 20ms
- [ ] Flipper Zero: Connects and responds
- [ ] Telegram: Messages received in app

**If all checkboxes are checked, you're ready for full integration!** ✓

