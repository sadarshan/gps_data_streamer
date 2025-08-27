import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from database import get_db_size, AsyncSessionLocal
from crud import get_gps_data_count, create_system_stats, get_gps_data_filtered
from backup_manager import handle_database_management

logger = logging.getLogger(__name__)

# Database size limits (100MB max, 90% warning, 95% emergency)
MAX_DB_SIZE = 100 * 1024 * 1024  # 100 MB
WARNING_THRESHOLD = 0.90  # 90%
EMERGENCY_THRESHOLD = 0.95  # 95%

# Rate tracking for POST requests
post_request_times = []

def record_post_request():
    """Record a POST request timestamp for rate monitoring"""
    global post_request_times
    current_time = datetime.utcnow()
    post_request_times.append(current_time)
    
    # Clean old timestamps (older than 1 minute)
    cutoff_time = current_time - timedelta(minutes=1)
    post_request_times = [t for t in post_request_times if t > cutoff_time]

def get_posts_last_minute() -> int:
    """Get number of POST requests in the last minute"""
    current_time = datetime.utcnow()
    cutoff_time = current_time - timedelta(minutes=1)
    return len([t for t in post_request_times if t > cutoff_time])

def calculate_average_posts_per_minute(minutes: int = 5) -> Optional[float]:
    """Calculate average POST requests per minute over the last N minutes"""
    if not post_request_times:
        return None
    
    current_time = datetime.utcnow()
    cutoff_time = current_time - timedelta(minutes=minutes)
    recent_posts = [t for t in post_request_times if t > cutoff_time]
    
    if len(recent_posts) == 0:
        return 0.0
    
    return len(recent_posts) / minutes

async def collect_system_metrics():
    """Collect and store system metrics"""
    try:
        async with AsyncSessionLocal() as db:
            # Get database metrics
            db_size = await get_db_size()
            usage_percentage = (db_size / MAX_DB_SIZE) * 100
            total_records = await get_gps_data_count(db)
            
            # Get rate metrics
            posts_last_minute = get_posts_last_minute()
            avg_posts_per_minute = calculate_average_posts_per_minute()
            
            # Store metrics
            await create_system_stats(
                db,
                total_gps_records=total_records,
                database_size_bytes=db_size,
                database_usage_percentage=usage_percentage,
                post_requests_last_minute=posts_last_minute,
                average_posts_per_minute=avg_posts_per_minute
            )
            
            await db.commit()
            
            logger.info(f"System metrics collected - DB: {db_size/1024/1024:.1f}MB ({usage_percentage:.1f}%), Records: {total_records}, Posts/min: {posts_last_minute}")
            
            # Handle database management (backup/purging)
            await handle_database_management(usage_percentage)
            
            # Broadcast system stats to WebSocket clients
            try:
                # Import here to avoid circular imports
                from websocket_manager import ws_manager
                await ws_manager.broadcast({
                    "type": "system_stats",
                    "data": {
                        "total_gps_records": total_records,
                        "database_size_bytes": db_size,
                        "database_usage_percentage": usage_percentage,
                        "post_requests_last_minute": posts_last_minute,
                        "average_posts_per_minute": avg_posts_per_minute,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
                # Also broadcast recent GPS data
                recent_data = await get_gps_data_filtered(db, limit=5)
                await ws_manager.broadcast({
                    "type": "gps_data",
                    "data": [
                        {
                            "id": record.id,
                            "device_id": record.device_id,
                            "latitude": record.latitude,
                            "longitude": record.longitude,
                            "timestamp": record.timestamp.isoformat()
                        }
                        for record in recent_data
                    ]
                })
            except Exception as ws_error:
                logger.warning(f"Error broadcasting WebSocket update: {ws_error}")
            
            # Check for warnings
            if usage_percentage >= WARNING_THRESHOLD * 100:
                if usage_percentage >= EMERGENCY_THRESHOLD * 100:
                    logger.critical(f"EMERGENCY: Database at {usage_percentage:.1f}% capacity!")
                else:
                    logger.warning(f"WARNING: Database at {usage_percentage:.1f}% capacity!")
                    
    except Exception as e:
        logger.error(f"Error collecting system metrics: {str(e)}")

async def start_monitoring_task():
    """Start the background monitoring task that runs every 5 minutes"""
    logger.info("Starting system monitoring task (5-minute intervals)")
    
    while True:
        try:
            await collect_system_metrics()
            await asyncio.sleep(300)  # 5 minutes
        except Exception as e:
            logger.error(f"Error in monitoring task: {str(e)}")
            await asyncio.sleep(60)  # Retry after 1 minute on error