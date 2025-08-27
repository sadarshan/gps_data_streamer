import asyncio
import json
import csv
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from database import AsyncSessionLocal
from crud import get_all_gps_data_for_export, delete_oldest_records, get_gps_data_count
from models import GPSData

logger = logging.getLogger(__name__)

# Backup settings
BACKUP_DIR = "./backups"
BACKUP_EXPIRY_HOURS = 24

class BackupManager:
    def __init__(self):
        self.backup_dir = Path(BACKUP_DIR)
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(self, format: str = "json") -> str:
        """Create a backup file and return the filename"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"gps_backup_{timestamp}.{format}"
        filepath = self.backup_dir / filename
        
        try:
            async with AsyncSessionLocal() as db:
                # Get all GPS data
                gps_data = await get_all_gps_data_for_export(db)
                
                if format == "json":
                    await self._create_json_backup(gps_data, filepath)
                elif format == "csv":
                    await self._create_csv_backup(gps_data, filepath)
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                logger.info(f"Backup created: {filename} ({len(gps_data)} records)")
                return filename
                
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise
    
    async def _create_json_backup(self, gps_data: List[GPSData], filepath: Path):
        """Create JSON backup file"""
        backup_data = {
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "record_count": len(gps_data),
                "format": "json"
            },
            "gps_data": []
        }
        
        for record in gps_data:
            backup_data["gps_data"].append({
                "id": record.id,
                "device_id": record.device_id,
                "latitude": record.latitude,
                "longitude": record.longitude,
                "altitude": record.altitude,
                "speed": record.speed,
                "heading": record.heading,
                "accuracy": record.accuracy,
                "timestamp": record.timestamp.isoformat(),
                "created_at": record.created_at.isoformat(),
                "additional_data": record.additional_data
            })
        
        with open(filepath, 'w') as f:
            json.dump(backup_data, f, indent=2)
    
    async def _create_csv_backup(self, gps_data: List[GPSData], filepath: Path):
        """Create CSV backup file"""
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'id', 'device_id', 'latitude', 'longitude', 'altitude',
                'speed', 'heading', 'accuracy', 'timestamp', 'created_at',
                'additional_data'
            ])
            
            # Write data
            for record in gps_data:
                writer.writerow([
                    record.id,
                    record.device_id,
                    record.latitude,
                    record.longitude,
                    record.altitude,
                    record.speed,
                    record.heading,
                    record.accuracy,
                    record.timestamp.isoformat(),
                    record.created_at.isoformat(),
                    record.additional_data
                ])
    
    def get_backup_files(self) -> List[Dict[str, Any]]:
        """Get list of available backup files with metadata"""
        backup_files = []
        
        for file_path in self.backup_dir.glob("gps_backup_*.json"):
            stat = file_path.stat()
            created_time = datetime.fromtimestamp(stat.st_ctime)
            expires_time = created_time + timedelta(hours=BACKUP_EXPIRY_HOURS)
            
            backup_files.append({
                "filename": file_path.name,
                "size_bytes": stat.st_size,
                "created_at": created_time.isoformat(),
                "expires_at": expires_time.isoformat(),
                "expired": datetime.utcnow() > expires_time,
                "format": file_path.suffix[1:]  # Remove the dot
            })
        
        for file_path in self.backup_dir.glob("gps_backup_*.csv"):
            stat = file_path.stat()
            created_time = datetime.fromtimestamp(stat.st_ctime)
            expires_time = created_time + timedelta(hours=BACKUP_EXPIRY_HOURS)
            
            backup_files.append({
                "filename": file_path.name,
                "size_bytes": stat.st_size,
                "created_at": created_time.isoformat(),
                "expires_at": expires_time.isoformat(),
                "expired": datetime.utcnow() > expires_time,
                "format": file_path.suffix[1:]  # Remove the dot
            })
        
        return sorted(backup_files, key=lambda x: x["created_at"], reverse=True)
    
    def cleanup_expired_backups(self):
        """Remove expired backup files"""
        current_time = datetime.utcnow()
        removed_count = 0
        
        for file_path in self.backup_dir.glob("gps_backup_*"):
            stat = file_path.stat()
            created_time = datetime.fromtimestamp(stat.st_ctime)
            expires_time = created_time + timedelta(hours=BACKUP_EXPIRY_HOURS)
            
            if current_time > expires_time:
                try:
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"Removed expired backup: {file_path.name}")
                except Exception as e:
                    logger.error(f"Error removing expired backup {file_path.name}: {str(e)}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired backup files")
    
    def get_backup_file_path(self, filename: str) -> Path:
        """Get the full path to a backup file"""
        return self.backup_dir / filename

# Global backup manager instance
backup_manager = BackupManager()

async def handle_database_management(usage_percentage: float) -> bool:
    """Handle database management based on usage percentage
    
    Returns:
        bool: True if any action was taken, False otherwise
    """
    action_taken = False
    
    try:
        if usage_percentage >= 95.0:
            # Emergency purge - remove 50% of oldest data immediately
            logger.critical(f"EMERGENCY PURGE: Database at {usage_percentage:.1f}% - purging 50% of old data")
            
            async with AsyncSessionLocal() as db:
                deleted_count = await delete_oldest_records(db, 50.0)
                await db.commit()
                logger.critical(f"Emergency purge completed: {deleted_count} records deleted")
                action_taken = True
                
        elif usage_percentage >= 90.0:
            # Create backup and purge 25% of oldest data
            logger.warning(f"AUTO BACKUP: Database at {usage_percentage:.1f}% - creating backup and purging 25% of old data")
            
            # Create backup first
            backup_filename = await backup_manager.create_backup("json")
            logger.info(f"Backup created: {backup_filename}")
            
            # Then purge old data
            async with AsyncSessionLocal() as db:
                deleted_count = await delete_oldest_records(db, 25.0)
                await db.commit()
                logger.warning(f"Auto purge completed: {deleted_count} records deleted after backup")
                action_taken = True
        
        # Always cleanup expired backups
        backup_manager.cleanup_expired_backups()
        
        return action_taken
        
    except Exception as e:
        logger.error(f"Error in database management: {str(e)}")
        return False