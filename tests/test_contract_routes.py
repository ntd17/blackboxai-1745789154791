import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.models.contract import Contract, ContractAdjustment
from app.models.weather_prediction import WeatherPrediction

def test_generate_contract(client, init_database, mock_weather_data, mock_storacha_cid, mock_blockchain_tx):
    """Test contract generation endpoint"""
    contract_data = {
        'creator_id': 1,
        'title': 'Test Painting Contract',
        'location': {
            'city': 'Test City',
            'state': 'TS',
            'coordinates': {
                'lat': 0,
                'lon': 0
            }
        },
        'planned_start_date': '2024-01-01',
        'planned_duration_days': 7,
        'contractor_details': {
            'name': 'Test Contractor',
            'email': 'contractor@example.com'
        },
        'provider_details': {
            'name': 'Test Provider',
            'email': 'provider@example.com'
        },
        'payment_details': {
            'amount': 1000.00,
            'method': 'Credit Card'
        }
    }
    
    # Mock weather service
    with patch('app.services.weather_service.WeatherService.get_forecast') as mock_forecast:
        mock_forecast.return_value = mock_weather_data
        
        # Mock ML prediction
        with patch('app.services.ml_service.MLPredictor.predict_duration') as mock_predict:
            mock_predict.return_value = {
                'delay_days': 2,
                'recommended_duration': 9,
                'rain_probability': 0.3,
                'confidence_score': 0.8,
                'model_version': '1.0.0',
                'metadata': {}
            }
            
            # Mock PDF generation and Storacha upload
            with patch('app.services.pdf_generator.generate_contract_pdf') as mock_pdf:
                mock_pdf.return_value = b'PDF content'
                
                with patch('app.services.storacha.StorachaClient.upload_content') as mock_upload:
                    mock_upload.return_value = mock_storacha_cid
                    
                    # Mock blockchain registration
                    with patch('app.blockchain.web3_client.Web3Client.register_contract') as mock_register:
                        mock_register.return_value = mock_blockchain_tx
                        
                        # Test successful contract generation
                        response = client.post(
                            '/api/contrato/gerar',
                            json=contract_data
                        )
                        
                        assert response.status_code == 201
                        data = json.loads(response.data)
                        assert 'contract' in data
                        assert data['contract']['title'] == 'Test Painting Contract'
                        assert data['contract']['initial_cid'] == mock_storacha_cid
                        assert data['contract']['blockchain_tx'] == mock_blockchain_tx
                        assert 'weather_prediction' in data
    
    # Test missing required fields
    invalid_data = contract_data.copy()
    del invalid_data['location']
    
    response = client.post('/api/contrato/gerar', json=invalid_data)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Missing required fields' in data['error']
    
    # Test invalid date format
    invalid_data = contract_data.copy()
    invalid_data['planned_start_date'] = 'invalid-date'
    
    response = client.post('/api/contrato/gerar', json=invalid_data)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid date format' in data['error']

