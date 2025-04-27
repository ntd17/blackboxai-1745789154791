import pytest
import json
from io import BytesIO
from unittest.mock import patch, MagicMock
from app.models.upload import Upload

def test_upload_file(client, init_database, mock_storacha_cid, mock_blockchain_tx):
    """Test file upload endpoint"""
    
    # Create test file
    file_content = b'Test file content'
    file_data = {
        'file': (BytesIO(file_content), 'test.txt', 'text/plain'),
        'user_id': '1'
    }
    
    # Mock Storacha upload
    with patch('app.services.storacha.StorachaClient.upload_file') as mock_upload:
        mock_upload.return_value = mock_storacha_cid
        
        # Mock blockchain registration
        with patch('app.blockchain.web3_client.Web3Client.register_cid') as mock_register:
            mock_register.return_value = mock_blockchain_tx
            
            # Test successful upload
            response = client.post(
                '/api/upload',
                data=file_data,
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert 'upload' in data
            assert data['upload']['cid'] == mock_storacha_cid
            assert data['upload']['blockchain_tx'] == mock_blockchain_tx
            
    # Test missing file
    response = client.post(
        '/api/upload',
        data={'user_id': '1'},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'No file provided' in data['error']
    
    # Test missing user_id
    response = client.post(
        '/api/upload',
        data={'file': (BytesIO(b'content'), 'test.txt', 'text/plain')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'User ID required' in data['error']

def test_list_cids(client, init_database, mock_storacha_cid):
    """Test CID listing endpoint"""
    # Create test upload
    with patch('app.services.storacha.StorachaClient.upload_file') as mock_upload:
        mock_upload.return_value = mock_storacha_cid
        
        file_data = {
            'file': (BytesIO(b'test content'), 'test.txt', 'text/plain'),
            'user_id': '1'
        }
        
        client.post('/api/upload', data=file_data, content_type='multipart/form-data')
    
    # Test listing all CIDs
    response = client.get('/api/cids')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'cids' in data
    assert len(data['cids']) > 0
    assert data['cids'][0]['cid'] == mock_storacha_cid
    
    # Test filtering by user
    response = client.get('/api/cids?user_id=1')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['cids']) > 0
    assert all(cid['user_id'] == 1 for cid in data['cids'])
    
    # Test non-existent user
    response = client.get('/api/cids?user_id=999')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['cids']) == 0

def test_get_cid_info(client, init_database, mock_storacha_cid):
    """Test CID info endpoint"""
    # Create test upload
    with patch('app.services.storacha.StorachaClient.upload_file') as mock_upload:
        mock_upload.return_value = mock_storacha_cid
        
        file_data = {
            'file': (BytesIO(b'test content'), 'test.txt', 'text/plain'),
            'user_id': '1'
        }
        
        client.post('/api/upload', data=file_data, content_type='multipart/form-data')
    
    # Mock IPFS and blockchain checks
    with patch('app.services.storacha.StorachaClient.check_cid_availability') as mock_check:
        mock_check.return_value = True
        
        with patch('app.blockchain.web3_client.Web3Client.get_cid_status') as mock_status:
            mock_status.return_value = {'is_registered': True, 'timestamp': 123456789}
            
            # Test getting existing CID info
            response = client.get(f'/api/cids/{mock_storacha_cid}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['cid'] == mock_storacha_cid
            assert data['ipfs_available'] is True
            assert 'blockchain_status' in data
    
    # Test non-existent CID
    response = client.get('/api/cids/nonexistentcid')
    
    assert response.status_code == 404

def test_upload_model():
    """Test Upload model functionality"""
    upload = Upload(
        user_id=1,
        filename='test.txt',
        cid='testcid',
        mime_type='text/plain',
        file_size=100
    )
    
    # Test initialization
    assert upload.user_id == 1
    assert upload.filename == 'test.txt'
    assert upload.cid == 'testcid'
    assert upload.status == 'pending'
    assert upload.ipfs_url == 'ipfs://testcid'
    
    # Test blockchain status update
    upload.update_blockchain_status('0xtxhash')
    assert upload.blockchain_tx == '0xtxhash'
    assert upload.status == 'confirmed'
    
    # Test to_dict method
    upload_dict = upload.to_dict()
    assert upload_dict['user_id'] == 1
    assert upload_dict['filename'] == 'test.txt'
    assert upload_dict['cid'] == 'testcid'
    assert upload_dict['blockchain_tx'] == '0xtxhash'
    assert upload_dict['status'] == 'confirmed'

def test_storacha_integration():
    """Test StorachaClient functionality"""
    from app.services.storacha import StorachaClient
    
    client = StorachaClient(api_key='test_key')
    
    # Test file upload
    test_file = BytesIO(b'test content')
    test_file.filename = 'test.txt'
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'cid': 'testcid'}
        
        cid = client.upload_file(test_file)
        assert cid == 'testcid'
    
    # Test content upload
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'cid': 'testcid2'}
        
        cid = client.upload_content(b'test content', 'test.txt')
        assert cid == 'testcid2'
    
    # Test CID availability check
    with patch('requests.head') as mock_head:
        mock_head.return_value.status_code = 200
        
        is_available = client.check_cid_availability('testcid')
        assert is_available is True
        
        mock_head.return_value.status_code = 404
        is_available = client.check_cid_availability('nonexistentcid')
        assert is_available is False
