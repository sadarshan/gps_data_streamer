from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import AsyncGenerator

DATABASE_URL = os.getenv("MONGODB_URL", "mongodb+srv://darshannitt:<db_password>@cluster0.f9ik0l3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "gps_streamer")

client: AsyncIOMotorClient = None
database = None

async def init_db():
    """Initialize MongoDB connection"""
    global client, database
    
    # Replace <db_password> with actual password from environment
    db_password = os.getenv("DB_PASSWORD", "")
    mongodb_url = DATABASE_URL.replace("<db_password>", db_password)
    
    # Try multiple connection configurations
    connection_configs = [
        {
            # Standard SSL configuration
            "tls": True,
            "retryWrites": True,
            "maxPoolSize": 10,
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 10000,
        },
        {
            # Alternative SSL configuration for problematic environments
            "tls": True,
            "tlsAllowInvalidCertificates": True,
            "retryWrites": True,
            "maxPoolSize": 10,
            "serverSelectionTimeoutMS": 15000,
            "connectTimeoutMS": 15000,
        },
        {
            # Fallback with minimal SSL
            "ssl": True,
            "ssl_cert_reqs": None,
            "retryWrites": True,
            "maxPoolSize": 5,
            "serverSelectionTimeoutMS": 20000,
            "connectTimeoutMS": 20000,
        }
    ]
    
    for i, config in enumerate(connection_configs, 1):
        try:
            print(f"Attempting MongoDB connection (method {i}/3)...")
            client = AsyncIOMotorClient(mongodb_url, **config)
            database = client[DATABASE_NAME]
            
            # Test the connection
            await client.admin.command('ping')
            print(f"Connected to MongoDB successfully using method {i}!")
            return
            
        except Exception as e:
            print(f"Connection method {i} failed: {e}")
            if i == len(connection_configs):
                print("All connection methods failed")
                raise
            else:
                continue

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