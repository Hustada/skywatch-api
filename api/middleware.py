"""Middleware for API key validation, rate limiting, and usage tracking."""

import time
from collections import defaultdict, deque
from datetime import datetime, UTC
from typing import Dict, Deque

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, update

from api.database import get_db_session
from api.models import ApiKey, Usage
from api.auth import verify_api_key, get_rate_limit_for_tier, is_quota_expired
from api.errors import create_error_response, AuthenticationError, RateLimitError, QuotaExceededError


# In-memory rate limiting storage (in production, use Redis)
class RateLimiter:
    def __init__(self):
        # Store request timestamps per API key
        self.requests: Dict[str, Deque[float]] = defaultdict(lambda: deque())
    
    def is_allowed(self, api_key_hash: str, rate_limit: int) -> bool:
        """Check if request is allowed based on rate limit (requests per hour)."""
        now = time.time()
        hour_ago = now - 3600  # 1 hour ago
        
        # Clean old requests (older than 1 hour)
        requests = self.requests[api_key_hash]
        while requests and requests[0] < hour_ago:
            requests.popleft()
        
        # Check if under rate limit
        if len(requests) >= rate_limit:
            return False
        
        # Add current request
        requests.append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


class APIKeyMiddleware:
    """Middleware to validate API keys and track usage."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip middleware for public endpoints
        if self._is_public_endpoint(request.url.path):
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Extract API key from headers
        api_key = self._extract_api_key(request)
        if not api_key:
            response = create_error_response(
                request=request,
                error="authentication_error",
                message="API key required. Include 'X-API-Key' header or 'Authorization: Bearer <key>' header.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            await response(scope, receive, send)
            return
        
        # Validate API key and get key info
        api_key_info = await self._validate_api_key(api_key)
        if not api_key_info:
            response = create_error_response(
                request=request,
                error="authentication_error",
                message="The provided API key is invalid or has been revoked.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            await response(scope, receive, send)
            return
        
        # Check if key is active
        if not api_key_info.is_active:
            response = create_error_response(
                request=request,
                error="authentication_error",
                message="This API key has been disabled.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            await response(scope, receive, send)
            return
        
        # Check quota (monthly limit)
        if await self._is_quota_exceeded(api_key_info):
            response = create_error_response(
                request=request,
                error="quota_exceeded",
                message=f"Monthly quota of {api_key_info.quota_limit} requests exceeded.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                details={
                    "quota_limit": api_key_info.quota_limit,
                    "quota_used": api_key_info.quota_used,
                    "quota_reset_date": api_key_info.quota_reset_date.isoformat()
                }
            )
            await response(scope, receive, send)
            return
        
        # Check rate limit (hourly limit)
        rate_limit = get_rate_limit_for_tier(api_key_info.tier)
        if not rate_limiter.is_allowed(api_key_info.key_hash, rate_limit):
            response = create_error_response(
                request=request,
                error="rate_limit_exceeded",
                message=f"Rate limit of {rate_limit} requests per hour exceeded.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                details={
                    "rate_limit": rate_limit,
                    "retry_after": 3600  # Retry after 1 hour
                }
            )
            await response(scope, receive, send)
            return
        
        # Add API key info to request scope for use in endpoints
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["api_key"] = api_key_info
        scope["state"]["api_key_id"] = api_key_info.id
        
        # Create a custom send wrapper to capture response details
        response_status = 200
        
        async def custom_send(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
        
        # Process the request
        await self.app(scope, receive, custom_send)
        
        # Record usage
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        await self._record_usage(
            api_key_info.id,
            request.url.path,
            request.method,
            response_status,
            response_time_ms,
            request.headers.get("user-agent"),
            self._get_client_ip(request)
        )
        
        # Update API key usage count and last used timestamp
        await self._update_api_key_usage(api_key_info.id)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (doesn't require API key)."""
        public_endpoints = [
            "/",                  # Landing page
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/swagger",
            "/static",
            "/map",               # Public map page
            "/v1/map",            # Public map API endpoints
            "/v1/auth/register",  # Public registration
            "/v1/auth/login",     # Public login
            "/v1/auth/me",        # JWT token auth (web UI)
            "/v1/auth/keys",      # JWT token auth (web UI)
            "/v1/research",       # Public research endpoints
        ]
        
        for public_path in public_endpoints:
            if path.startswith(public_path):
                return True
        return False
    
    def _extract_api_key(self, request: Request) -> str | None:
        """Extract API key from request headers."""
        # Try X-API-Key header first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        # Try Authorization header (Bearer token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        return None
    
    async def _validate_api_key(self, api_key: str) -> ApiKey | None:
        """Validate API key and return key info if valid."""
        async with get_db_session() as session:
            # Get all active API keys and check hashes
            result = await session.execute(
                select(ApiKey).where(ApiKey.is_active == True)
            )
            api_keys = result.scalars().all()
            
            for key_info in api_keys:
                if verify_api_key(api_key, key_info.key_hash):
                    return key_info
            
            return None
    
    async def _is_quota_exceeded(self, api_key_info: ApiKey) -> bool:
        """Check if API key has exceeded its monthly quota."""
        # Check if quota period has expired and reset if needed
        if is_quota_expired(api_key_info.quota_reset_date):
            await self._reset_quota(api_key_info.id)
            return False  # Quota was reset, so not exceeded
        
        return api_key_info.quota_used >= api_key_info.quota_limit
    
    async def _reset_quota(self, api_key_id: int):
        """Reset the quota for an API key."""
        from api.auth import calculate_quota_reset_date
        
        async with get_db_session() as session:
            await session.execute(
                update(ApiKey)
                .where(ApiKey.id == api_key_id)
                .values(
                    quota_used=0,
                    quota_reset_date=calculate_quota_reset_date()
                )
            )
            await session.commit()
    
    async def _record_usage(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        user_agent: str | None,
        ip_address: str | None
    ):
        """Record API usage for analytics and billing."""
        async with get_db_session() as session:
            usage = Usage(
                api_key_id=api_key_id,
                endpoint=endpoint,
                method=method,
                response_status=status_code,
                response_time_ms=response_time_ms,
                user_agent=user_agent,
                ip_address=ip_address,
                timestamp=datetime.now(UTC)
            )
            session.add(usage)
            await session.commit()
    
    async def _update_api_key_usage(self, api_key_id: int):
        """Update API key usage count and last used timestamp."""
        async with get_db_session() as session:
            await session.execute(
                update(ApiKey)
                .where(ApiKey.id == api_key_id)
                .values(
                    quota_used=ApiKey.quota_used + 1,
                    last_used=datetime.now(UTC)
                )
            )
            await session.commit()
    
    def _get_client_ip(self, request: Request) -> str | None:
        """Extract client IP address from request."""
        # Check for forwarded headers first (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None