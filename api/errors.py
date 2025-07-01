"""Centralized error handling and custom exceptions."""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime, UTC
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detailed error information."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: str
    timestamp: str
    path: Optional[str] = None
    method: Optional[str] = None


class APIException(Exception):
    """Base exception for API errors."""
    def __init__(
        self,
        error: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationError(APIException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error="authentication_error",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(APIException):
    """Raised when authorization fails."""
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error="authorization_error",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class NotFoundError(APIException):
    """Raised when a resource is not found."""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            error="not_found",
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)}
        )


class RateLimitError(APIException):
    """Raised when rate limit is exceeded."""
    def __init__(self, limit: int, reset_time: datetime):
        super().__init__(
            error="rate_limit_exceeded",
            message="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={
                "limit": limit,
                "reset_time": reset_time.isoformat()
            }
        )


class QuotaExceededError(APIException):
    """Raised when quota is exceeded."""
    def __init__(self, quota_limit: int, quota_used: int, reset_date: datetime):
        super().__init__(
            error="quota_exceeded",
            message="Monthly quota exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={
                "quota_limit": quota_limit,
                "quota_used": quota_used,
                "reset_date": reset_date.isoformat()
            }
        )


class ValidationError(APIException):
    """Raised when input validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error="validation_error",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


def create_error_response(
    request: Request,
    error: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response."""
    error_detail = ErrorDetail(
        error=error,
        message=message,
        details=details,
        request_id=str(uuid.uuid4()),
        timestamp=datetime.now(UTC).isoformat(),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_detail.model_dump(exclude_none=True)
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions."""
    return create_error_response(
        request=request,
        error=exc.error,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    error_mapping = {
        400: "bad_request",
        401: "authentication_error",
        403: "authorization_error",
        404: "not_found",
        405: "method_not_allowed",
        429: "rate_limit_exceeded",
        500: "internal_server_error",
        503: "service_unavailable"
    }
    
    error_type = error_mapping.get(exc.status_code, "http_error")
    
    return create_error_response(
        request=request,
        error=error_type,
        message=exc.detail or "An error occurred",
        status_code=exc.status_code,
        details={"status_code": exc.status_code}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        request=request,
        error="validation_error",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    # In production, you'd want to log this properly
    print(f"Unexpected error: {type(exc).__name__}: {str(exc)}")
    
    return create_error_response(
        request=request,
        error="internal_server_error",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"type": type(exc).__name__} if request.app.debug else None
    )