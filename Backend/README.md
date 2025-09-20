# HARVEST Backend API

A comprehensive agricultural prediction and marketplace platform built with FastAPI.

## Features

- **Agricultural Predictions**: ML-powered crop yield, weather, and pest/disease predictions
- **Market Trends**: Real-time agricultural commodity prices and market analysis
- **Smart Alerts**: Customizable notifications for weather, pest, and market conditions
- **Marketplace**: Agricultural product trading platform with multi-language support
- **Real-time Communication**: WebSocket support for live updates
- **Multi-language Support**: Translation services for global accessibility

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session management and caching
- **ML**: Scikit-learn, Pandas, NumPy for predictions
- **Background Tasks**: Celery with Redis broker
- **Monitoring**: Structured logging with health checks
- **Authentication**: JWT-based authentication
- **External APIs**: Weather data, SMS notifications, translation services

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+

### Installation

1. **Clone and navigate to backend**:
   ```bash
   cd backend/
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**:
   ```bash
   # Create database
   createdb harvest_db
   
   # Run migrations
   python scripts/init_db.py
   ```

6. **Start the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Using Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Documentation

Once running, access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality (database, cache)
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── utils/            # Utilities and helpers
├── data/                 # Data storage
├── ml/                   # Machine learning models
├── tests/                # Test suite
├── scripts/              # Utility scripts
└── migrations/           # Database migrations
```

## Configuration

Key environment variables:

```bash
# Application
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/harvest_db
REDIS_URL=redis://localhost:6379

# External Services
WEATHER_API_KEY=your-api-key
TWILIO_ACCOUNT_SID=your-sid
GOOGLE_TRANSLATE_API_KEY=your-key
```

## API Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe

### Predictions
- `POST /api/v1/predict/crop-yield` - Crop yield prediction
- `POST /api/v1/predict/weather` - Weather forecasting
- `POST /api/v1/predict/pest-disease` - Pest/disease risk assessment
- `GET /api/v1/predict/history/{user_id}` - Prediction history

### Market Trends
- `GET /api/v1/trends/prices/{commodity}` - Price trends
- `GET /api/v1/trends/demand/{commodity}` - Demand forecasting
- `GET /api/v1/trends/supply/{commodity}` - Supply analysis
- `GET /api/v1/trends/market-summary` - Market overview

### Alerts
- `POST /api/v1/alerts` - Create alert
- `GET /api/v1/alerts/{user_id}` - Get user alerts
- `PUT /api/v1/alerts/{alert_id}` - Update alert
- `DELETE /api/v1/alerts/{alert_id}` - Delete alert

### Marketplace
- `POST /api/v1/marketplace/products` - Create product listing
- `GET /api/v1/marketplace/products` - Browse products
- `GET /api/v1/marketplace/products/{id}` - Get product details
- `POST /api/v1/marketplace/orders` - Place order
- `GET /api/v1/marketplace/orders/{user_id}` - Get orders

## Development

### Running Tests
```bash
pytest tests/ -v --cov=app
```

### Code Quality
```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint
flake8 app/ tests/
mypy app/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Background Tasks
```bash
# Start Celery worker
celery -A app.core.scheduler worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.core.scheduler beat --loglevel=info
```

## Deployment

### Production Setup

1. **Environment variables**: Set production values in `.env`
2. **Database**: Use managed PostgreSQL service
3. **Cache**: Use managed Redis service
4. **Application**: Deploy with Gunicorn
5. **Reverse proxy**: Use Nginx for SSL termination
6. **Monitoring**: Configure logging and health checks

### Docker Production
```bash
# Build production image
docker build -t harvest-backend .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

- **Health checks**: Built-in endpoints for monitoring
- **Structured logging**: JSON logs for analysis
- **Performance tracking**: Request timing and metrics
- **Error tracking**: Comprehensive error logging

## Security

- JWT authentication for API access
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- CORS configuration for cross-origin requests
- Rate limiting on sensitive endpoints
- Environment-based configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [Full API docs](http://localhost:8000/docs)
- Email: support@harvest-platform.com