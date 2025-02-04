from flask import Blueprint

def register_blueprints(app):
    # Import blueprints
    from .camera import create_camera_blueprint
    from .main import bp

    # Register main blueprint
    app.register_blueprint(bp)

    # Register camera blueprints dynamically
    for camera_id in [101,201,301,401,501,601,701,801,901]:  # For cameras 1-8
        bp = create_camera_blueprint(camera_id)
        app.register_blueprint(bp, url_prefix=f'/camera{camera_id}')
