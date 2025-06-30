"""
Import NUFORC UFO sighting data from Kaggle dataset.
"""
import asyncio
import csv
import os
from datetime import datetime, UTC
from typing import Optional
import re

from sqlalchemy import text
from api.database import get_db_session, create_tables
from api.models import Sighting


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Parse datetime string from various formats in the dataset."""
    if not datetime_str or datetime_str.strip() == "":
        return None
    
    # Clean the datetime string
    datetime_str = datetime_str.strip()
    
    # Common formats in NUFORC data
    formats = [
        "%m/%d/%Y %H:%M",  # 10/10/1949 20:30
        "%m/%d/%Y %H:%M:%S",  # with seconds
        "%Y-%m-%d %H:%M:%S",  # ISO format
        "%Y-%m-%d %H:%M",  # ISO without seconds
        "%m/%d/%y %H:%M",  # 2-digit year
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    # If no format works, try to extract at least year/month/day
    try:
        # Extract date part only
        date_part = datetime_str.split()[0] if " " in datetime_str else datetime_str
        return datetime.strptime(date_part, "%m/%d/%Y")
    except ValueError:
        print(f"Could not parse datetime: {datetime_str}")
        return None


def parse_posted_date(posted_str: str) -> Optional[datetime]:
    """Parse the 'date posted' field."""
    if not posted_str or posted_str.strip() == "":
        return None
    
    posted_str = posted_str.strip()
    
    formats = [
        "%m/%d/%Y",  # 4/27/2004
        "%Y-%m-%d",  # ISO format
        "%m/%d/%y",  # 2-digit year
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(posted_str, fmt)
        except ValueError:
            continue
    
    print(f"Could not parse posted date: {posted_str}")
    return None


def clean_text(text: str) -> str:
    """Clean text content by decoding HTML entities and fixing encoding issues."""
    if not text:
        return ""
    
    # Decode common HTML entities
    text = text.replace("&#44", ",")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def parse_duration(duration_str: str) -> str:
    """Parse duration string and return a standardized format."""
    if not duration_str or duration_str.strip() == "":
        return "unknown"
    
    duration_str = duration_str.strip()
    
    # If it's already in a readable format, keep it
    if any(word in duration_str.lower() for word in ["minute", "hour", "second", "day"]):
        return duration_str
    
    # Try to convert seconds to readable format
    try:
        seconds = float(duration_str)
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minutes"
        else:
            hours = int(seconds / 3600)
            remaining_minutes = int((seconds % 3600) / 60)
            if remaining_minutes > 0:
                return f"{hours} hours {remaining_minutes} minutes"
            else:
                return f"{hours} hours"
    except (ValueError, TypeError):
        pass
    
    return duration_str


async def import_kaggle_dataset(filename: str = "scrubbed.csv", limit: Optional[int] = None):
    """Import UFO sightings from Kaggle NUFORC dataset."""
    
    # Determine file path
    if os.path.exists(filename):
        file_path = filename
    elif os.path.exists(f"docs/{filename}"):
        file_path = f"docs/{filename}"
    elif os.path.exists(f"data/{filename}"):
        file_path = f"data/{filename}"
    else:
        raise FileNotFoundError(f"Could not find {filename}")
    
    print(f"Importing UFO data from {file_path}")
    
    # Create tables if they don't exist
    await create_tables()
    
    # Clear existing data
    async with get_db_session() as session:
        await session.execute(text("DELETE FROM sightings"))
        await session.commit()
        print("Cleared existing sighting data")
    
    imported_count = 0
    skipped_count = 0
    
    async with get_db_session() as session:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
            reader = csv.DictReader(csvfile)
            
            batch = []
            batch_size = 1000
            
            for row_num, row in enumerate(reader, 1):
                if limit and imported_count >= limit:
                    break
                
                # Parse datetime
                sighting_datetime = parse_datetime(row.get('datetime', ''))
                if not sighting_datetime:
                    skipped_count += 1
                    continue
                
                # Parse posted date
                posted_date = parse_posted_date(row.get('date posted', ''))
                if not posted_date:
                    posted_date = datetime.now(UTC)
                
                # Extract and clean data
                city = clean_text(row.get('city', '')).title()
                state = clean_text(row.get('state', '')).upper() if row.get('state') else None
                shape = clean_text(row.get('shape', '')).lower()
                comments = clean_text(row.get('comments', ''))
                
                # Parse coordinates
                try:
                    latitude = float(row.get('latitude', '')) if row.get('latitude') else None
                    longitude = float(row.get('longitude', '')) if row.get('longitude') else None
                except (ValueError, TypeError):
                    latitude = longitude = None
                
                # Parse duration
                duration = parse_duration(row.get('duration (hours/min)', '') or row.get('duration (seconds)', ''))
                
                # Create summary from first 100 characters of comments
                summary = comments[:100] + "..." if len(comments) > 100 else comments
                
                # Skip if essential data is missing
                if not city or not comments:
                    skipped_count += 1
                    continue
                
                # Create sighting object
                sighting = Sighting(
                    date_time=sighting_datetime,
                    city=city,
                    state=state,
                    shape=shape,
                    duration=duration,
                    summary=summary,
                    text=comments,
                    posted=posted_date,
                    latitude=latitude,
                    longitude=longitude
                )
                
                batch.append(sighting)
                
                # Process batch
                if len(batch) >= batch_size:
                    session.add_all(batch)
                    await session.commit()
                    imported_count += len(batch)
                    print(f"Imported {imported_count} sightings...")
                    batch = []
            
            # Process remaining batch
            if batch:
                session.add_all(batch)
                await session.commit()
                imported_count += len(batch)
    
    print(f"\nImport complete!")
    print(f"Imported: {imported_count} sightings")
    print(f"Skipped: {skipped_count} sightings (missing essential data)")
    print(f"Total processed: {imported_count + skipped_count} records")


async def main():
    """Main function to run the import."""
    import sys
    
    # Allow command line arguments
    filename = "scrubbed.csv"  # Default to scrubbed dataset
    limit = None
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
            print(f"Limiting import to {limit} records for testing")
        except ValueError:
            print("Invalid limit, importing all records")
    
    await import_kaggle_dataset(filename, limit)


if __name__ == "__main__":
    asyncio.run(main())