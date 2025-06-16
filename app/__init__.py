from flask import Flask
from .extensions import jwt
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    jwt.init_app(app)

    # Register blueprints
    from .auth import auth_bp
    from .routes import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/api')

    return app