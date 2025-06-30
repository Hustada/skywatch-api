from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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

    def __repr__(self) -> str:
        return (
            f"<Sighting(id={self.id}, city={self.city}, state={self.state}, "
            f"shape={self.shape}, date={self.date_time})>"
        )
