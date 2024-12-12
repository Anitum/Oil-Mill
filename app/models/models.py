from datetime import datetime
from app import db

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Camera(db.Model, TimestampMixin):
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE, MAINTENANCE
    ip_address = db.Column(db.String(45))
    last_maintenance = db.Column(db.DateTime)
    
    # Relationships
    readings = db.relationship('Reading', backref='camera', lazy=True)

class Reading(db.Model, TimestampMixin):
    __tablename__ = 'readings'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Float)
    flow_rate = db.Column(db.Float)
    oil_quality = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class MaintenanceLog(db.Model, TimestampMixin):
    __tablename__ = 'maintenance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    maintenance_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    performed_by = db.Column(db.String(100))

