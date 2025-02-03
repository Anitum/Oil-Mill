from flask import Blueprint, render_template, jsonify
import json
from datetime import datetime
import os

bp = Blueprint('main', __name__)

def read_json_file(filename):
    """Helper function to read JSON files from input directory"""
    try:
        file_path = os.path.join('input', filename)
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error reading {filename}: {str(e)}")
        return {}

def process_people_data():
    """Process and aggregate people count data"""
    try:
        data = read_json_file('people-count.json')
        if not data or 'data' not in data:
            return {
                'labels': [],
                'values': []
            }
        
        # Get last 12 data points
        recent_data = data['data'][-12:]
        return {
            'labels': [datetime.fromisoformat(entry['timestamp']).strftime('%H:%M') 
                      for entry in recent_data],
            'values': [float(entry['total_count']) for entry in recent_data]
        }
    except Exception as e:
        print(f"Error processing people data: {str(e)}")
        return {
            'labels': [],
            'values': []
        }

def process_machine_data():
    """Process machine usage data"""
    try:
        data = read_json_file('machine-usage.json')
        if not data or 'machines' not in data:
            return {
                'labels': [],
                'values': [],
                'efficiency': []
            }
        
        # Get latest efficiency for each machine
        latest_data = {}
        for machine_id, machine in data['machines'].items():
            if machine['usage_data']:
                latest = machine['usage_data'][-1]
                latest_data[machine['name']] = {
                    'usage': float(latest['usage_minutes']),
                    'efficiency': float(latest['efficiency'])
                }
        
        return {
            'labels': list(latest_data.keys()),
            'values': [d['usage'] for d in latest_data.values()],
            'efficiency': [d['efficiency'] for d in latest_data.values()]
        }
    except Exception as e:
        print(f"Error processing machine data: {str(e)}")
        return {
            'labels': [],
            'values': [],
            'efficiency': []
        }

def process_activity_data():
    """Process and summarize activity data"""
    try:
        data = read_json_file('activity-data.json')
        if not data or 'activities' not in data:
            return {
                'labels': [],
                'values': [],
                'efficiency': []
            }
        
        # Get latest count for each activity
        latest_data = {}
        for activity_id, activity in data['activities'].items():
            if activity['data']:
                latest = activity['data'][-1]
                latest_data[activity['name']] = {
                    'count': float(latest['count']),
                    'efficiency': float(latest['efficiency'])
                }
        
        return {
            'labels': list(latest_data.keys()),
            'values': [d['count'] for d in latest_data.values()],
            'efficiency': [d['efficiency'] for d in latest_data.values()]
        }
    except Exception as e:
        print(f"Error processing activity data: {str(e)}")
        return {
            'labels': [],
            'values': [],
            'efficiency': []
        }

def get_camera_summary():
    """Get simplified camera status summary"""
    try:
        data = read_json_file('camera-status.json')
        if not data or 'cameras' not in data:
            return []
        
        return [{
            'id': str(cam_id),
            'status': str(camera['status']),
            'name': str(camera['name'])
        } for cam_id, camera in data['cameras'].items()]
    except Exception as e:
        print(f"Error processing camera data: {str(e)}")
        return []

@bp.route('/')
def index():
    """Main dashboard route with pre-processed data"""
    # Create input directory if it doesn't exist
    os.makedirs('input', exist_ok=True)
    
    # Process all data
    people_data = process_people_data()
    machine_data = process_machine_data()
    activity_data = process_activity_data()
    cameras = get_camera_summary()
    
    return render_template('index.html',
                         people_data=people_data,
                         machine_data=machine_data,
                         activity_data=activity_data,
                         cameras=cameras)

@bp.route('/api/update-data')
def get_updated_data():
    """Endpoint for periodic updates"""
    return jsonify({
        'people': process_people_data(),
        'machine': process_machine_data(),
        'activity': process_activity_data(),
        'cameras': get_camera_summary()
    })

@bp.route('/api/toggle-camera/<camera_id>', methods=['POST'])
def toggle_camera(camera_id):
    """Toggle camera geofencing"""
    try:
        data = read_json_file('camera-status.json')
        if camera_id in data['cameras']:
            camera = data['cameras'][camera_id]
            camera['status'] = 'inactive' if camera['status'] == 'active' else 'active'
            # In a real application, save the updated status back to the file
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
