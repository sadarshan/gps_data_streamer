"""
WebSocket Connection Manager - Real-time GPS data streaming
Features: Connection pooling, broadcast messaging, connection health monitoring
"""
import json
import asyncio
import logging
from typing import List, Dict, Any, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Real-time WebSocket connection manager
    - Multiple client connections
    - Broadcast messaging for GPS updates
    - Connection health monitoring
    - Automatic cleanup of dead connections
    """
    
    def __init__(self):
        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []
        self.connection_stats: Dict[str, Any] = {
            "total_connections": 0,
            "current_connections": 0,
            "total_messages_sent": 0,
            "connection_errors": 0
        }
        
        logger.info("🔌 WebSocket manager initialized")
    
    async def connect(self, websocket: WebSocket):
        """
        Accept new WebSocket connection
        - Add to active connections pool
        - Send welcome message with system status
        - Update connection statistics
        """
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            self.connection_stats["total_connections"] += 1
            self.connection_stats["current_connections"] = len(self.active_connections)
            
            client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
            logger.info(f"🔗 WebSocket connected: {client_info} (Total: {len(self.active_connections)})")
            
            # Send welcome message with connection info
            welcome_message = {
                "type": "connection_established",
                "message": "Connected to GPS Data Streamer",
                "timestamp": datetime.utcnow().isoformat(),
                "client_id": client_info,
                "features": [
                    "Real-time GPS updates",
                    "System status monitoring",
                    "Database capacity alerts"
                ]
            }
            await self._send_to_connection(websocket, welcome_message)
            
        except Exception as e:
            logger.error(f"💥 WebSocket connection error: {e}")
            self.connection_stats["connection_errors"] += 1
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection
        - Clean up from active connections
        - Update connection statistics
        - Log disconnection event
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_stats["current_connections"] = len(self.active_connections)
            
            client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
            logger.info(f"🔌 WebSocket disconnected: {client_info} (Remaining: {len(self.active_connections)})")
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients
        - Send to all active connections
        - Handle connection failures gracefully
        - Update message statistics
        """
        if not self.active_connections:
            return  # No active connections to broadcast to
        
        # Add timestamp to message
        message["broadcast_timestamp"] = datetime.utcnow().isoformat()
        
        # Track connections to remove (failed sends)
        connections_to_remove = []
        successful_sends = 0
        
        # Send to all active connections
        for websocket in self.active_connections.copy():  # Use copy to avoid modification during iteration
            try:
                await self._send_to_connection(websocket, message)
                successful_sends += 1
            except Exception as e:
                logger.warning(f"⚠️  WebSocket send failed, removing connection: {e}")
                connections_to_remove.append(websocket)
                self.connection_stats["connection_errors"] += 1
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            self.disconnect(websocket)
        
        # Update statistics
        self.connection_stats["total_messages_sent"] += successful_sends
        
        if successful_sends > 0:
            logger.debug(f"📡 Broadcast sent to {successful_sends} clients: {message['type']}")
    
    async def _send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send message to specific WebSocket connection
        - JSON serialization with error handling
        - Connection validation
        - Timeout handling for slow clients
        """
        try:
            # Serialize message with proper datetime handling
            message_json = json.dumps(message, default=str, ensure_ascii=False)
            
            # Send with timeout to prevent blocking
            await asyncio.wait_for(
                websocket.send_text(message_json),
                timeout=5.0  # 5-second timeout
            )
        except asyncio.TimeoutError:
            raise Exception("WebSocket send timeout")
        except WebSocketDisconnect:
            raise Exception("WebSocket disconnected")
        except Exception as e:
            raise Exception(f"WebSocket send error: {e}")
    
    async def broadcast_gps_update(self, gps_data: Dict[str, Any]):
        """
        Broadcast GPS data update to all clients
        - Specialized method for GPS updates
        - Enhanced with location and speed information
        - Real-time dashboard updates
        """
        message = {
            "type": "gps_update",
            "data": gps_data,
            "update_category": "live_tracking"
        }
        
        await self.broadcast(message)
    
    async def broadcast_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """
        Broadcast system alerts and notifications
        - Database capacity warnings
        - System maintenance notifications
        - Error alerts
        """
        alert_message = {
            "type": "system_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(alert_message)
        logger.info(f"📢 System alert broadcasted: {alert_type} ({severity})")
    
    async def broadcast_system_stats(self, stats: Dict[str, Any]):
        """
        Broadcast real-time system statistics
        - Database usage and capacity
        - Request rates and performance
        - Connection and monitoring data
        """
        message = {
            "type": "system_stats",
            "stats": stats,
            "update_category": "monitoring"
        }
        
        await self.broadcast(message)
    
    async def send_ping_to_all(self):
        """
        Send ping to all connections to check health
        - Keep-alive mechanism
        - Detect and cleanup dead connections
        - Maintain connection pool health
        """
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat(),
            "server_status": "healthy"
        }
        
        await self.broadcast(ping_message)
        logger.debug(f"💓 Ping sent to {len(self.active_connections)} connections")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive WebSocket connection statistics
        - Current and historical connection counts
        - Message transmission statistics
        - Error rates and connection health
        """
        return {
            **self.connection_stats,
            "active_connections": len(self.active_connections),
            "connection_health": "healthy" if len(self.active_connections) >= 0 else "no_connections",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def cleanup_stale_connections(self):
        """
        Periodic cleanup of stale/dead connections
        - Send ping to detect dead connections
        - Remove unresponsive connections
        - Maintain connection pool health
        """
        if not self.active_connections:
            return
        
        logger.debug("🧹 Performing WebSocket connection cleanup...")
        
        # Test connections with ping
        await self.send_ping_to_all()
        
        # The actual cleanup happens during broadcast if connections fail
        logger.debug(f"✅ WebSocket cleanup completed - {len(self.active_connections)} active connections")
    
    async def start_periodic_cleanup(self):
        """
        Start background task for periodic connection cleanup
        - Runs every 5 minutes
        - Maintains connection health
        - Prevents memory leaks from dead connections
        """
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                await self.cleanup_stale_connections()
            except Exception as e:
                logger.error(f"💥 WebSocket cleanup task error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

# Global WebSocket manager instance
ws_manager = WebSocketManager()

# Start cleanup task when module is imported
async def init_websocket_manager():
    """Initialize WebSocket manager with background tasks"""
    asyncio.create_task(ws_manager.start_periodic_cleanup())
    logger.info("🔄 WebSocket periodic cleanup task started")