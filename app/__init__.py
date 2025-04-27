from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Register blueprints
    from app.routes import user_bp, storage_bp, contract_bp, signature_bp
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(storage_bp, url_prefix='/api')
    app.register_blueprint(contract_bp, url_prefix='/api')
    app.register_blueprint(signature_bp, url_prefix='/api')

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {"error": "Internal server error"}, 500

    return app
