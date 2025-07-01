from math import ceil, radians, cos, sin, asin, sqrt
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.dependencies import CurrentApiKey
from api.models import Sighting
from api.schemas import SightingResponse, SightingListResponse, ErrorResponse
from api.errors import NotFoundError

router = APIRouter(prefix="/v1", tags=["sightings"])


@router.get(
    "/sightings",
    response_model=SightingListResponse,
    summary="List UFO sightings",
    description="Retrieve a paginated list of UFO sighting reports with optional filtering.",
)
async def list_sightings(
    api_key: CurrentApiKey,
    state: Optional[str] = Query(
        None, description="Filter by state (2-letter code)", max_length=2
    ),
    city: Optional[str] = Query(None, description="Filter by city name"),
    shape: Optional[str] = Query(None, description="Filter by object shape"),
    date_from: Optional[datetime] = Query(
        None, description="Filter sightings from this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Filter sightings until this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
    ),
    lat: Optional[float] = Query(
        None, description="Latitude for geographic search", ge=-90, le=90
    ),
    lng: Optional[float] = Query(
        None, description="Longitude for geographic search", ge=-180, le=180
    ),
    radius: Optional[float] = Query(
        50, description="Search radius in kilometers (default: 50km, max: 500km)", ge=1, le=500
    ),
    sort_by: Optional[str] = Query(
        "date", description="Sort by: date (default), city, state", pattern="^(date|city|state)$"
    ),
    sort_order: Optional[str] = Query(
        "desc", description="Sort order: asc or desc (default)", pattern="^(asc|desc)$"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Records per page"),
    db: AsyncSession = Depends(get_db),
):
    """List UFO sightings with pagination and filtering."""

    # Build base query
    query = select(Sighting)
    count_query = select(func.count(Sighting.id))

    # Apply filters
    filters = []
    
    if state:
        filters.append(Sighting.state == state.upper())

    if city:
        filters.append(Sighting.city.ilike(f"%{city}%"))

    if shape:
        filters.append(Sighting.shape.ilike(f"%{shape}%"))
    
    # Date range filtering
    if date_from:
        filters.append(Sighting.date_time >= date_from)
    
    if date_to:
        filters.append(Sighting.date_time <= date_to)
    
    # Geographic filtering (if coordinates provided)
    if lat is not None and lng is not None:
        # Filter by sightings that have coordinates
        filters.append(Sighting.latitude.isnot(None))
        filters.append(Sighting.longitude.isnot(None))
        
        # We'll filter in Python after fetching candidates within a bounding box
        # This is more efficient than complex SQL distance calculations
        lat_range = radius / 111.0  # Rough conversion: 1 degree latitude ≈ 111 km
        lng_range = radius / (111.0 * cos(radians(lat)))  # Adjust for latitude
        
        filters.append(Sighting.latitude.between(lat - lat_range, lat + lat_range))
        filters.append(Sighting.longitude.between(lng - lng_range, lng + lng_range))
    
    # Apply all filters
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Calculate pagination
    pages = ceil(total / per_page) if total > 0 else 1
    offset = (page - 1) * per_page

    # Apply sorting
    if sort_by == "city":
        order_column = Sighting.city
    elif sort_by == "state":
        order_column = Sighting.state
    else:  # default to date
        order_column = Sighting.date_time
    
    if sort_order == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())
    
    # Apply pagination
    query = query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    sightings = result.scalars().all()
    
    # If geographic search, filter by exact distance
    if lat is not None and lng is not None:
        filtered_sightings = []
        for sighting in sightings:
            if sighting.latitude and sighting.longitude:
                # Calculate distance using Haversine formula
                distance = haversine_distance(lat, lng, sighting.latitude, sighting.longitude)
                if distance <= radius:
                    filtered_sightings.append(sighting)
        sightings = filtered_sightings
        
        # Adjust total count for geographic filtering
        total = len(sightings)
        pages = ceil(total / per_page) if total > 0 else 1

    return SightingListResponse(
        sightings=[SightingResponse.model_validate(sighting) for sighting in sightings],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two points on Earth using the Haversine formula.
    
    Returns distance in kilometers.
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Earth's radius in kilometers
    r = 6371
    
    return c * r


@router.get(
    "/sightings/{sighting_id}",
    response_model=SightingResponse,
    summary="Get UFO sighting by ID",
    description="Retrieve detailed information about a specific UFO sighting.",
    responses={404: {"model": ErrorResponse, "description": "Sighting not found"}},
)
async def get_sighting(
    sighting_id: int, 
    api_key: CurrentApiKey,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific UFO sighting by ID."""

    result = await db.execute(select(Sighting).where(Sighting.id == sighting_id))
    sighting = result.scalar_one_or_none()

    if not sighting:
        raise NotFoundError("Sighting", sighting_id)

    return SightingResponse.model_validate(sighting)
