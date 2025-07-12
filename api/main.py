from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.routers import health, sightings, auth, map, research
from api.database import create_tables
from api.middleware import APIKeyMiddleware
from api.config import settings
from api.errors import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    try:
        await create_tables()
        print("Database tables created/verified")
        
        # In production with in-memory database, add some demo data
        if settings.ENVIRONMENT == "production":
            print("Production mode: Using in-memory database with minimal demo data")
            
    except Exception as e:
        print(f"Database initialization warning: {e}")
        # Continue startup even if database setup fails
    
    yield
    # Shutdown
    print("Application shutdown")


app = FastAPI(
    title=settings.API_TITLE,
    description="API for querying UFO sighting reports sourced from the National UFO Reporting Center (NUFORC) database",
    version=settings.API_VERSION,
    docs_url=None,  # Disable default docs
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add HSTS header for production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

# Add middleware in correct order (from outermost to innermost)
# 1. Security headers (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 3. Trusted Host (prevent host header attacks)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.skywatch.io", "*.skywatch.io"],  # Update with your actual domain
    )

# 4. API key middleware (innermost)
app.add_middleware(APIKeyMiddleware)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Landing page
@app.get("/", include_in_schema=False)
async def landing_page(request: Request):
    """SkyWatch API landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})


# Custom docs endpoint with Stripe-inspired design
@app.get("/docs", include_in_schema=False)
async def custom_docs(request: Request):
    return templates.TemplateResponse("docs.html", {"request": request})


# Interactive map endpoint
@app.get("/map", include_in_schema=False)
async def sightings_map(request: Request):
    """Interactive map showing UFO sightings geographically."""
    return templates.TemplateResponse("map.html", {"request": request})

# Keep Swagger UI available at /swagger for development
@app.get("/swagger", include_in_schema=False)
async def swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_css_url="/static/custom-swagger.css",
    )


# Register exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# Uncomment for production to catch all unhandled exceptions
# app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(sightings.router)
app.include_router(map.router)
app.include_router(research.router)
