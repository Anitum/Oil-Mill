#!/bin/bash

# Configuration
WATCH_DIR="/media/mayank/Ubuntu1/NewOillMill/Oil-Mill/inputs"
PYTHON_SCRIPT="/media/mayank/Ubuntu1/NewOillMill/Oil-Mill/check_in_the_box.py"  # Update this path
LOG_FILE="./cctv_processing.log"
LOCK_FILE="./cctv_processing.lock"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to check if script is already running
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        PID=$(cat "$LOCK_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            log_message "Script already running with PID $PID"
            exit 1
        else
            # Remove stale lock file
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
}

# Function to clean up
cleanup() {
    rm -f "$LOCK_FILE"
    log_message "Script stopped"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGTERM SIGINT

# Create log file if it doesn't exist
touch "$LOG_FILE"

# Start script
log_message "Starting CCTV monitoring script"
check_lock

# Main loop
while true; do
    # Check if directory exists
    if [ ! -d "$WATCH_DIR" ]; then
        log_message "Error: Watch directory does not exist: $WATCH_DIR"
        sleep 60
        continue
    fi

    # Check if there are any CSV files
    csv_count=$(ls -1 "$WATCH_DIR"/*.csv 2>/dev/null | wc -l)
    
    if [ "$csv_count" -gt 0 ]; then
        log_message "Found $csv_count CSV files. Processing..."
        
        # Execute Python script
        if /home/mridul/Oil-Mill/venv/bin/python "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1; then
            log_message "Successfully processed files"
        else
            log_message "Error processing files"
        fi
    fi

    # Wait for a short period before next check
    sleep 5
done
