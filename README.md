# 🛸 NUFORC UFO Sightings API

A modern REST API for querying UFO sighting reports from the National UFO Reporting Center (NUFORC) database.

## 🚀 Features

- **Fast & Modern**: Built with FastAPI for high performance
- **Well-Tested**: Comprehensive test coverage with pytest
- **Type-Safe**: Full type hints with Pydantic models
- **Auto-Documentation**: Interactive API docs with custom theme
- **Clean Code**: Formatted with Black, linted with flake8

## 🛠 Development Setup

1. **Clone and navigate to the project**:
   ```bash
   git clone <repo-url>
   cd nuforc-api
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Run tests**:
   ```bash
   pytest
   ```

5. **Start development server**:
   ```bash
   uvicorn api.main:app --reload
   ```

6. **View API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🧪 Testing

This project follows Test-Driven Development (TDD):

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api

# Run specific test file
pytest tests/test_health.py -v
```

## 🎨 Code Quality

```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy api --ignore-missing-imports
```

## 📦 Project Structure

```
nuforc-api/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── routers/
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoint
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test configuration
│   └── test_health.py       # Health endpoint tests
├── static/
│   └── custom-swagger.css   # Custom API docs theme
├── .github/
│   └── workflows/
│       └── test.yml         # CI/CD pipeline
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
└── README.md
```

## 🔧 Environment Configuration

Copy `.env.example` to `.env` and customize as needed:

```bash
cp .env.example .env
```

## 📊 Current API Endpoints

- `GET /health` - Health check endpoint

More endpoints coming soon as we implement the full NUFORC data API!

## 🎯 Design Theme

The API documentation features a custom theme with:
- **Primary**: Charcoal (#1a1a1a)
- **Background**: White (#ffffff)  
- **Accent**: Burnt Orange (#cc5500)

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Write tests first (TDD approach)
3. Implement the feature
4. Ensure all tests pass and code is formatted
5. Submit a pull request

## 📝 License

[Add your license here]