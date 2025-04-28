from flask_jwt_extended import JWTManager
from datetime import timedelta

jwt = JWTManager()

def init_jwt(app):
    """Initialize JWT manager with app configuration"""
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    jwt.init_app(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {
            'success': False,
            'error': 'Token has expired',
            'message': 'Please log in again.',
            'status_code': 401
        }, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {
            'success': False,
            'error': 'Invalid token',
            'message': 'Please provide a valid token.',
            'status_code': 401
        }, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {
            'success': False,
            'error': 'Authorization required',
            'message': 'Please provide an access token.',
            'status_code': 401
        }, 401

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return {
            'success': False,
            'error': 'Fresh token required',
            'message': 'Please log in again.',
            'status_code': 401
        }, 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {
            'success': False,
            'error': 'Token has been revoked',
            'message': 'Please log in again.',
            'status_code': 401
        }, 401

    return jwt
