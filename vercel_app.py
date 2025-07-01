"""
Vercel-specific entry point for the FastAPI application.
This ensures the entire app runs as a single serverless function.
"""

from api.main import app

# Export the FastAPI app for Vercel
# This will be the single entry point for all routes
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)