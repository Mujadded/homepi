#!/bin/bash

################################################################################
# HomePi Bluetooth Speaker Setup - All-in-One Script
# This script handles everything: connection, pairing, audio routing
# Works with both PulseAudio and PipeWire
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "════════════════════════════════════════════════════════════"
echo "  🔊 HomePi Bluetooth Speaker Setup - All-in-One"
echo "════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo ""

# Function to print colored messages
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run as root. Run as regular user (e.g., pi or mujadded)"
    exit 1
fi

################################################################################
# STEP 1: Install Required Packages
################################################################################

echo -e "${BLUE}━━━ Step 1: Installing Required Packages ━━━${NC}"
echo ""

# Check and install Bluetooth
if ! command -v bluetoothctl &> /dev/null; then
    print_info "Installing Bluetooth packages..."
    sudo apt-get update
    sudo apt-get install -y bluetooth bluez
else
    print_success "Bluetooth packages already installed"
fi

# Detect audio system and install appropriate packages
if systemctl --user is-active --quiet pipewire 2>/dev/null || systemctl is-active --quiet pipewire 2>/dev/null; then
    AUDIO_SYSTEM="pipewire"
    print_info "Detected PipeWire audio system"
    print_info "Installing PipeWire components..."
    sudo apt-get install -y pipewire pipewire-pulse wireplumber
else
    AUDIO_SYSTEM="pulseaudio"
    print_info "Detected PulseAudio system"
    print_info "Installing PulseAudio components..."
    sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth
fi

print_success "Audio system: $AUDIO_SYSTEM"
echo ""

################################################################################
# STEP 2: Prepare Bluetooth Service
################################################################################

echo -e "${BLUE}━━━ Step 2: Preparing Bluetooth Service ━━━${NC}"
echo ""

# Unblock Bluetooth
print_info "Unblocking Bluetooth..."
sudo rfkill unblock bluetooth
sleep 1

# Restart Bluetooth service
print_info "Restarting Bluetooth service..."
sudo systemctl restart bluetooth
sleep 2

# Start/restart audio system
if [ "$AUDIO_SYSTEM" = "pipewire" ]; then
    print_info "Restarting PipeWire..."
    systemctl --user restart pipewire pipewire-pulse wireplumber 2>/dev/null || true
    sleep 3
else
    print_info "Restarting PulseAudio..."
    pulseaudio --kill 2>/dev/null || true
    sleep 2
    pulseaudio --start
    sleep 2
fi

print_success "Audio and Bluetooth services ready"
echo ""

################################################################################
# STEP 3: Connect Bluetooth Speaker
################################################################################

echo -e "${BLUE}━━━ Step 3: Connecting Bluetooth Speaker ━━━${NC}"
echo ""

# Check if any speaker is already connected
print_info "Checking for already connected speakers..."
CONNECTED_MAC=$(bluetoothctl devices Connected 2>/dev/null | grep "Device" | awk '{print $2}' | head -1)

if [ -n "$CONNECTED_MAC" ]; then
    DEVICE_NAME=$(bluetoothctl info "$CONNECTED_MAC" | grep "Name:" | cut -d: -f2- | xargs)
    print_success "Found already connected speaker: $DEVICE_NAME ($CONNECTED_MAC)"
    echo ""
    echo "Options:"
    echo "  1) Use this connected speaker"
    echo "  2) Disconnect and scan for a different speaker"
    echo ""
    read -p "Enter choice (1 or 2): " CHOICE
    echo ""
    
    if [ "$CHOICE" = "1" ]; then
        SPEAKER_MAC="$CONNECTED_MAC"
        print_success "Using connected speaker!"
        CHOICE="skip_scan"
    else
        print_info "Disconnecting current speaker..."
        bluetoothctl disconnect "$CONNECTED_MAC"
        sleep 2
        CHOICE="2"
    fi
else
    # Check if a speaker MAC is already saved
    SAVED_MAC=""
    if [ -f ~/.homepi_bluetooth_speaker ]; then
        SAVED_MAC=$(cat ~/.homepi_bluetooth_speaker)
        print_info "Found previously paired speaker: $SAVED_MAC"
        echo ""
        echo "Options:"
        echo "  1) Connect to saved speaker ($SAVED_MAC)"
        echo "  2) Scan for new speaker"
        echo ""
        read -p "Enter choice (1 or 2): " CHOICE
        echo ""
        
        if [ "$CHOICE" = "1" ]; then
            SPEAKER_MAC="$SAVED_MAC"
            print_info "Connecting to $SPEAKER_MAC..."
            
            # Try to connect
            if echo -e "connect $SPEAKER_MAC\nquit" | bluetoothctl | grep -q "Connection successful"; then
                print_success "Connected to saved speaker!"
            else
                print_warning "Connection failed. Will try pairing..."
                echo -e "pair $SPEAKER_MAC\ntrust $SPEAKER_MAC\nconnect $SPEAKER_MAC\nquit" | bluetoothctl
            fi
            CHOICE="skip_scan"
        else
            CHOICE="2"
        fi
    else
        CHOICE="2"
    fi
