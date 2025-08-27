from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from bson import ObjectId

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
    id: Optional[str] = Field(default=None, alias="_id")
    device_id: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    created_at: datetime
    additional_data: Optional[str] = None
    
    @validator('id', pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    class Config:
        populate_by_name = True

class SystemStatsResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    timestamp: datetime
    total_gps_records: int
    database_size_bytes: int
    database_usage_percentage: float
    post_requests_last_minute: Optional[int] = None
    average_posts_per_minute: Optional[float] = None
    
    @validator('id', pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    class Config:
        populate_by_name = True

class GPSDataDocument(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    additional_data: Optional[str] = None

class SystemStatsDocument(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_gps_records: int
    database_size_bytes: int
    database_usage_percentage: float
    post_requests_last_minute: Optional[int] = None
    average_posts_per_minute: Optional[float] = None