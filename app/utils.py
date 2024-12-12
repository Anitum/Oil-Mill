import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime

def save_reading(camera_id, reading_data):
    """Save sensor reading data to JSON file"""
    filename = f'camera_{camera_id}_readings.json'
    path = os.path.join('app', 'static', 'data', filename)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Add timestamp to reading
    reading_data['timestamp'] = datetime.now().isoformat()
    
    # Load existing data
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
    else:
        data = []
    
    # Append new reading
    data.append(reading_data)
    
    # Save updated data
    with open(path, 'w') as f:
        json.dump(data, f)
    
    return True

def get_camera_readings(camera_id, limit=100):
    """Get latest readings for a camera"""
    filename = f'camera_{camera_id}_readings.json'
    path = os.path.join('app', 'static', 'data', filename)
    
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
            return data[-limit:]  # Return last 'limit' readings
    return []

def format_timestamp(timestamp):
    """Format timestamp for display"""
    return datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S')

