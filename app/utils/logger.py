import logging
import os
from logging.handlers import RotatingFileHandler
from flask import current_app, request
from datetime import datetime
from typing import Optional, Dict, Any

class APILogger:
    """Custom logger for API operations"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize logger with Flask app"""
        self.app = app
        
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Create handlers
        self._setup_file_handler()
        self._setup_request_logging()
    
    def _setup_file_handler(self):
        """Setup rotating file handler"""
        file_handler = RotatingFileHandler(
            'logs/api.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.app.logger.addHandler(file_handler)
        self.app.logger.setLevel(logging.INFO)
    
    def _setup_request_logging(self):
        """Setup request logging"""
        def log_request():
            """Log incoming request details"""
            self.log_request(request)
        
        def log_response(response):
            """Log outgoing response details"""
            self.log_response(response)
            return response
        
        self.app.before_request(log_request)
        self.app.after_request(log_response)
    
    def log_request(self, request) -> None:
        """
        Log request details
        
        Args:
            request: Flask request object
        """
        try:
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers),
                'args': dict(request.args),
                'remote_addr': request.remote_addr
            }
            
            # Log request body for JSON requests
            if request.is_json:
                log_data['json'] = request.get_json()
            elif request.form:
                log_data['form'] = dict(request.form)
            
            self.app.logger.info(f"Request: {log_data}")
            
        except Exception as e:
            self.app.logger.error(f"Error logging request: {str(e)}")
    
    def log_response(self, response) -> None:
        """
        Log response details
        
        Args:
            response: Flask response object
        """
        try:
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
            
            # Try to parse JSON response
            try:
                if response.is_json:
                    log_data['json'] = response.get_json()
            except:
                pass
            
            self.app.logger.info(f"Response: {log_data}")
            
        except Exception as e:
            self.app.logger.error(f"Error logging response: {str(e)}")
    
    def log_blockchain_tx(self, tx_hash: str, operation: str, metadata: Optional[Dict] = None) -> None:
        """
        Log blockchain transaction
        
        Args:
            tx_hash: Transaction hash
            operation: Operation description
            metadata: Optional transaction metadata
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'tx_hash': tx_hash,
            'operation': operation
        }
        
        if metadata:
            log_data['metadata'] = metadata
        
        self.app.logger.info(f"Blockchain Transaction: {log_data}")
    
    def log_storage_operation(self, operation: str, cid: str, metadata: Optional[Dict] = None) -> None:
        """
        Log storage operation
        
        Args:
            operation: Operation description (upload, download, etc.)
            cid: IPFS CID
            metadata: Optional operation metadata
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'cid': cid
        }
        
        if metadata:
            log_data['metadata'] = metadata
        
        self.app.logger.info(f"Storage Operation: {log_data}")
    
    def log_contract_operation(self, operation: str, contract_id: int, metadata: Optional[Dict] = None) -> None:
        """
        Log contract operation
        
        Args:
            operation: Operation description
            contract_id: Contract ID
            metadata: Optional operation metadata
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'contract_id': contract_id
        }
        
        if metadata:
            log_data['metadata'] = metadata
        
        self.app.logger.info(f"Contract Operation: {log_data}")
    
    def log_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """
        Log error with context
        
        Args:
            error: Exception object
            context: Optional error context
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
        
        if context:
            log_data['context'] = context
        
        self.app.logger.error(f"Error: {log_data}")
    
    def log_weather_prediction(self, location: Dict[str, Any], prediction: Dict[str, Any]) -> None:
        """
        Log weather prediction
        
        Args:
            location: Location details
            prediction: Prediction results
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'location': location,
            'prediction': prediction
        }
        
        self.app.logger.info(f"Weather Prediction: {log_data}")

# Create logger instance
logger = APILogger()

def init_app(app):
    """Initialize logger with Flask app"""
    logger.init_app(app)
