#!/usr/bin/env python3
"""
Test script for GPS Data Streamer application
Tests MongoDB connection, API endpoints, and basic functionality
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_DEVICE_ID = "test_device_001"

# Test GPS data
TEST_GPS_DATA = {
    "device_id": TEST_DEVICE_ID,
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 10.5,
    "speed": 5.2,
    "heading": 180.0,
    "accuracy": 3.0,
    "timestamp": datetime.utcnow().isoformat(),
    "additional_data": '{"test": true}'
}

async def test_server_running() -> bool:
    """Test if the server is running"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server is running - {data.get('message', 'Unknown')}")
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Server is not running or unreachable: {e}")
        return False

async def test_dashboard_endpoint() -> bool:
    """Test if the dashboard endpoint is accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("✅ Dashboard endpoint is accessible")
                return True
            else:
                print(f"❌ Dashboard endpoint returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error accessing dashboard: {e}")
        return False

async def test_post_gps_data() -> bool:
    """Test posting GPS data"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/gps/data",
                json=TEST_GPS_DATA
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ GPS data posted successfully - ID: {data.get('id', 'Unknown')}")
                return True
            else:
                print(f"❌ Failed to post GPS data - Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error posting GPS data: {e}")
        return False

async def test_get_gps_data() -> bool:
    """Test retrieving GPS data"""
    try:
        async with httpx.AsyncClient() as client:
            # Get all GPS data
            response = await client.get(f"{BASE_URL}/api/gps/data")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved GPS data - Found {len(data)} records")
                
                # Test filtering by device ID
                response = await client.get(f"{BASE_URL}/api/gps/data?device_id={TEST_DEVICE_ID}")
                if response.status_code == 200:
                    filtered_data = response.json()
                    print(f"✅ Filtered GPS data by device - Found {len(filtered_data)} records")
                    return True
                else:
                    print(f"❌ Failed to filter GPS data - Status: {response.status_code}")
                    return False
            else:
                print(f"❌ Failed to retrieve GPS data - Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error retrieving GPS data: {e}")
        return False

async def test_system_stats() -> bool:
    """Test system stats endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/system/stats")
            if response.status_code == 200:
                data = response.json()
                if data:
                    print(f"✅ System stats retrieved - Records: {data.get('total_gps_records', 'Unknown')}")
                else:
                    print("✅ System stats endpoint working (no stats yet)")
                return True
            else:
                print(f"❌ Failed to retrieve system stats - Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error retrieving system stats: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🧪 Starting GPS Data Streamer Tests")
    print("=" * 50)
    
    tests = [
        ("Server Running", test_server_running),
        ("Dashboard Endpoint", test_dashboard_endpoint),
        ("Post GPS Data", test_post_gps_data),
        ("Get GPS Data", test_get_gps_data),
        ("System Stats", test_system_stats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Application is ready for deployment.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    print("Starting application tests...")
    print("Make sure the application is running with: python main.py")
    print("Waiting 3 seconds for you to confirm...")
    
    import time
    time.sleep(3)
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)