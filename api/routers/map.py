"""Map data endpoints for geographic visualization."""

from math import ceil
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.dependencies import CurrentApiKey
from api.models import Sighting
from api.schemas import ErrorResponse

router = APIRouter(prefix="/v1/map", tags=["map"])


@router.get(
    "/states",
    summary="Get available US states",
    description="Retrieve list of US states that have UFO sightings in the database.",
)
async def get_available_states(
    db: AsyncSession = Depends(get_db),
):
    """Get list of US states with sighting data."""
    
    # Query for US states (2-letter codes) with sighting counts
    query = select(
        Sighting.state,
        func.count(Sighting.id).label('sighting_count')
    ).where(
        Sighting.state.isnot(None),
        func.length(Sighting.state) == 2  # Filter to US states only
    ).group_by(Sighting.state).order_by(Sighting.state)
    
    result = await db.execute(query)
    states_data = result.all()
    
    # US state names mapping
    us_states = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
        'AS': 'American Samoa', 'GU': 'Guam', 'MP': 'Northern Mariana Islands',
        'PR': 'Puerto Rico', 'VI': 'Virgin Islands'
    }
    
    # Format response with state names
    states = []
    for state_data in states_data:
        state_code = state_data.state
        state_name = us_states.get(state_code, state_code)
        states.append({
            'code': state_code,
            'name': state_name,
            'sighting_count': state_data.sighting_count
        })
    
    return {
        'states': states,
        'total_states': len(states)
    }


