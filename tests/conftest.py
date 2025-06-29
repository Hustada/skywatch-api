import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.database import create_tables, drop_tables


@pytest.fixture
async def client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def db_setup():
    """Set up test database with clean tables."""
    # Clean up any existing tables
    await drop_tables()
    # Create fresh tables
    await create_tables()
    yield
    # Clean up after test
    await drop_tables()
