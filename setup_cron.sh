#!/bin/bash

#Full paths
PROJECT_DIR="/Users/prashanth/wikipedia-assistant"
LOG_DIR="$PROJECT_DIR/logs"
CRON_FILE="$PROJECT_DIR/crontab.txt"
SETUP_SCRIPT="$PROJECT_DIR/setup.sh"
LOG_FILE="$LOG_DIR/wiki_etl.log"


# Create logs directory if not exists
mkdir -p "$LOG_DIR"


# Create crontab.txt with the job - running at 4 AM on 1st of every month
echo "0 4 1 * * $SETUP_SCRIPT >> $LOG_FILE 2>&1" > "$CRON_FILE"

# Create crontab.txt with the job - running at 11.10 PM later today
#echo "10 23 * * * $SETUP_SCRIPT > $LOG_FILE 2>&1" > "$CRON_FILE"


# Install the crontab
crontab "$CRON_FILE"

# Show installed crontab for verification
echo "Installed cron jobs:"
crontab -l
