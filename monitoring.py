"""
System Monitoring and Automatic Data Management
Features: Real-time capacity monitoring, automatic data purging, performance tracking
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import time
from collections import defaultdict

from database import get_db, get_db_size
from crud import (
    get_gps_data_count, delete_oldest_records, create_system_stats,
    get_performance_metrics
)

logger = logging.getLogger(__name__)

# Global monitoring state
request_times = []
post_request_count = 0
last_cleanup_time = datetime.utcnow()

# Database size limits (100MB total limit)
DATABASE_SIZE_LIMIT_BYTES = 100 * 1024 * 1024  # 100MB
WARNING_THRESHOLD = 0.90  # 90%
EMERGENCY_THRESHOLD = 0.95  # 95%

async def start_monitoring_task():
    """
    Start background monitoring and data management tasks
    - Monitor database capacity every 30 seconds
    - Automatic purging when limits exceeded
    - System statistics recording
    """
    logger.info("🔄 Starting system monitoring and data management...")
    
    while True:
        try:
            await monitor_system_health()
            await asyncio.sleep(300)  # Monitor every 30 seconds
        except Exception as e:
            logger.error(f"💥 Monitoring task error: {e}")
            await asyncio.sleep(60)  # Longer delay on error

async def monitor_system_health():
    """
    Comprehensive system health monitoring
    - Database size and usage tracking
    - Automatic data management
    - Performance metrics collection
    """
    try:
        db = get_db()
        
        # Get current database metrics
        db_size_bytes = await get_db_size()
        total_records = await get_gps_data_count(db)
        usage_percentage = (db_size_bytes / DATABASE_SIZE_LIMIT_BYTES) * 100
        
        # Calculate request rate metrics
        current_time = time.time()
        post_requests_last_minute = len([
            t for t in request_times 
            if current_time - t <= 60
        ])
        
        # Calculate average posts per minute (last 10 minutes)
        posts_last_10_min = len([
            t for t in request_times 
            if current_time - t <= 600
        ])
        avg_posts_per_minute = posts_last_10_min / 10 if posts_last_10_min > 0 else 0
        
        # Log current status
        logger.info(
            f"📊 System Status - Records: {total_records:,}, "
            f"DB Size: {db_size_bytes / (1024*1024):.1f}MB ({usage_percentage:.1f}%), "
            f"Requests/min: {post_requests_last_minute}"
        )
        
        # Automatic data management based on usage thresholds
        deleted_count = 0
        if usage_percentage >= EMERGENCY_THRESHOLD * 100:
            # Emergency: Delete 20% of oldest data
            logger.warning(
                f"🚨 EMERGENCY: Database at {usage_percentage:.1f}% capacity - "
                "performing emergency purge (20% of data)"
            )
            deleted_count = await delete_oldest_records(db, 20)
            
        elif usage_percentage >= WARNING_THRESHOLD * 100:
            # Warning: Delete 10% of oldest data
            logger.warning(
                f"⚠️  WARNING: Database at {usage_percentage:.1f}% capacity - "
                "performing maintenance purge (10% of data)"
            )
            deleted_count = await delete_oldest_records(db, 10)
        
        # Update metrics after potential deletion
        if deleted_count > 0:
            db_size_bytes = await get_db_size()
            total_records = await get_gps_data_count(db)
            usage_percentage = (db_size_bytes / DATABASE_SIZE_LIMIT_BYTES) * 100
            logger.info(
                f"✅ Purge completed - New stats: {total_records:,} records, "
                f"{usage_percentage:.1f}% capacity"
            )
        
        # Record system statistics
        await create_system_stats(
            db=db,
            total_gps_records=total_records,
            database_size_bytes=db_size_bytes,
            database_usage_percentage=usage_percentage,
            post_requests_last_minute=post_requests_last_minute,
            average_posts_per_minute=avg_posts_per_minute
        )
        
        # Cleanup old request tracking data (keep last 1 hour)
        cleanup_old_request_data()
        
    except Exception as e:
        logger.error(f"💥 System health monitoring failed: {e}")

def record_post_request():
    """
    Record GPS data POST request for rate monitoring
    Thread-safe tracking of request timestamps
    """
    global post_request_count
    current_time = time.time()
    request_times.append(current_time)
    post_request_count += 1
    
    # Clean up old entries (keep last hour only)
    if len(request_times) > 1000:  # Limit memory usage
        cleanup_old_request_data()

def cleanup_old_request_data():
    """Clean up old request tracking data to prevent memory bloat"""
    global request_times
    current_time = time.time()
    one_hour_ago = current_time - 3600
    
    # Keep only requests from last hour
    request_times = [t for t in request_times if t > one_hour_ago]

def get_request_rate_stats() -> Dict[str, float]:
    """
    Get current request rate statistics
    Returns rates for different time windows
    """
    current_time = time.time()
    
    # Count requests in different time windows
    last_minute = len([t for t in request_times if current_time - t <= 60])
    last_5_minutes = len([t for t in request_times if current_time - t <= 300])
    last_hour = len([t for t in request_times if current_time - t <= 3600])
    
    return {
        "requests_per_minute": last_minute,
        "requests_per_5_minutes": last_5_minutes / 5,
        "requests_per_hour": last_hour / 60,
        "total_requests": post_request_count
    }

async def get_monitoring_summary() -> Dict:
    """
    Get comprehensive monitoring summary for dashboard
    Combines database, performance, and request rate metrics
    """
    try:
        db = get_db()
        
        # Database metrics
        db_size_bytes = await get_db_size()
        total_records = await get_gps_data_count(db)
        usage_percentage = (db_size_bytes / DATABASE_SIZE_LIMIT_BYTES) * 100
        
        # Request rate metrics
        rate_stats = get_request_rate_stats()
        
        # Performance metrics
        perf_metrics = await get_performance_metrics(db)
        
        # Capacity status
        if usage_percentage >= EMERGENCY_THRESHOLD * 100:
            capacity_status = "CRITICAL"
            capacity_color = "red"
        elif usage_percentage >= WARNING_THRESHOLD * 100:
            capacity_status = "WARNING"
            capacity_color = "orange"
        else:
            capacity_status = "OK"
            capacity_color = "green"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "total_records": total_records,
                "size_bytes": db_size_bytes,
                "size_mb": round(db_size_bytes / (1024 * 1024), 2),
                "usage_percentage": round(usage_percentage, 1),
                "limit_mb": round(DATABASE_SIZE_LIMIT_BYTES / (1024 * 1024), 1),
                "capacity_status": capacity_status,
                "capacity_color": capacity_color
            },
            "requests": rate_stats,
            "performance": perf_metrics,
            "thresholds": {
                "warning_percent": WARNING_THRESHOLD * 100,
                "emergency_percent": EMERGENCY_THRESHOLD * 100
            }
        }
        
    except Exception as e:
        logger.error(f"💥 Error generating monitoring summary: {e}")
        return {
            "error": "Failed to generate monitoring data",
            "timestamp": datetime.utcnow().isoformat()
        }

async def force_cleanup(percentage: float = 15) -> Dict:
    """
    Force manual cleanup of old GPS data
    Used for emergency situations or manual maintenance
    """
    try:
        db = get_db()
        initial_count = await get_gps_data_count(db)
        initial_size = await get_db_size()
        
        deleted_count = await delete_oldest_records(db, percentage)
        
        final_count = await get_gps_data_count(db)
        final_size = await get_db_size()
        
        space_freed = initial_size - final_size
        
        logger.info(f"🧹 Manual cleanup completed - Removed {deleted_count:,} records")
        
        return {
            "success": True,
            "deleted_records": deleted_count,
            "initial_records": initial_count,
            "final_records": final_count,
            "space_freed_mb": round(space_freed / (1024 * 1024), 2),
            "percentage_deleted": percentage
        }
        
    except Exception as e:
        logger.error(f"💥 Force cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_system_uptime() -> Dict:
    """Get system uptime and basic status information"""
    global last_cleanup_time
    
    uptime = datetime.utcnow() - last_cleanup_time
    
    return {
        "monitoring_started": last_cleanup_time.isoformat(),
        "uptime_seconds": uptime.total_seconds(),
        "uptime_hours": round(uptime.total_seconds() / 3600, 2),
        "total_post_requests": post_request_count,
        "monitoring_active": True
    }