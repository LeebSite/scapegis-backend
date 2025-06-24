"""
Database configuration and connection management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from geoalchemy2 import Geometry  # Will be enabled after GDAL installation
from supabase import create_client, Client
from app.core.config import settings

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Only create engines if DATABASE_URL is configured and valid
async_engine = None
sync_engine = None

if SQLALCHEMY_DATABASE_URL and "your-password" not in SQLALCHEMY_DATABASE_URL:
    try:
        # Async engine for async operations
        async_engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.DEBUG
        )

        # Sync engine for migrations and sync operations
        sync_engine = create_engine(
            SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"),
            echo=settings.DEBUG
        )
    except Exception as e:
        print(f"Warning: Could not create database engines: {e}")
        async_engine = None
        sync_engine = None

# Session makers (only if engines are available)
AsyncSessionLocal = None
SessionLocal = None

if async_engine:
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

if sync_engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Base class for models
Base = declarative_base()

# Supabase client (only if configured)
supabase: Client = None
supabase_admin: Client = None

if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
    supabase = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )

if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
    supabase_admin = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )


# Dependency to get async database session
async def get_async_db():
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Dependency to get sync database session
def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Optional dependency to get sync database session (returns None if not configured)
def get_db_optional():
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency to get Supabase client
def get_supabase() -> Client:
    return supabase


# Dependency to get Supabase admin client
def get_supabase_admin() -> Client:
    return supabase_admin


# Import models to ensure they are registered with SQLAlchemy
from app.models import Project, Layer, UserProfile
