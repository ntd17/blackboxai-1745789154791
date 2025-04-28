from app import db
from datetime import datetime

class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @classmethod
    def get_value(cls, key, default=None):
        """Get setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set_value(cls, key, value):
        """Set or update setting value"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        db.session.commit()

    @classmethod
    def get_default_signature_method(cls):
        """Get default signature method"""
        return cls.get_value('default_signature_method', 'signature_click_only')

    @classmethod
    def set_default_signature_method(cls, method):
        """Set default signature method"""
        valid_methods = [
            'signature_click_only',
            'signature_token_email',
            'signature_icp_upload',
            'signature_icp_direct'
        ]
        if method not in valid_methods:
            raise ValueError(f"Invalid signature method. Must be one of: {', '.join(valid_methods)}")
        cls.set_value('default_signature_method', method)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