def test_get_contract_status(client, init_database, mock_storacha_cid):
    """Test contract status endpoint"""
    # Create test contract with weather prediction
    contract = Contract.query.first()
    contract.initial_cid = mock_storacha_cid
    
    weather_prediction = WeatherPrediction(
        contract_id=contract.id,
        location={'city': 'Test City'},
        start_date=datetime.now().date(),
        end_date=datetime.now().date() + timedelta(days=7),
        original_duration=7,
        weather_data={'daily': []}
    )
    
    from app import db
    db.session.add(weather_prediction)
    db.session.commit()
    
    # Mock IPFS and blockchain checks
    with patch('app.services.storacha.StorachaClient.check_cid_availability') as mock_check:
        mock_check.return_value = True
        
        with patch('app.blockchain.web3_client.Web3Client.verify_contract') as mock_verify:
            mock_verify.return_value = {
                'is_registered': True,
                'timestamp': 123456789,
                'status': 'draft'
            }
            
            # Test getting contract status
            response = client.get(f'/api/contrato/status/{mock_storacha_cid}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['initial_cid'] == mock_storacha_cid
            assert data['ipfs_status'] is True
            assert 'blockchain_status' in data
            assert 'weather_prediction' in data
    
    # Test non-existent contract
    response = client.get('/api/contrato/status/nonexistentcid')
    
    assert response.status_code == 404

def test_estimate_gas_cost(client, init_database, mock_storacha_cid):
    """Test gas cost estimation endpoint"""
    # Create test contract
    contract = Contract.query.first()
    contract.initial_cid = mock_storacha_cid
    
    from app import db
    db.session.commit()
    
    # Mock gas estimation
    with patch('app.blockchain.web3_client.Web3Client.estimate_register_gas') as mock_register:
        mock_register.return_value = {
            'gas_estimate': 100000,
            'gas_price': 20000000000,
            'total_cost_wei': 2000000000000,
            'total_cost_eth': 0.002
        }
        
        with patch('app.blockchain.web3_client.Web3Client.estimate_signature_gas') as mock_signature:
            mock_signature.return_value = {
                'gas_estimate': 150000,
                'gas_price': 20000000000,
                'total_cost_wei': 3000000000000,
                'total_cost_eth': 0.003
            }
            
            # Test getting gas estimates
            response = client.get(f'/api/custo/{mock_storacha_cid}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'contract_id' in data
            assert 'cid' in data
            assert 'gas_estimates' in data
            assert 'register_contract' in data['gas_estimates']
            assert 'update_signature' in data['gas_estimates']
    
    # Test non-existent contract
    response = client.get('/api/custo/nonexistentcid')
    
    assert response.status_code == 404

def test_contract_model():
    """Test Contract model functionality"""
    contract = Contract(
        creator_id=1,
        title='Test Contract',
        location={'city': 'Test City'},
        planned_start_date=datetime.now().date(),
        planned_duration_days=7,
        contractor_name='Test Contractor',
        contractor_email='contractor@example.com',
        provider_name='Test Provider',
        provider_email='provider@example.com',
        amount=1000.00,
        payment_method='Credit Card'
    )
    
    # Test initialization
    assert contract.creator_id == 1
    assert contract.title == 'Test Contract'
    assert contract.status == 'draft'
    
    # Test duration adjustment
    contract.adjust_duration(9, 'Weather-based adjustment')
    assert contract.adjusted_duration_days == 9
    
    # Test signature update
    contract.update_signature('signed_cid', {'signer': 'Test Signer'})
    assert contract.signed_cid == 'signed_cid'
    assert contract.status == 'signed'
    assert contract.signature_metadata == {'signer': 'Test Signer'}
    
    # Test to_dict method
    contract_dict = contract.to_dict()
    assert contract_dict['title'] == 'Test Contract'
    assert contract_dict['status'] == 'signed'
    assert contract_dict['adjusted_duration_days'] == 9

def test_weather_prediction_model():
    """Test WeatherPrediction model functionality"""
    prediction = WeatherPrediction(
        contract_id=1,
        location={'city': 'Test City'},
        start_date=datetime.now().date(),
        end_date=datetime.now().date() + timedelta(days=7),
        original_duration=7,
        weather_data={'daily': []}
    )
    
    # Test initialization
    assert prediction.contract_id == 1
    assert prediction.original_duration == 7
    
    # Test prediction update
    prediction.update_prediction(
        rain_probability=0.3,
        predicted_delay=2,
        adjusted_duration=9,
        confidence_score=0.8,
        model_version='1.0.0',
        metadata={'source': 'test'}
    )
    
    assert prediction.rain_probability == 0.3
    assert prediction.predicted_delay_days == 2
    assert prediction.adjusted_duration == 9
    assert prediction.confidence_score == 0.8
    assert prediction.model_version == '1.0.0'
    
    # Test to_dict method
    pred_dict = prediction.to_dict()
    assert pred_dict['rain_probability'] == 0.3
    assert pred_dict['predicted_delay_days'] == 2
    assert pred_dict['confidence_score'] == 0.8
