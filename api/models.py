from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""

    pass


class Sighting(Base):
    """UFO sighting report model based on NUFORC data structure."""

    __tablename__ = "sightings"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Core sighting information
    date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    shape: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    duration: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    posted: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Geographic coordinates (optional, for enhanced queries)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)

    # Source tracking for multi-source data
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="nuforc", index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Sighting(id={self.id}, city={self.city}, state={self.state}, "
            f"shape={self.shape}, date={self.date_time})>"
        )


class User(Base):
    """User model for API key management."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User information
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status and timestamps
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"


class ApiKey(Base):
    """API key model for authentication and usage tracking."""

    __tablename__ = "api_keys"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Key information
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # User-friendly name
    tier: Mapped[str] = mapped_column(String(20), default="free", nullable=False)  # free, basic, pro, enterprise
    
    # Usage limits and tracking
    quota_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)  # Monthly limit
    quota_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quota_reset_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Status and timestamps
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user: Mapped[User] = relationship("User", back_populates="api_keys")
    usage_records: Mapped[list["Usage"]] = relationship("Usage", back_populates="api_key", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name}, tier={self.tier}, user_id={self.user_id})>"


class Usage(Base):
    """Usage tracking model for API requests."""

    __tablename__ = "usage"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Request information
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)  # GET, POST, etc.
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Client information (optional)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Foreign key to API key
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"), nullable=False)
    
    # Relationships
    api_key: Mapped[ApiKey] = relationship("ApiKey", back_populates="usage_records")

    def __repr__(self) -> str:
        return f"<Usage(id={self.id}, endpoint={self.endpoint}, status={self.response_status}, timestamp={self.timestamp})>"


class ResearchCache(Base):
    """Cache model for storing AI research results to improve performance."""

    __tablename__ = "research_cache"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Sighting reference
    sighting_id: Mapped[int] = mapped_column(ForeignKey("sightings.id"), nullable=False, index=True)
    
    # Research type and results
    research_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'quick' or 'full'
    analysis_result: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of the analysis
    
    # AI model information for cache invalidation
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'gemini-2.0-flash-exp'
    
    # Cache metadata
    cache_hits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Track usage
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    sighting: Mapped["Sighting"] = relationship("Sighting")

    def __repr__(self) -> str:
        return f"<ResearchCache(id={self.id}, sighting_id={self.sighting_id}, type={self.research_type}, hits={self.cache_hits})>"
