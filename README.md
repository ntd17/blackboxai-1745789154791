# Blockchain-Based Painting Contract System

A Flask-based application for managing painting contracts with weather-based duration predictions, blockchain storage, and digital signatures.

## Features

- User registration and management
- File upload to IPFS via Storacha
- Smart contract integration with Ethereum (Ganache)
- Weather-based contract duration predictions using TensorFlow
- PDF contract generation with digital signatures
- Email notifications
- Blockchain verification of documents

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 14+ (for Ganache)
- Storacha API key
- OpenWeatherMap API key
- SMTP server credentials

## Project Structure

```
blockchain-storage-app/
├── app/
│   ├── models/         # Database models
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic
│   └── blockchain/     # Smart contract & Web3 client
├── data/
│   ├── ml_models/      # TensorFlow models
│   ├── sqlite/         # Database files
│   └── contracts/      # Contract artifacts
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd blockchain-storage-app
   ```

2. Create and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

4. Initialize the database:
   ```bash
   docker-compose exec app flask db upgrade
   ```

## API Documentation

The API documentation is available at http://localhost:5000/docs/

### API Endpoints and CURL Examples

### User Management
- `POST /api/usuarios` - Register new user
- `GET /api/usuarios` - List users

Example - Register a new user:
```bash
curl -X POST http://localhost:5000/api/usuarios \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### File Storage
- `POST /api/upload` - Upload file to Storacha
- `GET /api/cids` - List stored CIDs

Example - Upload a file:
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@/path/to/your/file.pdf" \
  -F "user_id=1"
```

Example - List CIDs:
```bash
curl -X GET http://localhost:5000/api/cids
```

### Contract Management
- `POST /api/contrato/gerar` - Generate new contract
- `GET /api/contrato/status/{cid}` - Get contract status
- `GET /api/custo/{cid}` - Estimate gas costs
- `POST /api/contrato/assinar/{cid}` - Sign contract

Example - Generate a contract:
```bash
curl -X POST http://localhost:5000/api/contrato/gerar \
  -H "Content-Type: application/json" \
  -d '{
    "creator_id": 1,
    "title": "House Painting Contract",
    "location": {
      "city": "São Paulo",
      "state": "SP",
      "coordinates": {
        "lat": -23.550520,
        "lon": -46.633308
      }
    },
    "planned_start_date": "2024-01-15",
    "planned_duration_days": 7,
    "contractor_details": {
      "name": "John Doe",
      "email": "john@example.com"
    },
    "provider_details": {
      "name": "Paint Pro Services",
      "email": "provider@paintpro.com"
    },
    "payment_details": {
      "amount": 5000.00,
      "method": "Bank Transfer"
    }
  }'
```

Example - Sign a contract:
```bash
curl -X POST http://localhost:5000/api/contrato/assinar/QmYourCIDHere \
  -H "Content-Type: application/json" \
  -d '{
    "signer_email": "provider@paintpro.com",
    "signature_data": {
      "signature": "digital_signature_here",
      "timestamp": "2024-01-10T14:30:00Z"
    }
  }'
```

Example - Check contract status:
```bash
curl -X GET http://localhost:5000/api/contrato/status/QmYourCIDHere
```

Example - Estimate gas cost:
```bash
curl -X GET http://localhost:5000/api/custo/QmYourCIDHere
```

### Response Format

All API endpoints return JSON responses with the following structure:

Success Response:
```json
{
  "message": "Operation successful",
  "data": {
    // Operation-specific data
  }
}
```

Error Response:
```json
{
  "error": "Error message",
  "details": "Additional error details (if available)"
}
```

### HTTP Status Codes

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

### Testing with Postman

1. Import the provided Postman collection:
   - Open Postman
   - Click "Import"
   - Select the `painting_contract_api.postman_collection.json` file

2. Set up environment variables:
   - Create a new environment
   - Add variables:
     - `base_url`: http://localhost:5000
     - `user_id`: (after creating a user)
     - `contract_cid`: (after generating a contract)

3. Run the requests in sequence:
   1. Create User
   2. Upload File
   3. Generate Contract
   4. Sign Contract
   5. Check Status

## Weather-Based Duration Prediction

The system uses machine learning to predict optimal contract durations based on:
- Historical weather data
- Rain probability
- Temperature trends
- Location characteristics

## Smart Contract

The Ethereum smart contract (`StorageContract.sol`) manages:
- File CID storage
- Contract registration
- Digital signatures
- Verification methods

## Development

1. Start development environment:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

2. Run tests:
   ```bash
   docker-compose exec app pytest
   ```

3. Deploy new contract:
   ```bash
   docker-compose run contract-deployer
   ```

## Environment Variables

- `FLASK_APP`: Application entry point
- `DATABASE_URL`: SQLite database location
- `GANACHE_URL`: Ethereum testnet URL
- `STORACHA_API_KEY`: IPFS storage API key
- `OPENWEATHER_API_KEY`: Weather API key
- `SMTP_*`: Email configuration
- `ML_MODEL_PATH`: TensorFlow model location

## Production Deployment

1. Update environment variables for production
2. Build production images:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
   ```
3. Deploy using your preferred orchestration tool

## Security Considerations

- All contract interactions are recorded on the blockchain
- Digital signatures are verified and timestamped
- File integrity is ensured through IPFS hashing
- Environment variables protect sensitive credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Submit pull request

## License

MIT License - see LICENSE file for details
