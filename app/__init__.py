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
    from app.routes.camera2 import bp as camera2_bp
    from app.routes.camera3 import bp as camera3_bp
    from app.routes.camera4 import bp as camera4_bp
    from app.routes.camera5 import bp as camera5_bp
    from app.routes.camera6 import bp as camera6_bp
    from app.routes.camera7 import bp as camera7_bp
    from app.routes.camera8 import bp as camera8_bp
    from app.routes.camera9 import bp as camera9_bp
    from app.routes.camera10 import bp as camera10_bp


    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(camera1_bp, url_prefix='/camera1')
    app.register_blueprint(camera2_bp, url_prefix='/camera2')
    app.register_blueprint(camera3_bp, url_prefix='/camera3')
    app.register_blueprint(camera4_bp, url_prefix='/camera4')
    app.register_blueprint(camera5_bp, url_prefix='/camera5')
    app.register_blueprint(camera6_bp, url_prefix='/camera6')
    app.register_blueprint(camera7_bp, url_prefix='/camera7')
    app.register_blueprint(camera8_bp, url_prefix='/camera8')
    app.register_blueprint(camera9_bp, url_prefix='/camera9')
    app.register_blueprint(camera10_bp, url_prefix='/camera10')



    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app

