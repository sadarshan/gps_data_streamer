from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import AsyncGenerator

DATABASE_URL = os.getenv("MONGODB_URL", "mongodb+srv://darshannitt:<db_password>@cluster0.f9ik0l3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "gps_streamer")

# Alternative connection URLs for different SSL configurations
ALT_DATABASE_URLS = [
    # Try with explicit SSL settings in URL
    "mongodb+srv://darshannitt:<db_password>@cluster0.f9ik0l3.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true&tlsInsecure=true&appName=Cluster0",
    # Try direct MongoDB (not SRV) connection
    "mongodb://darshannitt:<db_password>@ac-fljqn0p-shard-00-00.f9ik0l3.mongodb.net:27017,ac-fljqn0p-shard-00-01.f9ik0l3.mongodb.net:27017,ac-fljqn0p-shard-00-02.f9ik0l3.mongodb.net:27017/?ssl=true&replicaSet=atlas-10jjw3-shard-0&authSource=admin&retryWrites=true&w=majority",
    # Try with minimal SSL
    "mongodb+srv://darshannitt:<db_password>@cluster0.f9ik0l3.mongodb.net/gps_streamer?retryWrites=true&w=majority&appName=Cluster0"
]

client: AsyncIOMotorClient = None
database = None

async def init_db():
    """Initialize MongoDB connection"""
    global client, database
    
    # Replace <db_password> with actual password from environment
    db_password = os.getenv("DB_PASSWORD", "")
    
    # Try different URLs and configurations
    urls_to_try = [DATABASE_URL] + ALT_DATABASE_URLS
    configs_to_try = [
        {"maxPoolSize": 10, "serverSelectionTimeoutMS": 10000, "connectTimeoutMS": 10000},
        {"tlsAllowInvalidCertificates": True, "maxPoolSize": 10, "serverSelectionTimeoutMS": 15000, "connectTimeoutMS": 15000},
        {"maxPoolSize": 5, "serverSelectionTimeoutMS": 20000, "connectTimeoutMS": 20000}
    ]
    
    for url_idx, mongodb_url in enumerate(urls_to_try):
        mongodb_url_final = mongodb_url.replace("<db_password>", db_password)
        
        for config_idx, config in enumerate(configs_to_try):
            method_num = url_idx * len(configs_to_try) + config_idx + 1
            try:
                print(f"Attempting MongoDB connection (method {method_num})...")
                print(f"Using URL approach {url_idx + 1} with config {config_idx + 1}")
                
                client = AsyncIOMotorClient(mongodb_url_final, **config)
                database = client[DATABASE_NAME]
                
                # Test the connection with shorter timeout
                await client.admin.command('ping')
                print(f"Connected to MongoDB successfully using method {method_num}!")
                return
                
            except Exception as e:
                print(f"Connection method {method_num} failed: {e}")
                continue
    
    print("All connection methods failed")
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