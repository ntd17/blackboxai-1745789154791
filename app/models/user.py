from app import db
from app.models import TimestampMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(TimestampMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    # Relationships
    uploads = db.relationship('Upload', backref='user', lazy='dynamic')
    contracts_created = db.relationship('Contract', 
                                     foreign_keys='Contract.creator_id',
                                     backref='creator', 
                                     lazy='dynamic')

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<User {self.email}>'
