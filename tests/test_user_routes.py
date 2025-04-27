import pytest
import json
from app.models.user import User

def test_register_user(client):
    """Test user registration"""
    # Test successful registration
    response = client.post('/api/usuarios', json={
        'name': 'New User',
        'email': 'newuser@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['name'] == 'New User'
    assert data['user']['email'] == 'newuser@example.com'
    
    # Test duplicate email
    response = client.post('/api/usuarios', json={
        'name': 'Another User',
        'email': 'newuser@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 409
    data = json.loads(response.data)
    assert 'error' in data
    assert 'already registered' in data['error']
    
    # Test missing fields
    response = client.post('/api/usuarios', json={
        'name': 'Invalid User'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Missing required fields' in data['error']
    
    # Test invalid email format
    response = client.post('/api/usuarios', json={
        'name': 'Invalid User',
        'email': 'invalid-email',
        'password': 'password123'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid email format' in data['error']

def test_get_users(client, init_database):
    """Test getting user list"""
    # Test getting all users
    response = client.get('/api/usuarios')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'users' in data
    assert len(data['users']) > 0
    assert data['users'][0]['email'] == 'test@example.com'

def test_get_user(client, init_database):
    """Test getting specific user"""
    # Test getting existing user
    response = client.get('/api/usuarios/1')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['email'] == 'test@example.com'
    
    # Test getting non-existent user
    response = client.get('/api/usuarios/999')
    
    assert response.status_code == 404

def test_user_model():
    """Test User model functionality"""
    user = User(name='Test User', email='test@example.com')
    user.set_password('password123')
    
    # Test password hashing
    assert user.password_hash is not None
    assert user.password_hash != 'password123'
    assert user.check_password('password123')
    assert not user.check_password('wrongpassword')
    
    # Test to_dict method
    user_dict = user.to_dict()
    assert user_dict['name'] == 'Test User'
    assert user_dict['email'] == 'test@example.com'
    assert 'password_hash' not in user_dict
    
    # Test string representation
    assert str(user) == '<User test@example.com>'

def test_user_validation():
    """Test user data validation"""
    # Test valid user
    user = User(name='Valid User', email='valid@example.com')
    assert user.name == 'Valid User'
    assert user.email == 'valid@example.com'
    
    # Test empty name
    with pytest.raises(ValueError):
        User(name='', email='valid@example.com')
    
    # Test None email
    with pytest.raises(ValueError):
        User(name='Valid User', email=None)
    
    # Test invalid email format
    with pytest.raises(ValueError):
        User(name='Valid User', email='invalid-email')

def test_user_relationships(app, init_database):
    """Test user relationships with other models"""
    with app.app_context():
        user = User.query.first()
        
        # Test uploads relationship
        assert hasattr(user, 'uploads')
        assert user.uploads.count() == 0
        
        # Test contracts relationship
        assert hasattr(user, 'contracts_created')
        assert user.contracts_created.count() == 1
        
        contract = user.contracts_created.first()
        assert contract.title == 'Test Contract'
