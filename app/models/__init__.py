from app import db
from datetime import datetime

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

from app.models.user import User
from app.models.upload import Upload
from app.models.contract import Contract, ContractAdjustment
from app.models.weather_prediction import WeatherPrediction
