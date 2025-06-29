from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from api.routers import health, sightings
from api.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    await create_tables()
    print("Database tables created/verified")
    yield
    # Shutdown
    print("Application shutdown")


app = FastAPI(
    title="NUFORC UFO Sightings API",
    description="API for querying UFO sighting reports from NUFORC database",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Custom docs endpoint with our theme
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_css_url="/static/custom-swagger.css",
    )


# Include routers
app.include_router(health.router)
app.include_router(sightings.router)
