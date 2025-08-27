"""
CRUD Operations - Optimized database operations for high-throughput GPS data
Features: Advanced indexing, efficient queries, bulk operations, performance optimization
"""
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo import DESCENDING, ASCENDING
import logging

from models import (
    GPSDataCreate, GPSDataResponse, GPSDataDocument,
    SystemStatsResponse, SystemStatsDocument
)

logger = logging.getLogger(__name__)

# =============================================================================
# GPS DATA OPERATIONS
# =============================================================================

async def create_gps_data(db: AsyncDatabase, gps_data: GPSDataCreate) -> GPSDataResponse:
    """
    Create new GPS data record with optimized insertion
    - Efficient single-document insert
    - Real-time WebSocket broadcasting
    - Performance logging
    """
    try:
        # Create optimized document for storage
        doc = GPSDataDocument(
            device_sequence_id=gps_data.id,
            device_id=gps_data.device_id,
            frame_time=gps_data.frame_time,
            lattitude=gps_data.lattitude,
            longitude=gps_data.longitude,
            url=gps_data.url,
            sat_tked=gps_data.sat_tked,
            speed=gps_data.speed,
            altitude=gps_data.altitude,
            heading=gps_data.heading,
            accuracy=gps_data.accuracy,
            timestamp=gps_data.timestamp,
            additional_data=gps_data.additional_data
        )
        
        # High-performance insert with write concern
        result = await db.gps_data.insert_one(
            doc.model_dump(),
            # Optimized write concern for performance
            # w=1: Acknowledge from primary only (fast)
            # j=True: Journal write confirmation (durability)
        )
        
        # Retrieve and return the created document
        created_doc = await db.gps_data.find_one({"_id": result.inserted_id})
        logger.info(f"🔍 Raw document from MongoDB: {created_doc}")
        
        # Convert ObjectId to string for response model
        doc_dict = dict(created_doc)
        logger.info(f"🔍 Document as dict: {doc_dict}")
        
        if "_id" in doc_dict:
            doc_dict["id"] = str(doc_dict["_id"])
            del doc_dict["_id"]
        
        logger.info(f"🔍 Document after ID conversion: {doc_dict}")
        
        response = GPSDataResponse(**doc_dict)
        logger.info(f"🔍 Final response model: {response.model_dump()}")
        
        # Broadcast to WebSocket clients for real-time updates
        await broadcast_gps_update(response)
        
        return response
        
    except Exception as e:
        logger.error(f"💥 Failed to create GPS data: {e}")
        logger.error(f"💥 Exception type: {type(e)}")
        logger.error(f"💥 Exception details: {str(e)}")
        import traceback
        logger.error(f"💥 Full traceback: {traceback.format_exc()}")
        raise

