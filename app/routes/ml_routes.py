from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
from app.services.ml_service import MLPredictor
from app.utils.logger import get_logger
from app.utils.validators.marshmallow_schemas import MLPredictionRequestSchema
from app.utils.error_handlers import ValidationError, MLPredictionError
from app.utils.cache import cached
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter

ml_bp = Blueprint('ml_bp', __name__)
logger = get_logger()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_url=current_app.config['REDIS_URL']
)

@ml_bp.route('/predict_rain', methods=['POST'])
@limiter.limit("100/hour")  # Rate limit for ML predictions
@swag_from({
    'tags': ['Machine Learning'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'weather_data': {
                        'type': 'array',
                        'items': {'type': 'object'},
                        'description': 'List of daily forecasts'
                    },
                    'location': {
                        'type': 'object',
                        'description': 'City and country information'
                    },
                    'original_duration': {
                        'type': 'integer',
                        'description': 'Original contract duration in days'
                    }
                },
                'required': ['weather_data', 'location', 'original_duration']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Prediction result',
            'schema': {
                'type': 'object',
                'properties': {
                    'delay_days': {'type': 'integer'},
                    'recommended_duration': {'type': 'integer'},
                    'confidence_score': {'type': 'number', 'format': 'float'},
                    'rain_probability': {'type': 'number', 'format': 'float'},
                    'metadata': {'type': 'object'}
                }
            }
        },
        400: {
            'description': 'Invalid input'
        },
        429: {
            'description': 'Rate limit exceeded'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
@cached(timeout=3600)  # Cache predictions for 1 hour
def predict_rain():
    """
    Predict painting duration based on weather forecast
    
    This endpoint uses machine learning to predict potential delays
    based on weather forecasts and historical data.
    """
    try:
        # Validate request data using Marshmallow schema
        schema = MLPredictionRequestSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as e:
            logger.warning(f"Validation error in ML prediction request: {e.messages}")
            return jsonify({
                'error': 'Validation error',
                'details': e.messages
            }), 400

        # Get prediction
        predictor = MLPredictor(current_app.config['ML_MODEL_PATH'])
        result = predictor.predict_duration(
            data['weather_data'],
            data['location'],
            data['original_duration']
        )

        # Check confidence threshold
        if result['confidence_score'] < current_app.config['MINIMUM_CONFIDENCE_THRESHOLD']:
            logger.warning(
                f"Low confidence prediction ({result['confidence_score']}) "
                f"for location {data['location']}"
            )
            # Add warning to response
            result['warnings'] = ['Low confidence prediction, consider manual review']

        # Log successful prediction
        logger.info(
            f"ML prediction successful for location {data['location']} "
            f"with confidence {result['confidence_score']}"
        )

        return jsonify({
            'success': True,
            'data': {
                'delay_days': result['delay_days'],
                'recommended_duration': result['recommended_duration'],
                'confidence_score': result['confidence_score'],
                'rain_probability': result['rain_probability'],
                'metadata': result['metadata'],
                'warnings': result.get('warnings', [])
            }
        }), 200

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'error': 'Validation error',
            'details': e.messages
        }), 400

    except MLPredictionError as e:
        logger.error(f"ML prediction error: {str(e)}")
        return jsonify({
            'error': 'Prediction error',
            'message': str(e),
            'fallback_prediction': e.fallback_prediction
        }), 500

    except Exception as e:
        logger.error(f"Unexpected error during ML prediction: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

@ml_bp.route('/model/status', methods=['GET'])
@limiter.limit("1000/day")
@swag_from({
    'tags': ['Machine Learning'],
    'responses': {
        200: {
            'description': 'Model status information',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'version': {'type': 'string'},
                    'last_updated': {'type': 'string'},
                    'total_predictions': {'type': 'integer'}
                }
            }
        }
    }
})
def model_status():
    """Get the current status of the ML model"""
    try:
        predictor = MLPredictor(current_app.config['ML_MODEL_PATH'])
        status = {
            'status': 'healthy',
            'version': predictor.model_version,
            'last_updated': predictor.last_updated.isoformat() if hasattr(predictor, 'last_updated') else None,
            'total_predictions': predictor.total_predictions if hasattr(predictor, 'total_predictions') else 0
        }
        return jsonify({'success': True, 'data': status}), 200

    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to get model status'
        }), 500

@ml_bp.route('/model/retrain', methods=['POST'])
@limiter.limit("10/day")  # Strict limit on retraining
def retrain_model():
    """Retrain the ML model with new data"""
    try:
        data = request.get_json()
        predictor = MLPredictor(current_app.config['ML_MODEL_PATH'])
        
        # Update model with new data
        predictor.update_model(data.get('training_data', []))
        
        return jsonify({
            'success': True,
            'message': 'Model successfully retrained',
            'new_version': predictor.model_version
        }), 200

    except Exception as e:
        logger.error(f"Error retraining model: {str(e)}")
        return jsonify({
            'error': 'Training error',
            'message': str(e)
        }), 500
