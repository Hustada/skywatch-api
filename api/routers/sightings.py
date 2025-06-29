from math import ceil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Sighting
from api.schemas import SightingResponse, SightingListResponse, ErrorResponse

router = APIRouter(prefix="/v1", tags=["sightings"])


@router.get(
    "/sightings",
    response_model=SightingListResponse,
    summary="List UFO sightings",
    description="Retrieve a paginated list of UFO sighting reports with optional filtering.",
)
async def list_sightings(
    state: Optional[str] = Query(
        None, description="Filter by state (2-letter code)", max_length=2
    ),
    city: Optional[str] = Query(None, description="Filter by city name"),
    shape: Optional[str] = Query(None, description="Filter by object shape"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Records per page"),
    db: AsyncSession = Depends(get_db),
):
    """List UFO sightings with pagination and filtering."""

    # Build base query
    query = select(Sighting)
    count_query = select(func.count(Sighting.id))

    # Apply filters
    if state:
        query = query.where(Sighting.state == state.upper())
        count_query = count_query.where(Sighting.state == state.upper())

    if city:
        query = query.where(Sighting.city.ilike(f"%{city}%"))
        count_query = count_query.where(Sighting.city.ilike(f"%{city}%"))

    if shape:
        query = query.where(Sighting.shape.ilike(f"%{shape}%"))
        count_query = count_query.where(Sighting.shape.ilike(f"%{shape}%"))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Calculate pagination
    pages = ceil(total / per_page) if total > 0 else 1
    offset = (page - 1) * per_page

    # Apply pagination and ordering
    query = query.order_by(Sighting.date_time.desc()).offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    sightings = result.scalars().all()

    return SightingListResponse(
        sightings=[SightingResponse.model_validate(sighting) for sighting in sightings],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/sightings/{sighting_id}",
    response_model=SightingResponse,
    summary="Get UFO sighting by ID",
    description="Retrieve detailed information about a specific UFO sighting.",
    responses={404: {"model": ErrorResponse, "description": "Sighting not found"}},
)
async def get_sighting(sighting_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific UFO sighting by ID."""

    result = await db.execute(select(Sighting).where(Sighting.id == sighting_id))
    sighting = result.scalar_one_or_none()

    if not sighting:
        raise HTTPException(
            status_code=404, detail=f"Sighting with ID {sighting_id} not found"
        )

    return SightingResponse.model_validate(sighting)
