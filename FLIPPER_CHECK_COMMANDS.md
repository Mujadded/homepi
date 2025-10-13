# Flipper Zero File Check Commands

## Check if Flipper is Connected

```bash
# SSH into Raspberry Pi first
ssh mujadded@192.168.0.26

# Check if Flipper is connected via USB
ls -la /dev/ttyACM*
# Expected output: /dev/ttyACM1 (or similar)

# Check USB devices
lsusb | grep -i flipper
# Expected: Should show Flipper Zero device
```

## Connect to Flipper CLI

```bash
# Install screen if not already installed
sudo apt-get install screen -y

# Connect to Flipper Zero via serial
screen /dev/ttyACM1 115200

# You should see the Flipper CLI prompt: >:
```

## Check if garage.sub File Exists

Once connected to Flipper CLI:

```bash
# List files in /ext/subghz/ directory
storage list /ext/subghz/

# Look for garage.sub in the output
# You should see something like:
# [D] garage.sub

# Check specific file
storage stat /ext/subghz/garage.sub

# If file exists, you'll see file info
# If not, you'll see an error
```

## Alternative: Use Python Script

Create a quick test script on the Raspberry Pi:

```bash
# Create test script
cat > ~/test_flipper.py << 'EOF'
#!/usr/bin/env python3
import serial
import time

try:
    # Connect to Flipper
    flipper = serial.Serial('/dev/ttyACM1', 115200, timeout=2)
    time.sleep(2)
    
    # Clear buffers
    flipper.reset_input_buffer()
    flipper.reset_output_buffer()
    
    # Check if garage.sub exists
    command = "storage stat /ext/subghz/garage.sub\n"
    flipper.write(command.encode('utf-8'))
    flipper.flush()
    
    time.sleep(1)
    
    # Read response
    response = flipper.read(flipper.in_waiting).decode('utf-8', errors='ignore')
    print("Response:")
    print(response)
    
    if "Size:" in response:
        print("\n✓ garage.sub file exists!")
    else:
        print("\n✗ garage.sub file NOT found!")
        print("\nTo create it:")
        print("1. On Flipper: Sub-GHz app → Read → Capture your garage signal")
        print("2. Save it as 'garage' (will save to /ext/subghz/garage.sub)")
    
    flipper.close()
    
except Exception as e:
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("- Check Flipper is connected: ls /dev/ttyACM*")
    print("- Check permissions: sudo usermod -a -G dialout $USER")
    print("- Disconnect qFlipper if running")
EOF

# Make executable
chmod +x ~/test_flipper.py

# Run it
python3 ~/test_flipper.py
```

## Exit Screen Session

To exit the `screen` session with Flipper:

```bash
# Press: Ctrl+A, then D (to detach)
# Or: Ctrl+A, then K (to kill)
```

## List All Sub-GHz Files

```bash
# In Flipper CLI
storage list /ext/subghz/

# You should see all your saved Sub-GHz signals
```

## Create garage.sub if Missing

If the file doesn't exist, you need to create it on the Flipper:

### Option 1: Via Flipper UI
1. Go to **Sub-GHz** app on Flipper
2. Select **Read**
3. Point Flipper at your garage remote
4. Press the button on your garage remote
5. Flipper should capture the signal
6. Press **Save** and name it **garage**
7. It will be saved to `/ext/subghz/garage.sub`

### Option 2: Copy from Another Location
If you have the signal saved with a different name:

```bash
# In Flipper CLI
storage copy /ext/subghz/old_name.sub /ext/subghz/garage.sub
```

## Test the Signal

```bash
# In Flipper CLI

# Load the signal
subghz load /ext/subghz/garage.sub

# Transmit it (WARNING: This will actually trigger your garage!)
subghz tx

# You should see: "Transmitting..."
```

## Quick Check Script (One-liner)

```bash
# On Raspberry Pi
echo "storage stat /ext/subghz/garage.sub" | screen -S flipper /dev/ttyACM1 115200
```

## Permissions Fix

If you get permission denied:

```bash
# Add your user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in, or:
newgrp dialout

# Check permissions
ls -l /dev/ttyACM1
# Should show: crw-rw---- 1 root dialout
```

## Using HomePi's Test Script

```bash
# Navigate to homepi directory
cd ~/homepi

# Activate virtual environment
source venv/bin/activate

# Run Flipper test
python3 flipper_controller.py

# Follow the prompts to test
```

