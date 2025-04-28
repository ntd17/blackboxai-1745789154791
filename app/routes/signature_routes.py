from flask import jsonify, request, current_app
from app import db
from app.models.contract import Contract
from app.models.settings import Settings
from app.routes import signature_bp
from app.services.storacha import StorachaClient
from app.services.pdf_generator import add_signature_to_pdf
from app.services.signature_service import SignatureService
from app.blockchain.web3_client import Web3Client, ContractStatus
from app.utils.validators.marshmallow_schemas import SignatureSchema, TokenRequestSchema
from app.utils.error_handlers import ValidationError, BlockchainError, StorageError
from app.utils.cache import cached
from app.services.email_service import EmailService
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import json

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_url=current_app.config['REDIS_URL']
)

@signature_bp.route('/contrato/solicitar/<string:cid>', methods=['POST'])
@limiter.limit("50/hour")
def request_signature(cid):
    """
    Request contract signature
    ---
    tags:
      - Signatures
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: Contract CID
    responses:
      200:
        description: Signature request sent successfully
      404:
        description: Contract not found
      429:
        description: Rate limit exceeded
    """
    try:
        contract = Contract.query.filter_by(initial_cid=cid).first_or_404()
        
        web3_client = Web3Client()
        tx_hash = web3_client.request_signature(contract.id)
        
        contract.update_status('pending_signature', tx_hash)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Signature request sent successfully',
            'data': {
                'contract': contract.to_dict(),
                'transaction_hash': tx_hash
            }
        }), 200
        
    except BlockchainError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Blockchain error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Signature request failed: {str(e)}")
        return jsonify({
            'error': 'Signature request failed',
            'message': str(e)
        }), 500

# Initialize services
signature_service = SignatureService(current_app.config)
email_service = EmailService()

@signature_bp.route('/contrato/metodos', methods=['GET'])
def get_signature_methods():
    """Get available signature methods"""
    methods = {
        'signature_click_only': 'Simple Click Signature',
        'signature_token_email': 'Email Token Verification',
        'signature_icp_upload': 'ICP-Brasil Certificate Upload',
        'signature_icp_direct': 'ICP-Brasil Direct Signature'
    }
    
    default_method = Settings.get_default_signature_method()
    
    return jsonify({
        'success': True,
        'data': {
            'methods': methods,
            'default_method': default_method
        }
    }), 200

