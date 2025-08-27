"""
Minimal Test - Just insert and retrieve your exact data format
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Your exact GPS data
gps_data = {
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
    "additional_data": None
}

print("🧪 Minimal GPS Data Test")
print("=" * 25)

# 1. Insert data
print("📤 Inserting data...")
response = requests.post(f"{BASE_URL}/api/gps/data", json=gps_data)

if response.status_code == 200:
    result = response.json()
    print("✅ Insert SUCCESS")
    
    # Show complete response
    print("\n📋 Complete response data:")
    for key, value in result.items():
        print(f"   {key}: {value}")
    
    # Access fields safely
    record_id = result.get('id', 'No ID field')
    device_id = result.get('device_id', 'No device_id field')
    lattitude = result.get('lattitude', 'No lattitude field')
    longitude = result.get('longitude', 'No longitude field')
    
    print(f"\n   ID: {record_id}")
    print(f"   Device: {device_id}")
    print(f"   Location: {lattitude}, {longitude}")
else:
    print(f"❌ Insert FAILED: {response.status_code}")
    print(f"   Error: {response.text}")
    exit(1)

# 2. Retrieve data
print("\n📥 Retrieving data...")
response = requests.get(f"{BASE_URL}/api/gps/data?limit=1")

if response.status_code == 200:
    data = response.json()
    if len(data) > 0:
        record = data[0]
        print("✅ Retrieve SUCCESS")
        print(f"   Device: {record['device_id']}")
        print(f"   Location: {record['lattitude']}, {record['longitude']}")
        print(f"   Speed: {record['speed']} km/h")
        print(f"   Satellites: {record.get('sat_tked', 'N/A')}")
    else:
        print("❌ No data found")
else:
    print(f"❌ Retrieve FAILED: {response.status_code}")

print("\n🎉 Test completed!")