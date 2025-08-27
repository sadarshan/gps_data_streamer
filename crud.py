from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo import DESCENDING, ASCENDING

from models import GPSDataCreate, GPSDataDocument, GPSDataResponse, SystemStatsDocument, SystemStatsResponse

async def create_gps_data(db: AsyncIOMotorDatabase, gps_data: GPSDataCreate) -> GPSDataResponse:
    # Create GPS data document
    gps_doc = GPSDataDocument(
        device_id=gps_data.device_id,
        latitude=gps_data.latitude,
        longitude=gps_data.longitude,
        altitude=gps_data.altitude,
        speed=gps_data.speed,
        heading=gps_data.heading,
        accuracy=gps_data.accuracy,
        timestamp=gps_data.timestamp,
        additional_data=gps_data.additional_data
    )
    
    # Insert into MongoDB
    result = await db.gps_data.insert_one(gps_doc.dict())
    
    # Return the created document
    created_doc = await db.gps_data.find_one({"_id": result.inserted_id})
    return GPSDataResponse(**created_doc)

async def get_gps_data_filtered(
    db: AsyncIOMotorDatabase,
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[GPSDataResponse]:
    # Build query filter
    query_filter = {}
    
    if device_id:
        query_filter["device_id"] = device_id
    if start_time:
        query_filter["timestamp"] = query_filter.get("timestamp", {})
        query_filter["timestamp"]["$gte"] = start_time
    if end_time:
        query_filter["timestamp"] = query_filter.get("timestamp", {})
        query_filter["timestamp"]["$lte"] = end_time
    
    # Query with sorting, skip, and limit
    cursor = db.gps_data.find(query_filter).sort("timestamp", DESCENDING).skip(offset).limit(limit)
    
    # Convert to response models
    results = []
    async for doc in cursor:
        results.append(GPSDataResponse(**doc))
    
    return results

async def get_gps_data_count(db: AsyncIOMotorDatabase) -> int:
    return await db.gps_data.count_documents({})

async def get_oldest_gps_data(db: AsyncIOMotorDatabase, limit: int) -> List[GPSDataResponse]:
    cursor = db.gps_data.find({}).sort("timestamp", ASCENDING).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(GPSDataResponse(**doc))
    
    return results

async def delete_oldest_records(db: AsyncIOMotorDatabase, percentage: float) -> int:
    # Get total count
    total_count = await get_gps_data_count(db)
    delete_count = int(total_count * percentage / 100)
    
    if delete_count == 0:
        return 0
    
    # Get IDs of oldest records
    cursor = db.gps_data.find({}, {"_id": 1}).sort("timestamp", ASCENDING).limit(delete_count)
    ids_to_delete = [doc["_id"] async for doc in cursor]
    
    # Delete the records
    if ids_to_delete:
        result = await db.gps_data.delete_many({"_id": {"$in": ids_to_delete}})
        return result.deleted_count
    
    return 0

async def get_all_gps_data_for_export(db: AsyncIOMotorDatabase) -> List[GPSDataResponse]:
    cursor = db.gps_data.find({}).sort("timestamp", ASCENDING)
    
    results = []
    async for doc in cursor:
        results.append(GPSDataResponse(**doc))
    
    return results

async def create_system_stats(
    db: AsyncIOMotorDatabase,
    total_gps_records: int,
    database_size_bytes: int,
    database_usage_percentage: float,
    post_requests_last_minute: Optional[int] = None,
    average_posts_per_minute: Optional[float] = None
) -> SystemStatsResponse:
    # Create system stats document
    stats_doc = SystemStatsDocument(
        total_gps_records=total_gps_records,
        database_size_bytes=database_size_bytes,
        database_usage_percentage=database_usage_percentage,
        post_requests_last_minute=post_requests_last_minute,
        average_posts_per_minute=average_posts_per_minute
    )
    
    # Insert into MongoDB
    result = await db.system_stats.insert_one(stats_doc.dict())
    
    # Return the created document
    created_doc = await db.system_stats.find_one({"_id": result.inserted_id})
    return SystemStatsResponse(**created_doc)

async def get_latest_system_stats(db: AsyncIOMotorDatabase) -> Optional[SystemStatsResponse]:
    doc = await db.system_stats.find_one({}, sort=[("timestamp", DESCENDING)])
    
    if doc:
        return SystemStatsResponse(**doc)
    return None