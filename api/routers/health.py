from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select, text, func
from api.database import get_db_session
from api.models import Sighting
from api.config import settings

router = APIRouter(tags=["health"])


class DatabaseHealth(BaseModel):
    status: str
    sighting_count: int


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    database: DatabaseHealth


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health status including database connectivity."""
    database_status = "connected"
    sighting_count = 0

    try:
        async with get_db_session() as session:
            # Test database connection
            await session.execute(text("SELECT 1"))

            # Get sighting count efficiently
            result = await session.execute(select(func.count(Sighting.id)))
            sighting_count = result.scalar() or 0

    except Exception:
        database_status = "disconnected"

    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        timestamp=datetime.now(UTC).isoformat(),
        database=DatabaseHealth(status=database_status, sighting_count=sighting_count),
    )
