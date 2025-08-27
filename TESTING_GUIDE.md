# GPS Data Streamer - Complete Testing Guide

Your GPS data format is now fully supported! Here's how to test everything locally.

## 🚀 Quick Start Testing

### 1. Start the Server
```bash
# In your GPS_streamer directory
python main.py
```

Wait for this message:
```
✅ MongoDB connected successfully (method 1)
📊 Database: gps_streamer
✅ GPS Data Streamer started successfully
```

### 2. Quick Test with Your Format
```bash
curl -X POST "http://localhost:8000/api/gps/data" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 183,
    "device_id": "darshan_002",    
    "frame_time": "21/07/24 00:12:24",
    "lattitude": 12.906504631042,
    "longitude": 77.640480041504,
    "url": "http://maps.google.com/maps?q=12.906505,77.640480",
    "sat_tked": 12,
    "speed": 15,
    "altitude": 100.5,
    "heading": 45.0,
    "accuracy": 3.0,
    "created_at": "",
    "additional_data": null
  }'
```

## 📋 Comprehensive Test Suite

### Option 1: Automated Test Runner
```bash
# Run all tests automatically
python run_tests.py
```

### Option 2: Individual Test Scripts

#### A. Test Your JSON Format
```bash
cd tests
python test_your_format.py
```

#### B. Complete API Test Suite
```bash
python tests/test_all_apis.py
```

#### C. Load and Performance Testing
```bash
python tests/load_test.py
```

#### D. WebSocket Real-time Testing
```bash
python tests/websocket_test.py
```

### Option 3: Manual curl Tests
```bash
# Quick manual tests with curl
./curl_tests.sh
```

## 🌐 Dashboard Testing

1. **Open Dashboard**: http://localhost:8000
2. **Check Connection**: Should show "Connected" with green indicator
3. **Submit Data**: Use any of the test scripts above
4. **Watch Real-time Updates**: Dashboard should update automatically

## 🧪 What Each Test Covers

### 1. Your JSON Format Test (`test_your_format.py`)
- ✅ Your exact JSON structure
- ✅ Multiple devices (darshan_001, darshan_002, darshan_003)
- ✅ Field validation (lattitude, sat_tked, frame_time, etc.)
- ✅ Edge cases and error handling

### 2. Complete API Test (`test_all_apis.py`)
- ✅ All endpoints (GPS data, system stats, backups)
- ✅ Rate limiting (1 request/second)
- ✅ Data validation and error responses
- ✅ Backup creation and download
- ✅ Filtering and pagination

### 3. Load Test (`load_test.py`)
- ✅ Sustained load with multiple devices
- ✅ Concurrent request handling
- ✅ Rate limiting under pressure
- ✅ Response time analysis
- ✅ System performance metrics

### 4. WebSocket Test (`websocket_test.py`)
- ✅ Real-time dashboard connections
- ✅ Live GPS data updates
- ✅ System alerts and statistics
- ✅ Multiple WebSocket clients

### 5. curl Test (`curl_tests.sh`)
- ✅ Manual testing with command line
- ✅ Your exact data format
- ✅ Quick verification of all endpoints
- ✅ Rate limiting demonstration

## 📊 Expected Results

### ✅ Successful GPS Submission Response:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "device_sequence_id": 183,
  "device_id": "darshan_002",
  "frame_time": "21/07/24 00:12:24",
  "lattitude": 12.906504631042,
  "longitude": 77.640480041504,
  "url": "http://maps.google.com/maps?q=12.906505,77.640480",
  "sat_tked": 12,
  "speed": 15,
  "altitude": 100.5,
  "heading": 45.0,
  "accuracy": 3.0,
  "timestamp": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T12:00:05Z",
  "additional_data": null,
  "speed_ms": 4.17,
  "distance_from_origin": 1428.35
}
```

### 📈 System Statistics Response:
```json
{
  "total_gps_records": 1250,
  "database_size_bytes": 45678912,
  "database_usage_percentage": 43.5,
  "post_requests_last_minute": 12,
  "average_posts_per_minute": 8.5,
  "database_size_mb": 43.54,
  "capacity_status": "OK"
}
```

## ⚡ Performance Expectations

- **Response Time**: < 200ms for GPS data submission
- **Rate Limiting**: 1 request/second per IP (HTTP 429 for excess)
- **Validation**: Invalid coordinates/speed rejected with HTTP 422
- **WebSocket**: Real-time updates within 100ms
- **Database**: Automatic purging at 90% capacity

## 🔍 Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is busy
lsof -i :8000

# Kill existing processes
kill -9 $(lsof -t -i:8000)
```

### MongoDB Connection Issues
- Verify `.env` file has correct MongoDB URLs
- Check internet connection
- Ensure MongoDB Atlas allows connections from your IP

### Rate Limiting Too Strict
- Modify `@limiter.limit("1/second")` in main.py
- Restart server after changes

### WebSocket Connection Fails
- Check browser console for errors
- Verify no firewall blocking WebSocket connections
- Try refreshing the dashboard page

## 🎯 Key Validation Rules

Your JSON format supports these validations:

- **lattitude**: -90 to +90, rejects exact 0.0
- **longitude**: -180 to +180, rejects exact 0.0  
- **speed**: 0 to 720 km/h maximum
- **sat_tked**: 0 to 50 satellites
- **accuracy**: 0 to 10,000 meters
- **heading**: 0 to 359.999 degrees
- **device_id**: 1-50 characters

## 📱 Testing on Different Scenarios

### Multiple Devices
```python
devices = ["darshan_001", "darshan_002", "darshan_003", "darshan_004"]
# Each device can submit data independently
```

### High Frequency (with rate limits)
```python
# Respects 1 request/second limit
for i in range(10):
    submit_gps_data()
    time.sleep(1.1)  # Just over 1 second
```

### Batch Testing
```bash
# Use the load test for sustained traffic
python tests/load_test.py
```

## 🌍 Production Readiness

After all tests pass:
- ✅ Your JSON format is fully supported
- ✅ Rate limiting prevents abuse
- ✅ Data validation ensures quality
- ✅ Real-time dashboard works
- ✅ Backup system operational
- ✅ MongoDB Atlas integration stable

## 🚀 Next Steps

1. **Run Tests**: Use `python run_tests.py`
2. **Check Dashboard**: http://localhost:8000
3. **Review API Docs**: http://localhost:8000/docs
4. **Deploy to Render**: Your code is ready for production

## 📞 Support

If any tests fail:
1. Check the error messages in test output
2. Verify server is running and responding
3. Check MongoDB connection in server logs
4. Ensure `.env` file is configured correctly

Your GPS Data Streamer is now ready for comprehensive testing with your exact JSON format! 🎉