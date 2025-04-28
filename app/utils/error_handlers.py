from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from web3.exceptions import Web3Exception
from marshmallow import ValidationError
import traceback
from typing import Dict, Any, Optional

def log_error(error: Exception, error_type: str) -> None:
    """
    Log error details with stack trace
    
    Args:
        error: The exception that occurred
        error_type: Type of error for logging
    """
    current_app.logger.error(
        f"{error_type} occurred: {str(error)}\n"
        f"Stack trace:\n{traceback.format_exc()}"
    )

def create_error_response(
    error_type: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None
) -> tuple:
    """
    Create standardized error response
    
    Args:
        error_type: Type of error
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        tuple: JSON response and status code
    """
    response = {
        'error': error_type,
        'message': message,
        'status_code': status_code
    }
    
    if details:
        response['details'] = details
        
    return jsonify(response), status_code

def register_error_handlers(app):
    """
    Register error handlers for the Flask application
    
    Handles various types of errors including:
    - HTTP exceptions
    - Validation errors
    - Database errors
    - Blockchain errors
    - Weather API errors
    - ML prediction errors
    - Rate limiting errors
    """
    
    @app.errorhandler(ValidationError)
    def validation_error(error):
        """Handle Marshmallow validation errors"""
        log_error(error, 'Validation Error')
        return create_error_response(
            'Validation Error',
            'Invalid input data',
            400,
            {'validation_errors': error.messages}
        )

    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle bad request errors"""
        log_error(error, 'Bad Request')
        return create_error_response(
            'Bad Request',
            str(error.description) if hasattr(error, 'description') else str(error),
            400
        )

    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle unauthorized access errors"""
        log_error(error, 'Unauthorized')
        return create_error_response(
            'Unauthorized',
            'Authentication required',
            401
        )

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle forbidden access errors"""
        log_error(error, 'Forbidden')
        return create_error_response(
            'Forbidden',
            str(error.description) if hasattr(error, 'description') else 'Access denied',
            403
        )

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle resource not found errors"""
        log_error(error, 'Not Found')
        return create_error_response(
            'Not Found',
            str(error.description) if hasattr(error, 'description') else 'Resource not found',
            404
        )

    @app.errorhandler(429)
    def ratelimit_error(error):
        """Handle rate limit exceeded errors"""
        log_error(error, 'Rate Limit Exceeded')
        return create_error_response(
            'Rate Limit Exceeded',
            'Too many requests. Please try again later.',
            429,
            {'retry_after': error.description}
        )

    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        """Handle database integrity errors"""
        log_error(error, 'Database Integrity Error')
        return create_error_response(
            'Conflict',
            'Database integrity error. Possible duplicate entry.',
            409,
            {'error_details': str(error)}
        )

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        """Handle general database errors"""
        log_error(error, 'Database Error')
        return create_error_response(
            'Database Error',
            'A database error occurred',
            500,
            {'error_details': str(error)}
        )

    @app.errorhandler(Web3Exception)
    def blockchain_error(error):
        """Handle blockchain interaction errors"""
        log_error(error, 'Blockchain Error')
        return create_error_response(
            'Blockchain Error',
            'Error interacting with the blockchain',
            500,
            {'error_details': str(error)}
        )

    @app.errorhandler(WeatherAPIError)
    def weather_api_error(error):
        """Handle weather API errors"""
        log_error(error, 'Weather API Error')
        return create_error_response(
            'Weather API Error',
            'Error fetching weather data',
            503,
            {'error_details': str(error)}
        )

    @app.errorhandler(MLPredictionError)
    def ml_prediction_error(error):
        """Handle ML prediction errors"""
        log_error(error, 'ML Prediction Error')
        return create_error_response(
            'ML Prediction Error',
            'Error generating prediction',
            500,
            {
                'error_details': str(error),
                'fallback_prediction': error.fallback_prediction if hasattr(error, 'fallback_prediction') else None
            }
        )

    @app.errorhandler(Exception)
    def general_error(error):
        """Handle all other unhandled exceptions"""
        log_error(error, 'Unhandled Exception')
        
        if isinstance(error, HTTPException):
            return create_error_response(
                error.name,
                error.description,
                error.code
            )
        
        return create_error_response(
            'Internal Server Error',
            'An unexpected error occurred',
            500,
            {'error_details': str(error)} if app.debug else None
        )

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

class WeatherAPIError(APIError):
    """Weather API error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=503, payload=payload)

class MLPredictionError(APIError):
    """ML prediction error"""
    def __init__(self, message, fallback_prediction=None, payload=None):
        super().__init__(message, status_code=500, payload=payload)
        self.fallback_prediction = fallback_prediction

class ValidationError(APIError):
    """Validation error"""
    def __init__(self, message, validation_errors=None):
        super().__init__(
            message,
            status_code=400,
            payload={'validation_errors': validation_errors}
        )

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
