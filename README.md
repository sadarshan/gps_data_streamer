# GPS Data Streamer

A high-throughput GPS data ingestion system with real-time monitoring, automatic data management, and comprehensive backup capabilities. Optimized for deployment on Render with MongoDB Atlas.

## 🚀 Features

- **High-throughput GPS data ingestion** with rate limiting (1 request/second with burst capability)
- **Real-time web dashboard** with WebSocket updates
- **Comprehensive GPS validation** (coordinates, speed, timestamps)
- **Automatic database management** (90% warning, 95% emergency purge)
- **Backup system** with JSON/CSV export and 24-hour expiration
- **MongoDB Atlas integration** with connection pooling and multiple fallback URLs
- **System monitoring** with performance metrics and capacity alerts

## 🛠️ Technology Stack

- **Backend**: FastAPI with async/await patterns
- **Database**: MongoDB Atlas with Motor (async driver)
- **Real-time**: WebSocket for live updates
- **Rate Limiting**: SlowAPI for request throttling
- **Deployment**: Render with Docker containerization
- **Validation**: Pydantic v2 with comprehensive GPS data validation

## 📋 Prerequisites

- Python 3.11+
- MongoDB Atlas account
- Render account (for deployment)

## 🔧 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd GPS_streamer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB Atlas password
   ```

4. **Run locally**
   ```bash
   python main.py
   ```

## 🌐 API Endpoints

### GPS Data Endpoints
- `POST /api/gps/data` - Submit GPS data (rate limited)
- `GET /api/gps/data` - Retrieve GPS data with filtering
- `GET /api/system/stats` - System statistics and monitoring

### Backup Management
- `POST /api/backup/create` - Create manual backup (JSON/CSV)
- `GET /api/backup/files` - List all backup files
- `GET /api/backup/download/{filename}` - Download backup file
- `DELETE /api/backup/cleanup` - Remove expired backups

### Dashboard & Monitoring
- `GET /` - Real-time web dashboard
- `GET /health` - Health check endpoint
- `WS /ws` - WebSocket for real-time updates

## 📊 GPS Data Format

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
  "additional_data": "{\"battery\": 85}"
}
```

## 🔒 Validation Rules

- **Coordinates**: -90 to +90 (lat), -180 to +180 (lng), rejects exact 0,0
- **Speed**: 0-200 m/s maximum (720 km/h commercial aircraft limit)
- **Timestamps**: Within 1 hour future, max 7 days old
- **Accuracy**: 0-10,000 meters, warnings for >50m

## 🗄️ Database Management

- **Automatic purging**: 10% at 90% capacity, 20% at 95%
- **100MB database limit** with real-time monitoring
- **Indexed queries** for optimal performance
- **Connection pooling** with automatic failover

## 📦 Deployment on Render

1. **Connect your GitHub repository** to Render
2. **Set environment variables**:
   - `DB_PASSWORD`: Your MongoDB Atlas password
   - `DATABASE_NAME`: gps_streamer
3. **Deploy** using the provided `render.yaml` configuration

## 🌍 Domain Configuration

To use with your custom domain (airpixel.in):
1. Deploy to Render and get the service URL
2. Configure DNS CNAME record pointing to Render
3. Update Render service with custom domain

## 📈 Monitoring

The system provides comprehensive monitoring:
- Real-time database usage tracking
- Request rate monitoring
- Connection health status
- Automatic alert system
- Performance metrics

## 🔧 Development

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your MongoDB password to .env

# Run the application
python main.py
```

### Docker Development
```bash
# Build Docker image
docker build -t gps-streamer .

# Run container
docker run -p 8000:8000 --env-file .env gps-streamer
```

## 📝 License

This project is for GPS data streaming and monitoring purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions, please use the GitHub issues tracker.