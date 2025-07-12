# External UFO API Research Analysis

## Overview
Research conducted on available external UFO sighting APIs for potential integration with SkyWatch API.

## APIs Discovered

### 1. RapidAPI UFO Sightings (by jamesalester)
- **URL**: https://rapidapi.com/jamesalester/api/ufo-sightings
- **Data Source**: MUFON database
- **Features**: 
  - Recent sightings retrieval
  - Search functionality
  - Image and video results
- **Status**: Limited documentation available without RapidAPI account
- **Integration Potential**: ⚠️ Uncertain - needs account for full evaluation

### 2. UFO Aficionado API (by almaguero95)
- **URL**: https://rapidapi.com/almaguero95/api/ufo-aficionado-api
- **Data Coverage**: 88,000 reports
- **Status**: Limited documentation available without RapidAPI account
- **Integration Potential**: ⚠️ Uncertain - needs account for full evaluation

### 3. Sample UFO Sightings API (GitHub - adavis)
- **URL**: https://github.com/adavis/ufo-sightings-api
- **Technology**: Kotlin + GraphQL
- **Data Source**: Kaggle UFO dataset (same as our current data)
- **Status**: Educational/demo project
- **Integration Potential**: ❌ Not suitable - same data source as ours

## Key Findings

### Data Sources Identified
1. **MUFON** - Mutual UFO Network database
2. **NUFORC** - National UFO Reporting Center (our current source)
3. **Kaggle** - Public dataset (our current source)

### Current UFO Reporting Statistics (2025)
- NUFORC reported 2,174 sightings in first half of 2025 (vs 1,492 in same period 2024)
- MUFON receives 500-1,000 reports monthly
- MUFON historical database: ~70,000 cases (as of 2006)

## Integration Challenges

### 1. Documentation Access
- Most APIs on RapidAPI require paid accounts for full documentation
- Limited free documentation available
- No clear JSON schema information found

### 2. Data Quality Concerns
- Unknown data overlap with our existing NUFORC dataset
- No clear information about data validation or quality standards
- Potential for significant duplicates

### 3. Cost Considerations
- RapidAPI typically has usage-based pricing
- No free tier information available without account signup

## Recommendations

### Immediate Actions
1. **Create RapidAPI account** to evaluate UFO Sightings API documentation
2. **Test sample API calls** to assess data quality and structure
3. **Compare response data** with our existing NUFORC schema

### Alternative Approaches
1. **Direct MUFON integration** - Contact MUFON for official API access
2. **Web scraping consideration** - Evaluate feasibility of scraping public MUFON data
3. **Focus on data enhancement** - Use external sources to enhance existing data rather than wholesale import

### Decision Matrix
| API Source | Data Quality | Documentation | Cost | Integration Effort | Recommendation |
|------------|--------------|---------------|------|-------------------|----------------|
| RapidAPI UFO | Unknown | Limited | Unknown | Medium | Investigate further |
| MUFON Direct | High | Unknown | Unknown | High | Contact directly |
| Web Scraping | Variable | N/A | Low | High | Last resort |

## Bulk Import Strategy

### One-Time Data Import Approach
1. **Use RapidAPI Free Tier** - Get free API key for testing and initial data fetch
2. **Bulk Download** - Fetch all historical data in one-time operation
3. **Local Storage** - Store external data in our database with source attribution
4. **Periodic Updates** - Weekly/monthly API calls for new sightings only

### Free Tier Considerations
- **Rate Limits**: Typically 100-1000 requests/month on free tier
- **Pagination**: May need multiple API calls for large datasets
- **Data Volume**: 88K records (UFO Aficionado) may require strategic batching

### Cost-Effective Implementation
```python
# One-time bulk import strategy
async def bulk_import_external_source():
    # 1. Fetch data in batches (respecting rate limits)
    # 2. Store with source='mufon' or source='rapidapi'
    # 3. Never make real-time API calls for user requests
    # 4. Schedule periodic updates for new data only
```

## Next Steps
1. **Get RapidAPI free account** - Test APIs with free tier
2. **Run test script** - Use `research/test_rapidapi.py` to analyze APIs
3. **Evaluate data quality** - Compare with our existing NUFORC schema
4. **Create bulk import script** - One-time historical data fetch
5. **Design incremental update system** - Periodic new data only
6. **Make go/no-go decision** on integration

## Schema Comparison Needed

Our current schema:
```sql
CREATE TABLE sightings (
    id INTEGER PRIMARY KEY,
    date_time DATETIME NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(10),
    shape VARCHAR(50) NOT NULL,
    duration VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    text TEXT NOT NULL,
    posted DATETIME NOT NULL,
    latitude FLOAT,
    longitude FLOAT
);
```

**TODO**: Compare with external API schemas once documented.