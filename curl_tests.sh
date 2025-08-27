#!/bin/bash

# GPS Data Streamer - Manual curl Tests
# Quick tests using your exact JSON format

BASE_URL="http://localhost:8000"

echo "🚀 GPS Data Streamer - curl Test Suite"
echo "======================================"

# Check if server is running
echo "🔍 Checking server health..."
curl -s "$BASE_URL/health" | jq '.' || {
    echo "❌ Server not responding! Make sure it's running on localhost:8000"
    exit 1
}

echo -e "\n✅ Server is running\n"

# Test 1: Submit your exact GPS data format
echo "📍 Test 1: Submitting your GPS data format..."
curl -X POST "$BASE_URL/api/gps/data" \
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
  }' | jq '.'

echo -e "\n"

# Test 2: Submit second device
echo "📱 Test 2: Submitting second device data..."
curl -X POST "$BASE_URL/api/gps/data" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 184,
    "device_id": "darshan_003",    
    "frame_time": "21/07/24 00:13:45",
    "lattitude": 12.907000,
    "longitude": 77.641000,
    "url": "http://maps.google.com/maps?q=12.907000,77.641000",
    "sat_tked": 15,
    "speed": 25,
    "altitude": 95.0,
    "heading": 90.0,
    "accuracy": 2.5,
    "created_at": "",
    "additional_data": "{\"battery\": 85}"
  }' | jq '.'

echo -e "\n"

# Wait for rate limiting
echo "⏸️  Waiting 2 seconds (rate limiting)..."
sleep 2

# Test 3: Get all GPS data
echo "📊 Test 3: Retrieving all GPS data (limit 5)..."
curl -s "$BASE_URL/api/gps/data?limit=5" | jq '.'

echo -e "\n"

# Test 4: Get data for specific device
echo "🎯 Test 4: Retrieving data for darshan_002..."
curl -s "$BASE_URL/api/gps/data?device_id=darshan_002" | jq '.'

echo -e "\n"

# Test 5: Get system statistics
echo "📈 Test 5: Getting system statistics..."
curl -s "$BASE_URL/api/system/stats" | jq '.'

echo -e "\n"

# Test 6: Create backup
echo "💾 Test 6: Creating JSON backup..."
curl -X POST "$BASE_URL/api/backup/create?format=json" | jq '.'

echo -e "\n"

# Test 7: List backup files
echo "📋 Test 7: Listing backup files..."
curl -s "$BASE_URL/api/backup/files" | jq '.'

echo -e "\n"

# Test 8: Rate limiting test
echo "🚦 Test 8: Testing rate limiting (rapid requests)..."
echo "Sending 3 rapid requests (should see rate limiting):"

for i in {1..3}; do
    echo "Request $i:"
    curl -X POST "$BASE_URL/api/gps/data" \
      -H "Content-Type: application/json" \
      -d "{
        \"device_id\": \"rate_test_$i\",
        \"lattitude\": 12.906,
        \"longitude\": 77.640,
        \"speed\": 20
      }" \
      -w "Status: %{http_code}, Time: %{time_total}s\n" \
      -s -o /dev/null
done

echo -e "\n"

# Test 9: Invalid data validation
echo "❌ Test 9: Testing validation with invalid data..."
echo "Submitting invalid coordinates (should fail):"
curl -X POST "$BASE_URL/api/gps/data" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "validation_test",
    "lattitude": 91.0,
    "longitude": -200.0,
    "speed": 800
  }' | jq '.'

echo -e "\n"

echo "🎉 curl Tests Complete!"
echo "💡 Check the dashboard: $BASE_URL"
echo "📚 API Documentation: $BASE_URL/docs"