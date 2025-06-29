import pytest
from datetime import datetime, UTC
from sqlalchemy import text
from api.database import get_db_session, get_engine
from api.models import Sighting


@pytest.mark.asyncio
async def test_database_connection():
    """Test that we can connect to the database."""
    engine = get_engine()
    assert engine is not None

    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_create_tables(db_setup):
    """Test that database tables can be created."""
    # Verify tables exist by trying to query them
    async with get_db_session() as session:
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = [row[0] for row in result.fetchall()]
        assert "sightings" in tables


@pytest.mark.asyncio
async def test_sighting_model_creation(db_setup):
    """Test creating a Sighting record."""
    sighting_data = {
        "date_time": datetime.now(UTC),
        "city": "Roswell",
        "state": "NM",
        "shape": "disk",
        "duration": "5 minutes",
        "summary": "Bright disk-shaped object hovering silently",
        "text": (
            "I was driving home when I saw a bright, disk-shaped object "
            "hovering silently above the highway..."
        ),
        "posted": datetime.now(UTC),
        "latitude": 33.3943,
        "longitude": -104.5230,
    }

    async with get_db_session() as session:
        sighting = Sighting(**sighting_data)
        session.add(sighting)
        await session.commit()
        await session.refresh(sighting)

        assert sighting.id is not None
        assert sighting.city == "Roswell"
        assert sighting.state == "NM"
        assert sighting.shape == "disk"


@pytest.mark.asyncio
async def test_sighting_model_queries(db_setup):
    """Test querying Sighting records."""
    # Create test data
    sighting1 = Sighting(
        date_time=datetime.now(UTC),
        city="Phoenix",
        state="AZ",
        shape="triangle",
        duration="10 minutes",
        summary="Large triangular craft",
        text="Three lights in triangle formation",
        posted=datetime.now(UTC),
    )

    sighting2 = Sighting(
        date_time=datetime.now(UTC),
        city="Sedona",
        state="AZ",
        shape="light",
        duration="2 minutes",
        summary="Bright light moving rapidly",
        text="Single bright light zigzagging across sky",
        posted=datetime.now(UTC),
    )

    async with get_db_session() as session:
        session.add_all([sighting1, sighting2])
        await session.commit()

        # Test query by state
        from sqlalchemy import select

        result = await session.execute(select(Sighting).where(Sighting.state == "AZ"))
        arizona_sightings = result.scalars().all()
        assert len(arizona_sightings) == 2

        # Test query by shape
        result = await session.execute(
            select(Sighting).where(Sighting.shape == "triangle")
        )
        triangle_sightings = result.scalars().all()
        assert len(triangle_sightings) == 1
        assert triangle_sightings[0].city == "Phoenix"
