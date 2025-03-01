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