fi

# Scan for new speaker
if [ "$CHOICE" = "2" ] || [ "$CHOICE" = "" ]; then
    echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  IMPORTANT: Put your Bluetooth speaker in PAIRING MODE now!${NC}"
    echo -e "${YELLOW}  (Usually: Press and hold Bluetooth button until it blinks)${NC}"
    echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
    echo ""
    read -p "Press Enter when your speaker is in pairing mode..."
    echo ""
    
    print_info "Scanning for Bluetooth devices (10 seconds)..."
    
    # Scan for devices
    TMP_FILE=$(mktemp)
    cat > "$TMP_FILE" << 'EOF'
power on
agent on
default-agent
scan on
EOF
    
    timeout 12s bluetoothctl < "$TMP_FILE" > /tmp/bt_scan.log 2>&1 &
    sleep 12
    echo "scan off" | bluetoothctl > /dev/null 2>&1
    
    echo ""
    print_success "Scan complete! Found devices:"
    echo ""
    
    # Show found devices
    DEVICE_COUNT=$(grep "Device" /tmp/bt_scan.log | grep -v "not available" | wc -l)
    
    if [ "$DEVICE_COUNT" -eq 0 ]; then
        print_error "No devices found!"
        echo ""
        echo "Troubleshooting:"
        echo "  • Make sure speaker is in pairing mode (flashing blue light)"
        echo "  • Keep speaker within 3 feet of Raspberry Pi"
        echo "  • Try turning speaker off and on again"
        echo "  • Make sure speaker isn't connected to another device"
        echo ""
        rm -f "$TMP_FILE" /tmp/bt_scan.log
        exit 1
    fi
    
    grep "Device" /tmp/bt_scan.log | grep -v "not available" | nl
    echo ""
    
    read -p "Enter the number of your speaker (1-$DEVICE_COUNT): " SELECTION
    echo ""
    
    # Validate selection
    if ! [[ "$SELECTION" =~ ^[0-9]+$ ]] || [ "$SELECTION" -lt 1 ] || [ "$SELECTION" -gt "$DEVICE_COUNT" ]; then
        print_error "Invalid selection. Please enter a number between 1 and $DEVICE_COUNT"
        rm -f "$TMP_FILE" /tmp/bt_scan.log
        exit 1
    fi
    
    # Get MAC address
    SPEAKER_MAC=$(grep "Device" /tmp/bt_scan.log | grep -v "not available" | sed -n "${SELECTION}p" | awk '{print $2}')
    
    if [ -z "$SPEAKER_MAC" ]; then
        print_error "Could not get MAC address"
        rm -f "$TMP_FILE" /tmp/bt_scan.log
        exit 1
    fi
    
    print_info "Selected speaker: $SPEAKER_MAC"
    echo ""
    
    # Pair and connect
    print_info "Pairing and connecting..."
    cat > "$TMP_FILE" << EOF
pair $SPEAKER_MAC
trust $SPEAKER_MAC
connect $SPEAKER_MAC
exit
EOF
    
    bluetoothctl < "$TMP_FILE"
    rm -f "$TMP_FILE" /tmp/bt_scan.log
    sleep 3
    
    # Save MAC for future use
    echo "$SPEAKER_MAC" > ~/.homepi_bluetooth_speaker
    print_success "Speaker MAC saved for future connections"
fi

echo ""

# Verify connection
if bluetoothctl info "$SPEAKER_MAC" 2>/dev/null | grep -q "Connected: yes"; then
    print_success "Bluetooth speaker connected!"
else
    print_error "Speaker not connected. Please try again."
    exit 1
fi

echo ""

################################################################################
# STEP 4: Configure Audio Routing
################################################################################

echo -e "${BLUE}━━━ Step 4: Configuring Audio Routing ━━━${NC}"
echo ""

sleep 2

# For PipeWire: Set A2DP profile
if [ "$AUDIO_SYSTEM" = "pipewire" ]; then
    print_info "Setting A2DP profile for high-quality audio..."
    
    # Find Bluetooth card
    BT_CARD=$(pactl list cards short | grep bluez | awk '{print $2}' | head -1)
    
    if [ -n "$BT_CARD" ]; then
        print_info "Found Bluetooth card: $BT_CARD"
        
        # Try both profile names (different PipeWire versions use different names)
        if pactl set-card-profile "$BT_CARD" a2dp-sink 2>/dev/null; then
            print_success "A2DP profile set (a2dp-sink)"
        elif pactl set-card-profile "$BT_CARD" a2dp_sink 2>/dev/null; then
            print_success "A2DP profile set (a2dp_sink)"
        else
            print_warning "Could not set A2DP profile automatically"
        fi
        
        sleep 2
    else
        print_warning "Bluetooth card not found yet, waiting..."
        sleep 3
    fi
fi

