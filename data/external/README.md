# External UFO Data Storage

This directory contains UFO sighting data fetched from external APIs.

## Directory Structure

```
data/external/
├── mufon/
│   ├── raw/           # Raw API responses
│   └── processed/     # Cleaned/deduplicated data
├── rapidapi/
│   ├── raw/
│   └── processed/
├── backups/           # Data backups
├── metadata/          # Tracking and metadata files
│   ├── sources.json   # Source tracking
│   └── import_log.json # Import history
└── .gitignore        # Git ignore rules
```

## Usage

### Store API Data
```python
from store_external_data import ExternalDataStorage

storage = ExternalDataStorage()
storage.store_batch("mufon", api_data, batch_number=1)
```

### Import to Database
```bash
python data/import_external_data.py --source mufon --file data/external/mufon/processed/deduplicated.json
```

## Data Sources

- **MUFON**: UFO sightings from Mutual UFO Network via RapidAPI
- **UFO Aficionado**: 88K UFO reports via RapidAPI

## Git Strategy

- Small processed files (< 10MB) are committed to repo
- Large raw files are stored locally but not committed
- Metadata and schemas are always committed
- Use data/external/.gitignore to control what gets committed

## Import to Production

1. Fetch data using RapidAPI
2. Store in raw/ directory
3. Process and deduplicate → processed/ directory  
4. Import processed data to main database
5. Update metadata tracking
