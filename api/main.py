from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
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
    title="SkyWatch API",
    description="API for querying UFO sighting reports sourced from the National UFO Reporting Center (NUFORC) database",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Custom docs endpoint with Stripe-inspired design
@app.get("/docs", include_in_schema=False)
async def custom_docs(request: Request):
    return templates.TemplateResponse("docs.html", {"request": request})

# Keep Swagger UI available at /swagger for development
@app.get("/swagger", include_in_schema=False)
async def swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_css_url="/static/custom-swagger.css",
    )


# Include routers
app.include_router(health.router)
app.include_router(sightings.router)
