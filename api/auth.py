"""Authentication utilities for API key management and JWT tokens."""

import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

from api.config import settings

# Configuration from environment
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    # Generate 32 random bytes and encode as hex
    random_bytes = secrets.token_bytes(32)
    return f"sk_live_{random_bytes.hex()}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage using bcrypt."""
    # Use bcrypt for better security against brute force attacks
    # Note: We use a lower cost factor (10) for API keys to balance security and performance
    return bcrypt.hash(api_key, rounds=10)


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its bcrypt hash."""
    try:
        return bcrypt.verify(api_key, hashed_key)
    except Exception:
        # Handle invalid hash format
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_quota_limit_for_tier(tier: str) -> int:
    """Get the monthly quota limit for a given tier."""
    tier_limits = {
        "free": 1000,
        "basic": 10000,
        "pro": 100000,
        "enterprise": 1000000,  # Default for enterprise, can be customized
    }
    return tier_limits.get(tier, 1000)  # Default to free tier


def get_rate_limit_for_tier(tier: str) -> int:
    """Get the hourly rate limit for a given tier."""
    tier_limits = {
        "free": 60,      # 60 requests per hour
        "basic": 300,    # 300 requests per hour
        "pro": 1000,     # 1000 requests per hour
        "enterprise": 5000,  # 5000 requests per hour
    }
    return tier_limits.get(tier, 60)  # Default to free tier


def calculate_quota_reset_date() -> datetime:
    """Calculate the next quota reset date (first day of next month)."""
    now = datetime.now(UTC)
    # First day of next month
    if now.month == 12:
        return datetime(now.year + 1, 1, 1, tzinfo=UTC)
    else:
        return datetime(now.year, now.month + 1, 1, tzinfo=UTC)


def is_quota_expired(reset_date: datetime) -> bool:
    """Check if the quota period has expired and should be reset."""
    # Ensure both datetimes are timezone-aware
    now = datetime.now(UTC)
    if reset_date.tzinfo is None:
        reset_date = reset_date.replace(tzinfo=UTC)
    return now >= reset_date