from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt
)
from app.models.user import User
from app.utils.validators import validate_email
from app.utils.response_utils import success_response, error_response
from app import db
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              description: User's email
            password:
              type: string
              description: User's password
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            success:
              type: boolean
            access_token:
              type: string
            refresh_token:
              type: string
            user:
              type: object
              properties:
                id:
                  type: integer
                email:
                  type: string
                name:
                  type: string
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return error_response('Email and password are required', 400)
    
    if not validate_email(data['email']):
        return error_response('Invalid email format', 400)
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return error_response('Invalid email or password', 401)
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return success_response({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }, 'Login successful')

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh Access Token
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Token refreshed successfully
      401:
        description: Invalid refresh token
    """
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    
    return success_response({
        'access_token': new_access_token
    }, 'Token refreshed successfully')

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User Logout
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Logout successful
      401:
        description: Invalid token
    """
    # In a production environment, you might want to blacklist the token
    # For now, we'll just return a success response as the client should
    # delete the token
    return success_response(message='Logout successful')

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_info():
    """
    Get Current User Info
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: User information retrieved successfully
      401:
        description: Invalid token
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return error_response('User not found', 404)
    
    return success_response({
        'user': user.to_dict()
    }, 'User information retrieved successfully')

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change User Password
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - current_password
            - new_password
          properties:
            current_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Password changed successfully
      401:
        description: Invalid current password
    """
    data = request.get_json()
    
    if not data or 'current_password' not in data or 'new_password' not in data:
        return error_response('Current and new passwords are required', 400)
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return error_response('User not found', 404)
    
    if not user.check_password(data['current_password']):
        return error_response('Current password is incorrect', 401)
    
    if len(data['new_password']) < 8:
        return error_response('New password must be at least 8 characters long', 400)
    
    user.set_password(data['new_password'])
    db.session.commit()
    
    return success_response(message='Password changed successfully')

# Admin-only routes
def admin_required():
    """Decorator to check if user is admin"""
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.is_admin:
                return error_response('Admin access required', 403)
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@auth_bp.route('/admin/users', methods=['GET'])
@admin_required()
def list_users():
    """
    List All Users (Admin Only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: List of all users
      403:
        description: Admin access required
    """
    users = User.query.all()
    return success_response({
        'users': [user.to_dict() for user in users]
    }, 'Users retrieved successfully')
