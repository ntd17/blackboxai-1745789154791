from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
from config import Config
from app.utils.error_handlers import register_error_handlers
from app.utils.response_utils import success_response, error_response
from app.utils.logger import init_app as init_logger
from app.utils.cache import Cache

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Initialize rate limiter
    limiter.init_app(app)
    
    # Initialize Redis cache
    app.cache = Cache(app.config['REDIS_URL'])
    
    # Initialize logger
    init_logger(app)
    
    # Swagger configuration
    app.config['SWAGGER'] = {
        'title': 'Painting Contract API',
        'uiversion': 3,
        'version': '1.0.0',
        'description': '''
        API for managing painting contracts with blockchain integration and weather-based predictions.
        
        Features:
        - User management
        - File storage on IPFS via Storacha
        - Smart contract integration
        - Weather-based contract duration predictions
        - Digital signatures and verification
        ''',
        'termsOfService': '',
        'specs_route': '/docs/',
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header'
            }
        }
    }
    
    # Initialize Swagger
    Swagger(app)
    
    # Initialize extensions that need app context
    from app.routes.storage_routes import init_limiter
    init_limiter(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    from app.routes import user_bp, storage_bp, contract_bp, signature_bp
    from app.routes.ml_routes import ml_bp

    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(storage_bp, url_prefix='/api')
    app.register_blueprint(contract_bp, url_prefix='/api')
    app.register_blueprint(signature_bp, url_prefix='/api')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """
        Health Check Endpoint
        ---
        tags:
          - System
        responses:
          200:
            description: Service is healthy
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                status_code:
                  type: integer
                  example: 200
                data:
                  type: object
                  properties:
                    status:
                      type: string
                      example: healthy
                message:
                  type: string
                  example: Service is running
        """
        return success_response(
            data={'status': 'healthy'},
            message='Service is running'
        )
    
    # Root endpoint with API information
    @app.route('/')
    def root():
        """
        API Information Endpoint
        ---
        tags:
          - System
        responses:
          200:
            description: API information
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                status_code:
                  type: integer
                  example: 200
                data:
                  type: object
                  properties:
                    name:
                      type: string
                      example: Painting Contract API
                    version:
                      type: string
                      example: 1.0.0
                    documentation:
                      type: string
                      example: /docs
        """
        return success_response(
            data={
                'name': 'Painting Contract API',
                'version': '1.0.0',
                'documentation': '/docs'
            },
            message='Welcome to the Painting Contract API'
        )
    
    app.logger.info('Application startup complete')
    return app
