"""Authentication and user management endpoints."""

from datetime import datetime, timedelta, UTC
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from api.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_api_key,
    hash_api_key,
    get_quota_limit_for_tier,
    calculate_quota_reset_date,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from api.database import get_db_session
from api.dependencies import CurrentUser, CurrentApiKey, CurrentUserFromApiKey
from api.models import User, ApiKey, Usage
from api.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyCreateResponse,
    Token,
    UsageStats,
    UsageRecord,
    ErrorResponse
)

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user account."""
    async with get_db_session() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC)
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        return new_user


@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return access token."""
    async with get_db_session() as session:
        # Find user by email
        result = await session.execute(
            select(User).where(User.email == user_credentials.email, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    """Get current user information."""
    return current_user


@router.get("/keys", response_model=List[ApiKeyResponse])
async def list_api_keys(current_user: CurrentUser):
    """List all active API keys for the current user."""
    async with get_db_session() as session:
        result = await session.execute(
            select(ApiKey)
            .where(ApiKey.user_id == current_user.id, ApiKey.is_active == True)
            .order_by(desc(ApiKey.created_at))
        )
        api_keys = result.scalars().all()
        
        return api_keys


@router.post("/keys", response_model=ApiKeyCreateResponse)
async def create_api_key(key_data: ApiKeyCreate, current_user: CurrentUser):
    """Create a new API key for the current user."""
    async with get_db_session() as session:
        # Check if user already has maximum number of keys (optional limit)
        result = await session.execute(
            select(func.count(ApiKey.id))
            .where(ApiKey.user_id == current_user.id, ApiKey.is_active == True)
        )
        active_key_count = result.scalar()
        
        if active_key_count >= 10:  # Limit to 10 active keys per user
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of API keys reached (10)"
            )
        
        # Generate new API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Create API key record
        new_api_key = ApiKey(
            key_hash=key_hash,
            name=key_data.name,
            tier=key_data.tier,
            quota_limit=get_quota_limit_for_tier(key_data.tier),
            quota_used=0,
            quota_reset_date=calculate_quota_reset_date(),
            user_id=current_user.id,
            created_at=datetime.now(UTC)
        )
        
        session.add(new_api_key)
        await session.commit()
        await session.refresh(new_api_key)
        
        return {
            "api_key": api_key,
            "key_info": new_api_key
        }


@router.post("/keys/{key_id}/regenerate", response_model=ApiKeyCreateResponse)
async def regenerate_api_key(key_id: int, current_user: CurrentUser):
    """Regenerate an API key, returning the new key value."""
    async with get_db_session() as session:
        # Find the API key
        result = await session.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == current_user.id,
                ApiKey.is_active == True
            )
        )
        api_key_record = result.scalar_one_or_none()
        
        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Generate new API key
        new_api_key = generate_api_key()
        new_key_hash = hash_api_key(new_api_key)
        
        # Update the existing record with new hash
        api_key_record.key_hash = new_key_hash
        api_key_record.last_used = None  # Reset last used
        
        await session.commit()
        await session.refresh(api_key_record)
        
        return {
            "api_key": new_api_key,
            "key_info": api_key_record
        }


@router.delete("/keys/{key_id}")
async def deactivate_api_key(key_id: int, current_user: CurrentUser):
    """Deactivate an API key."""
    async with get_db_session() as session:
        # Find the API key
        result = await session.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == current_user.id
            )
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Deactivate the key
        api_key.is_active = False
        await session.commit()
        
        return {"message": "API key deactivated successfully"}


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(current_user: CurrentUserFromApiKey, current_api_key: CurrentApiKey):
    """Get usage statistics for the current API key."""
    async with get_db_session() as session:
        # Get total requests for this API key
        total_requests_result = await session.execute(
            select(func.count(Usage.id)).where(Usage.api_key_id == current_api_key.id)
        )
        total_requests = total_requests_result.scalar() or 0
        
        # Get requests this month
        month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_requests_result = await session.execute(
            select(func.count(Usage.id)).where(
                Usage.api_key_id == current_api_key.id,
                Usage.timestamp >= month_start
            )
        )
        requests_this_month = month_requests_result.scalar() or 0
        
        # Get most used endpoints
        endpoints_result = await session.execute(
            select(Usage.endpoint, func.count(Usage.id).label('count'))
            .where(Usage.api_key_id == current_api_key.id)
            .group_by(Usage.endpoint)
            .order_by(desc('count'))
            .limit(5)
        )
        most_used_endpoints = [
            {"endpoint": row.endpoint, "count": row.count}
            for row in endpoints_result
        ]
        
        return {
            "total_requests": total_requests,
            "requests_this_month": requests_this_month,
            "quota_limit": current_api_key.quota_limit,
            "quota_used": current_api_key.quota_used,
            "quota_remaining": max(0, current_api_key.quota_limit - current_api_key.quota_used),
            "quota_reset_date": current_api_key.quota_reset_date,
            "most_used_endpoints": most_used_endpoints
        }


@router.get("/usage/history", response_model=List[UsageRecord])
async def get_usage_history(
    current_user: CurrentUserFromApiKey,
    current_api_key: CurrentApiKey,
    limit: int = 100
):
    """Get recent usage history for the current API key."""
    async with get_db_session() as session:
        result = await session.execute(
            select(Usage)
            .where(Usage.api_key_id == current_api_key.id)
            .order_by(desc(Usage.timestamp))
            .limit(min(limit, 1000))  # Cap at 1000 records
        )
        usage_records = result.scalars().all()
        
        return usage_records