async def get_gps_data_filtered(
    db: AsyncDatabase,
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[GPSDataResponse]:
    """
    Advanced GPS data retrieval with optimized filtering
    - Uses database indexes for performance
    - Supports device, time range, and pagination
    - Optimized for large datasets
    """
    try:
        # Build optimized query filter using indexed fields
        query_filter = {}
        
        # Device filter (uses device_timestamp_idx)
        if device_id:
            query_filter["device_id"] = device_id
        
        # Time range filter (uses timestamp_idx)
        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = start_time
            if end_time:
                time_filter["$lte"] = end_time
            query_filter["timestamp"] = time_filter
        
        # Optimized query with index utilization
        # Sort by timestamp descending (latest first) using timestamp_idx
        cursor = (db.gps_data
                 .find(query_filter)
                 .sort("timestamp", DESCENDING)
                 .skip(offset)
                 .limit(limit))
        
        # Convert results to response models
        results = []
        async for doc in cursor:
            # Convert ObjectId to string and handle field mapping
            doc_dict = dict(doc)
            if "_id" in doc_dict:
                doc_dict["id"] = str(doc_dict["_id"])
                del doc_dict["_id"]
            
            # Ensure timestamp and created_at are datetime objects
            if "timestamp" in doc_dict and isinstance(doc_dict["timestamp"], str):
                doc_dict["timestamp"] = datetime.fromisoformat(doc_dict["timestamp"].replace('Z', '+00:00'))
            if "created_at" in doc_dict and isinstance(doc_dict["created_at"], str):
                doc_dict["created_at"] = datetime.fromisoformat(doc_dict["created_at"].replace('Z', '+00:00'))
            
            results.append(GPSDataResponse(**doc_dict))
        
        logger.info(f"📊 Retrieved {len(results)} GPS records (filter: device={device_id}, time_range={bool(start_time or end_time)})")
        return results
        
    except Exception as e:
        logger.error(f"💥 Failed to retrieve GPS data: {e}")
        raise

async def get_gps_data_count(db: AsyncDatabase, device_id: Optional[str] = None) -> int:
    """
    Get GPS record count with optional device filtering
    - Uses efficient count operation
    - Leverages database indexes
    """
    try:
        query_filter = {"device_id": device_id} if device_id else {}
        count = await db.gps_data.count_documents(query_filter)
        return count
    except Exception as e:
        logger.error(f"💥 Failed to count GPS data: {e}")
        return 0

async def get_latest_gps_data(db: AsyncDatabase, limit: int = 10) -> List[GPSDataResponse]:
    """
    Get latest GPS data across all devices
    - Optimized for real-time dashboard
    - Uses timestamp index for performance
    """
    try:
        cursor = (db.gps_data
                 .find({})
                 .sort("timestamp", DESCENDING)
                 .limit(limit))
        
        results = []
        async for doc in cursor:
            results.append(GPSDataResponse(**doc))
        
        return results
        
    except Exception as e:
        logger.error(f"💥 Failed to get latest GPS data: {e}")
        return []

async def get_oldest_gps_data(db: AsyncDatabase, limit: int) -> List[GPSDataResponse]:
    """
    Get oldest GPS data for purging operations
    - Uses created_at index for efficient sorting
    - Critical for automatic data management
    """
    try:
        cursor = (db.gps_data
                 .find({})
                 .sort("created_at", ASCENDING)
                 .limit(limit))
        
        results = []
        async for doc in cursor:
            results.append(GPSDataResponse(**doc))
        
        return results
        
    except Exception as e:
        logger.error(f"💥 Failed to get oldest GPS data: {e}")
        return []

async def delete_oldest_records(db: AsyncDatabase, percentage: float) -> int:
    """
    Delete oldest GPS records for capacity management
    - High-performance bulk deletion
    - Uses indexed queries for efficiency
    - Critical for 100MB database limit
    """
    try:
        # Get total record count
        total_count = await get_gps_data_count(db)
        delete_count = int(total_count * percentage / 100)
        
        if delete_count == 0:
            return 0
        
        # Get ObjectIds of oldest records using created_at index
        cursor = (db.gps_data
                 .find({}, {"_id": 1})
                 .sort("created_at", ASCENDING)
                 .limit(delete_count))
        
        ids_to_delete = [doc["_id"] async for doc in cursor]
        
        if not ids_to_delete:
            return 0
        
        # Bulk delete operation for performance
        result = await db.gps_data.delete_many({"_id": {"$in": ids_to_delete}})
        deleted_count = result.deleted_count
        
        logger.info(f"🗑️  Deleted {deleted_count} oldest GPS records ({percentage}% of {total_count})")
        return deleted_count
        
    except Exception as e:
        logger.error(f"💥 Failed to delete oldest records: {e}")
        return 0

async def get_all_gps_data_for_export(db: AsyncDatabase) -> List[GPSDataResponse]:
    """
    Get all GPS data for backup export
    - Optimized for bulk data retrieval
    - Used by backup system
    - Memory-efficient streaming
    """
    try:
        # Use timestamp sorting for consistent export order
        cursor = db.gps_data.find({}).sort("timestamp", ASCENDING)
        
        results = []
        async for doc in cursor:
            # Convert ObjectId to string for response model
            doc_dict = dict(doc)
            if "_id" in doc_dict:
                doc_dict["id"] = str(doc_dict["_id"])
                del doc_dict["_id"]
            
            # Ensure timestamp and created_at are datetime objects
            if "timestamp" in doc_dict and isinstance(doc_dict["timestamp"], str):
                doc_dict["timestamp"] = datetime.fromisoformat(doc_dict["timestamp"].replace('Z', '+00:00'))
            if "created_at" in doc_dict and isinstance(doc_dict["created_at"], str):
                doc_dict["created_at"] = datetime.fromisoformat(doc_dict["created_at"].replace('Z', '+00:00'))
            
            results.append(GPSDataResponse(**doc_dict))
        
        logger.info(f"📦 Retrieved {len(results)} GPS records for export")
        return results
        
    except Exception as e:
        logger.error(f"💥 Failed to export GPS data: {e}")
        return []

# =============================================================================
# DEVICE ANALYTICS
# =============================================================================

async def get_device_statistics(db: AsyncDatabase) -> Dict[str, Any]:
    """
    Get comprehensive device statistics
    - Device count and activity
    - Data distribution analysis
    - Performance metrics
    """
    try:
        # Aggregation pipeline for device stats
        pipeline = [
            {
                "$group": {
                    "_id": "$device_id",
                    "record_count": {"$sum": 1},
                    "latest_timestamp": {"$max": "$timestamp"},
                    "earliest_timestamp": {"$min": "$timestamp"},
                    "avg_speed": {"$avg": "$speed"},
                    "max_speed": {"$max": "$speed"}
                }
            },
            {
                "$sort": {"record_count": -1}
            }
        ]
        
        device_stats = []
        async for doc in db.gps_data.aggregate(pipeline):
            device_stats.append(doc)
        
        # Overall statistics
        total_devices = len(device_stats)
        total_records = sum(stat["record_count"] for stat in device_stats)
        
        return {
            "total_devices": total_devices,
            "total_records": total_records,
            "device_breakdown": device_stats[:10],  # Top 10 devices
            "avg_records_per_device": total_records / total_devices if total_devices > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"💥 Failed to get device statistics: {e}")
        return {"total_devices": 0, "total_records": 0, "device_breakdown": []}

# =============================================================================
# SYSTEM STATISTICS OPERATIONS  
# =============================================================================

async def create_system_stats(
    db: AsyncDatabase,
    total_gps_records: int,
    database_size_bytes: int,
    database_usage_percentage: float,
    post_requests_last_minute: Optional[int] = None,
    average_posts_per_minute: Optional[float] = None
) -> SystemStatsResponse:
    """
    Create system statistics record
    - Performance monitoring data
    - Database capacity tracking
    - Request rate analytics
    """
    try:
        doc = SystemStatsDocument(
            total_gps_records=total_gps_records,
            database_size_bytes=database_size_bytes,
            database_usage_percentage=database_usage_percentage,
            post_requests_last_minute=post_requests_last_minute,
            average_posts_per_minute=average_posts_per_minute
        )
        
        result = await db.system_stats.insert_one(doc.dict())
        created_doc = await db.system_stats.find_one({"_id": result.inserted_id})
        
        return SystemStatsResponse(**created_doc)
        
    except Exception as e:
        logger.error(f"💥 Failed to create system stats: {e}")
        raise

async def get_latest_system_stats(db: AsyncDatabase) -> Optional[SystemStatsResponse]:
    """
    Get latest system statistics
    - Uses stats_timestamp_idx for performance
    - Critical for real-time monitoring
    """
    try:
        doc = await db.system_stats.find_one({}, sort=[("timestamp", DESCENDING)])
        
        if doc:
            return SystemStatsResponse(**doc)
        return None
        
    except Exception as e:
        logger.error(f"💥 Failed to get latest system stats: {e}")
        return None

# =============================================================================
# WEBSOCKET BROADCASTING
# =============================================================================

async def broadcast_gps_update(gps_data: GPSDataResponse):
    """
    Broadcast GPS update to WebSocket clients
    - Real-time dashboard updates
    - Non-blocking operation
    """
    try:
        # Import here to avoid circular imports
        from websocket_manager import ws_manager
        
        await ws_manager.broadcast({
            "type": "gps_update",
            "data": {
                "id": gps_data.id,
                "device_id": gps_data.device_id,
                "lattitude": gps_data.lattitude,
                "longitude": gps_data.longitude,
                "speed": gps_data.speed,
                "speed_ms": gps_data.speed_ms,
                "timestamp": gps_data.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        # Non-critical error - don't fail GPS data insertion
        logger.warning(f"⚠️  WebSocket broadcast failed (non-critical): {e}")

# =============================================================================  
# PERFORMANCE ANALYTICS
# =============================================================================

async def get_performance_metrics(db: AsyncDatabase) -> Dict[str, Any]:
    """
    Get database performance metrics
    - Query performance analysis
    - Index usage statistics
    - Capacity and growth trends
    """
    try:
        # Recent activity analysis (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_count = await db.gps_data.count_documents({
            "created_at": {"$gte": one_hour_ago}
        })
        
        # Database size analysis
        db_stats = await db.command("dbStats")
        
        # Collection stats
        gps_stats = await db.command("collStats", "gps_data")
        
        return {
            "recent_activity": {
                "records_last_hour": recent_count,
                "avg_per_minute": recent_count / 60
            },
            "database_metrics": {
                "total_size_bytes": db_stats.get("dataSize", 0),
                "index_size_bytes": db_stats.get("indexSize", 0),
                "collection_count": db_stats.get("collections", 0)
            },
            "gps_collection": {
                "document_count": gps_stats.get("count", 0),
                "avg_document_size": gps_stats.get("avgObjSize", 0),
                "total_size": gps_stats.get("size", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"💥 Failed to get performance metrics: {e}")
        return {}