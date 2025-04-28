from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.services.ml_service import MLPredictor
from app.utils.logger import get_logger

ml_bp = Blueprint('ml_bp', __name__)
logger = get_logger()

@ml_bp.route('/predict_rain', methods=['POST'])
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
                    'rain_probability': {'type': 'number', 'format': 'float'}
                }
            }
        },
        400: {
            'description': 'Invalid input'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def predict_rain():
    try:
        data = request.get_json()
        weather_data = data.get('weather_data')
        location = data.get('location')
        original_duration = data.get('original_duration')

        if weather_data is None or location is None or original_duration is None:
            return jsonify({'error': 'Missing required fields'}), 400

        predictor = MLPredictor()
        result = predictor.predict_duration(weather_data, location, original_duration)

        response = {
            'delay_days': result.get('delay_days', 0),
            'recommended_duration': result.get('recommended_duration', original_duration),
            'confidence_score': result.get('confidence_score', 0.0),
            'rain_probability': result.get('rain_probability', 0.0)
        }

        logger.info(f"ML prediction successful for location {location} with result: {response}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error during ML prediction: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
