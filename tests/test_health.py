import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient, db_setup):
    """Test that the health endpoint returns expected response."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "database" in data
    assert data["database"]["status"] == "connected"
    assert "sighting_count" in data["database"]
    assert data["database"]["sighting_count"] == 0  # Empty database initially