@signature_bp.route('/contrato/token/solicitar', methods=['POST'])
@limiter.limit("5/minute")
def request_token():
    """Request email verification token"""
    try:
        schema = TokenRequestSchema()
        data = schema.load(request.get_json())
        
        contract = Contract.query.filter_by(initial_cid=data['cid']).first_or_404()
        
        # Verify email matches contract
        if (data['email'] != contract.provider_email and 
            data['email'] != contract.contractor_email):
            return jsonify({
                'error': 'Unauthorized email address'
            }), 403
        
        # Generate token
        token, expiry = signature_service.generate_email_token(
            email=data['email'],
            cpf=data['cpf']
        )
        
        # Store token in contract
        contract.set_token(token, expiry)
        db.session.commit()
        
        # Send token via email
        email_service.send_signature_token(
            email=data['email'],
            token=token,
            contract_title=contract.title
        )
        
        return jsonify({
            'success': True,
            'message': 'Token sent successfully',
            'data': {
                'expiry': expiry.isoformat()
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation error',
            'details': e.messages
        }), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Token request failed: {str(e)}")
        return jsonify({
            'error': 'Token request failed',
            'message': str(e)
        }), 500

@signature_bp.route('/contrato/token/validar', methods=['POST'])
@limiter.limit("5/minute")
def validate_token():
    """Validate email token"""
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({
                'error': 'Token is required'
            }), 400
            
        contract = Contract.query.filter_by(token_email=data['token']).first_or_404()
        
        # Validate token
        try:
            token_data = signature_service.validate_email_token(data['token'])
        except ValueError as e:
            return jsonify({
                'error': 'Invalid token',
                'message': str(e)
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Token validated successfully',
            'data': {
                'contract': contract.to_dict(),
                'token_data': token_data
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token validation failed: {str(e)}")
        return jsonify({
            'error': 'Token validation failed',
            'message': str(e)
        }), 500

@signature_bp.route('/contrato/assinar/<string:cid>', methods=['POST'])
@signature_bp.route('/api/contrato/assinar/<string:cid>', methods=['POST'])
@limiter.limit("20/hour")
def sign_contract(cid):
    """
    Sign a contract
    ---
    tags:
      - Signatures
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: Contract CID
      - in: body
        name: body
        schema:
          $ref: '#/definitions/SignatureRequest'
    responses:
      200:
        description: Contract signed successfully
      404:
        description: Contract not found
      429:
        description: Rate limit exceeded
    """
    try:
        # Validate request data
        schema = SignatureSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as e:
            return jsonify({
                'error': 'Validation error',
                'details': e.messages
            }), 400
            
        contract = Contract.query.filter_by(initial_cid=cid).first_or_404()
        
        # Get signature method
        signature_method = data.get('signature_method', Settings.get_default_signature_method())
        
        # Verify signer email matches contract
        if (data['signer_email'] != contract.provider_email and 
            data['signer_email'] != contract.contractor_email):
            return jsonify({
                'error': 'Unauthorized signer email'
            }), 403
            
        # Handle different signature methods
        if signature_method == 'signature_token_email':
            # Validate token if provided
            if not data.get('token'):
                return jsonify({
                    'error': 'Token is required for email verification method'
                }), 400
                
            try:
                token_data = signature_service.validate_email_token(data['token'])
                if token_data['email'] != data['signer_email']:
                    return jsonify({
                        'error': 'Token email mismatch'
                    }), 400
            except ValueError as e:
                return jsonify({
                    'error': 'Invalid token',
                    'message': str(e)
                }), 400
                
        elif signature_method in ['signature_icp_upload', 'signature_icp_direct']:
            # Validate ICP-Brasil certificate
            if not data.get('certificate_data'):
                return jsonify({
                    'error': 'Certificate data is required for ICP-Brasil methods'
                }), 400
                
            try:
                cert_info = signature_service.validate_icp_certificate(
                    data['certificate_data']
                )
                contract.set_certificate_info(cert_info)
            except ValueError as e:
                return jsonify({
                    'error': 'Invalid certificate',
                    'message': str(e)
                }), 400
            
        # Get original PDF from Storacha
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        try:
            original_pdf = storacha.get_content(cid)
        except Exception as e:
            raise StorageError("Failed to retrieve original contract", str(e))
            
        # Process signature based on method
        signature_metadata = signature_service.get_signature_metadata(
            method=signature_method,
            email=data['signer_email'],
            cpf=data.get('cpf'),
            ip_address=request.remote_addr,
            certificate_info=contract.certificate_info
        )
        
        if signature_method in ['signature_icp_upload', 'signature_icp_direct']:
            # Sign PDF with ICP-Brasil certificate
            signed_pdf = signature_service.sign_pdf_with_certificate(
                pdf_content=original_pdf,
                cert_data=data['certificate_data'],
                password=data.get('certificate_password', '')
            )
        else:
            # Regular signature
            signed_pdf = add_signature_to_pdf(
                pdf_content=original_pdf,
                signature_data=data['signature_data'],
                metadata=signature_metadata
            )
        
        # Upload signed version to Storacha
        try:
            signed_cid = storacha.upload_content(
                content=signed_pdf,
                filename=f"contract_{contract.id}_signed.pdf"
            )
        except Exception as e:
            raise StorageError("Failed to store signed contract", str(e))
        
        # Register in blockchain
        web3_client = Web3Client()
        tx_hash = web3_client.sign_contract(
            contract_id=contract.id,
            original_cid=cid,
            signed_cid=signed_cid,
            signature_metadata=signature_metadata
        )
        
        # Update contract
        contract.update_signature(
            signed_cid=signed_cid,
            signature_metadata=signature_metadata,
            signature_method=signature_method,
            blockchain_tx=tx_hash
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contract signed successfully',
            'data': {
                'contract': contract.to_dict(),
                'transaction_hash': tx_hash
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation error',
            'details': e.messages
        }), 400
        
    except StorageError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Storage error',
            'message': str(e)
        }), 500
        
    except BlockchainError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Blockchain error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contract signing failed: {str(e)}")
        return jsonify({
            'error': 'Contract signing failed',
            'message': str(e)
        }), 500

@signature_bp.route('/contrato/cancelar/<string:cid>', methods=['POST'])
@limiter.limit("20/hour")
def cancel_contract(cid):
    """
    Cancel a contract
    ---
    tags:
      - Signatures
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: Contract CID
    responses:
      200:
        description: Contract cancelled successfully
      404:
        description: Contract not found
      429:
        description: Rate limit exceeded
    """
    try:
        contract = Contract.query.filter_by(initial_cid=cid).first_or_404()
        
        web3_client = Web3Client()
        tx_hash = web3_client.cancel_contract(contract.id)
        
        contract.update_status('cancelled', tx_hash)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contract cancelled successfully',
            'data': {
                'contract': contract.to_dict(),
                'transaction_hash': tx_hash
            }
        }), 200
        
    except BlockchainError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Blockchain error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contract cancellation failed: {str(e)}")
        return jsonify({
            'error': 'Contract cancellation failed',
            'message': str(e)
        }), 500

