# Privacy Guidelines for Public Repository

## Overview
Since this repository will be public, we must be careful about what external data we commit.

## Data Privacy Rules

### ✅ SAFE TO COMMIT (Public repo friendly)
- **Processed/aggregated data** (no personal details)
- **Statistical summaries** 
- **Sample datasets** (< 100 records)
- **Metadata files** (sources.json, import_log.json)
- **Documentation and schemas**

### ❌ DO NOT COMMIT (Keep private)
- **Raw API responses** (may contain personal info)
- **Large datasets** (> 10MB files)
- **API keys or credentials**
- **Personal information** (names, addresses, emails)
- **Complete database dumps**

## Recommended Workflow for Public Repo

### 1. Data Sanitization
```python
def sanitize_sighting_data(raw_data):
    """Remove/anonymize personal info before public storage."""
    sanitized = []
    for record in raw_data:
        clean_record = {
            "id": hash_id(record.get("id")),  # Hash original ID
            "date": record.get("date"),
            "city": record.get("city"),
            "state": record.get("state"),
            "shape": record.get("shape"),
            "description": record.get("description"),
            "coordinates": record.get("coordinates"),
            # Remove: names, emails, phone numbers, addresses
        }
        sanitized.append(clean_record)
    return sanitized
```

### 2. Git Ignore Strategy
Already configured in `data/external/.gitignore`:
- Raw API responses are ignored
- Only processed/sanitized data is committed
- Large files (>100MB) are automatically ignored

### 3. Data Sharing Options

**Option A: Processed Data Only (Recommended)**
- Store raw data locally only
- Process and anonymize data
- Commit only sanitized, aggregated datasets
- Include clear data source attribution

**Option B: External Storage Links**
- Store large datasets in external storage (Google Drive, Dropbox)
- Commit only download links and metadata
- Include data access instructions

**Option C: Branch Strategy**
- Keep sensitive data in private branch
- Merge only sanitized data to public main branch
- Use `git filter-branch` to clean history if needed

## Legal Considerations

### Data Attribution
Always include proper attribution:
```json
{
  "data_source": "MUFON via RapidAPI",
  "license": "Educational/Research Use",
  "attribution": "Data provided by Mutual UFO Network (MUFON)",
  "disclaimer": "This data is provided for research purposes only"
}
```

### Copyright Compliance
- Most UFO sighting reports are public domain
- API terms may restrict bulk redistribution
- Include clear disclaimers about data usage rights

## Implementation

### Safe Public Data Structure
```
data/external/
├── processed/
│   ├── mufon_sample_100.json     # ✅ Safe: Small sample
│   ├── monthly_statistics.json   # ✅ Safe: Aggregated stats
│   └── schema_examples.json      # ✅ Safe: Data structure docs
├── metadata/
│   ├── sources.json              # ✅ Safe: Source tracking
│   └── import_log.json           # ✅ Safe: Import history
└── README.md                     # ✅ Safe: Documentation
```

### What Stays Local
```
data/external/
├── raw/                          # ❌ Local only: Full API responses
├── backups/                      # ❌ Local only: Complete datasets  
└── personal/                     # ❌ Local only: Any PII data
```

This approach lets you share your work publicly while respecting privacy and avoiding legal issues!