@router.get(
    "/data",
    summary="Get map visualization data",
    description="Retrieve sighting data optimized for map display with optional clustering.",
)
async def get_map_data(
    # Filtering parameters
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    shape: Optional[str] = Query(None, description="Filter by object shape"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    # Map-specific parameters
    bounds: Optional[str] = Query(
        None, 
        description="Map bounds as 'south,west,north,east' for viewport filtering"
    ),
    zoom_level: Optional[int] = Query(
        None, 
        description="Current zoom level for clustering optimization",
        ge=1, le=18
    ),
    format: str = Query(
        "geojson", 
        description="Response format",
        pattern="^(geojson|simple)$"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get sighting data optimized for map visualization."""

    # Build base query
    query = select(Sighting).where(
        Sighting.latitude.isnot(None),
        Sighting.longitude.isnot(None)
    )
    
    # Apply filters
    filters = []
    
    if state:
        if state.upper() == "US":
            # Show only US states (2-letter codes)
            filters.append(Sighting.state.isnot(None))
            filters.append(func.length(Sighting.state) == 2)
        elif state.upper() == "INTERNATIONAL":
            # Show only international sightings (non-US or null states)
            filters.append(
                (Sighting.state.is_(None)) | (func.length(Sighting.state) != 2)
            )
        else:
            # Show specific state
            filters.append(Sighting.state == state.upper())
    
    if city:
        filters.append(Sighting.city.ilike(f"%{city}%"))
    
    if shape:
        filters.append(Sighting.shape.ilike(f"%{shape}%"))
    
    if date_from:
        filters.append(Sighting.date_time >= date_from)
    
    if date_to:
        filters.append(Sighting.date_time <= date_to)
    
    # Apply viewport bounds filtering if provided
    if bounds:
        try:
            south, west, north, east = map(float, bounds.split(','))
            filters.extend([
                Sighting.latitude >= south,
                Sighting.latitude <= north,
                Sighting.longitude >= west,
                Sighting.longitude <= east
            ])
        except (ValueError, TypeError):
            # Invalid bounds format, ignore
            pass
    
    if filters:
        query = query.where(and_(*filters))
    
    # For map visualization, we want a good time distribution
    # Remove strict date ordering to get a better sample across all time periods
    
    # Apply smart limiting based on zoom level and request
    if zoom_level:
        limit = min(15000, max(100, zoom_level * 200))
        query = query.limit(limit)
    else:
        # Allow larger datasets for map visualization, but still reasonable limit
        query = query.limit(15000)  # Increased from 5000 to show more data
    
    # Execute query
    result = await db.execute(query)
    sightings = result.scalars().all()
    
    if format == "geojson":
        return create_geojson_response(sightings)
    else:
        return create_simple_response(sightings)


@router.get(
    "/hotspots",
    summary="Get sighting hotspots",
    description="Retrieve aggregated statistics for geographic hotspots.",
)
async def get_hotspots(
    # Filtering parameters
    state: Optional[str] = Query(None, description="Filter by state"),
    shape: Optional[str] = Query(None, description="Filter by object shape"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    # Aggregation parameters
    min_sightings: int = Query(5, description="Minimum sightings for hotspot", ge=1),
    limit: int = Query(20, description="Maximum hotspots to return", ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get geographic hotspots with sighting aggregations."""
    
    # Build query for hotspot analysis
    query = select(
        Sighting.city,
        Sighting.state,
        func.avg(Sighting.latitude).label('avg_lat'),
        func.avg(Sighting.longitude).label('avg_lng'),
        func.count(Sighting.id).label('sighting_count'),
        func.min(Sighting.date_time).label('earliest_sighting'),
        func.max(Sighting.date_time).label('latest_sighting')
    ).where(
        Sighting.latitude.isnot(None),
        Sighting.longitude.isnot(None)
    )
    
    # Apply filters
    filters = []
    
    if state:
        if state.upper() == "US":
            # Show only US states (2-letter codes)
            filters.append(Sighting.state.isnot(None))
            filters.append(func.length(Sighting.state) == 2)
        elif state.upper() == "INTERNATIONAL":
            # Show only international sightings (non-US or null states)
            filters.append(
                (Sighting.state.is_(None)) | (func.length(Sighting.state) != 2)
            )
        else:
            # Show specific state
            filters.append(Sighting.state == state.upper())
    
    if shape:
        filters.append(Sighting.shape.ilike(f"%{shape}%"))
    
    if date_from:
        filters.append(Sighting.date_time >= date_from)
    
    if date_to:
        filters.append(Sighting.date_time <= date_to)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Group by location
    query = query.group_by(Sighting.city, Sighting.state)
    
    # Filter by minimum sightings
    query = query.having(func.count(Sighting.id) >= min_sightings)
    
    # Order by sighting count (descending)
    query = query.order_by(func.count(Sighting.id).desc())
    
    # Apply limit
    query = query.limit(limit)
    
    # Execute query
    result = await db.execute(query)
    hotspots = result.all()
    
    # Format response
    hotspot_data = []
    for hotspot in hotspots:
        hotspot_data.append({
            "city": hotspot.city,
            "state": hotspot.state,
            "latitude": float(hotspot.avg_lat),
            "longitude": float(hotspot.avg_lng),
            "sighting_count": hotspot.sighting_count,
            "earliest_sighting": hotspot.earliest_sighting.isoformat(),
            "latest_sighting": hotspot.latest_sighting.isoformat(),
            "location": f"{hotspot.city}, {hotspot.state}"
        })
    
    return {
        "hotspots": hotspot_data,
        "total_hotspots": len(hotspot_data),
        "min_sightings_filter": min_sightings
    }


@router.get(
    "/stats",
    summary="Get map statistics",
    description="Get overall statistics for map visualization.",
)
async def get_map_stats(
    state: Optional[str] = Query(None, description="Filter by state"),
    shape: Optional[str] = Query(None, description="Filter by object shape"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics for the current map view."""
    
    # Build base query
    base_query = select(Sighting).where(
        Sighting.latitude.isnot(None),
        Sighting.longitude.isnot(None)
    )
    
    # Apply filters
    filters = []
    
    if state:
        if state.upper() == "US":
            # Show only US states (2-letter codes)
            filters.append(Sighting.state.isnot(None))
            filters.append(func.length(Sighting.state) == 2)
        elif state.upper() == "INTERNATIONAL":
            # Show only international sightings (non-US or null states)
            filters.append(
                (Sighting.state.is_(None)) | (func.length(Sighting.state) != 2)
            )
        else:
            # Show specific state
            filters.append(Sighting.state == state.upper())
    
    if shape:
        filters.append(Sighting.shape.ilike(f"%{shape}%"))
    
    if date_from:
        filters.append(Sighting.date_time >= date_from)
    
    if date_to:
        filters.append(Sighting.date_time <= date_to)
    
    if filters:
        base_query = base_query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count(Sighting.id)).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total_sightings = total_result.scalar()
    
    # Get shape distribution
    shape_query = select(
        Sighting.shape,
        func.count(Sighting.id).label('count')
    ).select_from(base_query.subquery()).group_by(Sighting.shape).order_by(func.count(Sighting.id).desc())
    
    shape_result = await db.execute(shape_query)
    shape_stats = [{"shape": row.shape, "count": row.count} for row in shape_result]
    
    # Get date range
    date_query = select(
        func.min(Sighting.date_time).label('earliest'),
        func.max(Sighting.date_time).label('latest')
    ).select_from(base_query.subquery())
    
    date_result = await db.execute(date_query)
    date_range = date_result.first()
    
    return {
        "total_sightings": total_sightings,
        "shape_distribution": shape_stats,
        "date_range": {
            "earliest": date_range.earliest.isoformat() if date_range.earliest else None,
            "latest": date_range.latest.isoformat() if date_range.latest else None
        }
    }


def create_geojson_response(sightings: List[Sighting]) -> Dict[str, Any]:
    """Create a GeoJSON FeatureCollection from sightings."""
    features = []
    
    for sighting in sightings:
        if not (sighting.latitude and sighting.longitude):
            continue
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(sighting.longitude), float(sighting.latitude)]
            },
            "properties": {
                "id": sighting.id,
                "city": sighting.city,
                "state": sighting.state,
                "shape": sighting.shape,
                "date_time": sighting.date_time.isoformat(),
                "duration": sighting.duration,
                "summary": sighting.summary,
                "posted": sighting.posted.isoformat()
            }
        }
        features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "total_features": len(features),
            "generated_at": datetime.utcnow().isoformat()
        }
    }


def create_simple_response(sightings: List[Sighting]) -> Dict[str, Any]:
    """Create a simple JSON response from sightings."""
    sighting_data = []
    
    for sighting in sightings:
        if not (sighting.latitude and sighting.longitude):
            continue
            
        sighting_data.append({
            "id": sighting.id,
            "latitude": float(sighting.latitude),
            "longitude": float(sighting.longitude),
            "city": sighting.city,
            "state": sighting.state,
            "shape": sighting.shape,
            "date_time": sighting.date_time.isoformat(),
            "duration": sighting.duration,
            "summary": sighting.summary
        })
    
    return {
        "sightings": sighting_data,
        "total": len(sighting_data),
        "generated_at": datetime.utcnow().isoformat()
    }