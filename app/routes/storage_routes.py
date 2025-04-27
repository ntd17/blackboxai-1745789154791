from flask import jsonify, request, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.upload import Upload
from app.routes import storage_bp
from app.services.storacha import StorachaClient
from app.blockchain.web3_client import Web3Client
import os

@storage_bp.route('/upload', methods=['POST'])
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
        description: File to upload
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
      500:
        description: Upload or blockchain registration failed
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        if 'user_id' not in request.form:
            return jsonify({'error': 'User ID required'}), 400
            
        file = request.files['file']
        user_id = request.form['user_id']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        filename = secure_filename(file.filename)
        
        # Initialize Storacha client
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        
        # Upload to Storacha
        cid = storacha.upload_file(file)
        
        if not cid:
            return jsonify({'error': 'Storacha upload failed'}), 500
            
        # Create upload record
        upload = Upload(
            user_id=user_id,
            filename=filename,
            cid=cid,
            mime_type=file.content_type,
            file_size=file.content_length if hasattr(file, 'content_length') else None
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
            current_app.logger.error(f"Blockchain registration failed: {str(e)}")
            # Continue even if blockchain registration fails
            
        return jsonify({
            'message': 'File uploaded successfully',
            'upload': upload.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload failed: {str(e)}")
        return jsonify({
            'error': 'Upload failed',
            'details': str(e)
        }), 500

@storage_bp.route('/cids', methods=['GET'])
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
    responses:
      200:
        description: List of CIDs
    """
    try:
        user_id = request.args.get('user_id', type=int)
        query = Upload.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
            
        uploads = query.order_by(Upload.created_at.desc()).all()
        
        return jsonify({
            'cids': [upload.to_dict() for upload in uploads]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error listing CIDs: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve CIDs',
            'details': str(e)
        }), 500

@storage_bp.route('/cids/<string:cid>', methods=['GET'])
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
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting CID info: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve CID information',
            'details': str(e)
        }), 500
