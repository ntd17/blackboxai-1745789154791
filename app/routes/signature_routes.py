from flask import jsonify, request, current_app
from app import db
from app.models.contract import Contract
from app.routes import signature_bp
from app.services.storacha import StorachaClient
from app.services.pdf_generator import add_signature_to_pdf
from app.blockchain.web3_client import Web3Client
from datetime import datetime
import json

@signature_bp.route('/contrato/assinar/<string:cid>', methods=['POST'])
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
          type: object
          required:
            - signer_email
            - signature_data
    responses:
      200:
        description: Contract signed successfully
      404:
        description: Contract not found
      400:
        description: Invalid signature data
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ('signer_email', 'signature_data')):
            return jsonify({
                'error': 'Missing required fields',
                'required': ['signer_email', 'signature_data']
            }), 400
            
        contract = Contract.query.filter_by(initial_cid=cid).first_or_404()
        
        # Verify signer email matches contract
        if (data['signer_email'] != contract.provider_email and 
            data['signer_email'] != contract.contractor_email):
            return jsonify({
                'error': 'Unauthorized signer email'
            }), 403
            
        # Get original PDF from Storacha
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        original_pdf = storacha.get_content(cid)
        
        if not original_pdf:
            return jsonify({
                'error': 'Failed to retrieve original contract'
            }), 500
            
        # Add signature to PDF
        signature_metadata = {
            'signer_email': data['signer_email'],
            'signature_data': data['signature_data'],
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr
        }
        
        signed_pdf = add_signature_to_pdf(
            pdf_content=original_pdf,
            signature_data=data['signature_data'],
            metadata=signature_metadata
        )
        
        # Upload signed version to Storacha
        signed_cid = storacha.upload_content(
            content=signed_pdf,
            filename=f"contract_{contract.id}_signed.pdf"
        )
        
        # Update contract
        contract.update_signature(
            signed_cid=signed_cid,
            signature_metadata=signature_metadata
        )
        
        # Register in blockchain
        try:
            web3_client = Web3Client()
            tx_hash = web3_client.register_signature(
                contract_id=contract.id,
                original_cid=cid,
                signed_cid=signed_cid,
                signature_metadata=signature_metadata
            )
            contract.blockchain_tx = tx_hash
        except Exception as e:
            current_app.logger.error(f"Blockchain signature registration failed: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'Contract signed successfully',
            'contract': contract.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contract signing failed: {str(e)}")
        return jsonify({
            'error': 'Contract signing failed',
            'details': str(e)
        }), 500

@signature_bp.route('/contrato/status/<string:cid>', methods=['GET'])
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
    """
    contract = Contract.query.filter(
        (Contract.initial_cid == cid) | (Contract.signed_cid == cid)
    ).first_or_404()
    
    try:
        response = {
            'contract_id': contract.id,
            'status': contract.status,
            'initial_cid': contract.initial_cid,
            'signed_cid': contract.signed_cid,
            'signature_date': contract.signature_date.isoformat() if contract.signature_date else None,
            'signature_metadata': contract.signature_metadata
        }
        
        # Check IPFS availability for both versions
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        
        response['ipfs_status'] = {
            'initial': storacha.check_cid_availability(contract.initial_cid),
            'signed': storacha.check_cid_availability(contract.signed_cid) if contract.signed_cid else None
        }
        
        # Get blockchain verification
        if contract.blockchain_tx:
            web3_client = Web3Client()
            response['blockchain_status'] = web3_client.verify_signature(
                contract_id=contract.id,
                original_cid=contract.initial_cid,
                signed_cid=contract.signed_cid
            )
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting signature status: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve signature status',
            'details': str(e)
        }), 500

@signature_bp.route('/contrato/validar/<string:cid>', methods=['GET'])
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
    """
    contract = Contract.query.filter_by(signed_cid=cid).first_or_404()
    
    try:
        if not contract.signature_metadata:
            return jsonify({
                'error': 'Contract has not been signed'
            }), 400
            
        # Verify signature in blockchain
        web3_client = Web3Client()
        blockchain_verification = web3_client.verify_signature(
            contract_id=contract.id,
            original_cid=contract.initial_cid,
            signed_cid=cid
        )
        
        # Verify IPFS availability
        storacha = StorachaClient(api_key=current_app.config['STORACHA_API_KEY'])
        ipfs_available = storacha.check_cid_availability(cid)
        
        response = {
            'is_valid': blockchain_verification['is_valid'] and ipfs_available,
            'blockchain_verification': blockchain_verification,
            'ipfs_available': ipfs_available,
            'signature_metadata': contract.signature_metadata,
            'contract_status': contract.status
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f"Error validating signature: {str(e)}")
        return jsonify({
            'error': 'Failed to validate signature',
            'details': str(e)
        }), 500
