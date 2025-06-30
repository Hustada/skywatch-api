from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SightingResponse(BaseModel):
    """Response model for individual UFO sighting."""

    id: int
    date_time: datetime = Field(..., description="Date and time of the sighting")
    city: str = Field(..., description="City where sighting occurred")
    state: Optional[str] = Field(None, description="State/province code (US states or international)")
    shape: str = Field(..., description="Shape of the observed object")
    duration: str = Field(..., description="Duration of the sighting")
    summary: str = Field(..., description="Brief summary of the sighting")
    text: str = Field(..., description="Detailed description of the sighting")
    posted: datetime = Field(..., description="Date when report was posted")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Records per page")
    pages: int = Field(..., description="Total number of pages")


class SightingListResponse(BaseModel):
    """Response model for paginated list of sightings."""

    sightings: List[SightingResponse] = Field(..., description="List of UFO sightings")
    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Records per page")
    pages: int = Field(..., description="Total number of pages")


class SightingFilters(BaseModel):
    """Query parameters for filtering sightings."""

    state: Optional[str] = Field(None, description="Filter by state/province code")
    city: Optional[str] = Field(None, description="Filter by city name")
    shape: Optional[str] = Field(None, description="Filter by object shape")
    date_from: Optional[datetime] = Field(
        None, description="Filter sightings from this date"
    )
    date_to: Optional[datetime] = Field(
        None, description="Filter sightings to this date"
    )
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(25, ge=1, le=100, description="Records per page")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message")
