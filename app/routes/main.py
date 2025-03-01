from flask import Blueprint, render_template, jsonify
import json
from datetime import datetime
import os
from apscheduler.schedulers.background import BackgroundScheduler
from machine_usage_processor import MachineUsageProcessor

bp = Blueprint('main', __name__)

# Initialize the scheduler
scheduler = BackgroundScheduler()
machine_processor = MachineUsageProcessor()

def update_machine_usage():
    """Background job to update machine usage data every 30 minutes"""
    print(f"Updating machine usage data at {datetime.now()}")
    try:
        machine_processor.process_and_save()
    except Exception as e:
        print(f"Error updating machine usage: {e}")

def read_json_file(filename):
    """Helper function to read JSON files from input directory"""
    try:
        # First try the direct path
        file_path = os.path.join('input', filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        
        # If not found, try in json_dir
        file_path = os.path.join('input', 'json_dir', filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
                
        print(f"Could not find {filename} in input/ or input/json_dir/")
        return {}
    except Exception as e:
        print(f"Error reading {filename}: {str(e)}")
        return {}

# Start the scheduler when the blueprint is created
scheduler.add_job(
    func=update_machine_usage,
    trigger="interval",
    minutes=30,
    id="machine_usage_updater",
    replace_existing=True
)

# Run the initial update
update_machine_usage()

# Start the scheduler if not already running
if not scheduler.running:
    scheduler.start()

@bp.route('/')
def index():
    """Main dashboard route"""
    return render_template('index.html')

@bp.route('/api/camera-status')
def get_camera_status():
    """Endpoint to get camera status data"""
    data = read_json_file('camera-status.json')
    return jsonify(data)

@bp.route('/api/people-count')
def get_people_count():
    """Endpoint to get people count data"""
    data = read_json_file('people-count.json')
    return jsonify(data)

@bp.route('/api/machine-usage')
def get_machine_usage():
    """Endpoint to get machine usage data"""
    data = read_json_file('machine-usage.json')
    return jsonify(data)

@bp.route('/api/activity-data')
def get_activity_data():
    """Endpoint to get activity data"""
    data = read_json_file('activity-data.json')
    return jsonify(data)

@bp.route('/api/toggle-camera/<camera_id>', methods=['POST'])
def toggle_camera(camera_id):
    """Endpoint to toggle camera geofencing"""
    try:
        data = read_json_file('camera-status.json')
        if camera_id in data['cameras']:
            camera = data['cameras'][camera_id]
            camera['status'] = 'inactive' if camera['status'] == 'active' else 'active'
            # In a real application, you would save this back to the file
            # For demo purposes, we'll just return the updated status
            return jsonify({
                'success': True,
                'camera_id': camera_id,
                'new_status': camera['status']
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
