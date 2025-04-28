import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'))

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Redis Cache
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://redis:6379/0'
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 3600))
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day"  # Default rate limit
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_STRATEGY = 'fixed-window'  # Valid options: fixed-window, moving-window
    RATELIMIT_HEADERS_ENABLED = True
    
    # API Rate Limits
    RATELIMIT_API_DEFAULT = "100 per hour"
    RATELIMIT_API_WEATHER = "500 per day"  # Weather API specific limit
    RATELIMIT_API_ML = "1000 per day"      # ML predictions limit
    RATELIMIT_API_BLOCKCHAIN = "50 per hour"  # Blockchain operations limit
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Blockchain
    GANACHE_URL = os.environ.get('GANACHE_URL') or 'http://ganache:8545'
    CHAIN_ID = int(os.environ.get('CHAIN_ID', 1337))
    GAS_PRICE = int(os.environ.get('GAS_PRICE', 20000000000))
    
    # Storage
    STORACHA_API_KEY = os.environ.get('STORACHA_API_KEY')
    IPFS_GATEWAY_URL = os.environ.get('IPFS_GATEWAY_URL')
    
    # Email
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # Weather API
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    OPENWEATHER_API_URL = os.environ.get('OPENWEATHER_API_URL')
    
    # Machine Learning
    ML_MODEL_PATH = os.environ.get('ML_MODEL_PATH', 'app/ml/models/duration_predictor.h5')
    MINIMUM_CONFIDENCE_THRESHOLD = float(os.environ.get('MINIMUM_CONFIDENCE_THRESHOLD', 0.7))
