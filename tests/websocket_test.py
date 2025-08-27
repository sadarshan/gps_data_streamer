"""
WebSocket Real-time Testing
Test the real-time dashboard WebSocket functionality
"""
import asyncio
import websockets
import json
import requests
import time
import threading
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

class WebSocketTester:
    def __init__(self):
        self.received_messages = []
        self.connected = False
        
    async def websocket_client(self, duration_seconds=30):
        """Connect to WebSocket and listen for messages"""
        print(f"🔌 Connecting to WebSocket: {WS_URL}")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                self.connected = True
                print("✅ WebSocket connected successfully")
                
                # Listen for messages
                start_time = time.time()
                while time.time() - start_time < duration_seconds:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        
                        try:
                            data = json.loads(message)
                            self.received_messages.append({
                                "timestamp": datetime.now(),
                                "data": data
                            })
                            
                            self.handle_websocket_message(data)
                        except json.JSONDecodeError:
                            print(f"⚠️  Received non-JSON message: {message}")
                            
                    except asyncio.TimeoutError:
                        # No message received, continue listening
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        print("❌ WebSocket connection closed")
                        break
                        
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            self.connected = False
    
    def handle_websocket_message(self, data):
        """Handle received WebSocket message"""
        message_type = data.get("type", "unknown")
        
        if message_type == "connection_established":
            print(f"🤝 Connection established: {data.get('message', '')}")
            
        elif message_type == "gps_update":
            gps_data = data.get("data", {})
            print(f"📍 GPS Update: Device {gps_data.get('device_id')} at "
                  f"({gps_data.get('lattitude'):.6f}, {gps_data.get('longitude'):.6f}) "
                  f"Speed: {gps_data.get('speed', 0)} km/h")
            
        elif message_type == "system_stats":
            stats = data.get("stats", {})
            db_info = stats.get("database", {})
            print(f"📊 System Stats: {db_info.get('total_records', 0):,} records, "
                  f"{db_info.get('usage_percentage', 0):.1f}% usage")
            
        elif message_type == "system_alert":
            severity = data.get("severity", "info")
            message = data.get("message", "")
            alert_type = data.get("alert_type", "")
            print(f"🚨 System Alert [{severity.upper()}]: {alert_type} - {message}")
            
        elif message_type == "ping":
            print("💓 Ping received from server")
            
        else:
            print(f"❓ Unknown message type: {message_type}")
    
    def send_test_gps_data(self, count=5):
        """Send GPS data to trigger WebSocket updates"""
        print(f"\n📡 Sending {count} GPS data points to trigger WebSocket updates...")
        
        base_data = {
            "device_id": "websocket_test_device",
            "lattitude": 12.906504631042,
            "longitude": 77.640480041504,
            "url": "http://maps.google.com/maps?q=12.906505,77.640480",
            "sat_tked": 12,
            "speed": 15,
            "altitude": 100.5,
            "heading": 45.0,
            "accuracy": 3.0,
            "created_at": "",
            "additional_data": None
        }
        
        for i in range(count):
            # Vary the data slightly
            test_data = base_data.copy()
            test_data["id"] = 200 + i
            test_data["lattitude"] += i * 0.0001
            test_data["longitude"] += i * 0.0001
            test_data["speed"] = 15 + (i * 5)
            test_data["frame_time"] = datetime.now().strftime("%d/%m/%y %H:%M:%S")
            
            print(f"   Sending data point {i+1}...")
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/gps/data",
                    json=test_data,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Data point {i+1} sent successfully")
                else:
                    print(f"   ❌ Data point {i+1} failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error sending data point {i+1}: {e}")
            
            # Wait between requests to respect rate limiting
            time.sleep(2)
    
    def print_summary(self):
        """Print summary of WebSocket test"""
        print("\n" + "=" * 50)
        print("📊 WebSocket Test Summary")
        print("=" * 50)
        
        print(f"🔌 Connection Status: {'✅ Connected' if self.connected else '❌ Failed'}")
        print(f"📨 Total Messages Received: {len(self.received_messages)}")
        
        if self.received_messages:
            message_types = {}
            for msg in self.received_messages:
                msg_type = msg["data"].get("type", "unknown")
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            print("\n📋 Message Type Breakdown:")
            for msg_type, count in message_types.items():
                print(f"   {msg_type}: {count}")
            
            print(f"\n⏰ Test Duration: {(self.received_messages[-1]['timestamp'] - self.received_messages[0]['timestamp']).total_seconds():.1f} seconds")
        
        print("\n💡 Open http://localhost:8000 in your browser to see the live dashboard!")

async def run_websocket_test():
    """Run complete WebSocket test"""
    print("🚀 GPS Data Streamer - WebSocket Real-time Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            return
    except:
        print("❌ Cannot connect to server - make sure it's running on localhost:8000")
        return
    
    print("✅ Server is running")
    
    tester = WebSocketTester()
    
    # Create tasks for WebSocket client and GPS data sending
    websocket_task = asyncio.create_task(tester.websocket_client(duration_seconds=25))
    
    # Wait a bit for WebSocket to connect
    await asyncio.sleep(2)
    
    if tester.connected:
        # Send GPS data in a separate thread to not block the WebSocket
        def send_data():
            time.sleep(3)  # Wait a bit more
            tester.send_test_gps_data(count=3)
        
        data_thread = threading.Thread(target=send_data)
        data_thread.start()
        
        # Wait for WebSocket task to complete
        await websocket_task
        
        # Wait for data sending thread to complete
        data_thread.join()
    else:
        print("❌ WebSocket connection failed, skipping data transmission test")
    
    tester.print_summary()

def test_dashboard_manually():
    """Instructions for manual dashboard testing"""
    print("\n🌐 Manual Dashboard Testing Instructions:")
    print("=" * 50)
    print("1. Open http://localhost:8000 in your web browser")
    print("2. You should see the GPS Data Streamer dashboard")
    print("3. Check that the Connection Status shows 'Connected' (green)")
    print("4. Submit some GPS data using the API or test scripts")
    print("5. Watch for real-time updates in the dashboard:")
    print("   - Live GPS Data section should update")
    print("   - System Statistics should refresh")
    print("   - Connection status should remain stable")
    print("\n📱 Test on different devices/browsers:")
    print("   - Desktop browser")
    print("   - Mobile browser") 
    print("   - Multiple tabs (test multiple WebSocket connections)")

if __name__ == "__main__":
    print("Starting WebSocket test...")
    
    # Run the async WebSocket test
    asyncio.run(run_websocket_test())
    
    # Show manual testing instructions
    test_dashboard_manually()