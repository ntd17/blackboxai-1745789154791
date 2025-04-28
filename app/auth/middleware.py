from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User
from app.utils.response_utils import error_response

def jwt_required_with_role(*roles):
    """
    Custom decorator that combines JWT verification with role checking
    
    Args:
        *roles: Variable number of role names required for access
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # First verify JWT token
            verify_jwt_in_request()
            
            # Get current user
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return error_response('User not found', 404)
            
            # If no roles specified, just check for valid JWT
            if not roles:
                return fn(*args, **kwargs)
            
            # Check if user has any of the required roles
            if not any(getattr(user, f'is_{role}', False) for role in roles):
                return error_response(
                    'Insufficient permissions',
                    403,
                    {'required_roles': roles}
                )
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def admin_required():
    """Decorator for admin-only routes"""
    return jwt_required_with_role('admin')

def owner_required(get_owner_id):
    """
    Decorator for routes that require resource ownership
    
    Args:
        get_owner_id: Function that extracts owner ID from request
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Get the owner ID using the provided function
            owner_id = get_owner_id(request, *args, **kwargs)
            
            if current_user_id != owner_id:
                return error_response('Not authorized to access this resource', 403)
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def validate_json(*required_fields):
    """
    Decorator to validate JSON payload
    
    Args:
        *required_fields: Required field names in the JSON payload
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if not request.is_json:
                return error_response('Content-Type must be application/json', 400)
            
            data = request.get_json()
            
            if not data:
                return error_response('No JSON data provided', 400)
            
            missing_fields = [
                field for field in required_fields
                if field not in data
            ]
            
            if missing_fields:
                return error_response(
                    'Missing required fields',
                    400,
                    {'missing_fields': missing_fields}
                )
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def rate_limit(limit=100, window=60):
    """
    Basic rate limiting decorator
    
    Args:
        limit: Maximum number of requests
        window: Time window in seconds
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    import threading
    
    # Store request counts per user
    requests = defaultdict(list)
    lock = threading.Lock()
    
    def cleanup_old_requests():
        """Remove requests older than the window"""
        now = datetime.now()
        with lock:
            for user_id in list(requests.keys()):
                requests[user_id] = [
                    req_time for req_time in requests[user_id]
                    if now - req_time < timedelta(seconds=window)
                ]
    
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            cleanup_old_requests()
            
            with lock:
                user_requests = requests[current_user_id]
                if len(user_requests) >= limit:
                    return error_response(
                        'Rate limit exceeded',
                        429,
                        {
                            'limit': limit,
                            'window': window,
                            'retry_after': window - (datetime.now() - user_requests[0]).seconds
                        }
                    )
                
                user_requests.append(datetime.now())
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# Example usage of combined decorators:
"""
@app.route('/api/protected')
@jwt_required_with_role('admin', 'manager')
@validate_json('name', 'email')
@rate_limit(limit=10, window=60)
def protected_route():
    # This route requires:
    # 1. Valid JWT token
    # 2. User must be admin or manager
    # 3. JSON payload must contain 'name' and 'email'
    # 4. Limited to 10 requests per minute
    pass
"""
