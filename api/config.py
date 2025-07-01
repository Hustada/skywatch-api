"""Configuration management using environment variables."""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Settings:
    """Application settings loaded from environment variables."""
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sightings.db")
    
    # API Settings
    API_TITLE: str = "SkyWatch API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Track UFO sightings across the globe"
    
    # CORS Settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "3600"))  # 1 hour in seconds
    
    # Redis (for future use)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # AI Research
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    def __init__(self):
        """Validate critical settings on initialization."""
        if self.ENVIRONMENT == "production" and self.JWT_SECRET_KEY == "your-secret-key-here":
            raise ValueError(
                "JWT_SECRET_KEY must be set to a secure value in production! "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()