"""
GPS Data Models - Comprehensive validation and data structures
Features: GPS coordinate validation, timestamp verification, speed reasonableness checks
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional, Any
from bson import ObjectId
import math

class GPSDataCreate(BaseModel):
    """
    GPS data input model with comprehensive validation
    Validates coordinates, timestamps, speed, and data integrity
    """
    id: Optional[int] = Field(None, description="Device sequence ID")
    
    device_id: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="Unique device identifier"
    )
    
    frame_time: Optional[str] = Field(
        None, 
        description="Frame time in DD/MM/YY HH:MM:SS format"
    )
    
    lattitude: float = Field(  # Note: keeping your spelling
        ..., 
        ge=-90, 
        le=90, 
        description="Latitude in decimal degrees (-90 to +90)"
    )
    
    longitude: float = Field(
        ..., 
        ge=-180, 
        le=180, 
        description="Longitude in decimal degrees (-180 to +180)"
    )
    
    url: Optional[str] = Field(
        None,
        description="Google Maps URL"
    )
    
    sat_tked: Optional[int] = Field(
        None,
        ge=0,
        le=50,
        description="Number of satellites tracked"
    )
    
    speed: Optional[float] = Field(
        None, 
        ge=0, 
        description="Speed in km/h (0 or positive)"
    )
    
    altitude: Optional[float] = Field(
        None, 
        ge=-1000, 
        le=10000, 
        description="Altitude in meters (-1000 to +10000)"
    )
    
    heading: Optional[float] = Field(
        None, 
        ge=0, 
        lt=360, 
        description="Heading in degrees (0-359.999)"
    )
    
    accuracy: Optional[float] = Field(
        None, 
        ge=0, 
        le=10000, 
        description="GPS accuracy in meters (0-10000)"
    )
    
    timestamp: Optional[datetime] = Field(
        None, 
        description="GPS timestamp (defaults to current time)"
    )
    
    created_at: Optional[str] = Field(
        None,
        description="Creation timestamp string"
    )
    
    additional_data: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Additional JSON data (max 1000 chars)"
    )

    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        """Set timestamp to current time if not provided"""
        return v or datetime.utcnow()
    
    @validator('lattitude')  # Note: using your field name
    def validate_latitude_precision(cls, v):
        """
        Validate latitude for GPS reasonableness
        - Reject exact 0.0 (Null Island - suspicious)
        - Allow high precision GPS coordinates (up to 12 decimal places)
        """
        if v == 0.0:
            raise ValueError("Exact 0.0 latitude is suspicious - check GPS fix quality")
        
        # Check for unreasonable precision (more than 12 decimal places)
        decimal_places = len(str(v).split('.')[-1]) if '.' in str(v) else 0
        if decimal_places > 12:
            raise ValueError("Latitude precision too high - GPS accuracy limit exceeded")
        
        return v
    
    @validator('longitude')
    def validate_longitude_precision(cls, v):
        """
        Validate longitude for GPS reasonableness  
        - Reject exact 0.0 (Null Island - suspicious)
        - Allow high precision GPS coordinates (up to 12 decimal places)
        """
        if v == 0.0:
            raise ValueError("Exact 0.0 longitude is suspicious - check GPS fix quality")
        
        # Check for unreasonable precision (more than 12 decimal places)
        decimal_places = len(str(v).split('.')[-1]) if '.' in str(v) else 0
        if decimal_places > 12:
            raise ValueError("Longitude precision too high - GPS accuracy limit exceeded")
        
        return v
    
    @validator('speed')
    def validate_speed_reasonableness(cls, v):
        """
        Validate speed for reasonableness (assuming km/h input)
        - Maximum reasonable speed: 720 km/h (faster than commercial aircraft)
        - Check for negative values
        """
        if v is None:
            return v
        
        if v < 0:
            raise ValueError("Speed cannot be negative")
        
        if v > 720:  # 720 km/h
            raise ValueError(f"Speed too high ({v:.1f} km/h) - exceeds reasonable limit")
        
        return v
    
    @validator('accuracy')
    def validate_accuracy_reasonableness(cls, v):
        """
        Validate GPS accuracy for reasonableness
        - Maximum: 10km (very poor GPS)
        - Warn about poor accuracy
        """
        if v is None:
            return v
        
        if v < 0:
            raise ValueError("GPS accuracy cannot be negative")
        
        if v > 10000:  # 10km
            raise ValueError(f"GPS accuracy too poor ({v:.1f}m) - signal quality insufficient")
        
        # Log warning for poor accuracy (but don't reject)
        if v > 50:  # 50 meters
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️  Poor GPS accuracy: {v:.1f}m")
        
        return v
    
    @validator('timestamp')
    def validate_timestamp_reasonableness(cls, v):
        """
        Validate timestamp for reasonableness
        - Not more than 1 hour in future (clock sync issues)
        - Not older than 7 days (stale data)
        - Handle timezone-aware datetimes
        """
        if v is None:
            return v
        
        now = datetime.utcnow()
        
        # Handle timezone-aware datetimes by converting to naive UTC
        if hasattr(v, 'tzinfo') and v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        
        # Future timestamp check
        if v > now + timedelta(hours=1):
            raise ValueError(f"Timestamp too far in future - check device clock sync")
        
        # Old timestamp check  
        if v < now - timedelta(days=7):
            raise ValueError(f"Timestamp too old (>{7} days) - data may be stale")
        
        return v
    
    @validator('additional_data')
    def validate_additional_data(cls, v):
        """Validate additional data is valid JSON if provided"""
        if v is None:
            return v
        
        # Try to parse as JSON to validate format
        import json
        try:
            json.loads(v)
        except json.JSONDecodeError:
            raise ValueError("Additional data must be valid JSON format")
        
        return v

class GPSDataResponse(BaseModel):
    """GPS data response model for API output"""
    id: Optional[str] = Field(None, alias="_id")
    device_sequence_id: Optional[int] = None
    device_id: str
    frame_time: Optional[str] = None
    lattitude: float  # Keep your field name
    longitude: float
    url: Optional[str] = None
    sat_tked: Optional[int] = None
    speed: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    created_at: datetime
    additional_data: Optional[str] = None
    
    # Computed fields for enhanced information
    speed_ms: Optional[float] = Field(None, description="Speed in m/s")
    distance_from_origin: Optional[float] = Field(None, description="Distance from 0,0 in km")
    
    @validator('id', pre=True)
    def convert_objectid_to_str(cls, v):
        """Convert MongoDB ObjectId to string for JSON serialization"""
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    @validator('speed_ms', pre=True, always=True)
    def calculate_speed_ms(cls, v, values):
        """Calculate speed in m/s from km/h"""
        speed_kmh = values.get('speed')
        if speed_kmh is not None:
            return round(speed_kmh / 3.6, 2)
        return None
    
    @validator('distance_from_origin', pre=True, always=True) 
    def calculate_distance_from_origin(cls, v, values):
        """Calculate distance from origin (0,0) in kilometers"""
        lat = values.get('lattitude', 0)  # Use your field name
        lon = values.get('longitude', 0)
        
        # Haversine formula for great circle distance
        R = 6371  # Earth's radius in km
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        a = (math.sin(lat_rad/2) ** 2 + 
             math.cos(0) * math.cos(lat_rad) * 
             math.sin(lon_rad/2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return round(distance, 2)
    
    class Config:
        populate_by_name = True

class GPSDataDocument(BaseModel):
    """Internal GPS data document for MongoDB storage"""
    device_sequence_id: Optional[int] = None
    device_id: str
    frame_time: Optional[str] = None
    lattitude: float
    longitude: float
    url: Optional[str] = None
    sat_tked: Optional[int] = None
    speed: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    additional_data: Optional[str] = None

class SystemStatsResponse(BaseModel):
    """System statistics response model for monitoring"""
    id: Optional[str] = Field(None, alias="_id")
    timestamp: datetime
    total_gps_records: int
    database_size_bytes: int
    database_usage_percentage: float
    post_requests_last_minute: Optional[int] = None
    average_posts_per_minute: Optional[float] = None
    
    # Enhanced monitoring fields
    database_size_mb: Optional[float] = Field(None, description="Database size in MB")
    capacity_status: Optional[str] = Field(None, description="Capacity status")
    
    @validator('id', pre=True)
    def convert_objectid_to_str(cls, v):
        """Convert MongoDB ObjectId to string"""
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    @validator('database_size_mb', pre=True, always=True)
    def calculate_size_mb(cls, v, values):
        """Calculate database size in MB"""
        size_bytes = values.get('database_size_bytes', 0)
        return round(size_bytes / (1024 * 1024), 2)
    
    @validator('capacity_status', pre=True, always=True)
    def determine_capacity_status(cls, v, values):
        """Determine capacity status based on usage percentage"""
        usage = values.get('database_usage_percentage', 0)
        
        if usage >= 95:
            return "CRITICAL"
        elif usage >= 90:
            return "WARNING"  
        elif usage >= 75:
            return "MODERATE"
        else:
            return "OK"
    
    class Config:
        populate_by_name = True

class SystemStatsDocument(BaseModel):
    """Internal system statistics document for MongoDB storage"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_gps_records: int
    database_size_bytes: int
    database_usage_percentage: float
    post_requests_last_minute: Optional[int] = None
    average_posts_per_minute: Optional[float] = None