"""
Main FastAPI application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.core.database import supabase
from app.api.v1 import test_router, projects_router, layers_router, projects_supabase_router, projects_mock_router, auth
import uvicorn

# Create FastAPI instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    description="ScapeGIS Backend API for GIS data management and processing"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(test_router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(layers_router, prefix="/api/v1")
app.include_router(projects_supabase_router, prefix="/api/v1")
app.include_router(projects_mock_router, prefix="/api/v1")

# Add trusted host middleware for production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.yourdomain.com", "yourdomain.com"]
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "not configured"

    if supabase:
        try:
            # Test simple query
            supabase.table("projects").select("count").execute()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)[:50]}..."

    return {
        "status": "healthy",
        "database": db_status,
        "supabase_configured": supabase is not None,
        "version": settings.APP_VERSION
    }


@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint for API v1"""
    return {"message": "API v1 is working!"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
