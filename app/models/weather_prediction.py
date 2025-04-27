from app import db
from app.models import TimestampMixin
from datetime import datetime

class WeatherPrediction(TimestampMixin, db.Model):
    __tablename__ = 'weather_predictions'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    
    # Location and Dates
    location = db.Column(db.JSON, nullable=False)  # City, coordinates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Weather Data
    weather_data = db.Column(db.JSON, nullable=False)  # Raw weather API response
    daily_forecasts = db.Column(db.JSON)  # Processed daily forecasts
    
    # Predictions
    rain_probability = db.Column(db.Float)  # Overall rain probability
    predicted_delay_days = db.Column(db.Integer)
    original_duration = db.Column(db.Integer, nullable=False)
    adjusted_duration = db.Column(db.Integer)
    
    # ML Model Results
    confidence_score = db.Column(db.Float)
    model_version = db.Column(db.String(50))
    prediction_metadata = db.Column(db.JSON)  # Additional ML model outputs
    
    def __init__(self, contract_id, location, start_date, end_date, 
                 original_duration, weather_data):
        self.contract_id = contract_id
        self.location = location
        self.start_date = start_date
        self.end_date = end_date
        self.original_duration = original_duration
        self.weather_data = weather_data

    def update_prediction(self, rain_probability, predicted_delay, 
                         adjusted_duration, confidence_score, 
                         model_version, metadata=None):
        self.rain_probability = rain_probability
        self.predicted_delay_days = predicted_delay
        self.adjusted_duration = adjusted_duration
        self.confidence_score = confidence_score
        self.model_version = model_version
        self.prediction_metadata = metadata or {}
        self.updated_at = datetime.utcnow()

    def process_daily_forecasts(self):
        """Process raw weather data into daily forecast summaries"""
        if not self.weather_data:
            return
            
        daily_forecasts = []
        for day in self.weather_data.get('daily', []):
            forecast = {
                'date': day.get('dt'),
                'temp_max': day.get('temp', {}).get('max'),
                'temp_min': day.get('temp', {}).get('min'),
                'humidity': day.get('humidity'),
                'rain_prob': day.get('pop'),
                'rain_amount': day.get('rain', 0),
                'weather_main': day.get('weather', [{}])[0].get('main'),
                'weather_description': day.get('weather', [{}])[0].get('description')
            }
            daily_forecasts.append(forecast)
            
        self.daily_forecasts = daily_forecasts

    def to_dict(self):
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'location': self.location,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'rain_probability': self.rain_probability,
            'predicted_delay_days': self.predicted_delay_days,
            'original_duration': self.original_duration,
            'adjusted_duration': self.adjusted_duration,
            'confidence_score': self.confidence_score,
            'model_version': self.model_version,
            'daily_forecasts': self.daily_forecasts,
            'prediction_metadata': self.prediction_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<WeatherPrediction {self.contract_id} ({self.start_date} to {self.end_date})>'
