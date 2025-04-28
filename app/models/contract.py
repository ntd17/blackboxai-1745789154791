from app import db
from app.models import TimestampMixin
from datetime import datetime

class Contract(TimestampMixin, db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Contract Details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.JSON, nullable=False)  # Address and coordinates
    planned_start_date = db.Column(db.Date, nullable=False)
    planned_duration_days = db.Column(db.Integer, nullable=False)
    adjusted_duration_days = db.Column(db.Integer)
    
    # Parties
    contractor_name = db.Column(db.String(100), nullable=False)
    contractor_email = db.Column(db.String(120), nullable=False)
    provider_name = db.Column(db.String(100), nullable=False)
    provider_email = db.Column(db.String(120), nullable=False)
    
    # Payment
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    
    # Document Status
    initial_cid = db.Column(db.String(255))  # Unsigned contract CID
    signed_cid = db.Column(db.String(255))   # Signed contract CID
    status = db.Column(db.String(20), default='draft')  # draft, pending_signature, signed, cancelled
    
    # Signature Details
    signature_date = db.Column(db.DateTime)
    signature_metadata = db.Column(db.JSON)
    signature_method = db.Column(db.String(50))
    token_email = db.Column(db.String(255))
    token_expiry = db.Column(db.DateTime)
    certificate_info = db.Column(db.JSON)
    
    # Blockchain
    blockchain_tx = db.Column(db.String(255))  # Transaction hash for contract registration
    
    # Relationships
    weather_prediction = db.relationship('WeatherPrediction', 
                                       backref='contract', 
                                       uselist=False)
    adjustments = db.relationship('ContractAdjustment', 
                                backref='contract', 
                                lazy='dynamic')

    def __init__(self, creator_id, title, location, planned_start_date, 
                 planned_duration_days, contractor_name, contractor_email,
                 provider_name, provider_email, amount, payment_method):
        self.creator_id = creator_id
        self.title = title
        self.location = location
        self.planned_start_date = planned_start_date
        self.planned_duration_days = planned_duration_days
        self.contractor_name = contractor_name
        self.contractor_email = contractor_email
        self.provider_name = provider_name
        self.provider_email = provider_email
        self.amount = amount
        self.payment_method = payment_method

    def update_signature(self, signed_cid, signature_metadata, signature_method=None):
        self.signed_cid = signed_cid
        self.status = 'signed'
        self.signature_date = datetime.utcnow()
        self.signature_metadata = signature_metadata
        if signature_method:
            self.signature_method = signature_method
        self.updated_at = datetime.utcnow()

    def set_token(self, token, expiry):
        """Set email verification token"""
        self.token_email = token
        self.token_expiry = expiry
        self.updated_at = datetime.utcnow()

    def set_certificate_info(self, cert_info):
        """Set ICP-Brasil certificate information"""
        self.certificate_info = cert_info
        self.updated_at = datetime.utcnow()

    def adjust_duration(self, adjusted_days, reason):
        self.adjusted_duration_days = adjusted_days
        adjustment = ContractAdjustment(
            contract_id=self.id,
            original_duration=self.planned_duration_days,
            adjusted_duration=adjusted_days,
            adjustment_reason=reason
        )
        db.session.add(adjustment)

    def to_dict(self):
        return {
            'id': self.id,
            'creator_id': self.creator_id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'planned_start_date': self.planned_start_date.isoformat(),
            'planned_duration_days': self.planned_duration_days,
            'adjusted_duration_days': self.adjusted_duration_days,
            'contractor_name': self.contractor_name,
            'contractor_email': self.contractor_email,
            'provider_name': self.provider_name,
            'provider_email': self.provider_email,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'initial_cid': self.initial_cid,
            'signed_cid': self.signed_cid,
            'status': self.status,
            'signature_date': self.signature_date.isoformat() if self.signature_date else None,
            'blockchain_tx': self.blockchain_tx,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContractAdjustment(TimestampMixin, db.Model):
    __tablename__ = 'contract_adjustments'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    original_duration = db.Column(db.Integer, nullable=False)
    adjusted_duration = db.Column(db.Integer, nullable=False)
    adjustment_reason = db.Column(db.Text, nullable=False)
    weather_prediction_id = db.Column(db.Integer, db.ForeignKey('weather_predictions.id'))
    user_override = db.Column(db.Boolean, default=False)
    override_reason = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'original_duration': self.original_duration,
            'adjusted_duration': self.adjusted_duration,
            'adjustment_reason': self.adjustment_reason,
            'weather_prediction_id': self.weather_prediction_id,
            'user_override': self.user_override,
            'override_reason': self.override_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
