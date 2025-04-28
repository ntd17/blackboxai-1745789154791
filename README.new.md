# Blockchain-Based Painting Contract System

A Flask-based application for managing painting contracts with weather-based duration predictions, blockchain storage, and digital signatures.

## Features

- User registration and management
- File storage on IPFS via Storacha with bridge token authentication
- Smart contract integration with Ethereum (Ganache)
- Weather-based contract duration predictions using TensorFlow
- PDF contract generation with digital signatures
- Email notifications
- Blockchain verification of documents
- Multilingual support (🇺🇸 EN, 🇧🇷 PT, 🇨🇴 ES)

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Storacha Bridge Token credentials
- OpenWeatherMap API key
- SMTP server credentials

## Project Structure

```
painting-contract/
├── app/
│   ├── static/          # Static assets
│   │   ├── css/        # Stylesheets
│   │   ├── js/         # JavaScript files
│   │   ├── img/        # Images
│   │   └── fonts/      # Custom fonts
│   └── templates/      # Jinja2 templates
│       ├── admin/     # Admin panel templates
│       ├── auth/      # Authentication templates
│       └── contracts/ # Contract templates
├── apache/            # Apache configuration
│   ├── certs/        # SSL certificates
│   └── logs/         # Apache logs
└── data/             # Persistent data
    ├── ml_models/    # TensorFlow models
    ├── sqlite/       # Database files
    └── contracts/    # Contract files
```

## Storacha Integration

### Authentication

The system uses Storacha's bridge token authentication system, which requires two tokens:

1. X-Auth-Secret: Used in the `X-Auth-Secret` header
2. Authorization Token: Used in the `Authorization` header

Configure these in your environment:

```bash
STORACHA_X_AUTH_SECRET=your-x-auth-secret
STORACHA_AUTHORIZATION_TOKEN=your-authorization-token
```

Both tokens are required for all Storacha API operations (upload, retrieve, etc.).

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd painting-contract
   ```

2. Create and configure environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your configuration, including Storacha credentials
   ```

3. Set up directory structure:
   ```bash
   ./setup_directories.sh
   ```

4. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

## API Endpoints

### User Management
- `POST /api/usuarios` - Register new user
- `GET /api/usuarios` - List users

### File Storage
- `POST /api/upload` - Upload file to Storacha (requires authentication)
- `GET /api/cids` - List stored CIDs

### Contract Management
- `POST /api/contrato/gerar` - Generate new contract
- `GET /api/contrato/status/{cid}` - Get contract status
- `GET /api/custo/{cid}` - Estimate gas costs
- `POST /api/contrato/assinar/{cid}` - Sign contract

## Development

1. Start development environment:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

2. Run tests:
   ```bash
   docker-compose exec app pytest
   ```

## Production Deployment

1. Update environment variables for production:
   ```bash
   cp env.example .env.production
   # Edit .env.production with production values
   ```

2. Deploy using the deployment script:
   ```bash
   ./deploy.sh
   ```

## Environment Variables

Key environment variables:

- `APP_NAME`: Application name
- `HOSTNAME`: Your domain name
- `STORACHA_X_AUTH_SECRET`: Storacha X-Auth-Secret header value
- `STORACHA_AUTHORIZATION_TOKEN`: Storacha Authorization header value
- `DATABASE_URL`: SQLite database location
- `OPENWEATHER_API_KEY`: Weather API key
- `SMTP_*`: Email configuration
- `LANGUAGES_ENABLED`: Enabled languages (comma-separated)

See `env.example` for all available options.

## Security Considerations

- All Storacha API requests require both authentication tokens
- Contract interactions are recorded on the blockchain
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
