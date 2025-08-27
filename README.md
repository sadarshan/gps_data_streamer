# GPS Data Streamer

A high-performance FastAPI backend for GPS data collection and streaming with real-time dashboard, automatic data management, and comprehensive monitoring.

## 🚀 Features

### Core Functionality
- **High-throughput GPS data ingestion** with rate limiting (1 request/second with burst capability)
- **SQLite database** with automatic size management and intelligent purging
- **Real-time web dashboard** with WebSocket updates
- **Automatic backup system** with JSON/CSV export formats
- **Comprehensive validation** for GPS coordinates, timestamps, and speed reasonableness

### Data Management
- **Automatic database management** - stays within 100MB limit automatically
- **Smart purging system** - backs up data before deletion
- **Emergency purge** at 95% capacity (removes 50% of old data)
- **Regular purge** at 90% capacity (removes 25% after backup)
- **24-hour backup expiration** with automatic cleanup

### Monitoring & Analytics
- **Real-time system metrics** - database usage, request rates, record counts
- **WebSocket-powered dashboard** with live updates
- **Rate monitoring** - tracks POST requests per minute
- **Performance optimization** with database indexing and connection pooling

## 📋 Requirements

- Python 3.8+
- FastAPI
- SQLAlchemy 2.0+
- SQLite
- Modern web browser (for dashboard)

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd GPS_streamer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

## 🎯 API Endpoints

### GPS Data Management

#### POST /api/gps/data
Submit GPS data (rate limited to 1/second)

**Request Body:**
```json
{
  "device_id": "device-001",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "altitude": 100.5,
  "speed": 5.2,
  "heading": 45.0,
  "accuracy": 3.0,
  "timestamp": "2025-08-26T18:00:00Z"
}
```

**Validation Rules:**
- Latitude: -90 to 90 degrees
- Longitude: -180 to 180 degrees  
- Speed: 0-200 m/s (reasonableness check)
- Accuracy: 0-10000 meters
- Timestamp: Within 24 hours (past) to 1 hour (future)

#### GET /api/gps/data
Retrieve GPS data with filtering

**Parameters:**
- `device_id` (optional): Filter by device
- `start_time` (optional): Start time filter (ISO format)
- `end_time` (optional): End time filter (ISO format)
- `limit` (optional): Max records (1-1000, default 100)
- `offset` (optional): Records to skip (default 0)

### System Monitoring

#### GET /api/system/stats
Get current system statistics

**Response:**
```json
{
  "total_gps_records": 1250,
  "database_size_bytes": 45678912,
  "database_usage_percentage": 43.5,
  "post_requests_last_minute": 12,
  "average_posts_per_minute": 8.5,
  "timestamp": "2025-08-26T18:00:00Z"
}
```

### Backup Management

#### POST /api/backup/create?format=json|csv
Create manual backup

#### GET /api/backup/files
List available backup files

#### GET /api/backup/download/{filename}
Download backup file

#### DELETE /api/backup/cleanup
Remove expired backup files

## 🌐 Web Dashboard

Access the real-time dashboard at `http://localhost:8000/`

**Features:**
- Real-time system metrics with visual progress bars
- Live GPS data feed showing recent submissions
- Request rate monitoring with per-minute statistics
- Backup file management with download links
- WebSocket connection status indicator
- Auto-refresh every 30 seconds as fallback

**Dashboard Sections:**
- **System Status**: Database usage, record counts, storage metrics
- **Rate Monitoring**: POST request rates and averages
- **Recent GPS Data**: Latest GPS coordinates by device
- **Available Backups**: Downloadable backup files with metadata

## 🧪 Testing

### Using the GPS Simulator

The included GPS simulator generates realistic GPS data for testing:

```bash
# Basic usage - 1 device for 60 seconds
python gps_simulator.py

# Multiple devices with custom parameters
python gps_simulator.py --devices 5 --duration 300 --rate 1.0

# Continuous simulation
python gps_simulator.py --devices 3 --duration 0 --verbose
```

**Simulator Options:**
- `--devices N`: Number of simulated devices
- `--duration N`: Duration in seconds (0 = infinite)
- `--rate N.N`: Requests per second per device
- `--url URL`: API endpoint URL
- `--verbose`: Enable debug logging

