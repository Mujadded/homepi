#!/bin/bash

# HomePi Watchdog Script
# Monitors the HomePi service and restarts if needed

LOG_FILE="/tmp/homepi-watchdog.log"
CHECK_INTERVAL=60  # Check every 60 seconds
MAX_RETRIES=3
RETRY_COUNT=0

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

check_service() {
    if systemctl is-active --quiet homepi.service; then
        return 0
    else
        return 1
    fi
}

check_api() {
    # Check if API is responding
    if curl -sf http://localhost:5000/api/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

restart_service() {
    log "Attempting to restart HomePi service..."
    sudo systemctl restart homepi.service
    sleep 10
    
    if check_service && check_api; then
        log "Service restarted successfully"
        RETRY_COUNT=0
        return 0
    else
        log "Service restart failed"
        RETRY_COUNT=$((RETRY_COUNT + 1))
        return 1
    fi
}

log "Watchdog started"

while true; do
    sleep $CHECK_INTERVAL
    
    # Check if service is running
    if ! check_service; then
        log "ERROR: HomePi service is not running!"
        restart_service
        continue
    fi
    
    # Check if API is responding
    if ! check_api; then
        log "WARNING: API not responding!"
        
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            restart_service
        else
            log "ERROR: Max retries reached. Manual intervention needed."
            # Send notification (could add email here)
            RETRY_COUNT=0
            sleep 300  # Wait 5 minutes before trying again
        fi
        continue
    fi
    
    # Everything is OK
    RETRY_COUNT=0
done

