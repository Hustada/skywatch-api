from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routers import health
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
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(health.router)
