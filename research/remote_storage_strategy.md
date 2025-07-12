# Remote Storage Strategy for External UFO Data

## Overview
Store fetched RapidAPI data remotely to avoid repeated API calls and enable access from multiple environments.

## Storage Options

### Option 1: GitHub Repository Data Storage 🎯 **Recommended**
**Pros:**
- Free and unlimited for public repos
- Version controlled (track data changes)
- Easy CI/CD integration
- Accessible from anywhere
- Perfect for one-time bulk imports

**Implementation:**
```bash
# Create data repository
git clone https://github.com/hustada/skywatch-data.git
cd skywatch-data

# Store fetched data as JSON files
data/
├── mufon/
│   ├── sightings_batch_001.json
│   ├── sightings_batch_002.json
│   └── metadata.json
├── rapidapi/
│   ├── ufo_sightings_001.json
│   └── metadata.json
└── processed/
    └── deduplicated_sightings.json
```

### Option 2: Cloud Database (PostgreSQL)
**Services:** Railway, Supabase, PlanetScale
**Cost:** $5-20/month
**Pros:** Direct SQL access, real-time queries
**Cons:** Ongoing costs

### Option 3: Object Storage (S3/GCS)
**Cost:** ~$1/month for JSON files
**Pros:** Scalable, cheap, API access
**Cons:** Setup complexity

### Option 4: Production Database
**Current:** Your existing database with new tables
**Pros:** Centralized storage
**Cons:** Bloats production DB

## Recommended Implementation: GitHub Data Repository

### 1. Setup Data Repository
```bash
# Create separate repo for UFO data
mkdir skywatch-data
cd skywatch-data
git init
git remote add origin https://github.com/hustada/skywatch-data.git

# Directory structure
mkdir -p data/{mufon,rapidapi,processed,backups}
```

### 2. Fetch and Store Script
```python
import json
import requests
from datetime import datetime
import os

class RemoteDataStorage:
    def __init__(self, repo_path="./skywatch-data"):
        self.repo_path = repo_path
        self.data_path = os.path.join(repo_path, "data")
    
    def store_api_batch(self, source: str, batch_data: list, batch_number: int):
        """Store a batch of API data as JSON file."""
        filename = f"{source}_batch_{batch_number:03d}.json"
        filepath = os.path.join(self.data_path, source, filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump({
                "source": source,
                "batch_number": batch_number,
                "fetch_timestamp": datetime.now().isoformat(),
                "record_count": len(batch_data),
                "data": batch_data
            }, f, indent=2)
        
        return filepath
    
    def commit_and_push(self, message: str):
        """Commit and push data to GitHub."""
        os.system(f"cd {self.repo_path} && git add .")
        os.system(f"cd {self.repo_path} && git commit -m '{message}'")
        os.system(f"cd {self.repo_path} && git push origin main")
```

### 3. Data Access from SkyWatch API
```python
# In your main API, fetch from GitHub
import requests

class RemoteDataFetcher:
    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com/hustada/skywatch-data/main/data"
    
    def fetch_processed_data(self):
        """Fetch processed/deduplicated data for import."""
        url = f"{self.base_url}/processed/deduplicated_sightings.json"
        response = requests.get(url)
        return response.json()
    
    def list_available_batches(self, source: str):
        """List available data batches from GitHub API."""
        api_url = f"https://api.github.com/repos/hustada/skywatch-data/contents/data/{source}"
        response = requests.get(api_url)
        return [item["name"] for item in response.json() if item["name"].endswith(".json")]
```

## Implementation Steps

### Phase 1: Test API and Store Sample Data
```bash
# 1. Run the API test
cd research
python test_rapidapi.py

# 2. Create data repository
mkdir ../skywatch-data
cd ../skywatch-data
git init
git remote add origin https://github.com/hustada/skywatch-data.git

# 3. Store test results
mkdir -p data/test-results
cp ../research/rapidapi_test_results_*.json data/test-results/
git add .
git commit -m "Initial API test results"
git push -u origin main
```

### Phase 2: Bulk Data Fetch
```python
# Enhanced bulk fetcher with remote storage
async def bulk_fetch_with_storage():
    storage = RemoteDataStorage()
    
    # Fetch in batches (respect rate limits)
    for batch_num in range(1, 100):  # Adjust based on API limits
        try:
            batch_data = await fetch_api_batch(batch_num)
            if not batch_data:
                break
                
            # Store locally
            filepath = storage.store_api_batch("mufon", batch_data, batch_num)
            print(f"Stored batch {batch_num}: {len(batch_data)} records")
            
            # Commit to GitHub every 10 batches
            if batch_num % 10 == 0:
                storage.commit_and_push(f"Add batches {batch_num-9} to {batch_num}")
            
            # Rate limiting
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Error in batch {batch_num}: {e}")
            break
```

### Phase 3: Import to Production
```python
# Import from remote storage to local database
async def import_from_remote_storage():
    fetcher = RemoteDataFetcher()
    processed_data = fetcher.fetch_processed_data()
    
    # Import using existing import logic
    await import_external_sightings(processed_data, source="mufon")
```

## Benefits of GitHub Storage

1. **Free & Reliable** - No ongoing costs
2. **Version Control** - Track data changes over time
3. **Backup** - Data is safely stored in the cloud
4. **Collaboration** - Team can access and contribute data
5. **CI/CD Integration** - Automatic processing workflows
6. **Global CDN** - Fast access from anywhere

## Security Considerations

- **Public Repository**: Don't store sensitive data (API keys, personal info)
- **Data Sanitization**: Clean data before storing
- **Access Control**: Use private repo if needed ($4/month)

This approach lets you fetch data once using your free RapidAPI tier, store it permanently on GitHub, and import it into any environment without repeated API calls!