# Find Bluetooth audio sink
print_info "Looking for Bluetooth audio sink..."
BT_SINK=""
for i in {1..5}; do
    BT_SINK=$(pactl list short sinks | grep -i bluez | awk '{print $2}' | head -1)
    if [ -n "$BT_SINK" ]; then
        break
    fi
    print_info "Attempt $i/5: Waiting for sink to appear..."
    sleep 2
done

if [ -z "$BT_SINK" ]; then
    print_error "Bluetooth audio sink not found!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check connection: bluetoothctl info $SPEAKER_MAC"
    echo "2. List cards: pactl list cards"
    if [ "$AUDIO_SYSTEM" = "pipewire" ]; then
        echo "3. Set profile: pactl set-card-profile bluez_card.XX_XX_XX_XX_XX_XX a2dp-sink"
    fi
    echo ""
    exit 1
fi

print_success "Found Bluetooth sink: $BT_SINK"
echo ""

# Set as default sink
print_info "Setting Bluetooth speaker as default audio output..."
pactl set-default-sink "$BT_SINK"

# Set volume
print_info "Setting volume to 70%..."
pactl set-sink-volume "$BT_SINK" 70%

# Unmute
pactl set-sink-mute "$BT_SINK" 0

print_success "Audio routing configured!"
echo ""

################################################################################
# STEP 5: Test Audio
################################################################################

echo -e "${BLUE}━━━ Step 5: Testing Audio ━━━${NC}"
echo ""

print_info "Playing test sound..."
echo "You should hear audio from your Bluetooth speaker now..."
echo ""

# Try to play test sound
if command -v speaker-test &> /dev/null; then
    speaker-test -t wav -c 2 -l 1 2>/dev/null || true
elif [ -f /usr/share/sounds/alsa/Front_Center.wav ]; then
    aplay /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null || true
fi

echo ""
read -p "Did you hear the test sound? (y/n): " HEARD

if [ "$HEARD" = "y" ] || [ "$HEARD" = "Y" ]; then
    print_success "Great! Audio is working!"
else
    print_warning "If you didn't hear anything, check:"
    echo "  • Speaker volume (physical buttons)"
    echo "  • Speaker battery level"
    echo "  • Distance to Raspberry Pi"
fi

echo ""

################################################################################
# STEP 6: Save Configuration
################################################################################

echo -e "${BLUE}━━━ Step 6: Saving Configuration ━━━${NC}"
echo ""

# Create a reconnect script
cat > ~/reconnect-bluetooth.sh << EOF
#!/bin/bash
# Quick reconnect script for Bluetooth speaker

SPEAKER_MAC="$SPEAKER_MAC"
BT_SINK="$BT_SINK"

echo "Reconnecting to Bluetooth speaker..."
bluetoothctl connect \$SPEAKER_MAC
sleep 3

if [ "$AUDIO_SYSTEM" = "pipewire" ]; then
    BT_CARD=\$(pactl list cards short | grep bluez | awk '{print \$2}' | head -1)
    if [ -n "\$BT_CARD" ]; then
        pactl set-card-profile "\$BT_CARD" a2dp-sink 2>/dev/null || pactl set-card-profile "\$BT_CARD" a2dp_sink 2>/dev/null
        sleep 2
    fi
fi

BT_SINK=\$(pactl list short sinks | grep -i bluez | awk '{print \$2}' | head -1)
if [ -n "\$BT_SINK" ]; then
    pactl set-default-sink "\$BT_SINK"
    pactl set-sink-volume "\$BT_SINK" 70%
    echo "✅ Connected and configured!"
else
    echo "❌ Could not find Bluetooth sink"
fi
EOF

chmod +x ~/reconnect-bluetooth.sh

print_success "Created ~/reconnect-bluetooth.sh for quick reconnection"
echo ""

################################################################################
# FINAL SUMMARY
################################################################################

echo -e "${GREEN}"
echo "════════════════════════════════════════════════════════════"
echo "  🎉 Setup Complete!"
echo "════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo ""
echo "Configuration Summary:"
echo "  • Audio System: $AUDIO_SYSTEM"
echo "  • Speaker MAC: $SPEAKER_MAC"
echo "  • Audio Sink: $BT_SINK"
echo ""
echo "What's next:"
echo ""
echo "  1️⃣  Start HomePi:"
echo "      cd ~/homepi"
echo "      bash start.sh"
echo ""
echo "  2️⃣  Open web interface:"
echo "      http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "  3️⃣  To reconnect speaker later:"
echo "      ~/reconnect-bluetooth.sh"
echo ""
echo "  4️⃣  Manual connection:"
echo "      bluetoothctl connect $SPEAKER_MAC"
echo ""
echo "Quick Commands:"
echo "  • Check connection: bluetoothctl info $SPEAKER_MAC"
echo "  • Set as default: pactl set-default-sink $BT_SINK"
echo "  • Adjust volume: pactl set-sink-volume @DEFAULT_SINK@ 80%"
echo ""
echo -e "${GREEN}Enjoy your wireless music! 🎵${NC}"
echo ""

