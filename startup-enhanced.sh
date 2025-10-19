#!/bin/bash
# HomePi Enhanced Startup Script with Watchdog
# This script ensures all services start properly and stay running

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOMEPI_DIR="/home/mujadded/homepi"
SERVICE_NAME="homepi.service"
WATCHDOG_SERVICE="homepi-watchdog.service"
LOG_FILE="/var/log/homepi-startup.log"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Install required packages
install_dependencies() {
    log "Installing watchdog dependencies..."
    
    # Install Python packages
    pip3 install --upgrade psutil requests
    
    # Install system utilities if not present
    apt-get update -qq
    apt-get install -y -qq curl wget htop iotop nethogs
    
    log_success "Dependencies installed"
}

# Setup logging
setup_logging() {
    log "Setting up logging..."
    
    # Create log directory
    mkdir -p /var/log
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    # Setup logrotate for watchdog logs
    cat > /etc/logrotate.d/homepi-watchdog << EOF
/var/log/homepi-watchdog.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
    
    log_success "Logging configured"
}

# Install and enable watchdog service
install_watchdog() {
    log "Installing watchdog service..."
    
    # Copy watchdog script
    cp "$HOMEPI_DIR/homepi_watchdog.py" /usr/local/bin/
    chmod +x /usr/local/bin/homepi_watchdog.py
    
    # Copy service file
    cp "$HOMEPI_DIR/homepi-watchdog.service" /etc/systemd/system/
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$WATCHDOG_SERVICE"
    
    log_success "Watchdog service installed and enabled"
}

# Fix common system issues
fix_system_issues() {
    log "Fixing common system issues..."
    
    # Fix Bluetooth if script exists
    if [[ -f "$HOMEPI_DIR/fix-pipewire-bluetooth.sh" ]]; then
        log "Running Bluetooth fix..."
        bash "$HOMEPI_DIR/fix-pipewire-bluetooth.sh"
    fi
    
    # Ensure network interface is up
    log "Checking network interface..."
    if ! ip link show eth0 | grep -q "state UP"; then
        log_warning "Ethernet interface down, attempting to bring up..."
        ip link set eth0 up
        sleep 2
    fi
    
    # Check if we have internet connectivity
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        log_warning "No internet connectivity detected"
        # Try to restart networking
        systemctl restart networking
        sleep 5
    fi
    
    # Ensure proper permissions
    chown -R mujadded:mujadded "$HOMEPI_DIR"
    chmod +x "$HOMEPI_DIR"/*.py
    chmod +x "$HOMEPI_DIR"/*.sh
    
    # Make Bluetooth fix script executable
    if [[ -f "$HOMEPI_DIR/fix-pipewire-bluetooth.sh" ]]; then
        chmod +x "$HOMEPI_DIR/fix-pipewire-bluetooth.sh"
        log_success "Bluetooth fix script made executable"
    fi
    
    log_success "System issues fixed"
}

# Start and verify services
start_services() {
    log "Starting HomePi services..."
    
    # Start main service
    systemctl start "$SERVICE_NAME"
    sleep 5
    
    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "HomePi service started successfully"
    else
        log_error "Failed to start HomePi service"
        systemctl status "$SERVICE_NAME" --no-pager
        return 1
    fi
    
    # Start watchdog service
    systemctl start "$WATCHDOG_SERVICE"
    sleep 2
    
    if systemctl is-active --quiet "$WATCHDOG_SERVICE"; then
        log_success "Watchdog service started successfully"
    else
        log_warning "Failed to start watchdog service"
        systemctl status "$WATCHDOG_SERVICE" --no-pager
    fi
    
    # Verify web interface is accessible
    sleep 10
    if curl -s http://localhost:5000/api/health > /dev/null; then
        log_success "Web interface is accessible"
    else
        log_warning "Web interface not accessible yet"
    fi
}

# Display system status
show_status() {
    log "HomePi System Status:"
    echo "===================="
    
    # Service status
    echo "Services:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    systemctl status "$WATCHDOG_SERVICE" --no-pager -l
    echo ""
    
    # Network status
    echo "Network:"
    ip addr show eth0
    echo ""
    
    # System resources
    echo "System Resources:"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "Memory: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo "Disk: $(df -h / | awk 'NR==2{print $5}')"
    echo ""
    
    # Recent logs
    echo "Recent HomePi logs:"
    journalctl -u "$SERVICE_NAME" --no-pager -n 10
    echo ""
    
    echo "Recent Watchdog logs:"
    journalctl -u "$WATCHDOG_SERVICE" --no-pager -n 5
}

# Main function
main() {
    log "Starting HomePi Enhanced Startup Script"
    
    check_root
    install_dependencies
    setup_logging
    install_watchdog
    fix_system_issues
    start_services
    
    log_success "HomePi startup completed successfully!"
    
    # Show status
    show_status
    
    log "Watchdog will monitor the system and auto-fix issues"
    log "Check logs with: journalctl -u homepi-watchdog.service -f"
}

# Handle script arguments
case "${1:-}" in
    "status")
        show_status
        ;;
    "restart")
        log "Restarting HomePi services..."
        systemctl restart "$SERVICE_NAME"
        systemctl restart "$WATCHDOG_SERVICE"
        show_status
        ;;
    "stop")
        log "Stopping HomePi services..."
        systemctl stop "$WATCHDOG_SERVICE"
        systemctl stop "$SERVICE_NAME"
        ;;
    "logs")
        journalctl -u "$SERVICE_NAME" -u "$WATCHDOG_SERVICE" -f
        ;;
    *)
        main
        ;;
esac
