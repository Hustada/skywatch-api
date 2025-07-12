#!/usr/bin/env python3
"""
Bulk import UFO Aficionado API data with real-time progress display.
Imports directly into the existing sightings database with source tracking.
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Add the project root to the path so we can import our models
sys.path.append(str(Path(__file__).parent))

from api.database import get_db_session, create_tables
from api.models import Sighting
from api.utils.geography import correct_state_from_coordinates
from sqlalchemy import select, text

# API Configuration
API_KEY = "fff83eeb53mshbebc47c00f0f010p12c28djsnad02ed501215"
BASE_URL = "https://ufo-aficionado-api.p.rapidapi.com"

# Major US cities to import (expanded list)
CITIES_TO_IMPORT = [
    # Tier 1: Major cities (high UFO activity expected)
    "losangeles", "newyork", "chicago", "houston", "phoenix", 
    "philadelphia", "sanantonio", "sandiego", "dallas", "sanjose",
    "austin", "jacksonville", "fortworth", "columbus", "charlotte",
    "sanfrancisco", "indianapolis", "seattle", "denver", "washington",
    "boston", "elpaso", "detroit", "nashville", "portland",
    "oklahomacity", "lasvegas", "memphis", "louisville", "baltimore",
    "milwaukee", "albuquerque", "tucson", "fresno", "sacramento",
    "longbeach", "kansascity", "mesa", "virginiabeach", "atlanta",
    
    # Tier 2: Medium cities
    "coloradosprings", "omaha", "raleigh", "miami", "oakland",
    "minneapolis", "tulsa", "cleveland", "wichita", "arlington",
    "tampa", "honolulu", "santaana", "stlouis", "riverside",
    "lexington", "pittsburgh", "anchorage", "stockton", "cincinnati",
    "stpaul", "toledo", "greensboro", "plano", "henderson",
    "lincoln", "buffalo", "jerseycity", "fortwayne", "orlando",
    "stpetersburg", "chandler", "laredo", "norfolk", "durham",
    "madison", "lubbock", "irvine", "winston", "glendale",
    "garland", "hialeah", "reno", "chesapeake", "gilbert",
    "irving", "scottsdale", "fremont", "baton", "spokane"
]

class UFOAficionadoImporter:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = BASE_URL
        self.session = None
        self.stats = {
            "start_time": None,
            "cities_processed": 0,
            "total_cities": len(CITIES_TO_IMPORT),
            "total_api_calls": 0,
            "total_records_fetched": 0,
            "total_records_imported": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "current_city": None,
            "current_page": 0
        }
        
    def print_progress(self, message: str, level: str = "INFO"):
        """Print timestamped progress message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "PROGRESS": "🔄",
            "CITY": "🏙️",
            "API": "🌐",
            "DB": "🗄️"
        }
        symbol = symbols.get(level, "📍")
        print(f"[{timestamp}] {symbol} {message}")
    
    def print_stats(self):
        """Print current import statistics."""
        elapsed = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        records_per_minute = (self.stats["total_records_fetched"] / elapsed * 60) if elapsed > 0 else 0
        
        print("\n" + "="*60)
        print("📊 IMPORT STATISTICS")
        print("="*60)
        print(f"⏱️  Runtime: {elapsed/60:.1f} minutes")
        print(f"🏙️  Cities: {self.stats['cities_processed']}/{self.stats['total_cities']}")
        print(f"🌐 API calls: {self.stats['total_api_calls']}")
        print(f"📥 Records fetched: {self.stats['total_records_fetched']:,}")
        print(f"💾 Records imported: {self.stats['total_records_imported']:,}")
        print(f"🔄 Duplicates skipped: {self.stats['duplicates_skipped']:,}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⚡ Rate: {records_per_minute:.1f} records/minute")
        if self.stats["current_city"]:
            print(f"🎯 Current: {self.stats['current_city']} (page {self.stats['current_page']})")
        print("="*60)
    
    async def fetch_city_page(self, city: str, page: int) -> Optional[List[Dict]]:
        """Fetch a single page of data for a city."""
        try:
            url = f"{self.base_url}/ufos/city/{city}/page/{page}"
            cmd = [
                "curl", "--silent", "--request", "GET", "--max-time", "30",
                "--url", url,
                "--header", f"x-rapidapi-host: ufo-aficionado-api.p.rapidapi.com",
                "--header", f"x-rapidapi-key: {self.api_key}"
            ]
            
            self.stats["total_api_calls"] += 1
            
            # Execute request
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            
            if result.returncode != 0:
                self.print_progress(f"API request failed for {city} page {page}: {result.stderr}", "ERROR")
                return None
            
            # Parse response
            try:
                data = json.loads(result.stdout)
                
                # Check for API errors
                if isinstance(data, dict) and "message" in data:
                    if "does not exist" in data["message"]:
                        return []  # No more pages
                    else:
                        self.print_progress(f"API error for {city} page {page}: {data['message']}", "ERROR")
                        return None
                
                if isinstance(data, list):
                    self.stats["total_records_fetched"] += len(data)
                    return data
                else:
                    self.print_progress(f"Unexpected response format for {city} page {page}", "ERROR")
                    return None
                    
            except json.JSONDecodeError as e:
                self.print_progress(f"JSON decode error for {city} page {page}: {e}", "ERROR")
                return None
                
        except Exception as e:
            self.print_progress(f"Unexpected error fetching {city} page {page}: {e}", "ERROR")
            self.stats["errors"] += 1
            return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string from UFO Aficionado API."""
        if not date_str:
            return None
            
        try:
            # UFO Aficionado uses ISO format: "2006-05-15T00:00:00"
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Fallback for other formats
                return datetime.strptime(date_str[:10], "%Y-%m-%d")
            except:
                return None
    
    async def geocode_city_state(self, city: str, state: str) -> tuple[Optional[float], Optional[float]]:
        """Simple geocoding for city/state (placeholder - you might want to use a real geocoding service)."""
        # For now, return None - we'll enhance this later
        # You could integrate with Google Geocoding API, OpenStreetMap Nominatim, etc.
        return None, None
    
    async def record_exists(self, external_id: str) -> bool:
        """Check if a record with this external_id already exists."""
        try:
            result = await self.session.execute(
                select(Sighting).where(
                    Sighting.external_id == external_id,
                    Sighting.source == "ufo_aficionado"
                )
            )
            return result.scalar_one_or_none() is not None
        except Exception:
            return False
    
    async def import_record(self, record: Dict) -> bool:
        """Import a single UFO record into the database."""
        try:
            # Check for duplicates
            external_id = record.get("_id")
            if external_id and await self.record_exists(external_id):
                self.stats["duplicates_skipped"] += 1
                return True
            
            # Parse date
            sighting_date = self.parse_date(record.get("date"))
            if not sighting_date:
                # Skip records without valid dates
                return False
            
            # Extract and clean data
            city = record.get("city", "").strip().title()
            state = record.get("state", "").strip().upper()
            shape = record.get("shape", "").strip().lower()
            duration = record.get("duration", "").strip()
            summary = record.get("summary", "").strip()
            story = record.get("story", "").strip()
            source_url = record.get("link", "").strip()
            
            # Skip if essential data is missing
            if not city or not story:
                return False
            
            # Geocode city/state to coordinates (placeholder)
            latitude, longitude = await self.geocode_city_state(city, state)
            
            # Create sighting object
            sighting = Sighting(
                date_time=sighting_date,
                city=city,
                state=state,
                shape=shape if shape else "unknown",
                duration=duration if duration else "unknown",
                summary=summary if summary else story[:100] + "...",
                text=story,
                posted=datetime.now(UTC),  # Use import time as posted date
                latitude=latitude,
                longitude=longitude,
                source="ufo_aficionado",
                external_id=external_id,
                source_url=source_url
            )
            
            self.session.add(sighting)
            self.stats["total_records_imported"] += 1
            return True
            
        except Exception as e:
            self.print_progress(f"Error importing record {record.get('_id', 'unknown')}: {e}", "ERROR")
            self.stats["errors"] += 1
            return False
    
    async def import_city(self, city: str) -> int:
        """Import all UFO data for a specific city."""
        self.print_progress(f"Starting import for {city}", "CITY")
        self.stats["current_city"] = city
        
        city_records = 0
        page = 1
        
        while True:
            self.stats["current_page"] = page
            self.print_progress(f"{city} - fetching page {page}", "API")
            
            # Fetch page data
            page_data = await self.fetch_city_page(city, page)
            
            if page_data is None:
                # Error occurred
                break
            elif len(page_data) == 0:
                # No more data
                self.print_progress(f"{city} - completed ({city_records} records)", "SUCCESS")
                break
            
            # Import records from this page
            page_imported = 0
            for record in page_data:
                if await self.import_record(record):
                    page_imported += 1
            
            city_records += page_imported
            self.print_progress(f"{city} page {page} - imported {page_imported}/{len(page_data)} records", "DB")
            
            # Commit every page to avoid losing data
            try:
                await self.session.commit()
            except Exception as e:
                self.print_progress(f"Database commit error: {e}", "ERROR")
                await self.session.rollback()
                self.stats["errors"] += 1
            
            # Rate limiting - be respectful to the API
            await asyncio.sleep(2)
            
            page += 1
            
            # Safety limit to prevent runaway imports
            if page > 50:
                self.print_progress(f"{city} - hit page limit (50), stopping", "ERROR")
                break
        
        self.stats["cities_processed"] += 1
        return city_records
    
    async def run_import(self):
        """Run the complete bulk import process."""
        self.print_progress("🛸 Starting UFO Aficionado bulk import", "SUCCESS")
        self.stats["start_time"] = time.time()
        
        # Ensure database tables exist
        await create_tables()
        
        # Get database session
        async with get_db_session() as session:
            self.session = session
            
            # Check if we need to add new columns for source tracking
            try:
                # Try to add new columns if they don't exist
                await session.execute(text("ALTER TABLE sightings ADD COLUMN source VARCHAR(50) DEFAULT 'nuforc'"))
                await session.execute(text("ALTER TABLE sightings ADD COLUMN external_id VARCHAR(100)"))
                await session.execute(text("ALTER TABLE sightings ADD COLUMN source_url VARCHAR(500)"))
                await session.commit()
                self.print_progress("Added source tracking columns to database", "DB")
            except Exception:
                # Columns probably already exist
                await session.rollback()
            
            # Import each city
            for i, city in enumerate(CITIES_TO_IMPORT, 1):
                try:
                    self.print_progress(f"Processing city {i}/{len(CITIES_TO_IMPORT)}: {city}", "PROGRESS")
                    
                    city_count = await self.import_city(city)
                    
                    # Print progress every 10 cities
                    if i % 10 == 0:
                        self.print_stats()
                    
                    # Longer pause every 20 cities to be extra respectful to API
                    if i % 20 == 0:
                        self.print_progress("Taking longer break to respect API limits...", "INFO")
                        await asyncio.sleep(10)
                
                except KeyboardInterrupt:
                    self.print_progress("Import interrupted by user", "ERROR")
                    break
                except Exception as e:
                    self.print_progress(f"Unexpected error processing {city}: {e}", "ERROR")
                    self.stats["errors"] += 1
                    continue
        
        # Final statistics
        self.print_stats()
        self.print_progress("🎉 UFO Aficionado import completed!", "SUCCESS")

async def main():
    """Main entry point."""
    print("🛸 UFO Aficionado Bulk Importer")
    print("=" * 50)
    print("This will import UFO sighting data directly into your existing database.")
    print("Progress will be displayed in real-time.")
    print("You can stop anytime with Ctrl+C")
    print("")
    
    # Confirm before starting
    response = input("Ready to start import? (y/N): ").strip().lower()
    if response != 'y':
        print("Import cancelled.")
        return
    
    # Run the import
    importer = UFOAficionadoImporter()
    await importer.run_import()

if __name__ == "__main__":
    asyncio.run(main())