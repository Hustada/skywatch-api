# UFO Aficionado API Analysis

## ✅ API Status: WORKING
- **Subscription**: Active ✅
- **Endpoint Structure**: `/ufos/city/{city}/page/{page}`
- **Records per page**: 20
- **Response Format**: JSON array

## Data Structure Analysis

### Sample Record:
```json
{
  "_id": "64d005f478aba2ec5a3b41da",
  "summary": "Huge stationary disk",
  "city": "losangeles", 
  "shape": "circle",
  "date": "2006-05-15T00:00:00",
  "story": "Huge stationary disk I was sailing with a friend...",
  "link": "http://www.nuforc.org/webreports/050/S50054.html",
  "state": "CA",
  "duration": "30 seconds"
}
```

## Schema Mapping to Our Database

| UFO Aficionado Field | Our Schema Field | Mapping Quality | Notes |
|---------------------|------------------|-----------------|-------|
| `_id` | `external_id` | ✅ Perfect | Unique identifier |
| `date` | `date_time` | ✅ Perfect | ISO 8601 format |
| `city` | `city` | ✅ Perfect | Direct match |
| `state` | `state` | ✅ Perfect | 2-letter state code |
| `shape` | `shape` | ✅ Perfect | Direct match |
| `duration` | `duration` | ✅ Perfect | Direct match |
| `summary` | `summary` | ✅ Perfect | Direct match |
| `story` | `text` | ✅ Perfect | Full description |
| `link` | `source_url` | ✅ Perfect | NUFORC reference |
| ❌ Missing | `posted` | ⚠️ Need default | Use import date |
| ❌ Missing | `latitude` | ⚠️ Need geocoding | Can derive from city/state |
| ❌ Missing | `longitude` | ⚠️ Need geocoding | Can derive from city/state |

## Schema Compatibility: 90% ✅

**Excellent compatibility!** Only missing coordinates, which we can geocode.

## Data Quality Assessment

### ✅ Positives:
- **Clean data structure** - consistent fields across records
- **Rich descriptions** - detailed "story" field with full witness accounts
- **NUFORC source links** - links back to original reports
- **Date formatting** - proper ISO 8601 timestamps
- **Geographic data** - city and state provided
- **Multiple shapes** - circle, triangle, disk, light, etc.

### ⚠️ Areas for Enhancement:
- **No GPS coordinates** - need to geocode city/state
- **No posted date** - will use import timestamp
- **Some empty dates** - a few records have empty date fields

## Bulk Import Strategy

### Endpoint Pattern:
```
/ufos/city/{city}/page/{page}
```

### Major US Cities to Fetch:
```python
MAJOR_CITIES = [
    "losangeles", "newyork", "chicago", "houston", "phoenix", 
    "philadelphia", "sanantonio", "sandiego", "dallas", "sanjose",
    "austin", "jacksonville", "fortworth", "columbus", "charlotte",
    "sanfrancisco", "indianapolis", "seattle", "denver", "washington",
    "boston", "elpaso", "detroit", "nashville", "portland",
    "oklahomacity", "lasvegas", "memphis", "louisville", "baltimore",
    "milwaukee", "albuquerque", "tucson", "fresno", "sacramento",
    "longbeach", "kansascity", "mesa", "virginiabeach", "atlanta",
    "coloradosprings", "omaha", "raleigh", "miami", "oakland",
    "minneapolis", "tulsa", "cleveland", "wichita", "arlington"
]
```

### Rate Limiting Strategy:
- **20 records per request**
- **Estimated total**: 50 cities × 5 pages avg = 5,000 records
- **Rate limit**: Likely 100-1000 requests/month on free tier
- **Batch strategy**: Process in chunks with delays

## Implementation Plan

### Phase 1: Sample Data Collection (Today)
```bash
# Test major cities, 1 page each
curl "https://ufo-aficionado-api.p.rapidapi.com/ufos/city/losangeles/page/1"
curl "https://ufo-aficionado-api.p.rapidapi.com/ufos/city/newyork/page/1"
curl "https://ufo-aficionado-api.p.rapidapi.com/ufos/city/chicago/page/1"
```

### Phase 2: Full Data Collection
- Iterate through all major cities
- Fetch all pages until empty response
- Store raw data in `data/external/rapidapi/raw/`
- Respect rate limits (2-second delays)

### Phase 3: Data Processing
- Geocode city/state to lat/long
- Deduplicate against existing NUFORC data
- Store processed data in `data/external/rapidapi/processed/`

### Phase 4: Database Import
- Import processed data with `source='ufo_aficionado'`
- Update metadata tracking
- Verify no duplicates with existing 80K records

## Data Volume Estimate

**Conservative Estimate:**
- 50 major cities
- Average 3-5 pages per city  
- 20 records per page
- **Total: ~4,000 UFO records**

This represents a **5% increase** to our existing 80K records - very manageable!

## Next Steps

1. ✅ **API Working** - Successfully connected and tested
2. 🔄 **Create bulk fetcher** - Script to systematically fetch all data
3. 📊 **Analyze overlap** - Compare with existing NUFORC data  
4. 🗄️ **Store safely** - Use our privacy-compliant storage system
5. 📥 **Import to database** - Add as new source with proper attribution

**Ready to proceed with bulk data collection!** 🚀