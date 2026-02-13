# Query Tuner Tool - Backend

FastAPI backend for Oracle Database Performance Tuning Tool.

## Setup

### Prerequisites

- Python 3.11+
- Oracle Instant Client
- Access to Oracle Database (11g+)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt
```

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Oracle Database
ORACLE_USER=monitor_user
ORACLE_PASSWORD=your_password
ORACLE_DSN=host:1521/service_name

# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Redis
REDIS_URL=redis://localhost:6379
```

## Running

### Development Server

```bash
# With uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m app.main
```

### Access

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_connection.py

# Run specific test
pytest tests/unit/test_connection.py::TestConnectionManager::test_create_pool
```

## Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/
pylint app/

# Type check
mypy app/
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── dependencies.py      # Dependency injection
│   ├── api/                 # API endpoints
│   │   └── v1/
│   │       ├── router.py    # Main router
│   │       ├── queries.py   # Query endpoints
│   │       └── ...
│   ├── core/                # Business logic
│   │   ├── oracle/          # Oracle integration
│   │   └── analysis/        # Analysis logic
│   ├── models/              # Data models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Service layer
│   └── utils/               # Utilities
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── conftest.py          # Test configuration
└── requirements/
    ├── base.txt             # Base requirements
    ├── dev.txt              # Development requirements
    ├── test.txt             # Testing requirements
    └── prod.txt             # Production requirements
```

## API Documentation

See [/docs](http://localhost:8000/docs) for interactive API documentation.

## Contributing

See [../docs/development/CONTRIBUTING.md](../docs/development/CONTRIBUTING.md) for contribution guidelines.
