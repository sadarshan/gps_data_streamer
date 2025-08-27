from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("MONGODB_URL", "mongodb+srv://darshannitt:<db_password>@cluster0.f9ik0l3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "gps_streamer")

# Alternative connection URLs for different SSL configurations
ALT_DATABASE_URLS = [
    # Try with tlsAllowInvalidCertificates only
    "mongodb+srv://darshannitt:<db_password>@cluster0.f9ik0l3.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true&appName=Cluster0",
    # Try with tlsInsecure only
    "mongodb+srv://darshannitt:<db_password>@cluster0.f9ik0l3.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsInsecure=true&appName=Cluster0",
    # Try direct MongoDB connection with SSL disabled
    "mongodb://darshannitt:<db_password>@ac-fljqn0p-shard-00-00.f9ik0l3.mongodb.net:27017,ac-fljqn0p-shard-00-01.f9ik0l3.mongodb.net:27017,ac-fljqn0p-shard-00-02.f9ik0l3.mongodb.net:27017/gps_streamer?ssl=false&replicaSet=atlas-10jjw3-shard-0&authSource=admin&retryWrites=true&w=majority",
    # Try standard connection without TLS flags
    "mongodb+srv://darshannitt:<db_password>@cluster0.f9ik0l3.mongodb.net/gps_streamer?retryWrites=true&w=majority&appName=Cluster0"
]

client: AsyncIOMotorClient = None
database = None
using_mongodb = False

async def init_db():
    """Initialize database connection (MongoDB with PostgreSQL fallback)"""
    global client, database, using_mongodb
    
    # First try MongoDB
    try:
        await init_mongodb()
        using_mongodb = True
        logger.info("Using MongoDB as primary database")
        return
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}")
        logger.info("Attempting PostgreSQL fallback...")
        
        # Try PostgreSQL fallback
        try:
            from database_postgresql import init_postgresql
            postgres_success = await init_postgresql()
            if postgres_success:
                using_mongodb = False
                logger.info("Using PostgreSQL as fallback database")
                return
        except Exception as postgres_error:
            logger.error(f"PostgreSQL fallback also failed: {postgres_error}")
        
        # If both fail, raise the original MongoDB error
        raise Exception(f"Both MongoDB and PostgreSQL connections failed. MongoDB error: {e}")

async def init_mongodb():
    """Initialize MongoDB connection"""
    global client, database
    
    # Replace <db_password> with actual password from environment
    db_password = os.getenv("DB_PASSWORD", "")
    
    # Try different URLs and configurations
    urls_to_try = [DATABASE_URL] + ALT_DATABASE_URLS
    configs_to_try = [
        {"maxPoolSize": 10, "serverSelectionTimeoutMS": 5000, "connectTimeoutMS": 5000},
        {"tlsAllowInvalidCertificates": True, "maxPoolSize": 10, "serverSelectionTimeoutMS": 8000, "connectTimeoutMS": 8000},
        {"maxPoolSize": 5, "serverSelectionTimeoutMS": 10000, "connectTimeoutMS": 10000}
    ]
    
    for url_idx, mongodb_url in enumerate(urls_to_try):
        mongodb_url_final = mongodb_url.replace("<db_password>", db_password)
        
        for config_idx, config in enumerate(configs_to_try):
            method_num = url_idx * len(configs_to_try) + config_idx + 1
            try:
                logger.info(f"Attempting MongoDB connection (method {method_num})...")
                
                client = AsyncIOMotorClient(mongodb_url_final, **config)
                database = client[DATABASE_NAME]
                
                # Test the connection
                await client.admin.command('ping')
                logger.info(f"Connected to MongoDB successfully using method {method_num}!")
                return
                
            except Exception as e:
                logger.debug(f"Connection method {method_num} failed: {e}")
                continue
    
    raise Exception("Could not establish MongoDB connection with any method")

async def get_db():
    """Get database instance"""
    return database

async def close_db():
    """Close database connection"""
    global client
    if client:
        client.close()

async def get_db_size():
    """Get database size estimation"""
    try:
        stats = await database.command("dbStats")
        return stats.get("dataSize", 0)
    except Exception:
        return 0