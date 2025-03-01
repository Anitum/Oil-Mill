from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate
from config import Config
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()  # Create a Migrate instance

def create_app(config_class=Config):
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate with app and db
    
    # Import and register blueprints

    from app.routes import register_blueprints
    register_blueprints(app)   
    
    from app.routes.staff import bp as staff_bp
    app.register_blueprint(staff_bp, url_prefix='/staff')
    
    from app.routes.attendance import bp as attendance_bp
    app.register_blueprint(attendance_bp)
    
    # Register blueprints

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    # Create necessary directories
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'staff'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'documents'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)

    return app
