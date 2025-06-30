# SkyWatch API

A professional RESTful API for querying UFO sighting reports, built with FastAPI and featuring data sourced from the National UFO Reporting Center (NUFORC).

## Features

- 🛸 **80,000+ UFO Sightings** - Real historical data from NUFORC
- 🚀 **Fast & Modern** - Built with FastAPI and async SQLAlchemy
- 🎨 **Beautiful Documentation** - Stripe-inspired API docs with interactive testing
- 🔍 **Advanced Filtering** - Search by state, city, shape, and date ranges
- 📄 **Pagination Support** - Efficient data retrieval for large datasets
- 🧪 **Test-Driven Development** - 100% test coverage with pytest

## Quick Start

```bash
# Clone the repository
git clone https://github.com/hustada/skywatch-api.git
cd skywatch-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn api.main:app --reload

# Visit the docs
open http://localhost:8000/docs
```

## API Endpoints

### Health Check
```bash
GET /health
```

### List UFO Sightings
```bash
GET /v1/sightings?state=NM&city=Roswell&shape=disk&page=1&per_page=25
```

### Get Specific Sighting
```bash
GET /v1/sightings/{id}
```

## Example Usage

```javascript
// Fetch UFO sightings in New Mexico
fetch('http://localhost:8000/v1/sightings?state=NM')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.total} UFO sightings in New Mexico`);
    data.sightings.forEach(sighting => {
      console.log(`${sighting.city}: ${sighting.summary}`);
    });
  });
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Import sample data
python data/import_data.py

# Import full dataset (80k+ records)
python data/import_kaggle_data.py
```

## Tech Stack

- **FastAPI** - Modern web framework
- **SQLAlchemy** - Async ORM
- **SQLite** - Database (PostgreSQL ready)
- **Pydantic** - Data validation
- **pytest** - Testing framework

## Data Attribution

Data provided by the [National UFO Reporting Center (NUFORC)](https://nuforc.org). NUFORC has been collecting UFO sighting reports since 1974 and maintains the world's largest database of UFO encounters.

## License

MIT License - See LICENSE file for details