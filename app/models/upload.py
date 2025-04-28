from app import db
from app.models import TimestampMixin
from datetime import datetime

class Upload(TimestampMixin, db.Model):
    __tablename__ = 'uploads'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    cid = db.Column(db.String(255), nullable=False, unique=True)
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)  # Size in bytes
    blockchain_tx = db.Column(db.String(255))  # Transaction hash
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    
    # Metadata
    ipfs_url = db.Column(db.String(512))
    file_metadata = db.Column(db.JSON, info={'alias': 'metadata'})  # Renamed to avoid SQLAlchemy conflict

    def __init__(self, user_id, filename, cid, mime_type=None, file_size=None):
        self.user_id = user_id
        self.filename = filename
        self.cid = cid
        self.mime_type = mime_type
        self.file_size = file_size
        self.ipfs_url = f"ipfs://{cid}"

    def update_blockchain_status(self, tx_hash):
        self.blockchain_tx = tx_hash
        self.status = 'confirmed'
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'cid': self.cid,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'blockchain_tx': self.blockchain_tx,
            'status': self.status,
            'ipfs_url': self.ipfs_url,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Upload {self.filename} (CID: {self.cid})>'
