from flask import Blueprint, render_template, jsonify
from app.models.models import Camera, Reading
from app import db

def create_camera_blueprint(camera_id):
    bp = Blueprint(f'camera{camera_id}', __name__)

    @bp.route('/dashboard')
    def dashboard():
        return render_template('camera/dashboard.html', camera_id=camera_id)

    @bp.route('/data')
    def get_data():
        # Example data - replace with actual data from your database
        data = {
            'temperature': 75.5,
            'pressure': 2.3,
            'flow_rate': 350,
            'quality': 98.5
        }
        return jsonify(data)

    @bp.route('/status')
    def get_status():
        camera = Camera.query.filter_by(id=camera_id).first()
        return jsonify({
            'status': camera.status if camera else 'UNKNOWN',
            'last_reading': Reading.query.filter_by(camera_id=camera_id)
                                  .order_by(Reading.timestamp.desc())
                                  .first()
        })

    return bp
