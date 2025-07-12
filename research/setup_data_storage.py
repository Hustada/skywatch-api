#!/usr/bin/env python3
"""
Setup data storage within the existing skywatch-api repository.
Creates directory structure for storing external API data.
"""

import os
import json
from datetime import datetime
from pathlib import Path

def setup_data_directories():
    """Create directory structure for external data storage."""
    
    # Base paths
    base_dir = Path(__file__).parent.parent  # skywatch-api root
    data_dir = base_dir / "data" / "external"
    
    # Create directory structure
    directories = [
        data_dir / "mufon" / "raw",
        data_dir / "mufon" / "processed", 
        data_dir / "rapidapi" / "raw",
        data_dir / "rapidapi" / "processed",
        data_dir / "backups",
        data_dir / "metadata"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # Create .gitignore for large files
    gitignore_path = data_dir / ".gitignore"
    gitignore_content = """# Ignore very large data files (>100MB)
*.json.large
raw/*_batch_*.json
# Keep small test files and processed data
!processed/
!metadata/
!*_sample.json
!*_test.json
"""
    
    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content)
    print(f"✅ Created: {gitignore_path}")
    
    return data_dir

def create_metadata_structure(data_dir: Path):
    """Create metadata files for tracking data sources."""
    
    metadata_dir = data_dir / "metadata"
    
    # Source tracking metadata
    sources_metadata = {
        "last_updated": datetime.now().isoformat(),
        "sources": {
            "mufon": {
                "api_endpoint": "https://ufo-sightings.p.rapidapi.com",
                "description": "MUFON UFO sightings database via RapidAPI",
                "last_fetch": None,
                "total_records": 0,
                "status": "pending"
            },
            "rapidapi_ufo_aficionado": {
                "api_endpoint": "https://ufo-aficionado-api.p.rapidapi.com", 
                "description": "UFO Aficionado API with 88K reports",
                "last_fetch": None,
                "total_records": 0,
                "status": "pending"
            }
        }
    }
    
    with open(metadata_dir / "sources.json", 'w') as f:
        json.dump(sources_metadata, f, indent=2)
    
    # Import tracking
    import_log = {
        "imports": [],
        "last_import": None,
        "total_imported": 0
    }
    
    with open(metadata_dir / "import_log.json", 'w') as f:
        json.dump(import_log, f, indent=2)
    
    print(f"✅ Created metadata files")

def create_sample_storage_script(data_dir: Path):
    """Create a sample script for storing API data."""
    
    script_content = '''#!/usr/bin/env python3
"""
Store external API data with proper organization and metadata.
"""

import json
import os
from datetime import datetime
from pathlib import Path

class ExternalDataStorage:
    def __init__(self, base_data_dir: str = "data/external"):
        self.base_dir = Path(base_data_dir)
        self.metadata_dir = self.base_dir / "metadata"
    
    def store_batch(self, source: str, data: list, batch_number: int = None):
        """Store a batch of API data."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_suffix = f"_batch_{batch_number:03d}" if batch_number else ""
        filename = f"{source}_{timestamp}{batch_suffix}.json"
        
        # Store in raw directory
        raw_dir = self.base_dir / source / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        filepath = raw_dir / filename
        
        # Prepare data with metadata
        data_package = {
            "metadata": {
                "source": source,
                "fetch_timestamp": datetime.now().isoformat(),
                "batch_number": batch_number,
                "record_count": len(data),
                "api_key_used": "*** (hidden)",
                "schema_version": "1.0"
            },
            "data": data
        }
        
        # Write data
        with open(filepath, 'w') as f:
            json.dump(data_package, f, indent=2)
        
        print(f"✅ Stored {len(data)} records to {filepath}")
        self._update_source_metadata(source, len(data))
        
        return filepath
    
    def _update_source_metadata(self, source: str, record_count: int):
        """Update source metadata tracking."""
        
        metadata_file = self.metadata_dir / "sources.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {"sources": {}}
        
        if source not in metadata["sources"]:
            metadata["sources"][source] = {}
        
        metadata["sources"][source].update({
            "last_fetch": datetime.now().isoformat(),
            "total_records": metadata["sources"][source].get("total_records", 0) + record_count,
            "status": "active"
        })
        metadata["last_updated"] = datetime.now().isoformat()
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

# Example usage:
if __name__ == "__main__":
    # Example: Store sample MUFON data
    storage = ExternalDataStorage()
    
    sample_data = [
        {
            "id": "test_001",
            "date": "2024-01-15",
            "location": "Phoenix, AZ",
            "shape": "triangle",
            "description": "Large triangular craft with lights"
        }
    ]
    
    storage.store_batch("mufon", sample_data, batch_number=1)
    print("Sample storage complete!")
'''
    
    script_path = data_dir.parent / "store_external_data.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    print(f"✅ Created storage script: {script_path}")

def create_readme(data_dir: Path):
    """Create README for the data directory."""
    
    readme_content = """# External UFO Data Storage

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
"""
    
    readme_path = data_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Created: {readme_path}")

def main():
    """Setup external data storage in existing repository."""
    
    print("🛸 Setting up external UFO data storage...")
    print("=" * 50)
    
    # Create directory structure
    data_dir = setup_data_directories()
    
    # Create metadata structure
    create_metadata_structure(data_dir)
    
    # Create storage utilities
    create_sample_storage_script(data_dir)
    
    # Create documentation
    create_readme(data_dir)
    
    print("\n" + "=" * 50)
    print("✅ External data storage setup complete!")
    print(f"📁 Data directory: {data_dir}")
    print("📝 Next steps:")
    print("   1. Subscribe to UFO Sightings API on RapidAPI")
    print("   2. Test API: python research/test_rapidapi.py")
    print("   3. Bulk fetch: python store_external_data.py")
    print("   4. Import to DB: python data/import_external_data.py")

if __name__ == "__main__":
    main()