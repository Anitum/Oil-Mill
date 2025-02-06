from flask import Blueprint, render_template, jsonify, send_file
import json
import os
import glob
from datetime import datetime
import cv2
import numpy as np
import pandas as pd
from datetime import datetime

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
        try:
            # Read people detection data from file_counts.csv
            people_df = pd.read_csv('input/file_counts.csv')
            people_data = []

            # Filter for current camera
            camera_prefix = f'channel{camera_id}'
            camera_df = people_df[people_df['file_name'].str.startswith(camera_prefix)]

            for _, row in camera_df.iterrows():
                # Updated timestamp parsing
                timestamp = datetime.strptime(
                    row['file_name'].split('_')[1], 
                    '%Y%m%dT%H%M%S'  # Changed format string
                ).strftime('%Y-%m-%d %H:%M:%S')
                people_data.append({timestamp: round(row['count'])})

            # Get operation data based on camera
            operation_data = []
            if str(camera_id) == '301':
                op_df = pd.read_csv('input/Pouring_raw_Material.csv')
                for _, row in op_df.iterrows():
                    timestamp = datetime.strptime(
                        row['Filename'].split('_')[1], 
                        '%Y%m%dT%H%M%S'  # Changed format string
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    operation_data.append({timestamp: 1})

            elif str(camera_id) == '701':
                op_df = pd.read_csv('input/Oil_can_Filling.csv')
                for _, row in op_df.iterrows():
                    timestamp = datetime.strptime(
                        row['Filename'].split('_')[1], 
                        '%Y%m%dT%H%M%S'  # Changed format string
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    operation_data.append({timestamp: 1})

            # Special handling for camera 601
            machine_data = {}
            if str(camera_id) == '601':
                for machine in ['Mill1-2', 'Mill2-3', 'Mill3-4']:
                    df = pd.read_csv(f'input/{machine}.csv')
                    data = []
                    for _, row in df.iterrows():
                        timestamp = datetime.strptime(
                            row['Filename'].split('_')[1], 
                            '%Y%m%dT%H%M%S'  # Changed format string
                        ).strftime('%Y-%m-%d %H:%M:%S')
                        data.append({timestamp: 1})
                    machine_data[machine.lower().replace('-', '_')] = {'data': data}

                # Calculate usage data from all machine CSVs
                if machine_data:
                    all_timestamps = set()
                    for m_data in machine_data.values():
                        for entry in m_data['data']:
                            all_timestamps.update(entry.keys())

                    usage_data = []
                    for ts in sorted(all_timestamps):
                        usage_data.append({ts: 1})
                    machine_data['usage'] = {'data': usage_data}

            return jsonify({
                'people_data': people_data,
                'operation_data': operation_data,
                'machine_data': machine_data
            })
        except Exception as e:
            print(f"Error in get_data: {str(e)}")
            return jsonify({
                'people_data': [],
                'operation_data': [],
                'machine_data': {}
            })

    @bp.route('/heatmap')
    def get_heatmap():
        heatmap_path = os.path.join('heatmap_outputs', f'heatmap_channel_{camera_id}.png')
        print(heatmap_path)

        # First ensure the directory exists
        os.makedirs('heatmap_outputs', exist_ok=True)

        try:
            #making heatmap file just for demo 
            if not os.path.exists(heatmap_path):
                img = np.zeros((512, 512, 3), np.uint8)
                cv2.circle(img, (256, 256), 100, (0, 255, 0), -1)
                cv2.imwrite(heatmap_path, img)
                print('+'*50)

            # Add a small delay to ensure file is written (optional)
            import time
            time.sleep(0.1)

            if os.path.exists(heatmap_path):
                print('*'*50)
                return send_file(heatmap_path, mimetype='image/jpeg')

            print('#'*50)
            return jsonify({'error': 'Heatmap not found'}), 404

        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return bp