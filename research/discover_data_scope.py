#!/usr/bin/env python3
"""
Discover the scope of UFO Aficionado API data.
Test multiple cities and pages to estimate total records available.
"""

import json
import time
import subprocess
from datetime import datetime

# API Configuration
API_KEY = "fff83eeb53mshbebc47c00f0f010p12c28djsnad02ed501215"
BASE_URL = "https://ufo-aficionado-api.p.rapidapi.com"

# Major US cities to test
TEST_CITIES = [
    "losangeles", "newyork", "chicago", "houston", "phoenix", 
    "philadelphia", "sanantonio", "sandiego", "dallas", "sanjose",
    "austin", "jacksonville", "fortworth", "columbus", "charlotte",
    "sanfrancisco", "indianapolis", "seattle", "denver", "washington",
    "boston", "elpaso", "detroit", "nashville", "portland",
    "oklahomacity", "lasvegas", "memphis", "louisville", "baltimore",
    "milwaukee", "albuquerque", "tucson", "fresno", "sacramento",
    "longbeach", "kansascity", "mesa", "virginiabeach", "atlanta",
    "coloradosprings", "omaha", "raleigh", "miami", "oakland",
    "minneapolis", "tulsa", "cleveland", "wichita", "arlington",
    "tampa", "newark", "anaheim", "honolulu", "santaana",
    "stlouis", "riverside", "corpus", "lexington", "pittsburgh",
    "anchorage", "stockton", "cincinnati", "stpaul", "toledo",
    "greensboro", "newark", "plano", "henderson", "lincoln",
    "buffalo", "jerseycity", "chula", "fortwayne", "orlando",
    "stpetersburg", "chandler", "laredo", "norfolk", "durham",
    "madison", "lubbock", "irvine", "winston", "glendale",
    "garland", "hialeah", "reno", "chesapeake", "gilbert",
    "baton", "irving", "scottsdale", "northlas", "fremont"
]

def test_city_pages(city: str, max_pages: int = 10) -> dict:
    """Test how many pages of data exist for a city."""
    
    print(f"Testing {city}...")
    
    city_data = {
        "city": city,
        "pages_found": 0,
        "total_records": 0,
        "has_more": False,
        "error": None
    }
    
    for page in range(1, max_pages + 1):
        try:
            # Construct curl command
            url = f"{BASE_URL}/ufos/city/{city}/page/{page}"
            cmd = [
                "curl", "--silent", "--request", "GET",
                "--url", url,
                "--header", f"x-rapidapi-host: ufo-aficionado-api.p.rapidapi.com",
                "--header", f"x-rapidapi-key: {API_KEY}"
            ]
            
            # Execute request
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                city_data["error"] = f"Curl failed: {result.stderr}"
                break
            
            # Parse response
            try:
                data = json.loads(result.stdout)
                
                # Check if it's an error response
                if isinstance(data, dict) and "message" in data:
                    if "does not exist" in data["message"]:
                        # No more pages
                        break
                    else:
                        city_data["error"] = data["message"]
                        break
                
                # Check if we got records
                if isinstance(data, list):
                    record_count = len(data)
                    if record_count == 0:
                        # No more records
                        break
                    
                    city_data["pages_found"] = page
                    city_data["total_records"] += record_count
                    
                    # If we got less than 20 records, this might be the last page
                    if record_count < 20:
                        break
                    
                    print(f"  Page {page}: {record_count} records")
                
            except json.JSONDecodeError as e:
                city_data["error"] = f"JSON decode error: {e}"
                break
            
            # Rate limiting - be respectful
            time.sleep(1)
            
        except subprocess.TimeoutExpired:
            city_data["error"] = "Request timeout"
            break
        except Exception as e:
            city_data["error"] = f"Unexpected error: {e}"
            break
    
    return city_data

def discover_data_scope():
    """Discover the total scope of available UFO data."""
    
    print("🛸 Discovering UFO Aficionado API Data Scope")
    print("=" * 60)
    
    results = {
        "discovery_timestamp": datetime.now().isoformat(),
        "cities_tested": len(TEST_CITIES),
        "city_results": [],
        "summary": {
            "cities_with_data": 0,
            "total_records_found": 0,
            "estimated_total_records": 0,
            "cities_with_errors": 0,
            "max_pages_found": 0
        }
    }
    
    # Test each city
    for i, city in enumerate(TEST_CITIES, 1):
        print(f"\n[{i}/{len(TEST_CITIES)}] Testing {city}...")
        
        city_result = test_city_pages(city, max_pages=5)  # Limit to 5 pages for discovery
        results["city_results"].append(city_result)
        
        # Update summary
        if city_result["total_records"] > 0:
            results["summary"]["cities_with_data"] += 1
            results["summary"]["total_records_found"] += city_result["total_records"]
            results["summary"]["max_pages_found"] = max(
                results["summary"]["max_pages_found"], 
                city_result["pages_found"]
            )
        
        if city_result["error"]:
            results["summary"]["cities_with_errors"] += 1
            print(f"  ❌ Error: {city_result['error']}")
        else:
            print(f"  ✅ Found {city_result['total_records']} records across {city_result['pages_found']} pages")
        
        # Rate limiting between cities
        if i % 10 == 0:
            print(f"\n  🔄 Progress: {i}/{len(TEST_CITIES)} cities tested...")
            time.sleep(5)  # Longer pause every 10 cities
    
    # Calculate estimates
    if results["summary"]["cities_with_data"] > 0:
        avg_records_per_city = results["summary"]["total_records_found"] / results["summary"]["cities_with_data"]
        # Estimate total if all cities had data
        results["summary"]["estimated_total_records"] = int(avg_records_per_city * len(TEST_CITIES))
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data_scope_discovery_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 DISCOVERY SUMMARY")
    print("=" * 60)
    print(f"Cities tested: {results['summary']['cities_tested']}")
    print(f"Cities with data: {results['summary']['cities_with_data']}")
    print(f"Cities with errors: {results['summary']['cities_with_errors']}")
    print(f"Total records found: {results['summary']['total_records_found']:,}")
    print(f"Estimated total records: {results['summary']['estimated_total_records']:,}")
    print(f"Max pages found (single city): {results['summary']['max_pages_found']}")
    
    print(f"\n📁 Results saved to: {output_file}")
    
    # Top cities by record count
    city_counts = [(r["city"], r["total_records"]) for r in results["city_results"] if r["total_records"] > 0]
    city_counts.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 Top 10 Cities by UFO Reports:")
    for i, (city, count) in enumerate(city_counts[:10], 1):
        print(f"  {i:2d}. {city:15} {count:4d} reports")
    
    return results

if __name__ == "__main__":
    try:
        results = discover_data_scope()
        
        # Quick recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if results["summary"]["estimated_total_records"] > 0:
            print(f"   • Proceed with bulk import - estimated {results['summary']['estimated_total_records']:,} records available")
            print(f"   • This would increase your database by {results['summary']['estimated_total_records']/80000*100:.1f}%")
            if results["summary"]["estimated_total_records"] < 50000:
                print(f"   • ✅ Manageable data size for free tier import")
            else:
                print(f"   • ⚠️ Large dataset - consider city-by-city import strategy")
        else:
            print(f"   • ⚠️ Limited data found - reconsider bulk import strategy")
            
    except KeyboardInterrupt:
        print(f"\n\n⏸️ Discovery interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Discovery failed: {e}")