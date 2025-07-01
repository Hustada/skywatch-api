"""FastAPI dependencies for authentication and authorization."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from api.auth import verify_token
from api.database import get_db_session
from api.models import User, ApiKey


# Security scheme for Swagger UI
security = HTTPBearer()


async def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> User:
    """Get current user from JWT token (for authenticated web UI access)."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    async with get_db_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user


async def get_current_api_key(request: Request) -> ApiKey:
    """Get current API key from request (populated by middleware)."""
    # Check if API key is in request scope state
    if not hasattr(request, "scope") or "state" not in request.scope or "api_key" not in request.scope["state"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    
    return request.scope["state"]["api_key"]


async def get_current_user_from_api_key(
    api_key: Annotated[ApiKey, Depends(get_current_api_key)]
) -> User:
    """Get current user from API key."""
    async with get_db_session() as session:
        result = await session.execute(
            select(User).where(User.id == api_key.user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        return user


def require_tier(required_tier: str):
    """Dependency factory to require specific API key tier."""
    async def _require_tier(api_key: Annotated[ApiKey, Depends(get_current_api_key)]) -> ApiKey:
        tier_hierarchy = {
            "free": 0,
            "basic": 1,
            "pro": 2,
            "enterprise": 3,
        }
        
        current_tier_level = tier_hierarchy.get(api_key.tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 3)
        
        if current_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires {required_tier} tier or higher. Current tier: {api_key.tier}",
            )
        
        return api_key
    
    return _require_tier


# Common dependency aliases
CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
CurrentApiKey = Annotated[ApiKey, Depends(get_current_api_key)]
CurrentUserFromApiKey = Annotated[User, Depends(get_current_user_from_api_key)]

# Tier-specific dependencies
RequireBasicTier = Annotated[ApiKey, Depends(require_tier("basic"))]
RequireProTier = Annotated[ApiKey, Depends(require_tier("pro"))]
RequireEnterpriseTier = Annotated[ApiKey, Depends(require_tier("enterprise"))]