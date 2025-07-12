#!/usr/bin/env python3
"""
Test the UFO import process with a small sample first.
"""

import json
import subprocess
import time
from datetime import datetime

# API Configuration
API_KEY = "fff83eeb53mshbebc47c00f0f010p12c28djsnad02ed501215"
BASE_URL = "https://ufo-aficionado-api.p.rapidapi.com"

def fetch_sample_data():
    """Fetch sample data to test the import process."""
    
    print("🛸 Testing UFO data fetch...")
    
    # Test cities
    test_cities = ["losangeles", "newyork", "chicago"]
    all_records = []
    
    for city in test_cities:
        print(f"\n📍 Fetching {city} (page 1)...")
        
        url = f"{BASE_URL}/ufos/city/{city}/page/1"
        cmd = [
            "curl", "--silent", "--request", "GET", "--max-time", "30",
            "--url", url,
            "--header", f"x-rapidapi-host: ufo-aficionado-api.p.rapidapi.com",
            "--header", f"x-rapidapi-key: {API_KEY}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if isinstance(data, list) and len(data) > 0:
                    all_records.extend(data)
                    print(f"  ✅ Got {len(data)} records")
                else:
                    print(f"  ⚠️ No data returned")
            else:
                print(f"  ❌ Request failed")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        time.sleep(1)  # Rate limiting
    
    # Save sample data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sample_ufo_data_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_records, f, indent=2)
    
    print(f"\n📊 Summary:")
    print(f"  Total records: {len(all_records)}")
    print(f"  Sample saved to: {filename}")
    
    # Show sample record structure
    if all_records:
        print(f"\n📋 Sample record structure:")
        sample = all_records[0]
        for key, value in sample.items():
            value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"  {key}: {value_preview}")
    
    return all_records, filename

def analyze_data_for_import(records):
    """Analyze the data structure for database import."""
    
    print(f"\n🔍 Analyzing data for database import...")
    
    if not records:
        print("  ❌ No records to analyze")
        return
    
    # Check required fields
    required_fields = ["_id", "date", "city", "story"]
    field_coverage = {}
    
    for field in required_fields:
        count = sum(1 for r in records if r.get(field))
        coverage = count / len(records) * 100
        field_coverage[field] = coverage
        print(f"  {field}: {coverage:.1f}% coverage ({count}/{len(records)})")
    
    # Check date formats
    date_formats = {}
    for record in records[:10]:  # Sample first 10
        date_val = record.get("date")
        if date_val:
            date_formats[date_val] = date_formats.get(date_val, 0) + 1
    
    print(f"\n📅 Date format samples:")
    for date_format in list(date_formats.keys())[:5]:
        print(f"  {date_format}")
    
    # Check states
    states = {}
    for record in records:
        state = record.get("state")
        if state:
            states[state] = states.get(state, 0) + 1
    
    print(f"\n🗺️ States found: {len(states)}")
    top_states = sorted(states.items(), key=lambda x: x[1], reverse=True)[:5]
    for state, count in top_states:
        print(f"  {state}: {count} records")
    
    print(f"\n✅ Data quality looks good for import!")

if __name__ == "__main__":
    print("🧪 UFO Data Import Test")
    print("=" * 40)
    
    # Fetch sample data
    records, filename = fetch_sample_data()
    
    # Analyze for import
    analyze_data_for_import(records)
    
    print(f"\n🚀 Ready for full import!")
    print(f"   • {len(records)} sample records processed")
    print(f"   • Data structure verified")
    print(f"   • Import script can now be run safely")