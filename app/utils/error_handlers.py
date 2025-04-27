from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from web3.exceptions import Web3Exception

def register_error_handlers(app):
    """Register error handlers for the Flask application"""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle bad request errors"""
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else str(error),
            'status_code': 400
        }), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle unauthorized access errors"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle forbidden access errors"""
        return jsonify({
            'error': 'Forbidden',
            'message': str(error.description) if hasattr(error, 'description') else 'Access denied',
            'status_code': 403
        }), 403

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle resource not found errors"""
        return jsonify({
            'error': 'Not Found',
            'message': str(error.description) if hasattr(error, 'description') else 'Resource not found',
            'status_code': 404
        }), 404

    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        """Handle database integrity errors"""
        return jsonify({
            'error': 'Conflict',
            'message': 'Database integrity error. Possible duplicate entry.',
            'details': str(error),
            'status_code': 409
        }), 409

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        """Handle general database errors"""
        return jsonify({
            'error': 'Database Error',
            'message': 'A database error occurred',
            'details': str(error),
            'status_code': 500
        }), 500

    @app.errorhandler(Web3Exception)
    def blockchain_error(error):
        """Handle blockchain interaction errors"""
        return jsonify({
            'error': 'Blockchain Error',
            'message': 'Error interacting with the blockchain',
            'details': str(error),
            'status_code': 500
        }), 500

    @app.errorhandler(Exception)
    def general_error(error):
        """Handle all other unhandled exceptions"""
        # Log the error for debugging
        app.logger.error(f'Unhandled exception: {str(error)}')
        
        if isinstance(error, HTTPException):
            return jsonify({
                'error': error.name,
                'message': error.description,
                'status_code': error.code
            }), error.code
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500

class APIError(Exception):
    """Custom API error class"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert error to dictionary format"""
        error_dict = {
            'error': self.__class__.__name__,
            'message': self.message,
            'status_code': self.status_code
        }
        if self.payload:
            error_dict['details'] = self.payload
        return error_dict

class ValidationError(APIError):
    """Validation error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)

class ResourceNotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=404, payload=payload)

class BlockchainError(APIError):
    """Blockchain interaction error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=500, payload=payload)

class StorageError(APIError):
    """Storage (IPFS/Storacha) error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=500, payload=payload)

def success_response(data=None, message=None, status_code=200):
    """Create a standardized success response"""
    response = {
        'success': True,
        'status_code': status_code
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code

def error_response(error_msg, status_code=400, details=None):
    """Create a standardized error response"""
    response = {
        'success': False,
        'error': error_msg,
        'status_code': status_code
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code
