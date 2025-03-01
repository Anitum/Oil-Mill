from flask import Blueprint, render_template, jsonify, send_file
import json
import os
import glob
from datetime import datetime
import cv2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
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
        return render_template('camera/dashboard.html',
                             camera_id=camera_id,
                             machine_name=machine_name)
    @bp.route('/api/people-count')
    def get_people_count():
        try:
            # Read the CSV file
            people_df = pd.read_csv('input/file_counts.csv', names=['file_name', 'count'])
            
            # Convert the data into the required format
            people_df['timestamp'] = pd.to_datetime(
                people_df['file_name'].str.split('_').str[1],
                format='%Y%m%dT%H%M%S'
            )
            
            # Sort by timestamp and get the latest records
            people_df = people_df.sort_values('timestamp')
            
            # Format the data for the response
            data = [
                {
                    'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                    'count': int(count)
                }
                for ts, count in zip(people_df['timestamp'], people_df['count'])
            ]
            
            return jsonify({
                'success': True,
                'data': data
            })
        except Exception as e:
            print(f"Error processing people count data: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'data': []
            })
    @bp.route('/data')
    def get_data():
        try:
            print(f"\n{'='*50}")
            print(f"Processing data for camera {camera_id}")
            print(f"{'='*50}")
        
        # Read people detection data from file_counts.csv
            print("\nReading people detection data...")
            people_df = pd.read_csv('input/file_counts.csv')
            print(f"Found {len(people_df)} total records in file_counts.csv")
            
        # Filter for current camera and create timestamp column
            camera_prefix = f'channel{camera_id}'
            camera_df = people_df[people_df['file_name'].str.startswith(camera_prefix)].copy()
            print(f"Filtered {len(camera_df)} records for camera {camera_id}")
            
            # Extract timestamp more efficiently
            camera_df['timestamp'] = pd.to_datetime(
                camera_df['file_name'].str.split('_').str[1],
                format='%Y%m%dT%H%M%S'
            )
            
            # Sort by timestamp and convert to desired format
            camera_df = camera_df.sort_values('timestamp')
            people_data = [
                {ts.strftime('%Y-%m-%d %H:%M:%S'): round(count)} 
                for ts, count in zip(camera_df['timestamp'], camera_df['count'])
            ]
            print(f"Processed {len(people_data)} people detection records")

            # Get operation data based on camera
            operation_data = []
            machine_data = {}

            if str(camera_id) == '301':
                print("\nProcessing camera 301 (Pouring System)...")
                print("Reading Pouring_raw_Material.csv...")
                
                try:
                    op_df = pd.read_csv('input/Pouring_raw_Material.csv')
                    print(f"Raw CSV content (first few rows):")
                    print(op_df.head())
                    print(f"\nColumns in CSV: {op_df.columns.tolist()}")
                    
                    print("\nConverting timestamps...")
                    op_df['timestamp'] = pd.to_datetime(
                        op_df['Filename'].str.split('_').str[1],
                        format='%Y%m%dT%H%M%S'
                    )
                    op_df = op_df.sort_values('timestamp')
                    
                    print(f"Processed timestamps. Total records: {len(op_df)}")
                    
                    operation_data = [
                        {ts.strftime('%Y-%m-%d %H:%M:%S'): 1} 
                        for ts in op_df['timestamp']
                    ]
                    print(f"Created {len(operation_data)} operation data records")
                    
                    # Create initial usage data with active timestamps
                    active_timestamps = [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in op_df['timestamp']]
                    
                    # Create complete timeline with zeros for inactive periods
                    if active_timestamps:
                        # Convert to datetime objects
                        datetime_timestamps = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in active_timestamps]
                        start_time = min(datetime_timestamps)
                        end_time = max(datetime_timestamps)
                        
                        # Generate complete timeline with 15-minute intervals
                        complete_timeline = []
                        current = start_time
                        while current <= end_time:
                            complete_timeline.append(current.strftime('%Y-%m-%d %H:%M:%S'))
                            current += timedelta(minutes=15)
                        
                        # Create a dictionary of known active timestamps
                        active_dict = {ts: 1 for ts in active_timestamps}
                        
                        # Create usage data with zeros for inactive periods
                        usage_data = []
                        for ts in complete_timeline:
                            usage_data.append({ts: active_dict.get(ts, 0)})
                        
                        machine_data['usage'] = {'data': usage_data}
                        print(f"Created {len(usage_data)} usage data records with active and inactive periods")
                    else:
                        # If no active timestamps, create empty usage data
                        machine_data['usage'] = {'data': []}
                    
                    print("\nSample of machine_data:")
                    print(f"Keys in machine_data: {list(machine_data.keys())}")
                    if machine_data['usage']['data']:
                        print("First usage data entry:", machine_data['usage']['data'][0])
                    
                except Exception as e:
                    print(f"Error processing Pouring_raw_Material.csv: {str(e)}")
                    print(f"Current working directory: {os.getcwd()}")
                    print(f"Files in input directory: {os.listdir('input')}")

            elif str(camera_id) == '701':
                print("\nProcessing camera 701 (Filling System)...")
                op_df = pd.read_csv('input/Oil_can_Filling.csv')
                op_df['timestamp'] = pd.to_datetime(
                    op_df['Filename'].str.split('_').str[1],
                    format='%Y%m%dT%H%M%S'
                )
                op_df = op_df.sort_values('timestamp')
                operation_data = [
                    {ts.strftime('%Y-%m-%d %H:%M:%S'): 1} 
                    for ts in op_df['timestamp']
                ]
                print(f"Processed {len(operation_data)} operation data records")
                
                # Create initial usage data with active timestamps
                active_timestamps = [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in op_df['timestamp']]
                
                # Create complete timeline with zeros for inactive periods
                if active_timestamps:
                    # Convert to datetime objects
                    datetime_timestamps = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in active_timestamps]
                    start_time = min(datetime_timestamps)
                    end_time = max(datetime_timestamps)
                    
                    # Generate complete timeline with 15-minute intervals
                    complete_timeline = []
                    current = start_time
                    while current <= end_time:
                        complete_timeline.append(current.strftime('%Y-%m-%d %H:%M:%S'))
                        current += timedelta(minutes=15)
                    
                    # Create a dictionary of known active timestamps
                    active_dict = {ts: 1 for ts in active_timestamps}
                    
                    # Create usage data with zeros for inactive periods
                    usage_data = []
                    for ts in complete_timeline:
                        usage_data.append({ts: active_dict.get(ts, 0)})
                    
                    machine_data['usage'] = {'data': usage_data}
                    print(f"Created {len(usage_data)} usage data records with active and inactive periods")
                else:
                    # If no active timestamps, create empty usage data
                    machine_data['usage'] = {'data': []}

            elif str(camera_id) == '601':
                print("\nProcessing camera 601 (Machine Control)...")
                all_timestamps = set()
                
                for machine in ['Mill1-2', 'Mill2-3', 'Mill3-4']:
                    print(f"\nProcessing {machine}...")
                    df = pd.read_csv(f'input/{machine}.csv')
                    df['timestamp'] = pd.to_datetime(
                        df['Filename'].str.split('_').str[1],
                        format='%Y%m%dT%H%M%S'
                    )
                    df = df.sort_values('timestamp')
                    
                    # Get active timestamps for this machine
                    active_timestamps = [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in df['timestamp']]
                    all_timestamps.update(active_timestamps)
                    
                    data = [
                        {ts.strftime('%Y-%m-%d %H:%M:%S'): 1} 
                        for ts in df['timestamp']
                    ]
                    machine_data[machine.lower().replace('-', '_')] = {'data': data}
                    print(f"Added {len(data)} records for {machine}")

                # Create complete timeline with zeros for inactive periods for all machines
                if all_timestamps:
                    # Convert to datetime objects
                    datetime_timestamps = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in all_timestamps]
                    start_time = min(datetime_timestamps)
                    end_time = max(datetime_timestamps)
                    
                    # Generate complete timeline with 15-minute intervals
                    complete_timeline = []
                    current = start_time
                    while current <= end_time:
                        complete_timeline.append(current.strftime('%Y-%m-%d %H:%M:%S'))
                        current += timedelta(minutes=15)
                    
                    # Create a dictionary of known active timestamps
                    active_dict = {ts: 1 for ts in all_timestamps}
                    
                    # Create usage data with zeros for inactive periods
                    usage_data = []
                    for ts in complete_timeline:
                        usage_data.append({ts: active_dict.get(ts, 0)})
                    
                    machine_data['usage'] = {'data': usage_data}
                    print(f"\nCreated {len(usage_data)} usage data records with active and inactive periods")
                else:
                    # If no active timestamps, create empty usage data
                    machine_data['usage'] = {'data': []}

            print("\nFinal data summary:")
            print(f"People data records: {len(people_data)}")
            print(f"Operation data records: {len(operation_data)}")
            print(f"Machine data keys: {list(machine_data.keys())}")
            
            response_data = {
                'people_data': people_data,
                'operation_data': operation_data,
                'machine_data': machine_data
            }
            print("\nSending response...")
            return jsonify(response_data)
        
        except Exception as e:
            print(f"\nERROR in get_data: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            return jsonify({
                'people_data': [],
                'operation_data': [],
                'machine_data': {}
            })
    @bp.route('/heatmap')
    def get_heatmap():
        heatmap_path = os.path.join('heatmap_outputs', f'heatmap_channel_{camera_id}.png')
        print(heatmap_path)

        os.makedirs('heatmap_outputs', exist_ok=True)

        try:
            if not os.path.exists(heatmap_path):
                img = np.zeros((512, 512, 3), np.uint8)
                cv2.circle(img, (256, 256), 100, (0, 255, 0), -1)
                cv2.imwrite(heatmap_path, img)
                print('+'*50)

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