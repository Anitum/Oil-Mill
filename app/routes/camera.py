from flask import Blueprint, render_template, jsonify, send_file
import json
import os
import glob
from datetime import datetime
import cv2
import numpy as np

def create_camera_blueprint(camera_id):
    bp = Blueprint(f'camera{camera_id}', __name__)

    MACHINES = {
        '101': 'Raw Material Feeder',
        '201': 'Primary Feeder',
        '301': 'Pouring System',
        '401': 'Secondary Feeder',
        '501': 'Filter System',
        '601': 'Machine Control', 
        '701': 'Filling System'
    }

    def get_latest_data(pattern):
        files = glob.glob(os.path.join('input', pattern))
        if not files:
            return None
        latest_file = max(files)
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except:
            return None

    @bp.route('/dashboard')
    def dashboard():
        machine_name = MACHINES.get(str(camera_id), 'Unknown Machine')
        return render_template('camera/dashboard.html',  # Updated template path
                             camera_id=camera_id,
                             machine_name=machine_name)

    @bp.route('/data')
    def get_data():
        # Get people detection data
        people_data = get_latest_data(f'{camera_id}_people_detection_*.json')
        
        # Get operation data based on camera
        operation_data = None
        if str(camera_id) == '301':
            operation_data = get_latest_data('pouring_301_results_*.json')
        elif str(camera_id) == '501':
            operation_data = get_latest_data('filter_501_results_*.json')
        elif str(camera_id) == '701':
            operation_data = get_latest_data('filling_701_results_*.json')
        
        # Special handling for camera 601
        machine_data = {}
        if str(camera_id) == '601':
            machine_data['machine1-2'] = get_latest_data('machine1-2_601_results_*.json')
            machine_data['machine2-3'] = get_latest_data('machine2-3_601_results_*.json')
            machine_data['machine3-4'] = get_latest_data('machine3-4_601_results_*.json')
            machine_data['usage'] = get_latest_data('machine_usage_601_results_*.json')

        return jsonify({
            'people_data': people_data.get('data', []) if people_data else [],
            'operation_data': operation_data.get('data', []) if operation_data else [],
            'machine_data': machine_data
        })

    @bp.route('/heatmap')
    def get_heatmap():
        heatmap_path = os.path.join('input', f'{camera_id}_heatmap.jpg')
        if os.path.exists(heatmap_path):
            return send_file(heatmap_path, mimetype='image/jpeg')
        return jsonify({'error': 'Heatmap not found'}), 404

    return bp