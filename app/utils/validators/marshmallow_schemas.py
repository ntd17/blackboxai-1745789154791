from marshmallow import Schema, fields, validates, validates_schema, ValidationError
from datetime import datetime

class LocationSchema(Schema):
    """Schema for location data"""
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    city = fields.Str(required=True)
    country = fields.Str(required=True)

class WeatherDataSchema(Schema):
    """Schema for weather forecast data"""
    temp = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())
    humidity = fields.Float(required=True)
    wind_speed = fields.Float(required=True)
    rain_prob = fields.Float(required=True)
    rain_amount = fields.Float(required=True)

    @validates('rain_prob')
    def validate_rain_probability(self, value):
        if not 0 <= value <= 1:
            raise ValidationError('Rain probability must be between 0 and 1')

class ContractSchema(Schema):
    """Schema for contract data"""
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    start_date = fields.DateTime(required=True)
    estimated_duration = fields.Int(required=True)
    location = fields.Nested(LocationSchema, required=True)
    party_a = fields.Int(required=True)  # User ID
    party_b = fields.Int(required=True)  # User ID
    weather_data = fields.List(fields.Nested(WeatherDataSchema), required=False)
    status = fields.Str(required=True)

    @validates('estimated_duration')
    def validate_duration(self, value):
        if value <= 0:
            raise ValidationError('Duration must be positive')

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if 'start_date' in data and data['start_date'] < datetime.now():
            raise ValidationError('Start date cannot be in the past')

class SignatureSchema(Schema):
    """Schema for digital signatures"""
    contract_id = fields.Int(required=True)
    signer_id = fields.Int(required=True)
    signature_data = fields.Str(required=True)
    timestamp = fields.DateTime(required=True)
    metadata = fields.Dict(required=False)

    @validates('signature_data')
    def validate_signature(self, value):
        if len(value) < 50:  # Minimum signature data length
            raise ValidationError('Invalid signature data')

class UserSchema(Schema):
    """Schema for user data"""
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    full_name = fields.Str(required=True)
    role = fields.Str(required=True)
    company = fields.Str(required=False)

    @validates('username')
    def validate_username(self, value):
        if len(value) < 3:
            raise ValidationError('Username must be at least 3 characters long')

    @validates('role')
    def validate_role(self, value):
        valid_roles = ['contractor', 'client', 'admin']
        if value not in valid_roles:
            raise ValidationError(f'Role must be one of: {", ".join(valid_roles)}')

class MLPredictionRequestSchema(Schema):
    """Schema for ML prediction requests"""
    weather_data = fields.List(fields.Nested(WeatherDataSchema), required=True)
    location = fields.Nested(LocationSchema, required=True)
    original_duration = fields.Int(required=True)

    @validates('weather_data')
    def validate_weather_data(self, value):
        if len(value) < 1:
            raise ValidationError('Weather data cannot be empty')
        if len(value) > 30:  # Maximum 30 days forecast
            raise ValidationError('Weather forecast exceeds maximum length')

class BlockchainTransactionSchema(Schema):
    """Schema for blockchain transaction requests"""
    contract_id = fields.Int(required=True)
    cid = fields.Str(required=True)
    action = fields.Str(required=True)
    metadata = fields.Dict(required=False)

    @validates('action')
    def validate_action(self, value):
        valid_actions = ['store', 'sign', 'verify']
        if value not in valid_actions:
            raise ValidationError(f'Action must be one of: {", ".join(valid_actions)}')
