import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.models.contract import Contract

def test_sign_contract(client, init_database, mock_storacha_cid, mock_blockchain_tx):
    """Test contract signing endpoint"""
    # Create test contract
    contract = Contract.query.first()
    contract.initial_cid = mock_storacha_cid
    
    from app import db
    db.session.commit()
    
    signature_data = {
        'signer_email': 'provider@example.com',
        'signature_data': {
            'signature': 'test_signature',
            'timestamp': datetime.utcnow().isoformat()
        }
    }
    
    # Mock Storacha operations
    with patch('app.services.storacha.StorachaClient.get_content') as mock_get:
        mock_get.return_value = b'Original PDF content'
        
        with patch('app.services.pdf_generator.add_signature_to_pdf') as mock_sign_pdf:
            mock_sign_pdf.return_value = b'Signed PDF content'
            
            with patch('app.services.storacha.StorachaClient.upload_content') as mock_upload:
                mock_upload.return_value = 'signed_' + mock_storacha_cid
                
                # Mock blockchain registration
                with patch('app.blockchain.web3_client.Web3Client.register_signature') as mock_register:
                    mock_register.return_value = mock_blockchain_tx
                    
                    # Test successful signing
                    response = client.post(
                        f'/api/contrato/assinar/{mock_storacha_cid}',
                        json=signature_data
                    )
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['contract']['status'] == 'signed'
                    assert data['contract']['signed_cid'] == 'signed_' + mock_storacha_cid
                    assert data['contract']['blockchain_tx'] == mock_blockchain_tx
    
    # Test unauthorized signer
    invalid_data = signature_data.copy()
    invalid_data['signer_email'] = 'unauthorized@example.com'
    
    response = client.post(
        f'/api/contrato/assinar/{mock_storacha_cid}',
        json=invalid_data
    )
    
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Unauthorized signer' in data['error']
    
    # Test non-existent contract
    response = client.post(
        '/api/contrato/assinar/nonexistentcid',
        json=signature_data
    )
    
    assert response.status_code == 404

def test_get_signature_status(client, init_database, mock_storacha_cid):
    """Test signature status endpoint"""
    # Create test contract with signature
    contract = Contract.query.first()
    contract.initial_cid = mock_storacha_cid
    contract.signed_cid = 'signed_' + mock_storacha_cid
    contract.status = 'signed'
    contract.signature_metadata = {
        'signer_email': 'provider@example.com',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    from app import db
    db.session.commit()
    
    # Mock IPFS availability checks
    with patch('app.services.storacha.StorachaClient.check_cid_availability') as mock_check:
        mock_check.return_value = True
        
        # Mock blockchain verification
        with patch('app.blockchain.web3_client.Web3Client.verify_signature') as mock_verify:
            mock_verify.return_value = {
                'is_valid': True,
                'signature_time': 123456789,
                'metadata': contract.signature_metadata
            }
            
            # Test getting signature status
            response = client.get(f'/api/contrato/status/{mock_storacha_cid}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'signed'
            assert data['initial_cid'] == mock_storacha_cid
            assert data['signed_cid'] == 'signed_' + mock_storacha_cid
            assert data['signature_metadata'] == contract.signature_metadata
            assert data['ipfs_status']['initial'] is True
            assert data['ipfs_status']['signed'] is True
            assert 'blockchain_status' in data
    
    # Test non-existent contract
    response = client.get('/api/contrato/status/nonexistentcid')
    
    assert response.status_code == 404

def test_validate_signature(client, init_database, mock_storacha_cid):
    """Test signature validation endpoint"""
    # Create test contract with signature
    contract = Contract.query.first()
    contract.initial_cid = mock_storacha_cid
    contract.signed_cid = 'signed_' + mock_storacha_cid
    contract.status = 'signed'
    contract.signature_metadata = {
        'signer_email': 'provider@example.com',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    from app import db
    db.session.commit()
    
    # Mock blockchain verification
    with patch('app.blockchain.web3_client.Web3Client.verify_signature') as mock_verify:
        mock_verify.return_value = {
            'is_valid': True,
            'signature_time': 123456789,
            'metadata': contract.signature_metadata
        }
        
        # Mock IPFS availability
        with patch('app.services.storacha.StorachaClient.check_cid_availability') as mock_check:
            mock_check.return_value = True
            
            # Test signature validation
            response = client.get(
                f'/api/contrato/validar/signed_{mock_storacha_cid}'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['is_valid'] is True
            assert data['blockchain_verification']['is_valid'] is True
            assert data['ipfs_available'] is True
            assert data['signature_metadata'] == contract.signature_metadata
    
    # Test unsigned contract
    contract.signature_metadata = None
    db.session.commit()
    
    response = client.get(
        f'/api/contrato/validar/signed_{mock_storacha_cid}'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Contract has not been signed' in data['error']

def test_blockchain_integration():
    """Test Web3Client functionality"""
    from app.blockchain.web3_client import Web3Client
    from web3 import Web3
    
    # Mock Web3 provider
    with patch('web3.Web3.HTTPProvider') as mock_provider:
        mock_provider.return_value = MagicMock()
        
        # Mock contract loading
        with patch('app.blockchain.web3_client.Web3Client._load_contract') as mock_load:
            mock_load.return_value = None
            
            client = Web3Client()
            
            # Test CID registration
            with patch.object(client, 'contract') as mock_contract:
                mock_contract.functions.storeFile.return_value.build_transaction.return_value = {
                    'to': '0x123',
                    'data': '0x456',
                    'gas': 100000,
                    'gasPrice': 20000000000,
                    'nonce': 0,
                    'chainId': 1337
                }
                
                tx_hash = client.register_cid('testcid', 1)
                assert tx_hash is not None
            
            # Test contract registration
            with patch.object(client, 'contract') as mock_contract:
                mock_contract.functions.storeContract.return_value.build_transaction.return_value = {
                    'to': '0x123',
                    'data': '0x456',
                    'gas': 150000,
                    'gasPrice': 20000000000,
                    'nonce': 1,
                    'chainId': 1337
                }
                
                tx_hash = client.register_contract(1, 'testcid')
                assert tx_hash is not None
            
            # Test signature registration
            with patch.object(client, 'contract') as mock_contract:
                mock_contract.functions.signContract.return_value.build_transaction.return_value = {
                    'to': '0x123',
                    'data': '0x456',
                    'gas': 200000,
                    'gasPrice': 20000000000,
                    'nonce': 2,
                    'chainId': 1337
                }
                
                tx_hash = client.register_signature(
                    1,
                    'original_cid',
                    'signed_cid',
                    {'signer': 'test'}
                )
                assert tx_hash is not None

def test_smart_contract():
    """Test smart contract functionality"""
    from web3 import Web3
    import json
    import os
    
    # Load contract ABI
    contract_path = os.path.join(
        'app', 'blockchain', 'contracts', 'StorageContract.json'
    )
    
    assert os.path.exists(contract_path)
    
    with open(contract_path) as f:
        contract_data = json.load(f)
    
    assert 'abi' in contract_data
    assert 'bytecode' in contract_data
    
    # Verify contract interface
    abi = contract_data['abi']
    
    # Check required functions
    function_names = [item['name'] for item in abi if item['type'] == 'function']
    
    assert 'storeFile' in function_names
    assert 'storeContract' in function_names
    assert 'signContract' in function_names
    assert 'getContract' in function_names
    assert 'getSignature' in function_names
    assert 'verifyContract' in function_names
    assert 'verifySignature' in function_names
