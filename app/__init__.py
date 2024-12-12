from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Initialize extensions
db = SQLAlchemy()

def create_app(config_class=Config):
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Import and register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.camera1 import bp as camera1_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(camera1_bp, url_prefix='/camera1')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app

