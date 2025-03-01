#!/bin/bash

# This script resets the machine usage data at midnight
APP_DIR="/path/to/your/application"  # Change this to your actual application path
DATE=$(date '+%Y-%m-%d')

# Change to application directory
cd "$APP_DIR" || exit 1

# Create a backup of the current machine-usage.json
cp input/machine-usage.json "input/machine-usage-$DATE.json.bak"

# Reset the machine usage data for the new day
cat > input/machine-usage.json << EOF
{
  "last_updated": "$(date -Iseconds)",
  "interval": "hourly",
  "data": [
    {
      "timestamp": "$(date -Iseconds)",
      "total_count": 0,
      "by_area": {
        "filter": 0,
        "crusher": 0,
        "filling": 0
      }
    }
  ]
}
EOF

echo "Machine usage data reset for $DATE"

# Set up a cron job to run the script at midnight every day: crontab -e
# 0 0 * * * /path/to/reset_machine_usage.sh