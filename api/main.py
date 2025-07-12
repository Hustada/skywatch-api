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
from api.database import create_tables, get_db_session
from api.middleware import APIKeyMiddleware
from api.config import settings
from api.models import Sighting
from datetime import datetime
from api.errors import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)


async def load_demo_data():
    """Load sample UFO sighting data for production demo."""
    demo_sightings = [
        {
            "date_time": datetime(2023, 7, 4, 21, 30),
            "city": "Phoenix", "state": "AZ", "shape": "triangle",
            "duration": "5 minutes", "summary": "Large triangular craft with bright lights",
            "text": "Witnessed a large triangular craft with three bright lights at each corner moving silently across the night sky.",
            "posted": datetime(2023, 7, 5), "latitude": 33.4484, "longitude": -112.0740,
            "source": "nuforc"
        },
        {
            "date_time": datetime(2023, 8, 15, 22, 45),
            "city": "Los Angeles", "state": "CA", "shape": "disk",
            "duration": "2 minutes", "summary": "Metallic disk hovering above highway",
            "text": "A metallic disk-shaped object was observed hovering motionless above the 405 freeway before accelerating rapidly.",
            "posted": datetime(2023, 8, 16), "latitude": 34.0522, "longitude": -118.2437,
            "source": "ufo_aficionado"
        },
        {
            "date_time": datetime(2023, 9, 22, 20, 15),
            "city": "Chicago", "state": "IL", "shape": "light",
            "duration": "10 minutes", "summary": "Pulsating orange lights in formation",
            "text": "Multiple orange lights pulsating in a V-formation moved slowly across Lake Michigan.",
            "posted": datetime(2023, 9, 23), "latitude": 41.8781, "longitude": -87.6298,
            "source": "nuforc"
        }
    ]
    
    try:
        async with get_db_session() as session:
            for sighting_data in demo_sightings:
                sighting = Sighting(**sighting_data)
                session.add(sighting)
            await session.commit()
            print(f"✅ Loaded {len(demo_sightings)} demo sightings")
    except Exception as e:
        print(f"⚠️ Could not load demo data: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    try:
        await create_tables()
        print("Database tables created/verified")
        
        # In production with in-memory database, add some demo data
        if settings.ENVIRONMENT == "production":
            print("Production mode: Using in-memory database with demo data")
            await load_demo_data()
            
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
