import csv
import asyncio
from datetime import datetime
from sqlalchemy import select
from api.database import get_db_session, create_tables
from api.models import Sighting


def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string in NUFORC format."""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Try without seconds if format is different
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            # Fallback to date only
            return datetime.strptime(dt_str.split()[0], "%Y-%m-%d")


async def import_csv_data(csv_file_path: str) -> int:
    """
    Import sighting data from CSV file.

    Returns the number of new records imported.
    """
    imported_count = 0

    async with get_db_session() as session:
        with open(csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                # Check if this record already exists
                # (simple duplicate check by city, date, and shape)
                existing = await session.execute(
                    select(Sighting).where(
                        Sighting.city == row["city"],
                        Sighting.state == row["state"],
                        Sighting.date_time == parse_datetime(row["date_time"]),
                        Sighting.shape == row["shape"],
                    )
                )

                if existing.scalar_one_or_none() is not None:
                    continue  # Skip duplicate

                # Parse optional coordinates
                latitude = None
                longitude = None
                if row.get("latitude") and row["latitude"].strip():
                    try:
                        latitude = float(row["latitude"])
                    except ValueError:
                        pass

                if row.get("longitude") and row["longitude"].strip():
                    try:
                        longitude = float(row["longitude"])
                    except ValueError:
                        pass

                # Create new sighting record
                sighting = Sighting(
                    date_time=parse_datetime(row["date_time"]),
                    city=row["city"],
                    state=row["state"],
                    shape=row["shape"],
                    duration=row["duration"],
                    summary=row["summary"],
                    text=row["text"],
                    posted=parse_datetime(row["posted"]),
                    latitude=latitude,
                    longitude=longitude,
                )

                session.add(sighting)
                imported_count += 1

        await session.commit()

    return imported_count


async def main():
    """Main function to run data import."""
    print("Creating database tables...")
    await create_tables()

    print("Importing NUFORC sample data...")
    count = await import_csv_data("data/nuforc_sample.csv")
    print(f"Imported {count} sighting records.")


if __name__ == "__main__":
    asyncio.run(main())
