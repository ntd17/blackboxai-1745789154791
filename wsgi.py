import os
from app import create_app

# Load the appropriate configuration based on environment
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app()

if __name__ == '__main__':
    # Only for development
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
