from fastapi import FastAPI, HTTPException, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Set
import logging
import asyncio
import os
import json

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import get_db, init_db
from models import GPSData, GPSDataResponse, GPSDataCreate, SystemStats
from crud import create_gps_data, get_gps_data_filtered, create_system_stats, get_latest_system_stats
from monitoring import start_monitoring_task, record_post_request
from backup_manager import backup_manager
from websocket_manager import ws_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Start background monitoring task
    asyncio.create_task(start_monitoring_task())
    yield

app = FastAPI(
    title="GPS Data Streamer",
    description="FastAPI backend for GPS data collection and streaming",
    version="5.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files (if needed in the future)
# app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api")
async def api_root():
    return {"message": "GPS Data Streamer API", "version": "5.0.0"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.post("/api/gps/data", response_model=GPSDataResponse)
@limiter.limit("1/second")
async def receive_gps_data(
    request: Request,
    gps_data: GPSDataCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Record this request for rate monitoring
        record_post_request()
        
        stored_data = await create_gps_data(db, gps_data)
        logger.info(f"GPS data stored: {stored_data.id} from device {gps_data.device_id}")
        return stored_data
    except ValueError as e:
        # Validation errors from Pydantic models
        logger.warning(f"Invalid GPS data from {gps_data.device_id}: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid GPS data: {str(e)}")
    except Exception as e:
        logger.error(f"Error storing GPS data from {gps_data.device_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store GPS data")

@app.get("/api/gps/data", response_model=List[GPSDataResponse])
async def get_gps_data(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    start_time: Optional[datetime] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time filter (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db)
):
    try:
        data = await get_gps_data_filtered(
            db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        return data
    except Exception as e:
        logger.error(f"Error retrieving GPS data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve GPS data")

@app.get("/api/system/stats")
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    try:
        stats = await get_latest_system_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error retrieving system stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system stats")

@app.post("/api/backup/create")
async def create_backup_manual(format: str = "json"):
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        filename = await backup_manager.create_backup(format)
        return {"message": f"Backup created successfully", "filename": filename}
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create backup")

@app.get("/api/backup/files")
async def list_backup_files():
    try:
        files = backup_manager.get_backup_files()
        return {"backup_files": files}
    except Exception as e:
        logger.error(f"Error listing backup files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list backup files")

@app.get("/api/backup/download/{filename}")
async def download_backup_file(filename: str):
    try:
        # Security: Only allow downloading files with expected pattern
        if not filename.startswith("gps_backup_") or not (filename.endswith(".json") or filename.endswith(".csv")):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = backup_manager.get_backup_file_path(filename)
        
        # Check if file exists and hasn't expired
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Check if file has expired
        backup_files = backup_manager.get_backup_files()
        file_info = next((f for f in backup_files if f["filename"] == filename), None)
        
        if not file_info:
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        if file_info["expired"]:
            raise HTTPException(status_code=410, detail="Backup file has expired")
        
        # Determine content type based on file extension
        content_type = "application/json" if filename.endswith(".json") else "text/csv"
        
        logger.info(f"Serving backup download: {filename}")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download backup file")

@app.delete("/api/backup/cleanup")
async def cleanup_expired_backups():
    try:
        initial_count = len(backup_manager.get_backup_files())
        backup_manager.cleanup_expired_backups()
        final_count = len(backup_manager.get_backup_files())
        removed_count = initial_count - final_count
        
        return {"message": f"Cleanup completed", "files_removed": removed_count}
    except Exception as e:
        logger.error(f"Error during backup cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup backup files")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)