@signature_bp.route('/contrato/status/<string:cid>', methods=['GET'])
@limiter.limit("300/hour")
@cached(timeout=60)  # Cache for 1 minute
def get_signature_status(cid):
    """
    Get signature status and details
    ---
    tags:
      - Signatures
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: Contract CID (original or signed)
    responses:
      200:
        description: Signature status and details
      404:
        description: Contract not found
      429:
        description: Rate limit exceeded
    """
    contract = Contract.query.filter(
        (Contract.initial_cid == cid) | (Contract.signed_cid == cid)
    ).first_or_404()
    
    try:
        web3_client = Web3Client()
        contract_details = web3_client.get_contract_details(contract.id)
        
        # Get blockchain events
        events = web3_client.get_contract_events(contract.id)
        
        # Check IPFS availability
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        ipfs_status = {
            'initial': storacha.check_cid_availability(contract.initial_cid),
            'signed': storacha.check_cid_availability(contract.signed_cid) if contract.signed_cid else None
        }
        
        response = {
            'contract': contract.to_dict(),
            'blockchain_details': contract_details,
            'events': events,
            'ipfs_status': ipfs_status
        }
        
        return jsonify({
            'success': True,
            'data': response
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting signature status: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve signature status',
            'message': str(e)
        }), 500

@signature_bp.route('/contrato/validar/<string:cid>', methods=['GET'])
@limiter.limit("100/hour")
@cached(timeout=300)  # Cache for 5 minutes
def validate_signature(cid):
    """
    Validate contract signature
    ---
    tags:
      - Signatures
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: Signed contract CID
    responses:
      200:
        description: Signature validation result
      404:
        description: Contract not found
      429:
        description: Rate limit exceeded
    """
    contract = Contract.query.filter_by(signed_cid=cid).first_or_404()
    
    try:
        if not contract.signature_metadata:
            return jsonify({
                'error': 'Contract has not been signed'
            }), 400
            
        web3_client = Web3Client()
        
        # Get contract details and signature verification
        contract_details = web3_client.get_contract_details(contract.id)
        signature_details = web3_client.get_signature_details(contract.id)
        
        # Verify IPFS availability
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        ipfs_status = {
            'initial': storacha.check_cid_availability(contract.initial_cid),
            'signed': storacha.check_cid_availability(cid)
        }
        
        response = {
            'contract_details': contract_details,
            'signature_details': signature_details,
            'ipfs_status': ipfs_status,
            'validation': {
                'is_valid': (
                    contract_details['status'] == ContractStatus.Signed.name and
                    signature_details['signed_cid'] == cid and
                    all(ipfs_status.values())
                )
            }
        }
        
        return jsonify({
            'success': True,
            'data': response
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error validating signature: {str(e)}")
        return jsonify({
            'error': 'Failed to validate signature',
            'message': str(e)
        }), 500
