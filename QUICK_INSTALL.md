# Quick Installation Guide

If the setup script hangs or fails, follow these manual steps:

## 1. Install Python Dependencies

```bash
cd ~/homepi
source venv/bin/activate  # If using venv
pip install picamera2 pantilthat opencv-python pyserial python-telegram-bot numpy
```

## 2. Install Coral TPU Support (Optional - can skip for now)

The pycoral package includes runtime, so you can install it later:

```bash
pip install pycoral tflite-runtime
```

Or download manually:
```bash
cd /tmp
wget https://github.com/google-coral/libedgetpu/releases/download/release-frogfish/libedgetpu1-std_16.0_arm64.deb
sudo dpkg -i libedgetpu1-std_16.0_arm64.deb
sudo apt-get install -f -y
```

## 3. Enable I2C and Camera

```bash
# Enable I2C
sudo raspi-config nonint do_i2c 0

# Enable camera  
sudo raspi-config nonint do_camera 0

# Or edit manually:
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
```

## 4. Add User to Groups

```bash
sudo usermod -a -G video $USER
sudo usermod -a -G i2c $USER  
sudo usermod -a -G dialout $USER
sudo usermod -a -G plugdev $USER
```

## 5. Create Directories

```bash
cd ~/homepi
mkdir -p models recordings detections
```

## 6. Download Detection Model

```bash
cd ~/homepi/models
wget https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
```

## 7. Reboot

```bash
sudo reboot
```

## 8. Test Modules

After reboot:

```bash
cd ~/homepi
python3 test_security_modules.py
```

## Quick Test Individual Modules

```bash
# Test camera
python3 camera_manager.py

# Test pan-tilt
python3 pantilt_controller.py

# Test detector (needs Coral TPU)
python3 object_detector.py

# Test Flipper Zero
python3 flipper_controller.py

# Test Telegram
python3 telegram_notifier.py
```

## If Setup Script Froze

Press Ctrl+C to stop it, then:

```bash
# Clean up
sudo rm -f /etc/apt/sources.list.d/coral-edgetpu.list
sudo apt-get update

# Continue manually with steps above
```
