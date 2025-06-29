import pytest
from sqlalchemy import select
from api.database import get_db_session
from api.models import Sighting
from data.import_data import import_csv_data, parse_datetime


@pytest.mark.asyncio
async def test_parse_datetime():
    """Test datetime parsing function."""
    # Test standard format
    dt_str = "2023-12-15 20:30:00"
    parsed = parse_datetime(dt_str)
    assert parsed.year == 2023
    assert parsed.month == 12
    assert parsed.day == 15
    assert parsed.hour == 20
    assert parsed.minute == 30


@pytest.mark.asyncio
async def test_import_csv_data(db_setup):
    """Test importing data from CSV file."""
    # Import the sample data
    imported_count = await import_csv_data("data/nuforc_sample.csv")

    # Should have imported 10 records
    assert imported_count == 10

    # Verify data was actually imported
    async with get_db_session() as session:
        result = await session.execute(select(Sighting))
        sightings = result.scalars().all()
        assert len(sightings) == 10

        # Check first record details
        roswell_sighting = next(s for s in sightings if s.city == "Roswell")
        assert roswell_sighting.state == "NM"
        assert roswell_sighting.shape == "disk"
        assert roswell_sighting.latitude == 33.3943
        assert roswell_sighting.longitude == -104.5230


@pytest.mark.asyncio
async def test_import_csv_data_duplicate_handling(db_setup):
    """Test that importing the same data twice doesn't create duplicates."""
    # Import once
    count1 = await import_csv_data("data/nuforc_sample.csv")
    assert count1 == 10

    # Import again - should skip duplicates
    count2 = await import_csv_data("data/nuforc_sample.csv")
    assert count2 == 0  # No new records imported

    # Verify total count is still 10
    async with get_db_session() as session:
        result = await session.execute(select(Sighting))
        sightings = result.scalars().all()
        assert len(sightings) == 10


@pytest.mark.asyncio
async def test_import_csv_data_filtering(db_setup):
    """Test filtering imported data by criteria."""
    await import_csv_data("data/nuforc_sample.csv")

    async with get_db_session() as session:
        # Test filtering by state
        result = await session.execute(select(Sighting).where(Sighting.state == "AZ"))
        az_sightings = result.scalars().all()
        assert len(az_sightings) == 2  # Phoenix and Sedona

        # Test filtering by shape
        result = await session.execute(select(Sighting).where(Sighting.shape == "disk"))
        disk_sightings = result.scalars().all()
        assert len(disk_sightings) == 2  # Roswell and San Francisco
