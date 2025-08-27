"""
MongoDB Database Connection - Optimized for Render deployment
Features: Connection pooling, automatic failover, performance optimization
"""
import os
import logging
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

# Global database connection
client: Optional[AsyncMongoClient] = None
database = None

# Environment configuration
DATABASE_NAME = os.getenv("DATABASE_NAME", "gps_streamer")

# Get MongoDB URLs from environment variables
MONGODB_URLS = [
    os.getenv("MONGODB_URL_PRIMARY", ""),
    os.getenv("MONGODB_URL_SSL_BYPASS", ""),
    os.getenv("MONGODB_URL_DIRECT", "")
]

# Filter out empty URLs
MONGODB_URLS = [url for url in MONGODB_URLS if url]

async def init_db():
    """
    Initialize MongoDB connection with optimized settings for high-throughput GPS data
    Features: Connection pooling, automatic failover, performance tuning
    """
    global client, database
    
    if not MONGODB_URLS:
        raise Exception("❌ At least one MongoDB URL environment variable is required (MONGODB_URL_PRIMARY, MONGODB_URL_SSL_BYPASS, or MONGODB_URL_DIRECT)")
    
    logger.info("🔄 Initializing MongoDB connection...")
    
    # Try each connection URL for maximum compatibility
    for attempt, mongodb_url in enumerate(MONGODB_URLS, 1):
        try:
            logger.info(f"📡 Attempting MongoDB connection (method {attempt}/{len(MONGODB_URLS)})")
            # print(mongodb_url)
            # Create client with optimized settings for GPS data ingestion
            client = AsyncMongoClient(
                mongodb_url,
                # serverSelectionTimeoutMS=8000,   # 8 seconds for initial connection
                # connectTimeoutMS=8000,           # 8 seconds for socket connection
                # socketTimeoutMS=30000,           # 30 seconds for individual operations
                
                # Connection pooling for high-throughput
                # maxPoolSize=20,                  # Maximum connections in pool
                # minPoolSize=5,                   # Minimum connections to maintain
                # maxIdleTimeMS=45000,             # Close idle connections after 45s
                
                # Monitoring and reliability
                # heartbeatFrequencyMS=10000,      # Check server health every 10s
                # retryWrites=True,                # Automatic retry on write failures
            )
            # print(client.address)
            database = client[DATABASE_NAME]
            
            # Test connection with ping
            await asyncio.wait_for(client.admin.command('ping'), timeout=10.0)
            
            # Create database indexes for GPS data optimization
            await create_indexes()
            
            logger.info(f"✅ MongoDB connected successfully (method {attempt})")
            logger.info(f"📊 Database: {DATABASE_NAME}")
            logger.info(f"🏊 Connection pool: {client.options.pool_options.max_pool_size} max connections")
            
            return
            
        except Exception as e:
            logger.warning(f"❌ Connection method {attempt} failed: {e}")
            if client:
                client.close()
                client = None
            
            if attempt == len(MONGODB_URLS):
                logger.error("💥 All MongoDB connection methods failed!")
                raise Exception(f"Cannot connect to MongoDB Atlas. Last error: {e}")
            
            # Brief delay before trying next method
            await asyncio.sleep(1)

async def create_indexes():
    """
    Create optimized database indexes for GPS data performance
    - Geographic queries (lat/lng)
    - Device-based filtering
    - Time-based sorting and range queries  
    - System statistics optimization
    """
    try:
        # GPS data collection indexes
        await database.gps_data.create_index([
            ("device_id", 1),
            ("timestamp", -1)  # Descending for latest-first queries
        ], name="device_timestamp_idx")
        
        await database.gps_data.create_index([
            ("timestamp", -1)  # Primary time-based index
        ], name="timestamp_idx")
        
        await database.gps_data.create_index([
            ("lattitude", 1),  # Note: using your field name 'lattitude'
            ("longitude", 1)   # Geographic queries
        ], name="location_idx")
        
        await database.gps_data.create_index([
            ("created_at", -1)  # For data management and purging
        ], name="created_at_idx")
        
        # System statistics indexes
        await database.system_stats.create_index([
            ("timestamp", -1)   # Latest stats first
        ], name="stats_timestamp_idx")
        
        logger.info("📋 Database indexes created for optimized GPS data queries")
        
    except Exception as e:
        logger.warning(f"⚠️  Index creation failed (non-critical): {e}")

def get_db():
    """Get database instance for operations"""
    if database is None:
        raise Exception("❌ Database not initialized - call init_db() first")
    return database

async def close_db():
    """Clean shutdown of MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("🔐 MongoDB connection closed")

async def get_db_size():
    """
    Get database size for capacity management
    Returns size in bytes for 100MB limit monitoring
    """
    try:
        stats = await database.command("dbStats")
        return stats.get("dataSize", 0)
    except Exception as e:
        logger.error(f"💥 Error getting database size: {e}")
        return 0

async def get_collection_stats():
    """Get detailed collection statistics for monitoring"""
    try:
        # GPS data collection stats
        gps_stats = await database.command("collStats", "gps_data")
        
        # System stats collection  
        sys_stats = await database.command("collStats", "system_stats")
        
        return {
            "gps_data": {
                "count": gps_stats.get("count", 0),
                "size": gps_stats.get("size", 0),
                "avgObjSize": gps_stats.get("avgObjSize", 0),
                "indexSizes": gps_stats.get("indexSizes", {})
            },
            "system_stats": {
                "count": sys_stats.get("count", 0),
                "size": sys_stats.get("size", 0)
            }
        }
    except Exception as e:
        logger.error(f"💥 Error getting collection stats: {e}")
        return {"gps_data": {"count": 0, "size": 0}, "system_stats": {"count": 0, "size": 0}}

async def test_connection():
    """Test database connection health"""
    try:
        await client.admin.command('ping')
        return True
    except Exception:
        return False