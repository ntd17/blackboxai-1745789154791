from flask import Blueprint

# Create blueprints
user_bp = Blueprint('user', __name__)
storage_bp = Blueprint('storage', __name__)
contract_bp = Blueprint('contract', __name__)
signature_bp = Blueprint('signature', __name__)

# Import routes
from app.routes import user_routes
from app.routes import storage_routes
from app.routes import contract_routes
from app.routes import signature_routes

# Make blueprints available at module level
__all__ = ['user_bp', 'storage_bp', 'contract_bp', 'signature_bp']
