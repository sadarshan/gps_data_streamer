from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional, List

from models import GPSData, GPSDataCreate, SystemStats

async def create_gps_data(db: AsyncSession, gps_data: GPSDataCreate) -> GPSData:
    db_gps_data = GPSData(
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
    db.add(db_gps_data)
    await db.flush()
    await db.refresh(db_gps_data)
    return db_gps_data

async def get_gps_data_filtered(
    db: AsyncSession,
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[GPSData]:
    query = select(GPSData)
    
    conditions = []
    if device_id:
        conditions.append(GPSData.device_id == device_id)
    if start_time:
        conditions.append(GPSData.timestamp >= start_time)
    if end_time:
        conditions.append(GPSData.timestamp <= end_time)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(GPSData.timestamp)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_gps_data_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(GPSData.id)))
    return result.scalar()

async def get_oldest_gps_data(db: AsyncSession, limit: int) -> List[GPSData]:
    query = select(GPSData).order_by(GPSData.timestamp).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def delete_oldest_records(db: AsyncSession, percentage: float) -> int:
    # Get total count
    total_count = await get_gps_data_count(db)
    delete_count = int(total_count * percentage / 100)
    
    if delete_count == 0:
        return 0
    
    # Get IDs of oldest records
    oldest_query = select(GPSData.id).order_by(GPSData.timestamp).limit(delete_count)
    result = await db.execute(oldest_query)
    ids_to_delete = [row[0] for row in result.fetchall()]
    
    # Delete the records
    if ids_to_delete:
        delete_query = delete(GPSData).where(GPSData.id.in_(ids_to_delete))
        result = await db.execute(delete_query)
        return result.rowcount
    
    return 0

async def get_all_gps_data_for_export(db: AsyncSession) -> List[GPSData]:
    query = select(GPSData).order_by(GPSData.timestamp)
    result = await db.execute(query)
    return result.scalars().all()

async def create_system_stats(
    db: AsyncSession,
    total_gps_records: int,
    database_size_bytes: int,
    database_usage_percentage: float,
    post_requests_last_minute: Optional[int] = None,
    average_posts_per_minute: Optional[float] = None
) -> SystemStats:
    db_stats = SystemStats(
        total_gps_records=total_gps_records,
        database_size_bytes=database_size_bytes,
        database_usage_percentage=database_usage_percentage,
        post_requests_last_minute=post_requests_last_minute,
        average_posts_per_minute=average_posts_per_minute
    )
    db.add(db_stats)
    await db.flush()
    await db.refresh(db_stats)
    return db_stats

async def get_latest_system_stats(db: AsyncSession) -> Optional[SystemStats]:
    query = select(SystemStats).order_by(desc(SystemStats.timestamp)).limit(1)
    result = await db.execute(query)
    return result.scalars().first()