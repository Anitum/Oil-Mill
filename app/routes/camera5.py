
from flask import Blueprint, render_template, jsonify
from app.models.models import Camera, Reading
from app import db

bp = Blueprint('camera5', __name__)

@bp.route('/dashboard')
def dashboard():
    return render_template('camera5/Camera5.html')

@bp.route('/data')
def get_data():
    # Example data - replace with actual data from your database
    data = {
        'temperature': 75.5,
        'pressure': 2.3,
        'flow_rate': 550,
        'quality': 98.5
    }
    return jsonify(data)

@bp.route('/status')
def get_status():
    camera = Camera.query.filter_by(id=5).first()
    return jsonify({
        'status': camera.status if camera else 'UNKNOWN',
        'last_reading': Reading.query.filter_by(camera_id=5).order_by(Reading.timestamp.desc()).first()
    })

