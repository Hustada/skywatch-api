"""
Vercel-specific entry point for the FastAPI application.
"""

import os

# Set environment to production for Vercel
os.environ.setdefault("ENVIRONMENT", "production")

# Import the FastAPI app directly
from api.main import app

# Vercel expects the ASGI app to be available as 'app'
# No need for a handler function wrapper

# Deployment trigger comment - environment variables configured

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)