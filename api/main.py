from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routers import health

app = FastAPI(
    title="NUFORC UFO Sightings API",
    description="API for querying UFO sighting reports from NUFORC database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(health.router)
