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
    
    client = AsyncIOMotorClient(mongodb_url)
    database = client[DATABASE_NAME]
    
    # Test the connection
    try:
        await client.admin.command('ping')
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

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