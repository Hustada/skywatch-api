import pytest
from datetime import datetime, UTC

# Import test config first to set environment variables
import tests.test_config

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from api.main import app
from api.database import create_tables, drop_tables, get_db_session
from api.models import User, ApiKey, Sighting
from api.auth import get_password_hash, generate_api_key, hash_api_key, create_access_token


@pytest.fixture
async def client(db_setup):
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


@pytest.fixture
async def db_session():
    """Get a database session for tests."""
    async with get_db_session() as session:
        yield session


@pytest.fixture
async def test_user(db_setup):
    """Create a test user."""
    async with get_db_session() as session:
        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            created_at=datetime.now(UTC)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def auth_headers(test_user):
    """Get authorization headers with JWT token for test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_api_key(db_setup, test_user):
    """Create a test API key."""
    async with get_db_session() as session:
        api_key_str = generate_api_key()
        api_key = ApiKey(
            key_hash=hash_api_key(api_key_str),
            name="Test API Key",
            tier="basic",
            quota_limit=10000,
            quota_used=0,
            quota_reset_date=datetime.now(UTC).replace(day=1, month=((datetime.now(UTC).month % 12) + 1)),
            user_id=test_user.id,
            created_at=datetime.now(UTC)
        )
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)
        
        # Store the actual key string for use in tests
        api_key._key_string = api_key_str
        return api_key


@pytest.fixture
def test_api_key_string(test_api_key):
    """Get the actual API key string for testing."""
    return test_api_key._key_string


@pytest.fixture
async def sample_sightings(db_setup):
    """Create sample sighting data for tests."""
    async with get_db_session() as session:
        sightings = [
            Sighting(
                date_time=datetime(2023, 1, 15, 20, 30),
                city="Phoenix",
                state="AZ",
                shape="disk",
                duration="5 minutes",
                summary="Bright disk-shaped object hovering",
                text="Witnessed a bright disk-shaped object...",
                posted=datetime(2023, 1, 16),
                latitude=33.4484,
                longitude=-112.0740
            ),
            Sighting(
                date_time=datetime(2023, 6, 10, 22, 0),
                city="Seattle",
                state="WA",
                shape="triangle",
                duration="2 minutes",
                summary="Three lights in triangular formation",
                text="Three bright lights moving in perfect triangle...",
                posted=datetime(2023, 6, 11),
                latitude=47.6062,
                longitude=-122.3321
            ),
            Sighting(
                date_time=datetime(2023, 12, 25, 19, 45),
                city="Miami",
                state="FL",
                shape="sphere",
                duration="10 seconds",
                summary="Fast moving sphere with trail",
                text="Sphere with glowing trail moving rapidly...",
                posted=datetime(2023, 12, 26),
                latitude=25.7617,
                longitude=-80.1918
            )
        ]
        
        for sighting in sightings:
            session.add(sighting)
        
        await session.commit()
        return sightings
