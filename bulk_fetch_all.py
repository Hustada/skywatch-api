#!/usr/bin/env python3
"""
Efficient bulk fetcher - grab ALL UFO data first, curate later.
Just downloads and saves everything to JSON files for processing.
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
import concurrent.futures
import threading

# API Configuration
API_KEY = "fff83eeb53mshbebc47c00f0f010p12c28djsnad02ed501215"
BASE_URL = "https://ufo-aficionado-api.p.rapidapi.com"

# Comprehensive city list - all major US cities
ALL_CITIES = [
    # Major metros (Tier 1) - highest UFO activity expected
    "losangeles", "newyork", "chicago", "houston", "phoenix", "philadelphia", 
    "sanantonio", "sandiego", "dallas", "sanjose", "austin", "jacksonville",
    "fortworth", "columbus", "charlotte", "sanfrancisco", "indianapolis", 
    "seattle", "denver", "washington", "boston", "elpaso", "detroit", 
    "nashville", "portland", "oklahomacity", "lasvegas", "memphis", 
    "louisville", "baltimore", "milwaukee", "albuquerque", "tucson", 
    "fresno", "sacramento", "longbeach", "kansascity", "mesa", 
    "virginiabeach", "atlanta", "coloradosprings", "omaha", "raleigh", 
    "miami", "oakland", "minneapolis", "tulsa", "cleveland", "wichita", 
    "arlington", "tampa", "newark", "anaheim", "honolulu", "santaana",
    
    # Secondary cities (Tier 2) - good coverage
    "stlouis", "riverside", "corpus", "lexington", "pittsburgh", "anchorage",
    "stockton", "cincinnati", "stpaul", "toledo", "greensboro", "plano",
    "henderson", "lincoln", "buffalo", "jerseycity", "chula", "fortwayne",
    "orlando", "stpetersburg", "chandler", "laredo", "norfolk", "durham",
    "madison", "lubbock", "irvine", "winston", "glendale", "garland",
    "hialeah", "reno", "chesapeake", "gilbert", "baton", "irving",
    "scottsdale", "northlas", "fremont", "spokane", "richmond", "fontana",
    "moreno", "yonkers", "fayetteville", "birmingham", "rochester",
    "grandrapids", "huntsville", "saltlake", "amarillo", "mobilecity",
    "shreveport", "littlerock", "augusta", "providence", "knoxville",
    "worcester", "chattanooga", "brownsville", "tempe", "newport",
    "santa", "salem", "springfield", "kansas", "eugene", "fortlauderdale",
    "pembroke", "cape", "sioux", "peoria", "erie", "cedar", "dayton"
]

class BulkUFOFetcher:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = BASE_URL
        self.data_dir = Path("data/external/rapidapi/raw")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {
            "start_time": time.time(),
            "cities_completed": 0,
            "total_api_calls": 0,
            "total_records": 0,
            "errors": 0,
            "skipped_existing": 0
        }
        self.lock = threading.Lock()
    
    def log(self, message: str):
        """Thread-safe logging."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        with self.lock:
            print(f"[{timestamp}] {message}")
    
    def city_already_fetched(self, city: str) -> bool:
        """Check if we already have data for this city."""
        pattern = f"{city}_*.json"
        existing_files = list(self.data_dir.glob(pattern))
        return len(existing_files) > 0
    
    def fetch_city_complete(self, city: str) -> dict:
        """Fetch ALL data for a single city efficiently."""
        
        if self.city_already_fetched(city):
            self.log(f"⏭️ Skipping {city} - already fetched")
            with self.lock:
                self.stats["skipped_existing"] += 1
            return {"city": city, "status": "skipped", "records": 0}
        
        self.log(f"🏙️ Starting {city}")
        
        all_records = []
        page = 1
        api_calls = 0
        
        while True:
            try:
                # Fetch page
                url = f"{self.base_url}/ufos/city/{city}/page/{page}"
                cmd = [
                    "curl", "--silent", "--request", "GET", "--max-time", "20",
                    "--url", url,
                    "--header", f"x-rapidapi-host: ufo-aficionado-api.p.rapidapi.com",
                    "--header", f"x-rapidapi-key: {self.api_key}"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
                api_calls += 1
                
                if result.returncode != 0:
                    self.log(f"❌ {city} API failed on page {page}")
                    break
                
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    self.log(f"❌ {city} invalid JSON on page {page}")
                    break
                
                # Check for end conditions
                if isinstance(data, dict) and "message" in data:
                    if "does not exist" in data["message"]:
                        break  # No more pages
                    else:
                        self.log(f"❌ {city} API error: {data['message']}")
                        break
                
                if isinstance(data, list):
                    if len(data) == 0:
                        break  # No more data
                    
                    all_records.extend(data)
                    
                    # Show progress every 5 pages
                    if page % 5 == 0:
                        self.log(f"   📄 {city} page {page} - {len(all_records)} total records")
                    
                    if len(data) < 20:
                        break  # Last page (partial)
                
                page += 1
                
                # Safety limits
                if page > 100:  # Very generous limit
                    self.log(f"⚠️ {city} hit safety limit at page {page}")
                    break
                
                # Brief rate limiting
                time.sleep(0.5)  # Faster than before
                
            except Exception as e:
                self.log(f"❌ {city} error on page {page}: {e}")
                break
        
        # Save data
        if all_records:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_dir / f"{city}_{timestamp}.json"
            
            data_package = {
                "city": city,
                "fetch_timestamp": datetime.now().isoformat(),
                "record_count": len(all_records),
                "pages_fetched": page - 1,
                "api_calls": api_calls,
                "source": "ufo_aficionado_api",
                "records": all_records
            }
            
            with open(filename, 'w') as f:
                json.dump(data_package, f, indent=2)
            
            self.log(f"✅ {city} complete: {len(all_records)} records saved")
        else:
            self.log(f"⚠️ {city} no data found")
        
        # Update stats
        with self.lock:
            self.stats["cities_completed"] += 1
            self.stats["total_api_calls"] += api_calls
            self.stats["total_records"] += len(all_records)
            
            if len(all_records) == 0:
                self.stats["errors"] += 1
        
        return {
            "city": city,
            "status": "completed",
            "records": len(all_records),
            "api_calls": api_calls
        }
    
    def print_progress(self):
        """Print current progress."""
        elapsed = time.time() - self.stats["start_time"]
        rate = self.stats["cities_completed"] / elapsed * 60 if elapsed > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"📊 BULK FETCH PROGRESS")
        print(f"{'='*60}")
        print(f"⏱️  Runtime: {elapsed/60:.1f} minutes")
        print(f"🏙️  Cities completed: {self.stats['cities_completed']}/{len(ALL_CITIES)}")
        print(f"⏭️  Skipped existing: {self.stats['skipped_existing']}")
        print(f"🌐 Total API calls: {self.stats['total_api_calls']}")
        print(f"📥 Total records: {self.stats['total_records']:,}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⚡ Rate: {rate:.1f} cities/minute")
        print(f"{'='*60}")
    
    def run_bulk_fetch(self, max_workers=3):
        """Run bulk fetch with controlled concurrency."""
        
        self.log(f"🛸 Starting bulk UFO fetch")
        self.log(f"📋 Total cities: {len(ALL_CITIES)}")
        self.log(f"🔄 Concurrent workers: {max_workers}")
        self.log(f"💾 Data directory: {self.data_dir}")
        
        # Use ThreadPoolExecutor for controlled concurrency
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            
            # Submit all cities
            future_to_city = {
                executor.submit(self.fetch_city_complete, city): city 
                for city in ALL_CITIES
            }
            
            # Process results as they complete
            completed = 0
            for future in concurrent.futures.as_completed(future_to_city):
                city = future_to_city[future]
                completed += 1
                
                try:
                    result = future.result()
                    
                    # Progress update every 10 cities
                    if completed % 10 == 0:
                        self.print_progress()
                    
                except Exception as e:
                    self.log(f"❌ {city} failed with exception: {e}")
                    with self.lock:
                        self.stats["errors"] += 1
        
        # Final summary
        self.print_progress()
        self.log("🎉 Bulk fetch complete!")
        
        # Summary stats
        elapsed = time.time() - self.stats["start_time"]
        avg_records_per_city = self.stats["total_records"] / max(1, self.stats["cities_completed"])
        
        print(f"\n🎯 FINAL SUMMARY:")
        print(f"   ⏱️  Total time: {elapsed/60:.1f} minutes")
        print(f"   📥 Total records: {self.stats['total_records']:,}")
        print(f"   🌐 Total API calls: {self.stats['total_api_calls']}")
        print(f"   📊 Avg records/city: {avg_records_per_city:.1f}")
        print(f"   💰 Estimated cost: ${self.stats['total_api_calls'] * 0.01:.2f} (if $0.01/call)")
        print(f"   📁 Data files saved: {len(list(self.data_dir.glob('*.json')))}")

def main():
    """Main entry point."""
    print("🛸 UFO Bulk Data Fetcher")
    print("=" * 50)
    print("This will fetch ALL UFO data efficiently:")
    print("• Download everything to JSON files first")
    print("• Process/curate/import later")
    print("• Resume capability (skips existing)")
    print("• Concurrent fetching for speed")
    print("")
    
    fetcher = BulkUFOFetcher()
    fetcher.run_bulk_fetch(max_workers=2)  # Conservative concurrency

if __name__ == "__main__":
    main()