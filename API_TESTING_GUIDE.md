# GPS Data Streamer - Complete API Testing Guide

## 🚀 Quick Setup

1. **Replace YOUR_PASSWORD_HERE in .env file** with your actual MongoDB Atlas password
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Start the server**: `python main.py`
4. **Access dashboard**: http://localhost:8000

---

## 📍 Available APIs

### 🌐 Web Interface
- **Dashboard**: `GET /` - Real-time web dashboard with live updates
- **API Docs**: `GET /docs` - Interactive Swagger documentation
- **Alternative Docs**: `GET /redoc` - ReDoc documentation

### 📊 GPS Data APIs

#### 1. Submit GPS Data
```bash
POST /api/gps/data
Content-Type: application/json
Rate Limit: 1 request/second per IP
```

**Request Body:**
```json
{
  "device_id": "device_001",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "altitude": 100.5,
  "speed": 15.5,
  "heading": 180.0,
  "accuracy": 5.0,
  "timestamp": "2024-01-01T12:00:00Z",
  "additional_data": "{\"battery\": 85, \"signal_strength\": 95}"
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "device_id": "device_001",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "altitude": 100.5,
  "speed": 15.5,
  "speed_kmh": 55.8,
  "heading": 180.0,
  "accuracy": 5.0,
  "timestamp": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T12:00:05Z",
  "distance_from_origin": 4182.25,
  "additional_data": "{\"battery\": 85, \"signal_strength\": 95}"
}
```

#### 2. Retrieve GPS Data
```bash
GET /api/gps/data
```

**Query Parameters:**
- `device_id` (optional): Filter by specific device
- `start_time` (optional): ISO datetime string
- `end_time` (optional): ISO datetime string  
- `limit` (optional): 1-1000, default 100
- `offset` (optional): Skip records, default 0

**Examples:**
```bash
# Get all data (last 100 records)
GET /api/gps/data

# Get data for specific device
GET /api/gps/data?device_id=device_001

# Get data with time range
GET /api/gps/data?start_time=2024-01-01T00:00:00Z&end_time=2024-01-01T23:59:59Z

# Get data with pagination
GET /api/gps/data?limit=50&offset=100
```

### 📈 System Monitoring APIs

#### 3. System Statistics
```bash
GET /api/system/stats
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "timestamp": "2024-01-01T12:00:00Z",
  "total_gps_records": 1250,
  "database_size_bytes": 45678912,
  "database_usage_percentage": 43.5,
  "post_requests_last_minute": 12,
  "average_posts_per_minute": 8.5,
  "database_size_mb": 43.54,
  "capacity_status": "OK"
}
```

### 💾 Backup Management APIs

#### 4. Create Manual Backup
```bash
POST /api/backup/create?format=json
POST /api/backup/create?format=csv
```

**Response:**
```json
{
  "message": "Backup created successfully",
  "filename": "gps_backup_20240101_120000.json",
  "format": "json",
  "expires_in_hours": 24
}
```

#### 5. List Backup Files
```bash
GET /api/backup/files
```

**Response:**
```json
{
  "backup_files": [
    {
      "filename": "gps_backup_20240101_120000.json",
      "format": "json",
      "size_bytes": 1024768,
      "size_mb": 1.02,
      "created_at": "2024-01-01T12:00:00Z",
      "expires_at": "2024-01-02T12:00:00Z",
      "expired": false,
      "time_until_expiry": "23:45:30"
    }
  ],
  "total_files": 1,
  "active_files": 1
}
```

#### 6. Download Backup File
```bash
GET /api/backup/download/{filename}
```

#### 7. Cleanup Expired Backups
```bash
DELETE /api/backup/cleanup
```

### 🔌 WebSocket API

#### 8. Real-time Updates
```bash
WebSocket: ws://localhost:8000/ws
```

**Message Types Received:**
- `connection_established` - Welcome message
- `gps_update` - New GPS data submitted
- `system_stats` - Real-time system statistics
- `system_alert` - Capacity warnings/alerts
- `ping` - Keep-alive messages

### ⚕️ Health Check

#### 9. Health Status
```bash
GET /health
```

---

## 🧪 Complete Testing Script

Save this as `test_all_apis.py`:

```python
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_all_apis():
    print("🧪 GPS Data Streamer - Complete API Test")
    print("=" * 50)
    
    # 1. Test Health Check
    print("\n1️⃣  Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 2. Test GPS Data Submission
    print("\n2️⃣  Testing GPS Data Submission...")
    gps_data = {
        "device_id": "test_device_001",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "altitude": 100.5,
        "speed": 15.5,
        "heading": 180.0,
        "accuracy": 5.0,
        "additional_data": json.dumps({"battery": 85, "signal_strength": 95})
    }
    
    response = requests.post(f"{BASE_URL}/api/gps/data", json=gps_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        submitted_data = response.json()
        print(f"✅ GPS data submitted successfully!")
        print(f"ID: {submitted_data['id']}")
        print(f"Speed: {submitted_data['speed']} m/s ({submitted_data['speed_kmh']} km/h)")
    else:
        print(f"❌ Error: {response.text}")
    
    # 3. Test Rate Limiting
    print("\n3️⃣  Testing Rate Limiting...")
    print("Sending rapid requests (should get rate limited)...")
    for i in range(3):
        test_data = {
            "device_id": f"rate_test_{i}",
            "latitude": 37.7749 + i * 0.001,
            "longitude": -122.4194 + i * 0.001,
            "speed": 10.0
        }
        response = requests.post(f"{BASE_URL}/api/gps/data", json=test_data)
        print(f"Request {i+1}: Status {response.status_code}")
        if response.status_code == 429:
            print("✅ Rate limiting working!")
            break
        time.sleep(0.1)
    
    # 4. Test Data Retrieval
    print("\n4️⃣  Testing Data Retrieval...")
    response = requests.get(f"{BASE_URL}/api/gps/data?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {len(data)} GPS records")
        if data:
            print(f"Latest record: Device {data[0]['device_id']} at ({data[0]['latitude']}, {data[0]['longitude']})")
    
    # 5. Test Filtered Data Retrieval
    print("\n5️⃣  Testing Filtered Data Retrieval...")
    response = requests.get(f"{BASE_URL}/api/gps/data?device_id=test_device_001")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {len(data)} records for test_device_001")
    
    # 6. Test System Statistics
    print("\n6️⃣  Testing System Statistics...")
    response = requests.get(f"{BASE_URL}/api/system/stats")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ System Stats Retrieved:")
        print(f"   📊 Total Records: {stats.get('total_gps_records', 0):,}")
        print(f"   💾 Database Size: {stats.get('database_size_mb', 0):.2f} MB")
        print(f"   📈 Usage: {stats.get('database_usage_percentage', 0):.1f}%")
        print(f"   ⚡ Requests/min: {stats.get('post_requests_last_minute', 0)}")
    
    # 7. Test Backup Creation
    print("\n7️⃣  Testing Backup Creation...")
    response = requests.post(f"{BASE_URL}/api/backup/create?format=json")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        backup_info = response.json()
        print(f"✅ Backup created: {backup_info['filename']}")
        backup_filename = backup_info['filename']
    else:
        backup_filename = None
    
    # 8. Test Backup File Listing
    print("\n8️⃣  Testing Backup File Listing...")
    response = requests.get(f"{BASE_URL}/api/backup/files")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        backup_data = response.json()
        print(f"✅ Found {backup_data['total_files']} backup files")
        print(f"   Active files: {backup_data['active_files']}")
        if backup_data['backup_files']:
            latest = backup_data['backup_files'][0]
            print(f"   Latest: {latest['filename']} ({latest['size_mb']} MB)")
    
    # 9. Test Backup Download (if we created one)
    if backup_filename:
        print("\n9️⃣  Testing Backup Download...")
        response = requests.get(f"{BASE_URL}/api/backup/download/{backup_filename}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Backup download successful ({len(response.content)} bytes)")
        else:
            print(f"❌ Download failed: {response.text}")
    
    # 10. Test Invalid GPS Data (Validation)
    print("\n🔟 Testing GPS Data Validation...")
    invalid_data = {
        "device_id": "validation_test",
        "latitude": 91.0,  # Invalid: > 90
        "longitude": -200.0,  # Invalid: < -180
        "speed": 300.0  # Invalid: > 200 m/s
    }
    
    response = requests.post(f"{BASE_URL}/api/gps/data", json=invalid_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 422:
        print("✅ Validation working - rejected invalid data")
        print(f"Error: {response.json().get('detail', 'Validation error')}")
    
    print("\n" + "=" * 50)
    print("🎉 API Testing Complete!")
    print(f"📍 Dashboard: {BASE_URL}")
    print(f"📚 API Docs: {BASE_URL}/docs")

if __name__ == "__main__":
    test_all_apis()
```

---

## 🚀 Manual Testing Commands

### Basic GPS Data Submission
```bash
curl -X POST "http://localhost:8000/api/gps/data" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "curl_test_001",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "speed": 25.0,
    "heading": 45.0,
    "accuracy": 3.0
  }'
```

### Multiple Device Simulation
```bash
# Device 1 - San Francisco
curl -X POST "http://localhost:8000/api/gps/data" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "sf_device", "latitude": 37.7749, "longitude": -122.4194, "speed": 15.5}'

# Device 2 - New York
curl -X POST "http://localhost:8000/api/gps/data" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "ny_device", "latitude": 40.7128, "longitude": -74.0060, "speed": 22.3}'

# Device 3 - London
curl -X POST "http://localhost:8000/api/gps/data" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "london_device", "latitude": 51.5074, "longitude": -0.1278, "speed": 18.7}'
```

### Rate Limiting Test
```bash
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/gps/data" \
    -H "Content-Type: application/json" \
    -d "{\"device_id\": \"burst_$i\", \"latitude\": 37.77, \"longitude\": -122.41}" &
done
wait
```

### Data Retrieval Tests
```bash
# Get all data
curl "http://localhost:8000/api/gps/data"

# Get specific device data
curl "http://localhost:8000/api/gps/data?device_id=sf_device"

# Get with pagination
curl "http://localhost:8000/api/gps/data?limit=10&offset=0"

# Get system stats
curl "http://localhost:8000/api/system/stats"

# Create backup
curl -X POST "http://localhost:8000/api/backup/create?format=json"

# List backups
curl "http://localhost:8000/api/backup/files"
```

---

## 🔍 What to Verify

1. **✅ GPS Data Submission**: Valid data gets stored, invalid data gets rejected
2. **✅ Rate Limiting**: 1 request/second limit enforced
3. **✅ Real-time Dashboard**: WebSocket updates work
4. **✅ Data Filtering**: Device, time, pagination filters work
5. **✅ System Monitoring**: Database usage tracking
6. **✅ Backup System**: JSON/CSV export and download
7. **✅ Validation Rules**: Coordinate bounds, speed limits, timestamps
8. **✅ Database Management**: Automatic cleanup at capacity limits

---

## 📱 Dashboard Features to Test

1. **Connection Status**: Should show "Connected" with green indicator
2. **Live GPS Updates**: New submissions appear in real-time
3. **System Metrics**: Database usage, request rates
4. **Alerts**: Capacity warnings (when database reaches 90%+)

Replace `YOUR_PASSWORD_HERE` in the `.env` file and run `python main.py` to start testing!