"""
Vercel-specific entry point for the FastAPI application.
This ensures the entire app runs as a single serverless function.
"""

# Import the FastAPI app
try:
    from api.main import app
except Exception as e:
    # Create a fallback app if main app fails to load
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="SkyWatch API - Error")
    
    @app.get("/")
    async def error_handler():
        return JSONResponse(
            content={
                "error": "application_startup_failed",
                "message": f"Failed to initialize application: {str(e)}",
                "details": "Check environment variables and database configuration"
            },
            status_code=500
        )
    
    @app.get("/health")
    async def health_check():
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Application failed to start: {str(e)}"
            },
            status_code=500
        )

# This is the ASGI app that Vercel will use
handler = app

# Deployment trigger comment - environment variables configured

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)