import pytest
from app import create_app, db
from config import Config
import os
import tempfile

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # Use in-memory database
    WTF_CSRF_ENABLED = False
    STORACHA_API_KEY = 'test_key'
    OPENWEATHER_API_KEY = 'test_key'
    ML_MODEL_PATH = os.path.join(tempfile.gettempdir(), 'test_model.h5')

@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    app = create_app(TestConfig)
    
    # Create test database and tables
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Clean up
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def init_database(app):
    """Initialize database with test data"""
    with app.app_context():
        # Create test user
        from app.models.user import User
        user = User(name='Test User', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        
        # Create test contract
        from app.models.contract import Contract
        contract = Contract(
            creator_id=1,
            title='Test Contract',
            location={
                'city': 'Test City',
                'state': 'TS',
                'coordinates': {
                    'lat': 0,
                    'lon': 0
                }
            },
            planned_start_date='2024-01-01',
            planned_duration_days=7,
            contractor_name='Test Contractor',
            contractor_email='contractor@example.com',
            provider_name='Test Provider',
            provider_email='provider@example.com',
            amount=1000.00,
            payment_method='Credit Card'
        )
        db.session.add(contract)
        
        db.session.commit()
        
        yield

@pytest.fixture
def auth_headers():
    """Create authentication headers for testing"""
    return {
        'Authorization': 'Bearer test_token',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def mock_weather_data():
    """Mock weather forecast data"""
    return {
        'daily': [
            {
                'dt': 1640995200,  # 2022-01-01
                'temp': {
                    'day': 20,
                    'min': 15,
                    'max': 25
                },
                'humidity': 70,
                'wind_speed': 5,
                'pop': 0.3,  # 30% chance of rain
                'rain': 2,
                'weather': [
                    {
                        'main': 'Rain',
                        'description': 'light rain',
                        'icon': '10d'
                    }
                ]
            }
        ],
        'lat': 0,
        'lon': 0
    }

@pytest.fixture
def mock_blockchain_tx():
    """Mock blockchain transaction hash"""
    return '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'

@pytest.fixture
def mock_storacha_cid():
    """Mock Storacha CID"""
    return 'QmTest1234567890abcdef'
