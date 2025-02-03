from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta
import random

def create_camera_blueprint(camera_id):
    bp = Blueprint(f'camera{camera_id}', __name__)

    # Machine mapping
    MACHINES = {
        1: {'name': 'Feeder', 'cameras': [1, 2]},
        2: {'name': 'Crusher-1', 'cameras': [3]},
        3: {'name': 'Crusher-2', 'cameras': [4]},
        4: {'name': 'Crusher-3', 'cameras': [5]},
        5: {'name': 'Crusher-4', 'cameras': [6]},
        6: {'name': 'Filter', 'cameras': [7, 8]},
        7: {'name': 'Filler', 'cameras': [9, 10]}
    }

    def get_machine_for_camera(camera_id):
        for machine_id, info in MACHINES.items():
            if camera_id in info['cameras']:
                return info['name']
        return None

    @bp.route('/dashboard')
    def dashboard():
        machine_name = get_machine_for_camera(camera_id)
        return render_template('camera/dashboard.html', 
                             camera_id=camera_id,
                             machine_name=machine_name)

    @bp.route('/data')
    def get_data():
        # Generate realistic demo data based on machine type
        machine_name = get_machine_for_camera(camera_id)
        
        # Generate time series data for the last hour
        timestamps = [(datetime.now() - timedelta(minutes=x)).strftime('%H:%M') 
                     for x in range(60, -1, -5)]
        
        if machine_name == 'Feeder':
            data = {
                'live_feed': {
                    'feed_rate': [random.uniform(80, 100) for _ in timestamps],
                    'timestamps': timestamps
                },
                'people_count': {
                    'count': [random.randint(0, 3) for _ in timestamps],
                    'timestamps': timestamps
                },
                'machine_usage': random.uniform(75, 95),
                'heatmap_data': [
                    [random.randint(30, 100) for _ in range(8)] 
                    for _ in range(8)
                ]
            }
        elif 'Crusher' in machine_name:
            data = {
                'live_feed': {
                    'crushing_force': [random.uniform(150, 200) for _ in timestamps],
                    'timestamps': timestamps
                },
                'people_count': {
                    'count': [random.randint(0, 2) for _ in timestamps],
                    'timestamps': timestamps
                },
                'machine_usage': random.uniform(80, 98),
                'heatmap_data': [
                    [random.randint(40, 100) for _ in range(8)] 
                    for _ in range(8)
                ]
            }
        elif machine_name == 'Filter':
            data = {
                'live_feed': {
                    'filter_pressure': [random.uniform(2.0, 3.5) for _ in timestamps],
                    'timestamps': timestamps
                },
                'people_count': {
                    'count': [random.randint(0, 2) for _ in timestamps],
                    'timestamps': timestamps
                },
                'machine_usage': random.uniform(70, 90),
                'heatmap_data': [
                    [random.randint(20, 90) for _ in range(8)] 
                    for _ in range(8)
                ]
            }
        else:  # Filler
            data = {
                'live_feed': {
                    'fill_level': [random.uniform(90, 100) for _ in timestamps],
                    'timestamps': timestamps
                },
                'people_count': {
                    'count': [random.randint(1, 3) for _ in timestamps],
                    'timestamps': timestamps
                },
                'machine_usage': random.uniform(85, 99),
                'heatmap_data': [
                    [random.randint(30, 95) for _ in range(8)] 
                    for _ in range(8)
                ]
            }
        
        return jsonify(data)

    @bp.route('/status')
    def get_status():
        statuses = ['ACTIVE', 'ACTIVE', 'MAINTENANCE', 'OFFLINE']
        weights = [0.85, 0.10, 0.03, 0.02]  # 85% chance of being active
        
        return jsonify({
            'status': random.choices(statuses, weights=weights)[0],
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'machine_name': get_machine_for_camera(camera_id)
        })

    return bp
