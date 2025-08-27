"""
PostgreSQL database configuration as fallback for MongoDB issues
"""
import os
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import logging

logger = logging.getLogger(__name__)

# PostgreSQL configuration
POSTGRES_URL = os.getenv("DATABASE_URL", "")  # Render provides this automatically
POSTGRES_DATABASE_NAME = os.getenv("POSTGRES_DATABASE_NAME", "gps_streamer")

engine = None
AsyncSessionLocal = None
postgres_available = False

async def init_postgresql():
    """Initialize PostgreSQL connection as fallback"""
    global engine, AsyncSessionLocal, postgres_available
    
    if not POSTGRES_URL:
        logger.info("No PostgreSQL URL provided, skipping PostgreSQL initialization")
        return False
    
    try:
        # Convert postgres:// to postgresql+asyncpg:// if needed
        postgres_url = POSTGRES_URL
        if postgres_url.startswith('postgres://'):
            postgres_url = postgres_url.replace('postgres://', 'postgresql+asyncpg://', 1)
        elif not postgres_url.startswith('postgresql+asyncpg://'):
            postgres_url = f'postgresql+asyncpg://{postgres_url}'
        
        engine = create_async_engine(
            postgres_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20
        )
        
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Test the connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        logger.info("Connected to PostgreSQL successfully!")
        postgres_available = True
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        postgres_available = False
        return False

async def get_postgres_db() -> AsyncSession:
    """Get PostgreSQL database session"""
    if not postgres_available:
        raise Exception("PostgreSQL is not available")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_postgresql():
    """Close PostgreSQL connection"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("PostgreSQL connection closed")