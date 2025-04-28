from flask import jsonify, request
from app import db
from app.models.user import User
from app.routes import user_bp
from app.utils.validators import validate_email
from sqlalchemy.exc import IntegrityError

@user_bp.route('/usuarios', methods=['POST'])
@user_bp.route('/api/usuarios', methods=['POST'])
def register_user():
    """
    Register a new user
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - name
            - email
            - password
          properties:
            name:
              type: string
              description: User's full name
            email:
              type: string
              description: User's email address
            password:
              type: string
              description: User's password
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid input data
      409:
        description: Email already registered
    """
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('name', 'email', 'password')):
        return jsonify({
            'error': 'Missing required fields',
            'required': ['name', 'email', 'password']
        }), 400
    
    # Validate email format
    if not validate_email(data['email']):
        return jsonify({
            'error': 'Invalid email format'
        }), 400
    
    # Create new user
    try:
        user = User(
            name=data['name'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'error': 'Email already registered'
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@user_bp.route('/usuarios', methods=['GET'])
@user_bp.route('/api/usuarios', methods=['GET'])
def get_users():
    """
    Get list of users
    ---
    tags:
      - Users
    responses:
      200:
        description: List of users
    """
    users = User.query.all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    }), 200

@user_bp.route('/usuarios/<int:user_id>', methods=['GET'])
@user_bp.route('/api/usuarios/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user by ID
    ---
    tags:
      - Users
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: User details
      404:
        description: User not found
    """
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200
