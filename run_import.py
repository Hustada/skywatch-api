#!/usr/bin/env python3
"""
Auto-running UFO import with real-time progress display.
"""

import json
import subprocess
import time
import sqlite3
from datetime import datetime
from pathlib import Path

# API Configuration
API_KEY = "fff83eeb53mshbebc47c00f0f010p12c28djsnad02ed501215"
BASE_URL = "https://ufo-aficionado-api.p.rapidapi.com"

# Start with just a few cities for initial test
CITIES_TO_IMPORT = [
    "losangeles", "newyork", "chicago", "houston", "phoenix"
]

class UFOImporter:
    def __init__(self):
        self.stats = {
            "start_time": time.time(),
            "cities_processed": 0,
            "total_api_calls": 0,
            "total_records_fetched": 0,
            "total_records_imported": 0,
            "errors": 0
        }
        self.data_dir = Path("data/external/rapidapi/raw")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Log progress with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "PROGRESS": "🔄"}
        print(f"[{timestamp}] {symbols.get(level, '📍')} {message}")
        # Flush to ensure real-time display
        import sys
        sys.stdout.flush()
    
    def print_stats(self):
        """Print current statistics."""
        elapsed = time.time() - self.stats["start_time"]
        print("\n" + "="*50)
        print("📊 IMPORT PROGRESS")
        print("="*50)
        print(f"⏱️  Runtime: {elapsed/60:.1f} minutes")
        print(f"🏙️  Cities: {self.stats['cities_processed']}/{len(CITIES_TO_IMPORT)}")
        print(f"🌐 API calls: {self.stats['total_api_calls']}")
        print(f"📥 Records fetched: {self.stats['total_records_fetched']:,}")
        print(f"💾 Records imported: {self.stats['total_records_imported']:,}")
        print(f"❌ Errors: {self.stats['errors']}")
        print("="*50)
        import sys
        sys.stdout.flush()
    
    def fetch_city_data(self, city: str) -> list:
        """Fetch all data for a city."""
        self.log(f"🏙️ Starting {city}")
        
        all_records = []
        page = 1
        
        while True:
            self.log(f"  📄 {city} page {page}")
            
            # Fetch page
            url = f"{BASE_URL}/ufos/city/{city}/page/{page}"
            cmd = [
                "curl", "--silent", "--request", "GET", "--max-time", "30",
                "--url", url,
                "--header", f"x-rapidapi-host: ufo-aficionado-api.p.rapidapi.com",
                "--header", f"x-rapidapi-key: {API_KEY}"
            ]
            
            try:
                self.stats["total_api_calls"] += 1
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
                
                if result.returncode != 0:
                    self.log(f"    ❌ API request failed", "ERROR")
                    self.stats["errors"] += 1
                    break
                
                data = json.loads(result.stdout)
                
                # Check for errors or end of data
                if isinstance(data, dict) and "message" in data:
                    if "does not exist" in data["message"]:
                        break  # No more pages
                    else:
                        self.log(f"    ❌ API error: {data['message']}", "ERROR")
                        self.stats["errors"] += 1
                        break
                
                if isinstance(data, list):
                    if len(data) == 0:
                        break  # No more data
                    
                    all_records.extend(data)
                    self.stats["total_records_fetched"] += len(data)
                    self.log(f"    ✅ Got {len(data)} records (total: {len(all_records)})")
                    
                    if len(data) < 20:
                        break  # Last page
                
                # Rate limiting
                time.sleep(1)
                page += 1
                
                # Safety limit
                if page > 25:  # Reduced for initial test
                    self.log(f"    ⚠️ Hit page limit for {city}", "ERROR")
                    break
                    
            except Exception as e:
                self.log(f"    ❌ Error: {e}", "ERROR")
                self.stats["errors"] += 1
                break
        
        self.log(f"✅ {city} complete: {len(all_records)} records")
        return all_records
    
    def save_city_data(self, city: str, records: list):
        """Save city data to JSON file."""
        if not records:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"{city}_{timestamp}.json"
        
        data_package = {
            "city": city,
            "fetch_timestamp": datetime.now().isoformat(),
            "record_count": len(records),
            "source": "ufo_aficionado_api",
            "records": records
        }
        
        with open(filename, 'w') as f:
            json.dump(data_package, f, indent=2)
        
        self.log(f"💾 Saved {city} data to {filename}")
    
    def import_to_database(self, city: str, records: list):
        """Import records to SQLite database."""
        if not records:
            return 0
        
        self.log(f"🗄️ Importing {city} records to database...")
        
        # Connect to database
        db_path = "sightings.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add new columns if they don't exist
        try:
            cursor.execute("ALTER TABLE sightings ADD COLUMN source VARCHAR(50) DEFAULT 'nuforc'")
            cursor.execute("ALTER TABLE sightings ADD COLUMN external_id VARCHAR(100)")
            cursor.execute("ALTER TABLE sightings ADD COLUMN source_url VARCHAR(500)")
            conn.commit()
            self.log("  📋 Added source tracking columns")
        except sqlite3.OperationalError:
            # Columns already exist
            pass
        
        imported_count = 0
        skipped_count = 0
        
        for i, record in enumerate(records, 1):
            try:
                # Show progress for large imports
                if i % 50 == 0:
                    self.log(f"    Processing record {i}/{len(records)}")
                
                # Check for duplicates
                external_id = record.get("_id")
                if external_id:
                    cursor.execute(
                        "SELECT COUNT(*) FROM sightings WHERE external_id = ? AND source = 'ufo_aficionado'",
                        (external_id,)
                    )
                    if cursor.fetchone()[0] > 0:
                        skipped_count += 1
                        continue  # Skip duplicate
                
                # Parse date
                date_str = record.get("date", "")
                if not date_str:
                    skipped_count += 1
                    continue
                
                try:
                    sighting_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    skipped_count += 1
                    continue
                
                # Extract data
                city_name = record.get("city", "").strip().title()
                state = record.get("state", "").strip().upper()
                shape = record.get("shape", "unknown").strip().lower()
                duration = record.get("duration", "unknown").strip()
                summary = record.get("summary", "").strip()
                story = record.get("story", "").strip()
                source_url = record.get("link", "").strip()
                
                if not city_name or not story:
                    skipped_count += 1
                    continue
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO sightings (
                        date_time, city, state, shape, duration, summary, text, posted,
                        latitude, longitude, source, external_id, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sighting_date.isoformat(),
                    city_name,
                    state,
                    shape,
                    duration,
                    summary if summary else story[:100] + "...",
                    story,
                    datetime.now().isoformat(),
                    None,  # latitude (to be geocoded later)
                    None,  # longitude (to be geocoded later)
                    "ufo_aficionado",
                    external_id,
                    source_url
                ))
                
                imported_count += 1
                
            except Exception as e:
                self.log(f"    ❌ Error importing record: {e}", "ERROR")
                skipped_count += 1
                continue
        
        conn.commit()
        conn.close()
        
        self.stats["total_records_imported"] += imported_count
        self.log(f"✅ Imported {imported_count}/{len(records)} records ({skipped_count} skipped)")
        return imported_count
    
    def run_import(self):
        """Run the complete import process."""
        self.log("🛸 Starting UFO Aficionado import")
        self.log(f"📋 Cities to process: {', '.join(CITIES_TO_IMPORT)}")
        
        for i, city in enumerate(CITIES_TO_IMPORT, 1):
            try:
                self.log(f"🔄 Processing city {i}/{len(CITIES_TO_IMPORT)}: {city}", "PROGRESS")
                
                # Fetch data
                records = self.fetch_city_data(city)
                
                # Save to file
                self.save_city_data(city, records)
                
                # Import to database
                self.import_to_database(city, records)
                
                self.stats["cities_processed"] += 1
                
                # Progress update after each city
                self.print_stats()
                
                # Brief pause between cities
                if i < len(CITIES_TO_IMPORT):
                    self.log("⏸️ Brief pause before next city...")
                    time.sleep(3)
                
            except Exception as e:
                self.log(f"❌ Error processing {city}: {e}", "ERROR")
                self.stats["errors"] += 1
        
        # Final stats
        self.print_stats()
        self.log("🎉 Import complete!", "SUCCESS")

# Auto-start the import
if __name__ == "__main__":
    print("🛸 UFO Aficionado Importer - Auto-starting")
    print("=" * 50)
    
    importer = UFOImporter()
    importer.run_import()