"""
Backup System Manager - Automatic and manual GPS data backup
Features: JSON/CSV export, automatic expiration, file management, security validation
"""
import os
import json
import csv
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil

from database import get_db
from crud import get_all_gps_data_for_export

logger = logging.getLogger(__name__)

class BackupManager:
    """
    Comprehensive backup system for GPS data
    - Automatic and manual backup creation
    - Multiple export formats (JSON, CSV)
    - Automatic expiration and cleanup
    - Security validation for file access
    """
    
    def __init__(self, backup_directory: str = "backups"):
        self.backup_dir = Path(backup_directory)
        self.backup_dir.mkdir(exist_ok=True)
        self.expiration_hours = 24
        
        logger.info(f"📦 Backup system initialized - Directory: {self.backup_dir.absolute()}")
    
    async def create_backup(self, format: str = "json") -> str:
        """
        Create backup file in specified format
        - Exports all GPS data with metadata
        - Automatic filename generation with timestamp
        - Security validation for format parameter
        """
        if format not in ["json", "csv"]:
            raise ValueError(f"Unsupported backup format: {format}. Use 'json' or 'csv'")
        
        try:
            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"gps_backup_{timestamp}.{format}"
            filepath = self.backup_dir / filename
            
            logger.info(f"📦 Creating {format.upper()} backup: {filename}")
            
            # Fetch all GPS data
            db = get_db()
            gps_data = await get_all_gps_data_for_export(db)
            
            if not gps_data:
                logger.warning("⚠️  No GPS data found for backup")
                # Create empty backup with metadata
                backup_content = {
                    "metadata": self._generate_backup_metadata(0),
                    "data": []
                }
            else:
                logger.info(f"📊 Backing up {len(gps_data):,} GPS records")
                backup_content = {
                    "metadata": self._generate_backup_metadata(len(gps_data)),
                    "data": [self._serialize_gps_record(record) for record in gps_data]
                }
            
            # Write backup file
            if format == "json":
                await self._write_json_backup(filepath, backup_content)
            elif format == "csv":
                await self._write_csv_backup(filepath, backup_content)
            
            # Verify file creation
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Backup created successfully: {filename} ({file_size_mb:.2f} MB)")
            
            # Schedule automatic cleanup
            asyncio.create_task(self._schedule_file_expiration(filepath))
            
            return filename
            
        except Exception as e:
            logger.error(f"💥 Backup creation failed: {e}")
            raise
    
    async def _write_json_backup(self, filepath: Path, content: Dict[str, Any]):
        """Write GPS data backup in JSON format with proper formatting"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, default=str, ensure_ascii=False)
    
    async def _write_csv_backup(self, filepath: Path, content: Dict[str, Any]):
        """Write GPS data backup in CSV format with headers"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not content["data"]:
                # Empty file with headers only
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'device_sequence_id', 'device_id', 'frame_time', 'latitude', 
                    'longitude', 'url', 'sat_tked', 'speed', 'altitude', 'heading', 
                    'accuracy', 'timestamp', 'created_at', 'speed_ms', 'distance_from_origin', 
                    'additional_data'
                ])
                return
            
            # Write data with proper CSV formatting
            fieldnames = list(content["data"][0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in content["data"]:
                writer.writerow(record)
    
    def _generate_backup_metadata(self, record_count: int) -> Dict[str, Any]:
        """Generate backup metadata for tracking and validation"""
        return {
            "backup_created": datetime.utcnow().isoformat(),
            "backup_version": "2.0.0",
            "total_records": record_count,
            "export_type": "full_database_export",
            "expires_at": (datetime.utcnow() + timedelta(hours=self.expiration_hours)).isoformat(),
            "system_info": {
                "service": "GPS Data Streamer",
                "database": "MongoDB Atlas",
                "format_version": "v2"
            }
        }
    
    def _serialize_gps_record(self, record) -> Dict[str, Any]:
        """Convert GPS record to serializable dictionary"""
        return {
            "id": record.id,
            "device_sequence_id": getattr(record, 'device_sequence_id', None),
            "device_id": record.device_id,
            "frame_time": getattr(record, 'frame_time', None),
            "latitude": record.lattitude,  # Export as 'latitude' but get from 'lattitude'
            "longitude": record.longitude,
            "url": getattr(record, 'url', None),
            "sat_tked": getattr(record, 'sat_tked', None),
            "speed": record.speed,
            "altitude": record.altitude,
            "heading": record.heading,
            "accuracy": record.accuracy,
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "speed_ms": getattr(record, 'speed_ms', None),  # Computed field
            "distance_from_origin": getattr(record, 'distance_from_origin', None),  # Computed field
            "additional_data": record.additional_data
        }
    
    def get_backup_files(self) -> List[Dict[str, Any]]:
        """
        List all backup files with status and metadata
        - File information and sizes
        - Expiration status
        - Creation timestamps
        """
        backup_files = []
        
        for file_path in self.backup_dir.glob("gps_backup_*.json"):
            backup_files.append(self._get_file_info(file_path))
        
        for file_path in self.backup_dir.glob("gps_backup_*.csv"):
            backup_files.append(self._get_file_info(file_path))
        
        # Sort by creation time (newest first)
        backup_files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backup_files
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get comprehensive file information and status"""
        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        expires_at = created_at + timedelta(hours=self.expiration_hours)
        is_expired = datetime.utcnow() > expires_at
        
        return {
            "filename": file_path.name,
            "format": file_path.suffix[1:],  # Remove the dot
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "expired": is_expired,
            "time_until_expiry": str(expires_at - datetime.utcnow()) if not is_expired else "EXPIRED"
        }
    
    def get_backup_file_path(self, filename: str) -> Path:
        """
        Get secure file path with validation
        - Security: Validates filename format
        - Prevents directory traversal attacks
        """
        # Security validation
        if not filename.startswith("gps_backup_"):
            raise ValueError("Invalid backup filename format")
        
        if not (filename.endswith(".json") or filename.endswith(".csv")):
            raise ValueError("Invalid backup file extension")
        
        # Prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid characters in filename")
        
        return self.backup_dir / filename
    
    def cleanup_expired_backups(self) -> int:
        """
        Remove expired backup files
        - Automatic cleanup based on expiration time
        - Logs cleanup activity
        - Returns count of removed files
        """
        removed_count = 0
        current_time = datetime.utcnow()
        
        for backup_file in self.get_backup_files():
            if backup_file["expired"]:
                try:
                    file_path = self.backup_dir / backup_file["filename"]
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"🗑️  Removed expired backup: {backup_file['filename']}")
                except Exception as e:
                    logger.error(f"💥 Failed to remove expired backup {backup_file['filename']}: {e}")
        
        if removed_count > 0:
            logger.info(f"🧹 Cleanup completed - Removed {removed_count} expired backup files")
        
        return removed_count
    
    async def _schedule_file_expiration(self, filepath: Path):
        """
        Schedule automatic file deletion after expiration
        - Non-blocking background task
        - Automatic cleanup after 24 hours
        """
        try:
            # Wait for expiration time
            await asyncio.sleep(self.expiration_hours * 3600)  # Convert hours to seconds
            
            # Check if file still exists and remove it
            if filepath.exists():
                filepath.unlink()
                logger.info(f"🗑️  Auto-expired backup file: {filepath.name}")
        except Exception as e:
            logger.error(f"💥 Auto-expiration failed for {filepath.name}: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get backup storage statistics
        - Total storage used
        - File count by format
        - Expiration summary
        """
        backup_files = self.get_backup_files()
        
        total_size = sum(f["size_bytes"] for f in backup_files)
        active_files = [f for f in backup_files if not f["expired"]]
        expired_files = [f for f in backup_files if f["expired"]]
        
        json_files = [f for f in backup_files if f["format"] == "json"]
        csv_files = [f for f in backup_files if f["format"] == "csv"]
        
        return {
            "total_files": len(backup_files),
            "active_files": len(active_files),
            "expired_files": len(expired_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "formats": {
                "json": len(json_files),
                "csv": len(csv_files)
            },
            "backup_directory": str(self.backup_dir.absolute()),
            "expiration_hours": self.expiration_hours
        }
    
    async def create_automatic_backup(self):
        """
        Create automatic backup as part of system maintenance
        - Called by monitoring system
        - Creates JSON backup by default
        - Error handling for non-critical operation
        """
        try:
            filename = await self.create_backup("json")
            logger.info(f"🔄 Automatic backup created: {filename}")
            return filename
        except Exception as e:
            logger.error(f"⚠️  Automatic backup failed (non-critical): {e}")
            return None

# Global backup manager instance
backup_manager = BackupManager()