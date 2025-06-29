import pytest
from httpx import AsyncClient
from datetime import datetime, UTC
from api.database import get_db_session
from api.models import Sighting


@pytest.mark.asyncio
async def test_list_sightings_basic(client: AsyncClient, db_setup):
    """Test basic GET /v1/sightings endpoint."""
    # Add some test data first
    await _create_test_sightings()

    response = await client.get("/v1/sightings")

    assert response.status_code == 200
    data = response.json()

    assert "sightings" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "pages" in data

    assert isinstance(data["sightings"], list)
    assert data["total"] >= 3  # At least our test data
    assert data["page"] == 1
    assert data["per_page"] == 25  # Default pagination


@pytest.mark.asyncio
async def test_list_sightings_pagination(client: AsyncClient, db_setup):
    """Test pagination in sightings list."""
    await _create_test_sightings()

    # Test first page
    response = await client.get("/v1/sightings?page=1&per_page=2")
    assert response.status_code == 200
    data = response.json()

    assert len(data["sightings"]) <= 2
    assert data["page"] == 1
    assert data["per_page"] == 2

    # Test page bounds
    response = await client.get("/v1/sightings?page=999&per_page=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["sightings"]) == 0  # Empty page


@pytest.mark.asyncio
async def test_list_sightings_filter_by_state(client: AsyncClient, db_setup):
    """Test filtering sightings by state."""
    await _create_test_sightings()

    response = await client.get("/v1/sightings?state=AZ")
    assert response.status_code == 200
    data = response.json()

    # All returned sightings should be from Arizona
    for sighting in data["sightings"]:
        assert sighting["state"] == "AZ"


@pytest.mark.asyncio
async def test_list_sightings_filter_by_shape(client: AsyncClient, db_setup):
    """Test filtering sightings by shape."""
    await _create_test_sightings()

    response = await client.get("/v1/sightings?shape=disk")
    assert response.status_code == 200
    data = response.json()

    # All returned sightings should be disk-shaped
    for sighting in data["sightings"]:
        assert sighting["shape"] == "disk"


@pytest.mark.asyncio
async def test_list_sightings_filter_by_city(client: AsyncClient, db_setup):
    """Test filtering sightings by city."""
    await _create_test_sightings()

    response = await client.get("/v1/sightings?city=Phoenix")
    assert response.status_code == 200
    data = response.json()

    # All returned sightings should be from Phoenix
    for sighting in data["sightings"]:
        assert sighting["city"] == "Phoenix"


@pytest.mark.asyncio
async def test_get_sighting_by_id(client: AsyncClient, db_setup):
    """Test GET /v1/sightings/{id} endpoint."""
    sighting_id = await _create_test_sightings()

    response = await client.get(f"/v1/sightings/{sighting_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == sighting_id
    assert "city" in data
    assert "state" in data
    assert "shape" in data
    assert "date_time" in data
    assert "duration" in data
    assert "summary" in data
    assert "text" in data
    assert "posted" in data


@pytest.mark.asyncio
async def test_get_sighting_not_found(client: AsyncClient, db_setup):
    """Test GET /v1/sightings/{id} with non-existent ID."""
    response = await client.get("/v1/sightings/99999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_sighting_response_structure(client: AsyncClient, db_setup):
    """Test that sighting response has correct structure."""
    await _create_test_sightings()

    response = await client.get("/v1/sightings")
    assert response.status_code == 200
    data = response.json()

    if data["sightings"]:
        sighting = data["sightings"][0]

        # Required fields
        required_fields = [
            "id",
            "date_time",
            "city",
            "state",
            "shape",
            "duration",
            "summary",
            "text",
            "posted",
        ]
        for field in required_fields:
            assert field in sighting

        # Optional fields (may be null)
        optional_fields = ["latitude", "longitude"]
        for field in optional_fields:
            assert field in sighting  # Field exists but may be null


async def _create_test_sightings():
    """Helper function to create test sightings data."""
    async with get_db_session() as session:
        sightings = [
            Sighting(
                date_time=datetime(2023, 12, 15, 20, 30),
                city="Phoenix",
                state="AZ",
                shape="disk",
                duration="5 minutes",
                summary="Test disk sighting",
                text="Test sighting description for disk object",
                posted=datetime.now(UTC),
                latitude=33.4484,
                longitude=-112.0740,
            ),
            Sighting(
                date_time=datetime(2023, 11, 20, 19, 45),
                city="Sedona",
                state="AZ",
                shape="light",
                duration="2 minutes",
                summary="Test light sighting",
                text="Test sighting description for light object",
                posted=datetime.now(UTC),
                latitude=34.8697,
                longitude=-111.7610,
            ),
            Sighting(
                date_time=datetime(2023, 10, 31, 21, 0),
                city="Austin",
                state="TX",
                shape="oval",
                duration="15 minutes",
                summary="Test oval sighting",
                text="Test sighting description for oval object",
                posted=datetime.now(UTC),
                latitude=30.2672,
                longitude=-97.7431,
            ),
        ]

        for sighting in sightings:
            session.add(sighting)
        await session.commit()

        # Return the ID of the first sighting for individual tests
        await session.refresh(sightings[0])
        return sightings[0].id
