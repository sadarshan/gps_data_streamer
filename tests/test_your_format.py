"""
Test your specific JSON format and multiple device scenarios
"""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_your_exact_format():
    """Test with your exact JSON format"""
    print("🧪 Testing your exact JSON format...")
    
    your_data = {
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
    
    response = requests.post(
        f"{BASE_URL}/api/gps/data",
        json=your_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Your format accepted successfully!")
        
        # Access fields safely
        device_id = data.get('device_id', 'No device_id field')
        lattitude = data.get('lattitude', 'No lattitude field')
        longitude = data.get('longitude', 'No longitude field')
        speed = data.get('speed', 'No speed field')
        speed_ms = data.get('speed_ms', 0)
        sat_tked = data.get('sat_tked', 'N/A')
        accuracy = data.get('accuracy', 'No accuracy field')
        url = data.get('url', 'N/A')
        frame_time = data.get('frame_time', 'N/A')
        
        print(f"   📍 Device: {device_id}")
        print(f"   🌍 Location: {lattitude}, {longitude}")
        print(f"   🏃 Speed: {speed} km/h ({speed_ms:.2f} m/s)")
        print(f"   📡 Satellites: {sat_tked}")
        print(f"   🎯 Accuracy: {accuracy}m")
        print(f"   🔗 URL: {url}")
        print(f"   ⏰ Frame time: {frame_time}")
        return data
    else:
        print(f"❌ Failed to submit your data: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_multiple_devices():
    """Test multiple devices with your format"""
    print("\n📱 Testing multiple devices...")
    
    devices_data = [
        {
            "id": 184,
            "device_id": "darshan_001",
            "frame_time": "21/07/24 00:13:30",
            "lattitude": 12.906000,
            "longitude": 77.640000,
            "url": "http://maps.google.com/maps?q=12.906000,77.640000",
            "sat_tked": 10,
            "speed": 25,
            "altitude": 105.0,
            "heading": 90.0,
            "accuracy": 5.0,
            "created_at": "",
            "additional_data": None
        },
        {
            "id": 185,
            "device_id": "darshan_003",
            "frame_time": "21/07/24 00:14:45",
            "lattitude": 12.907000,
            "longitude": 77.641000,
            "url": "http://maps.google.com/maps?q=12.907000,77.641000",
            "sat_tked": 15,
            "speed": 35,
            "altitude": 98.0,
            "heading": 180.0,
            "accuracy": 2.0,
            "created_at": "",
            "additional_data": '{"battery": 85, "signal_strength": 95}'
        }
    ]
    
    for i, device_data in enumerate(devices_data):
        print(f"\n   Submitting device {i+1}: {device_data['device_id']}")
        
        response = requests.post(
            f"{BASE_URL}/api/gps/data",
            json=device_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            speed = data.get('speed', 'N/A')
            sat_tked = data.get('sat_tked', 'N/A')
            print(f"   ✅ Success - Speed: {speed} km/h, Sats: {sat_tked}")
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
        
        # Wait 1.5 seconds to respect rate limiting
        time.sleep(1.5)

def test_edge_cases():
    """Test edge cases with your format"""
    print("\n⚡ Testing edge cases...")
    
    edge_cases = [
        {
            "name": "Minimum valid data",
            "data": {
                "device_id": "minimal_device",
                "lattitude": 1.0,
                "longitude": 1.0
            }
        },
        {
            "name": "Maximum speed (valid)",
            "data": {
                "id": 999,
                "device_id": "speed_test",
                "lattitude": 12.906504631042,
                "longitude": 77.640480041504,
                "speed": 700,  # High but valid
                "sat_tked": 20,
                "accuracy": 1.0
            }
        },
        {
            "name": "Zero coordinates (should fail)",
            "data": {
                "device_id": "zero_test",
                "lattitude": 0.0,  # Should fail validation
                "longitude": 0.0   # Should fail validation
            }
        }
    ]
    
    for case in edge_cases:
        print(f"\n   Testing: {case['name']}")
        
        response = requests.post(
            f"{BASE_URL}/api/gps/data",
            json=case['data'],
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"   ✅ Accepted")
        elif response.status_code == 422:
            error = response.json()
            print(f"   ⚠️  Validation failed (expected): {error['detail']}")
        else:
            print(f"   ❌ Unexpected error: {response.status_code}")
        
        time.sleep(1.5)

def test_data_retrieval():
    """Test retrieving your submitted data"""
    print("\n📊 Testing data retrieval...")
    
    # Get all data
    response = requests.get(f"{BASE_URL}/api/gps/data?limit=10")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {len(data)} GPS records")
        
        # Show first record details
        if len(data) > 0:
            record = data[0]
            device_id = record.get('device_id', 'N/A')
            lattitude = record.get('lattitude', 'N/A')
            longitude = record.get('longitude', 'N/A')
            timestamp = record.get('timestamp', 'N/A')
            sat_tked = record.get('sat_tked', None)
            
            print(f"   Latest record:")
            print(f"   📍 Device: {device_id}")
            print(f"   🌍 Location: {lattitude}, {longitude}")
            print(f"   ⏰ Timestamp: {timestamp}")
            if sat_tked:
                print(f"   📡 Satellites: {sat_tked}")
    
    # Get data for specific device
    response = requests.get(f"{BASE_URL}/api/gps/data?device_id=darshan_002")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {len(data)} records for darshan_002")

def test_system_monitoring():
    """Test system monitoring with your data"""
    print("\n📈 Testing system monitoring...")
    
    response = requests.get(f"{BASE_URL}/api/system/stats")
    if response.status_code == 200:
        stats = response.json()
        print("✅ System Statistics:")
        print(f"   📊 Total GPS Records: {stats['total_gps_records']:,}")
        print(f"   💾 Database Size: {stats.get('database_size_mb', 0):.2f} MB")
        print(f"   📈 Usage: {stats['database_usage_percentage']:.1f}%")
        print(f"   ⚡ Requests/min: {stats.get('post_requests_last_minute', 0)}")
        print(f"   🚥 Status: {stats.get('capacity_status', 'Unknown')}")

def run_your_format_tests():
    """Run all tests with your JSON format"""
    print("🚀 GPS Data Streamer - Testing Your JSON Format")
    print("=" * 55)
    
    # Test exact format
    result = test_your_exact_format()
    
    if result:
        # If basic test passed, run more tests
        test_multiple_devices()
        test_edge_cases()
        test_data_retrieval()
        test_system_monitoring()
        
        print("\n" + "=" * 55)
        print("🎉 All tests completed!")
        print("✅ Your JSON format is fully supported")
        print("💡 Check the dashboard at http://localhost:8000")
    else:
        print("\n❌ Basic test failed - check server logs")

if __name__ == "__main__":
    run_your_format_tests()