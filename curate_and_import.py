#!/usr/bin/env python3
"""
Curate and import the bulk-fetched UFO data.
Process all JSON files and import clean data to database.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
import re

class UFOCurator:
    def __init__(self):
        self.data_dir = Path("data/external/rapidapi/raw")
        self.processed_dir = Path("data/external/rapidapi/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "files_processed": 0,
            "total_raw_records": 0,
            "records_after_dedup": 0,
            "records_imported": 0,
            "duplicates_removed": 0,
            "invalid_records": 0
        }
    
    def log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def load_all_raw_data(self) -> list:
        """Load all JSON files and combine records."""
        
        self.log("📂 Loading all raw data files...")
        
        all_records = []
        json_files = list(self.data_dir.glob("*.json"))
        
        self.log(f"📁 Found {len(json_files)} data files")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if "records" in data and isinstance(data["records"], list):
                    city_records = data["records"]
                    all_records.extend(city_records)
                    self.log(f"   ✅ {file_path.name}: {len(city_records)} records")
                    self.stats["files_processed"] += 1
                else:
                    self.log(f"   ⚠️ {file_path.name}: Invalid format")
                    
            except Exception as e:
                self.log(f"   ❌ {file_path.name}: Error - {e}")
        
        self.stats["total_raw_records"] = len(all_records)
        self.log(f"📊 Total raw records loaded: {len(all_records):,}")
        return all_records
    
    def deduplicate_records(self, records: list) -> list:
        """Remove duplicates based on _id field."""
        
        self.log("🔄 Deduplicating records...")
        
        seen_ids = set()
        unique_records = []
        
        for record in records:
            record_id = record.get("_id")
            if record_id and record_id not in seen_ids:
                seen_ids.add(record_id)
                unique_records.append(record)
            else:
                self.stats["duplicates_removed"] += 1
        
        self.stats["records_after_dedup"] = len(unique_records)
        self.log(f"✅ Removed {self.stats['duplicates_removed']:,} duplicates")
        self.log(f"📊 Unique records: {len(unique_records):,}")
        
        return unique_records
    
    def clean_record(self, record: dict) -> dict:
        """Clean and standardize a single record."""
        
        cleaned = {}
        
        # Required fields
        cleaned["external_id"] = record.get("_id", "")
        cleaned["date"] = record.get("date", "")
        cleaned["city"] = record.get("city", "").strip().title()
        cleaned["state"] = record.get("state", "").strip().upper()
        cleaned["shape"] = record.get("shape", "unknown").strip().lower()
        cleaned["duration"] = record.get("duration", "unknown").strip()
        cleaned["summary"] = record.get("summary", "").strip()
        cleaned["story"] = record.get("story", "").strip()
        cleaned["source_url"] = record.get("link", "").strip()
        
        # Data validation and cleaning
        if not cleaned["external_id"] or not cleaned["story"] or not cleaned["city"]:
            return None  # Invalid record
        
        # Clean summary - create from story if empty
        if not cleaned["summary"] and cleaned["story"]:
            cleaned["summary"] = cleaned["story"][:100] + "..." if len(cleaned["story"]) > 100 else cleaned["story"]
        
        # Clean state - handle international locations
        if cleaned["state"] and len(cleaned["state"]) > 2:
            cleaned["state"] = None  # Probably international
        
        # Clean shape
        if not cleaned["shape"] or cleaned["shape"] in ["unknown", "", "other"]:
            cleaned["shape"] = "unknown"
        
        return cleaned
    
    def parse_date(self, date_str: str) -> str:
        """Parse and standardize date."""
        if not date_str:
            return None
        
        try:
            # Handle ISO format: "2006-05-15T00:00:00"
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.isoformat()
        except:
            return None
    
    def curate_records(self, records: list) -> list:
        """Clean and curate all records."""
        
        self.log("🧹 Curating records...")
        
        curated = []
        invalid_count = 0
        
        for record in records:
            cleaned = self.clean_record(record)
            if cleaned:
                # Parse date
                cleaned["date_parsed"] = self.parse_date(cleaned["date"])
                if cleaned["date_parsed"]:
                    curated.append(cleaned)
                else:
                    invalid_count += 1
            else:
                invalid_count += 1
        
        self.stats["invalid_records"] = invalid_count
        self.log(f"✅ Curated {len(curated):,} valid records")
        self.log(f"⚠️ Rejected {invalid_count:,} invalid records")
        
        return curated
    
    def save_curated_data(self, records: list):
        """Save curated data to processed directory."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.processed_dir / f"curated_ufo_data_{timestamp}.json"
        
        curated_package = {
            "curation_timestamp": datetime.now().isoformat(),
            "total_records": len(records),
            "source": "ufo_aficionado_api_curated",
            "curation_stats": self.stats,
            "records": records
        }
        
        with open(output_file, 'w') as f:
            json.dump(curated_package, f, indent=2)
        
        self.log(f"💾 Saved curated data to: {output_file}")
        return output_file
    
    def import_to_database(self, records: list):
        """Import curated records to database."""
        
        self.log("🗄️ Importing to database...")
        
        # Connect to database
        conn = sqlite3.connect("sightings.db")
        cursor = conn.cursor()
        
        # Ensure columns exist
        try:
            cursor.execute("ALTER TABLE sightings ADD COLUMN source VARCHAR(50) DEFAULT 'nuforc'")
            cursor.execute("ALTER TABLE sightings ADD COLUMN external_id VARCHAR(100)")
            cursor.execute("ALTER TABLE sightings ADD COLUMN source_url VARCHAR(500)")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Columns exist
        
        imported = 0
        skipped = 0
        
        for record in records:
            try:
                # Check for existing
                cursor.execute(
                    "SELECT COUNT(*) FROM sightings WHERE external_id = ? AND source = 'ufo_aficionado'",
                    (record["external_id"],)
                )
                if cursor.fetchone()[0] > 0:
                    skipped += 1
                    continue
                
                # Insert new record
                cursor.execute("""
                    INSERT INTO sightings (
                        date_time, city, state, shape, duration, summary, text, posted,
                        latitude, longitude, source, external_id, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record["date_parsed"],
                    record["city"],
                    record["state"],
                    record["shape"],
                    record["duration"],
                    record["summary"],
                    record["story"],
                    datetime.now().isoformat(),
                    None,  # latitude - to be geocoded later
                    None,  # longitude - to be geocoded later
                    "ufo_aficionado",
                    record["external_id"],
                    record["source_url"]
                ))
                
                imported += 1
                
                # Progress update
                if imported % 1000 == 0:
                    self.log(f"   📊 Imported {imported:,} records...")
                
            except Exception as e:
                self.log(f"   ❌ Error importing record {record.get('external_id', 'unknown')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        self.stats["records_imported"] = imported
        self.log(f"✅ Imported {imported:,} records to database")
        self.log(f"⏭️ Skipped {skipped:,} existing records")
    
    def run_curation(self):
        """Run the complete curation process."""
        
        self.log("🛸 Starting UFO data curation")
        
        # Load all raw data
        raw_records = self.load_all_raw_data()
        if not raw_records:
            self.log("❌ No raw data found!")
            return
        
        # Deduplicate
        unique_records = self.deduplicate_records(raw_records)
        
        # Curate and clean
        curated_records = self.curate_records(unique_records)
        
        # Save curated data
        output_file = self.save_curated_data(curated_records)
        
        # Import to database
        self.import_to_database(curated_records)
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"🎉 CURATION COMPLETE")
        print(f"{'='*60}")
        print(f"📁 Files processed: {self.stats['files_processed']}")
        print(f"📥 Raw records: {self.stats['total_raw_records']:,}")
        print(f"🔄 After deduplication: {self.stats['records_after_dedup']:,}")
        print(f"⚠️ Invalid records: {self.stats['invalid_records']:,}")
        print(f"💾 Records imported: {self.stats['records_imported']:,}")
        print(f"📊 Database growth: +{self.stats['records_imported']:,} UFO sightings")
        print(f"💎 Curated data saved: {output_file}")
        print(f"{'='*60}")

def main():
    """Main entry point."""
    print("🧹 UFO Data Curator & Importer")
    print("=" * 50)
    print("This will:")
    print("• Load all raw JSON files")
    print("• Remove duplicates")
    print("• Clean and validate data")
    print("• Import to database")
    print("")
    
    curator = UFOCurator()
    curator.run_curation()

if __name__ == "__main__":
    main()