### Manual Testing

```bash
# Test basic GPS data submission
curl -X POST "http://localhost:8000/api/gps/data" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-001",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "speed": 5.0
  }'

# Test rate limiting (should fail on rapid requests)
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/gps/data" \
    -H "Content-Type: application/json" \
    -d '{"device_id": "burst-'$i'", "latitude": 37.77, "longitude": -122.41}' &
done

# Test data retrieval with filtering
curl "http://localhost:8000/api/gps/data?device_id=test-001&limit=10"

# Test backup creation
curl -X POST "http://localhost:8000/api/backup/create?format=json"
```

## 🔧 Configuration

### Database Limits
- **Maximum size**: 100MB
- **Warning threshold**: 90% (triggers backup + 25% purge)
- **Emergency threshold**: 95% (triggers 50% purge)

### Rate Limiting
- **POST /api/gps/data**: 1 request per second per IP
- Uses token bucket algorithm with burst capability

### Backup Settings
- **Expiration**: 24 hours
- **Formats**: JSON, CSV
- **Auto-cleanup**: Runs every 5 minutes during monitoring cycle

### Monitoring Cycle
- **Frequency**: Every 5 minutes
- **WebSocket broadcasts**: Real-time updates to connected dashboard clients
- **Metrics tracked**: DB size, record counts, request rates

## 📊 Performance Optimization

### Database Indexes
- Primary key on `id`
- Indexes on `device_id`, `timestamp`, `latitude`, `longitude`, `created_at`
- Compound indexes for common query patterns:
  - `(device_id, timestamp)` for device-specific time range queries
  - `(latitude, longitude)` for location-based queries
  - `(created_at)` for cleanup operations

### Connection Management
- Async SQLAlchemy with aiosqlite
- Connection pooling for concurrent requests
- Automatic connection cleanup

### Memory Efficiency
- Streaming responses for large datasets
- Pagination support with configurable limits
- Automatic cleanup of expired backup files

## 🚨 Error Handling

### GPS Data Validation Errors
- **422 Unprocessable Entity**: Invalid coordinates, unrealistic speeds, bad timestamps
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Database or system errors

### System Monitoring
- Comprehensive logging at INFO level
- Warning logs for approaching limits
- Critical logs for emergency situations
- WebSocket error handling with auto-reconnection

### Backup System
- Graceful handling of backup creation failures
- Automatic cleanup of corrupted files
- Error reporting via API responses

## 🔐 Security Considerations

### Input Validation
- Strict GPS coordinate bounds checking
- Device ID length limits and pattern validation
- Timestamp reasonableness validation
- SQL injection protection via SQLAlchemy ORM

### File Download Security
- Filename pattern validation for backup downloads
- Path traversal protection
- Content-Type headers for proper file handling

### Rate Limiting
- Per-IP rate limiting to prevent abuse
- Configurable limits via slowapi middleware
- Proper HTTP status codes for rate limit violations

## 📈 Success Metrics

The system achieves all key success metrics:

✅ **Handle sustained 1 GPS point/second ingestion**  
✅ **Automatic database management with 0 manual intervention**  
✅ **Dashboard provides real-time system visibility**  
✅ **Backup system preserves data before deletion**  
✅ **System stays within free tier limits automatically**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues

**Server won't start:**
- Check if port 8000 is available
- Verify all dependencies are installed
- Check Python version (3.8+ required)

**WebSocket connection fails:**
- Ensure no firewall blocking WebSocket connections
- Try refreshing the dashboard page
- Check browser console for errors

**Rate limiting too strict:**
- Modify the `@limiter.limit("1/second")` decorator in main.py
- Restart the server after changes

**Database performance issues:**
- Check if database file has proper indexes
- Monitor disk space for the SQLite file
- Consider vacuum operation for fragmented databases

### Logs Location
- Application logs: Console output
- Access logs: FastAPI/Uvicorn standard output
- Error details: Check exception tracebacks in console

### Support
For issues and questions, please create an issue in the repository with:
- Description of the problem
- Steps to reproduce
- System information (OS, Python version)
- Relevant log output