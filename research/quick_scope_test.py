#!/usr/bin/env python3
"""
Quick test to estimate UFO Aficionado API data scope.
Tests just major cities to get fast estimates.
"""

import json
import time
import subprocess
from datetime import datetime

# API Configuration
API_KEY = "fff83eeb53mshbebc47c00f0f010p12c28djsnad02ed501215"
BASE_URL = "https://ufo-aficionado-api.p.rapidapi.com"

# Test just the top 10 major cities for quick estimate
MAJOR_CITIES = [
    "losangeles", "newyork", "chicago", "houston", "phoenix", 
    "philadelphia", "seattle", "denver", "miami", "atlanta"
]

def quick_test_city(city: str) -> dict:
    """Quickly test a city to see data availability."""
    
    print(f"Testing {city}...", end=" ")
    
    city_data = {
        "city": city,
        "pages_tested": 0,
        "total_records": 0,
        "error": None
    }
    
    # Test just first 3 pages for speed
    for page in range(1, 4):
        try:
            url = f"{BASE_URL}/ufos/city/{city}/page/{page}"
            cmd = [
                "curl", "--silent", "--request", "GET", "--max-time", "10",
                "--url", url,
                "--header", f"x-rapidapi-host: ufo-aficionado-api.p.rapidapi.com",
                "--header", f"x-rapidapi-key: {API_KEY}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                city_data["error"] = "Request failed"
                break
            
            try:
                data = json.loads(result.stdout)
                
                if isinstance(data, dict) and "message" in data:
                    if "does not exist" in data["message"]:
                        break
                    else:
                        city_data["error"] = data["message"]
                        break
                
                if isinstance(data, list):
                    record_count = len(data)
                    if record_count == 0:
                        break
                    
                    city_data["pages_tested"] = page
                    city_data["total_records"] += record_count
                    
                    if record_count < 20:
                        break
                
            except json.JSONDecodeError:
                city_data["error"] = "Invalid JSON"
                break
            
            time.sleep(0.5)  # Quick rate limiting
            
        except Exception as e:
            city_data["error"] = str(e)
            break
    
    if city_data["error"]:
        print(f"❌ {city_data['error']}")
    else:
        print(f"✅ {city_data['total_records']} records in {city_data['pages_tested']} pages")
    
    return city_data

def main():
    """Quick scope discovery."""
    
    print("🛸 Quick UFO Data Scope Test")
    print("=" * 40)
    
    results = []
    total_records = 0
    cities_with_data = 0
    
    for city in MAJOR_CITIES:
        city_result = quick_test_city(city)
        results.append(city_result)
        
        if city_result["total_records"] > 0:
            cities_with_data += 1
            total_records += city_result["total_records"]
    
    print("\n" + "=" * 40)
    print("📊 QUICK SUMMARY")
    print("=" * 40)
    print(f"Cities tested: {len(MAJOR_CITIES)}")
    print(f"Cities with data: {cities_with_data}")
    print(f"Sample records found: {total_records:,}")
    
    if cities_with_data > 0:
        avg_per_city = total_records / cities_with_data
        # Estimate for ~100 cities total
        estimated_total = int(avg_per_city * 100)
        print(f"Average per city: {avg_per_city:.1f}")
        print(f"Estimated total (100 cities): {estimated_total:,}")
        print(f"Database increase: {estimated_total/80000*100:.1f}%")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"quick_scope_{timestamp}.json", 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "results": results,
            "summary": {
                "cities_tested": len(MAJOR_CITIES),
                "cities_with_data": cities_with_data,
                "total_records": total_records
            }
        }, f, indent=2)
    
    print(f"\n💡 Recommendation: {'✅ Proceed with bulk import' if total_records > 500 else '⚠️ Limited data available'}")

if __name__ == "__main__":
    main()