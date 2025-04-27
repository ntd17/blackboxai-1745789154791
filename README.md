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

## API Endpoints

### User Management
- `POST /api/usuarios` - Register new user
- `GET /api/usuarios` - List users

### File Storage
- `POST /api/upload` - Upload file to Storacha
- `GET /api/cids` - List stored CIDs

### Contract Management
- `POST /api/contrato/gerar` - Generate new contract
- `GET /api/contrato/status/{cid}` - Get contract status
- `GET /api/custo/{cid}` - Estimate gas costs
- `POST /api/contrato/assinar/{cid}` - Sign contract

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
