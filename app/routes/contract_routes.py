from flask import jsonify, request, current_app, send_file
from pathlib import Path
from app import db
from app.models.contract import Contract, ContractAdjustment
from app.models.weather_prediction import WeatherPrediction
from app.routes import contract_bp
from app.services.weather_service import WeatherService
from app.services.ml_service import MLPredictor
from app.services.pdf_generator import generate_contract_pdf, generate_pdf_from_html
from app.services.email_service import send_contract_email
from app.services.storacha import StorachaClient
from app.blockchain.web3_client import Web3Client
from app.services.contract_generator import ContractGenerator
from datetime import datetime, timedelta
from app.utils.validators.marshmallow_schemas import ContractSchema
from app.utils.error_handlers import ValidationError, BlockchainError
from app.utils.cache import cached
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_url=current_app.config['REDIS_URL']
)

@contract_bp.route('/contrato/gerar', methods=['POST'])
@contract_bp.route('/api/contrato/gerar', methods=['POST'])
@limiter.limit("20/hour")  # Stricter limit for contract generation
@contract_bp.route('/generate', methods=['POST'])
@limiter.limit("20/hour")
def generate_contract():
    """
    Generate a new painting contract with weather-based duration prediction (legacy)
    ---
    tags:
      - Contracts
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/ContractRequest'
    responses:
      201:
        description: Contract generated successfully
      400:
        description: Invalid input data
      429:
        description: Rate limit exceeded
      500:
        description: Contract generation failed
    """
    try:
        # Validate request data using Marshmallow schema
        schema = ContractSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as e:
            return jsonify({
                'error': 'Validation error',
                'details': e.messages
            }), 400
            
        # Parse dates
        start_date = datetime.strptime(data['planned_start_date'], '%Y-%m-%d').date()
            
        # Get weather prediction with caching
        weather_service = WeatherService(
            api_key=current_app.config['OPENWEATHER_API_KEY']
        )
        
        weather_data = weather_service.get_forecast(
            location=data['location'],
            start_date=start_date,
            days=data['planned_duration_days']
        )
        
        # Create contract
        contract = Contract(
            creator_id=data['creator_id'],
            title=data['title'],
            location=data['location'],
            planned_start_date=start_date,
            planned_duration_days=data['planned_duration_days'],
            contractor_name=data['contractor_details']['name'],
            contractor_email=data['contractor_details']['email'],
            provider_name=data['provider_details']['name'],
            provider_email=data['provider_details']['email'],
            amount=data['payment_details']['amount'],
            payment_method=data['payment_details']['method']
        )
        
        db.session.add(contract)
        db.session.flush()
        
        # Create weather prediction
        weather_prediction = WeatherPrediction(
            contract_id=contract.id,
            location=data['location'],
            start_date=start_date,
            end_date=start_date + timedelta(days=data['planned_duration_days']),
            original_duration=data['planned_duration_days'],
            weather_data=weather_data
        )
        
        weather_prediction.process_daily_forecasts()
        
        # Get ML prediction with caching
        ml_predictor = MLPredictor(
            model_path=current_app.config['ML_MODEL_PATH']
        )
        
        prediction = ml_predictor.predict_duration(
            weather_data=weather_prediction.daily_forecasts,
            location=data['location'],
            original_duration=data['planned_duration_days']
        )
        
        weather_prediction.update_prediction(
            rain_probability=prediction['rain_probability'],
            predicted_delay=prediction['delay_days'],
            adjusted_duration=prediction['recommended_duration'],
            confidence_score=prediction['confidence_score'],
            model_version=prediction['model_version'],
            metadata=prediction['metadata']
        )
        
        db.session.add(weather_prediction)
        
        # Adjust contract duration if confidence is high enough
        if (prediction['confidence_score'] >= 
            current_app.config['MINIMUM_CONFIDENCE_THRESHOLD']):
            contract.adjust_duration(
                prediction['recommended_duration'],
                f"Weather-based adjustment: {prediction['delay_days']} additional days recommended"
            )
        
        # Generate PDF using legacy generator
        pdf_content = generate_contract_pdf(
            contract=contract,
            weather_prediction=weather_prediction
        )

        # Generate new HTML-based contract
        generator = ContractGenerator()
        contract_data = {
            'contractor_name': contract.contractor_name,
            'client_name': contract.provider_name,
            'total_price': contract.amount,
            'start_date': contract.planned_start_date.strftime('%B %d, %Y'),
            'completion_date': (contract.planned_start_date + 
                               timedelta(days=contract.planned_duration_days)).strftime('%B %d, %Y'),
            'location': contract.location
        }
        html_pdf_path = generator.generate_painting_contract(contract_data)
        
        # Upload to Storacha
        storacha = StorachaClient(
            api_key=current_app.config['STORACHA_API_KEY']
        )
        
        cid = storacha.upload_content(
            content=pdf_content,
            filename=f"contract_{contract.id}.pdf"
        )
        
        contract.initial_cid = cid
        
        # Register in blockchain
        try:
            web3_client = Web3Client()
            tx_hash = web3_client.register_contract(
                contract_id=contract.id,
                cid=cid
            )
            contract.blockchain_tx = tx_hash
        except Exception as e:
            current_app.logger.error(f"Blockchain registration failed: {str(e)}")
            raise BlockchainError("Failed to register contract on blockchain", str(e))
        
        # Send email notification
        try:
            send_contract_email(
                recipient_email=contract.provider_email,
                contract=contract,
                cid=cid
            )
        except Exception as e:
            current_app.logger.error(f"Email notification failed: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contract generated successfully',
            'data': {
                'contract': contract.to_dict(),
                'weather_prediction': weather_prediction.to_dict()
            }
        }), 201
        
    except ValidationError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Validation error',
            'details': e.messages
        }), 400
        
    except BlockchainError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Blockchain error',
            'message': str(e),
            'details': e.payload
        }), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contract generation failed: {str(e)}")
        return jsonify({
            'error': 'Contract generation failed',
            'details': str(e)
        }), 500

