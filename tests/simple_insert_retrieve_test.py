"""
Simple Insert and Retrieve Test
Just test basic data insertion and retrieval with your exact format
"""
import requests
import json
import time

BASE_URL = "http://0.0.0.0:8000"

def test_simple_insert_and_retrieve():
    """Simple test to insert data and retrieve it"""
    print("🧪 Simple Insert and Retrieve Test")
    print("=" * 40)
    
    # Your exact data format
    test_data = {
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
    
    print("📤 Step 1: Inserting GPS data...")
    print(f"   Device: {test_data['device_id']}")
    print(f"   Location: {test_data['lattitude']}, {test_data['longitude']}")
    print(f"   Speed: {test_data['speed']} km/h")
    
    # Insert the data
    response = requests.post(
        f"{BASE_URL}/api/gps/data",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        inserted_data = response.json()
        print("✅ Data inserted successfully!")
        
        # Show what was actually returned
        print("\n📋 Complete response data:")
        for key, value in inserted_data.items():
            print(f"   {key}: {value}")
        
        # Now try to access expected fields safely
        record_id = inserted_data.get('id', 'No ID field')
        timestamp = inserted_data.get('timestamp', 'No timestamp field')
        print(f"\n   Generated ID: {record_id}")
        print(f"   Timestamp: {timestamp}")
        
        # Wait a moment
        time.sleep(1)
        
        print("\n📥 Step 2: Retrieving GPS data...")
        
        # Retrieve all data
        retrieve_response = requests.get(f"{BASE_URL}/api/gps/data?limit=5")
        
        if retrieve_response.status_code == 200:
            retrieved_data = retrieve_response.json()
            print(f"✅ Retrieved {len(retrieved_data)} records")
            
            if len(retrieved_data) > 0:
                latest_record = retrieved_data[0]  # Should be our record (sorted by timestamp desc)
                print("\n🔍 Latest record details:")
                print(f"   Device: {latest_record['device_id']}")
                print(f"   Location: {latest_record['lattitude']}, {latest_record['longitude']}")
                print(f"   Speed: {latest_record['speed']} km/h")
                print(f"   Frame Time: {latest_record.get('frame_time', 'N/A')}")
                print(f"   Satellites: {latest_record.get('sat_tked', 'N/A')}")
                print(f"   URL: {latest_record.get('url', 'N/A')}")
                
                # Verify it's our data
                if latest_record['device_id'] == test_data['device_id']:
                    print("✅ Retrieved data matches inserted data!")
                else:
                    print("⚠️  Retrieved data is from a different device")
            else:
                print("❌ No data retrieved")
        else:
            print(f"❌ Failed to retrieve data: {retrieve_response.status_code}")
            print(f"Error: {retrieve_response.text}")
        
        # Test specific device retrieval
        print(f"\n📥 Step 3: Retrieving data for device '{test_data['device_id']}'...")
        device_response = requests.get(f"{BASE_URL}/api/gps/data?device_id={test_data['device_id']}")
        
        if device_response.status_code == 200:
            device_data = device_response.json()
            print(f"✅ Found {len(device_data)} records for device {test_data['device_id']}")
            
            if len(device_data) > 0:
                print("📊 Device records:")
                for i, record in enumerate(device_data[:3]):  # Show first 3
                    print(f"   {i+1}. Speed: {record['speed']} km/h, "
                          f"Location: ({record['lattitude']:.6f}, {record['longitude']:.6f})")
        else:
            print(f"❌ Failed to retrieve device data: {device_response.status_code}")
            
    else:
        print(f"❌ Failed to insert data: {response.status_code}")
        print(f"Error: {response.text}")
        return False
    
    print("\n🎉 Test completed successfully!")
    return True

def test_multiple_records():
    """Test inserting multiple records"""
    print("\n📱 Testing multiple records...")
    
    devices_data = [
        {
            "id": 184,
            "device_id": "darshan_001",
            "lattitude": 12.906000,
            "longitude": 77.640000,
            "speed": 20
        },
        {
            "id": 185,
            "device_id": "darshan_003", 
            "lattitude": 12.907000,
            "longitude": 77.641000,
            "speed": 30
        }
    ]
    
    inserted_count = 0
    for data in devices_data:
        print(f"   Inserting {data['device_id']}...")
        response = requests.post(
            f"{BASE_URL}/api/gps/data",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            inserted_count += 1
            print(f"   ✅ {data['device_id']} inserted")
        else:
            print(f"   ❌ {data['device_id']} failed: {response.status_code}")
        
        time.sleep(1.1)  # Respect rate limiting
    
    print(f"📊 Inserted {inserted_count}/{len(devices_data)} records")
    
    # Retrieve all and show count
    response = requests.get(f"{BASE_URL}/api/gps/data")
    if response.status_code == 200:
        all_data = response.json()
        print(f"📈 Total records in database: {len(all_data)}")
        
        # Show unique devices
        devices = set(record['device_id'] for record in all_data)
        print(f"📱 Unique devices: {', '.join(sorted(devices))}")

def main():
    """Main test function"""
    print("🚀 Simple GPS Data Insert/Retrieve Test")
    print("=" * 45)
    
    # Check server
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server not healthy")
            return
    except:
        print("❌ Cannot connect to server")
        print("   Make sure server is running: python main.py")
        return
    
    print("✅ Server is running\n")
    
    # Run tests
    success = test_simple_insert_and_retrieve()
    
    if success:
        test_multiple_records()
        print("\n💡 Next steps:")
        print("   • Check dashboard: http://localhost:8000")
        print("   • View all data: http://localhost:8000/api/gps/data") 
        print("   • Run full test suite: python run_tests.py")
    
if __name__ == "__main__":
    main()