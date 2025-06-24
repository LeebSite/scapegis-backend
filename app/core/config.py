"""
Configuration settings for ScapeGIS Backend
"""
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "ScapeGIS Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = "https://fgpyqyiazgouorgpkavr.supabase.co"
    SUPABASE_ANON_KEY: Optional[str] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZncHlxeWlhemdvdW9yZ3BrYXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTY4NDgsImV4cCI6MjA2NjI3Mjg0OH0.mi6eHu3jJ9K2RXBz71IKCDNBGs9bnDPBf2a8-IcuvYI"
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Database Configuration (Supabase PostgreSQL)
    DATABASE_URL: Optional[str] = None  # Will be set via environment variable
    DATABASE_HOST: Optional[str] = "db.fgpyqyiazgouorgpkavr.supabase.co"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "postgres"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: Optional[str] = None  # Will be set via environment variable
    USE_DATABASE: bool = False  # For OAuth testing without database

    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # OAuth Redirect URLs
    GOOGLE_REDIRECT_URI: str = "http://localhost:8001/api/v1/auth/oauth/callback/google"
    GITHUB_REDIRECT_URI: str = "http://localhost:8001/api/v1/auth/oauth/callback/github"

    # Frontend URL for OAuth redirects
    FRONTEND_URL: str = "http://localhost:3001"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # File Upload
    MAX_FILE_SIZE: str = "50MB"
    UPLOAD_PATH: str = "./uploads"

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"]

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True


# Global settings instance
settings = Settings()