@contract_bp.route('/template', methods=['GET'])
@limiter.limit("100/hour")
@cached(timeout=300)
def get_contract_template():
    """Get contract template structure endpoint"""
    try:
        template_path = Path(__file__).parent.parent / 'templates/contracts/painting_contract.html'
        with open(template_path) as f:
            template = f.read()
        return jsonify({'template': template})
    except Exception as e:
        current_app.logger.error(f"Template retrieval failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@contract_bp.route('/contrato/status/<string:cid>', methods=['GET'])
@contract_bp.route('/api/status/<string:cid>', methods=['GET'])
@limiter.limit("100/hour")
@cached(timeout=300)
def get_contract_status(cid):
    """
    Get contract status by CID
    ---
    tags:
      - Contracts
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: Contract CID
    responses:
      200:
        description: Contract status
      404:
        description: Contract not found
      429:
        description: Rate limit exceeded
    """
    contract = Contract.query.filter(
        (Contract.initial_cid == cid) | (Contract.signed_cid == cid)
    ).first_or_404()
    
    try:
        # Check IPFS availability
        storacha = StorachaClient(
            api_key=current_app.config['STORACHA_API_KEY']
        )
        ipfs_status = storacha.check_cid_availability(cid)
        
        # Get blockchain verification
        web3_client = Web3Client()
        blockchain_status = web3_client.verify_contract(
            contract_id=contract.id,
            cid=cid
        )
        
        response = contract.to_dict()
        response.update({
            'ipfs_status': ipfs_status,
            'blockchain_status': blockchain_status
        })
        
        if contract.weather_prediction:
            response['weather_prediction'] = contract.weather_prediction.to_dict()
        
        return jsonify({
            'success': True,
            'data': response
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting contract status: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve contract status',
            'details': str(e)
        }), 500

@contract_bp.route('/custo/<string:cid>', methods=['GET'])
@contract_bp.route('/api/custo/<string:cid>', methods=['GET'])
@limiter.limit("50/hour")
@cached(timeout=300)  # Cache for 5 minutes
def estimate_gas_cost(cid):
    """
    Estimate gas cost for contract operations
    ---
    tags:
      - Contracts
    parameters:
      - in: path
        name: cid
        type: string
        required: true
        description: Contract CID
    responses:
      200:
        description: Gas cost estimation
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
        
        # Estimate gas for different operations
        estimates = {
            'register_contract': web3_client.estimate_register_gas(
                contract_id=contract.id,
                cid=cid
            ),
            'update_signature': web3_client.estimate_signature_gas(
                contract_id=contract.id,
                cid=cid
            )
        }
        
        return jsonify({
            'success': True,
            'data': {
                'contract_id': contract.id,
                'cid': cid,
                'gas_estimates': estimates
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error estimating gas cost: {str(e)}")
        return jsonify({
            'error': 'Failed to estimate gas cost',
            'details': str(e)
        }), 500
