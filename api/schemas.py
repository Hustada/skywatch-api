from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


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


# Authentication schemas

# User schemas
class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user information response."""
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# API Key schemas
class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name for the API key")
    tier: str = Field(default="free", description="Tier level: free, basic, pro, enterprise")


class ApiKeyResponse(BaseModel):
    """Schema for API key information (without the actual key)."""
    id: int
    name: str
    tier: str
    quota_limit: int
    quota_used: int
    quota_reset_date: datetime
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes the actual key)."""
    api_key: str = Field(..., description="The actual API key - store this securely, it won't be shown again")
    key_info: ApiKeyResponse


# Token schemas
class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


# Usage schemas
class UsageStats(BaseModel):
    """Schema for usage statistics."""
    total_requests: int
    requests_this_month: int
    quota_limit: int
    quota_used: int
    quota_remaining: int
    quota_reset_date: datetime
    most_used_endpoints: List[dict]


class UsageRecord(BaseModel):
    """Schema for individual usage record."""
    id: int
    endpoint: str
    method: str
    response_status: int
    response_time_ms: Optional[int]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
