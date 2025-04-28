from flask import jsonify, request, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.upload import Upload
from app.routes import storage_bp
from app.services.storacha import StorachaClient
from app.blockchain.web3_client import Web3Client
from app.utils.validators.marshmallow_schemas import UploadSchema
from app.utils.error_handlers import ValidationError, StorageError
from app.utils.cache import cached
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_url=current_app.config['REDIS_URL']
)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@storage_bp.route('/upload', methods=['POST'])
@limiter.limit("100/hour")  # Limit file uploads
def upload_file():
    """
    Upload file to Storacha and register CID
    ---
    tags:
      - Storage
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: File to upload (max 16MB)
      - in: formData
        name: user_id
        type: integer
        required: true
        description: ID of the user uploading the file
    responses:
      201:
        description: File uploaded successfully
      400:
        description: Invalid request
      413:
        description: File too large
      429:
        description: Rate limit exceeded
      500:
        description: Upload or blockchain registration failed
    """
    try:
        # Validate request
        if 'file' not in request.files:
            raise ValidationError('No file provided')
            
        if 'user_id' not in request.form:
            raise ValidationError('User ID required')
            
        file = request.files['file']
        user_id = request.form['user_id']
        
        if file.filename == '':
            raise ValidationError('No file selected')
            
        if not allowed_file(file.filename):
            raise ValidationError(f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}')
            
        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_FILE_SIZE:
            raise ValidationError('File too large. Maximum size is 16MB')
            
        filename = secure_filename(file.filename)
        
        # Initialize Storacha client
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        
        # Upload to Storacha
        try:
            cid = storacha.upload_file(file)
        except Exception as e:
            raise StorageError(f"Storacha upload failed: {str(e)}")
            
        if not cid:
            raise StorageError("Failed to get CID from Storacha")
            
        # Create upload record
        upload = Upload(
            user_id=user_id,
            filename=filename,
            cid=cid,
            mime_type=file.content_type,
            file_size=size
        )
        
        db.session.add(upload)
        db.session.commit()
        
        # Register CID in blockchain
        try:
            web3_client = Web3Client()
            tx_hash = web3_client.register_cid(cid, user_id)
            
            if tx_hash:
                upload.update_blockchain_status(tx_hash)
                db.session.commit()
                
        except Exception as e:
            current_app.logger.warning(f"Blockchain registration failed: {str(e)}")
            # Continue even if blockchain registration fails
            
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'data': upload.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation error',
            'message': str(e)
        }), 400
        
    except StorageError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Storage error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload failed: {str(e)}")
        return jsonify({
            'error': 'Upload failed',
            'message': str(e)
        }), 500

@storage_bp.route('/cids', methods=['GET'])
@limiter.limit("300/hour")
@cached(timeout=300)  # Cache for 5 minutes
def list_cids():
    """
    List all CIDs
    ---
    tags:
      - Storage
    parameters:
      - in: query
        name: user_id
        type: integer
        description: Filter by user ID
      - in: query
        name: page
        type: integer
        description: Page number (default: 1)
      - in: query
        name: per_page
        type: integer
        description: Items per page (default: 20, max: 100)
    responses:
      200:
        description: List of CIDs
      429:
        description: Rate limit exceeded
    """
    try:
        user_id = request.args.get('user_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = Upload.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
            
        pagination = query.order_by(Upload.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [upload.to_dict() for upload in pagination.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error listing CIDs: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve CIDs',
            'message': str(e)
        }), 500

@storage_bp.route('/cids/<string:cid>', methods=['GET'])
@limiter.limit("300/hour")
@cached(timeout=300)  # Cache for 5 minutes
def get_cid_info(cid):
    """
    Get information about a specific CID
    ---
    tags:
      - Storage
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: IPFS CID
    responses:
      200:
        description: CID information
      404:
        description: CID not found
      429:
        description: Rate limit exceeded
    """
    upload = Upload.query.filter_by(cid=cid).first_or_404()
    
    try:
        # Check IPFS availability
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        is_available = storacha.check_cid_availability(cid)
        
        # Get blockchain status
        web3_client = Web3Client()
        blockchain_status = web3_client.get_cid_status(cid)
        
        response = upload.to_dict()
        response.update({
            'ipfs_available': is_available,
            'blockchain_status': blockchain_status
        })
        
        return jsonify({
            'success': True,
            'data': response
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting CID info: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve CID information',
            'message': str(e)
        }), 500

@storage_bp.route('/cids/<string:cid>/verify', methods=['GET'])
@limiter.limit("100/hour")
@cached(timeout=60)  # Cache for 1 minute
def verify_cid(cid):
    """
    Verify CID integrity across storage and blockchain
    ---
    tags:
      - Storage
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: IPFS CID
    responses:
      200:
        description: Verification result
      404:
        description: CID not found
      429:
        description: Rate limit exceeded
    """
    upload = Upload.query.filter_by(cid=cid).first_or_404()
    
    try:
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        web3_client = Web3Client()
        
        verification = {
            'ipfs': {
                'available': storacha.check_cid_availability(cid),
                'timestamp': upload.created_at.isoformat()
            },
            'blockchain': web3_client.verify_cid(cid)
        }
        
        return jsonify({
            'success': True,
            'data': {
                'cid': cid,
                'verification': verification
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error verifying CID: {str(e)}")
        return jsonify({
            'error': 'Failed to verify CID',
            'message': str(e)
        }), 500
