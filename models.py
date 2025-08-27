from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from typing import Optional

Base = declarative_base()

class GPSData(Base):
    __tablename__ = "gps_data"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    altitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    additional_data = Column(Text, nullable=True)
    
    # Add compound indexes for common queries
    __table_args__ = (
        # Index for querying by device and time range
        Index('idx_device_timestamp', 'device_id', 'timestamp'),
        # Index for location-based queries
        Index('idx_location', 'latitude', 'longitude'),
        # Index for time-based cleanup operations
        Index('idx_created_at', 'created_at'),
    )

class SystemStats(Base):
    __tablename__ = "system_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    total_gps_records = Column(Integer, nullable=False)
    database_size_bytes = Column(Integer, nullable=False)
    database_usage_percentage = Column(Float, nullable=False)
    post_requests_last_minute = Column(Integer, nullable=True)
    average_posts_per_minute = Column(Float, nullable=True)

class GPSDataCreate(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=50, description="Device identifier")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    speed: Optional[float] = Field(None, ge=0, description="Speed in m/s")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Heading in degrees")
    accuracy: Optional[float] = Field(None, ge=0, description="Accuracy in meters")
    timestamp: Optional[datetime] = Field(None, description="GPS timestamp (defaults to current time)")
    additional_data: Optional[str] = Field(None, max_length=1000, description="Additional JSON data")
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()
    
    @validator('speed')
    def validate_speed(cls, v):
        if v is not None and v > 200:  # 200 m/s = ~720 km/h, reasonable upper limit
            raise ValueError('Speed seems unrealistic (>200 m/s)')
        if v is not None and v < 0:
            raise ValueError('Speed cannot be negative')
        return v
    
    @validator('accuracy')
    def validate_accuracy(cls, v):
        if v is not None and v > 10000:  # 10km accuracy limit
            raise ValueError('Accuracy value too large (>10000m)')
        if v is not None and v < 0:
            raise ValueError('Accuracy cannot be negative')
        return v
    
    @validator('latitude')
    def validate_latitude_precision(cls, v):
        # Check for reasonable GPS precision (5-6 decimal places max)
        if abs(v) < 0.00001:  # Too close to 0,0 (Null Island)
            if v == 0.0:
                raise ValueError('Exact 0.0 latitude is suspicious')
        return v
    
    @validator('longitude')
    def validate_longitude_precision(cls, v):
        # Check for reasonable GPS precision (5-6 decimal places max)  
        if abs(v) < 0.00001:  # Too close to 0,0 (Null Island)
            if v == 0.0:
                raise ValueError('Exact 0.0 longitude is suspicious')
        return v
    
    @validator('timestamp')
    def validate_timestamp_reasonable(cls, v):
        if v is not None:
            now = datetime.utcnow()
            
            # Handle timezone-aware datetimes
            if hasattr(v, 'tzinfo') and v.tzinfo is not None:
                # Convert to naive UTC for comparison
                v = v.replace(tzinfo=None)
            
            # Don't allow timestamps more than 1 hour in the future
            if v > now + timedelta(hours=1):
                raise ValueError('Timestamp cannot be more than 1 hour in the future')
            # Don't allow timestamps older than 24 hours
            if v < now - timedelta(hours=24):
                raise ValueError('Timestamp cannot be older than 24 hours')
        return v

class GPSDataResponse(BaseModel):
    id: int
    device_id: str
    latitude: float
    longitude: float
    altitude: Optional[float]
    speed: Optional[float]
    heading: Optional[float]
    accuracy: Optional[float]
    timestamp: datetime
    created_at: datetime
    additional_data: Optional[str]
    
    class Config:
        from_attributes = True

class SystemStatsResponse(BaseModel):
    id: int
    timestamp: datetime
    total_gps_records: int
    database_size_bytes: int
    database_usage_percentage: float
    post_requests_last_minute: Optional[int]
    average_posts_per_minute: Optional[float]
    
    class Config:
        from_attributes = True