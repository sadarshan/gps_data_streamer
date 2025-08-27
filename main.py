"""
GPS Data Streamer - High-throughput GPS data ingestion system
Features: Rate limiting, real-time dashboard, automatic backup, intelligent data management
Optimized for Render + MongoDB Atlas deployment
"""
from fastapi import FastAPI, HTTPException, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List
import logging
import asyncio
import os
from dotenv import load_dotenv

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# Import our modules
from database import init_db, close_db, get_db
from models import GPSDataCreate, GPSDataResponse, SystemStatsResponse
from crud import create_gps_data, get_gps_data_filtered, get_latest_system_stats
from monitoring import start_monitoring_task, record_post_request
from backup_manager import backup_manager
from websocket_manager import ws_manager

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    logger.info("🚀 Starting GPS Data Streamer...")
    
    # Initialize database with connection pooling
    await init_db()
    
    # Start background monitoring and management tasks
    asyncio.create_task(start_monitoring_task())
    
    logger.info("✅ GPS Data Streamer started successfully")
    yield
    
    # Cleanup on shutdown
    logger.info("🔄 Shutting down GPS Data Streamer...")
    await close_db()
    logger.info("✅ GPS Data Streamer stopped")

# FastAPI app initialization
app = FastAPI(
    title="GPS Data Streamer",
    description="High-throughput GPS data ingestion with real-time monitoring and automatic management",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for dashboard assets
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    logger.warning("Static files directory not found - dashboard styling may be limited")

# =============================================================================
# WEB ROUTES
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Real-time GPS data dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api", response_model=dict)
async def api_status():
    """API status and information"""
    return {
        "service": "GPS Data Streamer",
        "version": "2.0.0",
        "status": "online",
        "features": [
            "High-throughput data ingestion",
            "Real-time WebSocket updates",
            "Automatic backup system", 
            "Intelligent data management",
            "Comprehensive GPS validation"
        ],
        "timestamp": datetime.utcnow()
    }

# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# =============================================================================
# GPS DATA API ENDPOINTS
# =============================================================================

@app.post("/api/gps/data", response_model=GPSDataResponse)
@limiter.limit("1/second")  # Rate limiting: 1 request per second with burst capability
async def receive_gps_data(
    request: Request,
    gps_data: GPSDataCreate,
    db=Depends(get_db)
):
    """
    High-throughput GPS data ingestion endpoint
    - Rate limited to 1 request/second per IP
    - Comprehensive GPS validation
    - Real-time WebSocket broadcasting
    - Automatic monitoring integration
    """
    try:
        # Record request for rate monitoring
        record_post_request()
        
        logger.info(f"🔍 Incoming GPS data: {gps_data.model_dump()}")
        
        # Store GPS data with validation
        stored_data = await create_gps_data(db, gps_data)
        
        logger.info(f"🔍 Stored data response: {stored_data.model_dump()}")
        
        logger.info(
            f"📍 GPS data stored: {stored_data.id} from device {gps_data.device_id} "
            f"at ({gps_data.lattitude:.6f}, {gps_data.longitude:.6f})"
        )
        
        return stored_data
        
    except ValueError as e:
        # GPS validation errors
        logger.warning(f"❌ Invalid GPS data from {gps_data.device_id}: {str(e)}")
        raise HTTPException(
            status_code=422, 
            detail=f"GPS validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"💥 Error storing GPS data from {gps_data.device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to store GPS data"
        )

@app.get("/api/gps/data", response_model=List[GPSDataResponse])
async def get_gps_data(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    start_time: Optional[datetime] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time filter (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records (1-1000)"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    db=Depends(get_db)
):
    """
    Retrieve GPS data with advanced filtering
    - Device ID filtering
    - Time range filtering  
    - Pagination support
    - Optimized with database indexing
    """
    try:
        data = await get_gps_data_filtered(
            db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"📊 Retrieved {len(data)} GPS records (device: {device_id or 'all'})")
        return data
        
    except Exception as e:
        logger.error(f"💥 Error retrieving GPS data: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve GPS data"
        )

# =============================================================================
# SYSTEM MONITORING API
# =============================================================================

@app.get("/api/system/stats", response_model=SystemStatsResponse)
async def get_system_stats(db=Depends(get_db)):
    """
    Real-time system statistics
    - Database usage and capacity
    - Request rate monitoring
    - Record counts and performance metrics
    """
    try:
        stats = await get_latest_system_stats(db)
        return stats or {
            "total_gps_records": 0,
            "database_size_bytes": 0,
            "database_usage_percentage": 0.0,
            "post_requests_last_minute": 0,
            "average_posts_per_minute": 0.0,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"💥 Error retrieving system stats: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve system statistics"
        )

# =============================================================================
# BACKUP MANAGEMENT API
# =============================================================================

@app.post("/api/backup/create")
async def create_backup_manual(format: str = Query("json", regex="^(json|csv)$")):
    """
    Manual backup creation
    - JSON or CSV format selection
    - Automatic expiration in 24 hours
    - Downloadable backup files
    """
    try:
        filename = await backup_manager.create_backup(format)
        logger.info(f"📦 Manual backup created: {filename}")
        
        return {
            "message": f"Backup created successfully",
            "filename": filename,
            "format": format,
            "expires_in_hours": 24
        }
    except Exception as e:
        logger.error(f"💥 Error creating backup: {str(e)}")
        logger.error(f"💥 Exception type: {type(e)}")
        import traceback
        logger.error(f"💥 Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create backup: {str(e)}"
        )

@app.get("/api/backup/files")
async def list_backup_files():
    """List all available backup files with status"""
    try:
        files = backup_manager.get_backup_files()
        return {
            "backup_files": files,
            "total_files": len(files),
            "active_files": len([f for f in files if not f["expired"]])
        }
    except Exception as e:
        logger.error(f"💥 Error listing backup files: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to list backup files"
        )

@app.get("/api/backup/download/{filename}")
async def download_backup_file(filename: str):
    """Download backup file with security validation"""
    try:
        # Security: Validate filename format
        if not filename.startswith("gps_backup_") or not (filename.endswith(".json") or filename.endswith(".csv")):
            raise HTTPException(status_code=400, detail="Invalid backup filename")
        
        file_path = backup_manager.get_backup_file_path(filename)
        
        # Check file existence
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Check expiration
        backup_files = backup_manager.get_backup_files()
        file_info = next((f for f in backup_files if f["filename"] == filename), None)
        
        if not file_info or file_info["expired"]:
            raise HTTPException(status_code=410, detail="Backup file has expired")
        
        # Determine content type
        content_type = "application/json" if filename.endswith(".json") else "text/csv"
        
        logger.info(f"📥 Serving backup download: {filename}")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error downloading backup {filename}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to download backup file"
        )

@app.delete("/api/backup/cleanup")
async def cleanup_expired_backups():
    """Clean up expired backup files"""
    try:
        initial_count = len(backup_manager.get_backup_files())
        backup_manager.cleanup_expired_backups()
        final_count = len(backup_manager.get_backup_files())
        removed_count = initial_count - final_count
        
        logger.info(f"🧹 Backup cleanup: {removed_count} expired files removed")
        
        return {
            "message": "Backup cleanup completed",
            "files_removed": removed_count,
            "remaining_files": final_count
        }
    except Exception as e:
        logger.error(f"💥 Error during backup cleanup: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to cleanup backup files"
        )

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
async def health_check():
    """Application health check endpoint"""
    try:
        db = get_db()
        # Test database connection
        await db.command('ping')
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "GPS Data Streamer",
        "version": "2.0.0",
        "timestamp": datetime.utcnow(),
        "database": db_status
    }

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=True
    )