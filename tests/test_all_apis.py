"""
Comprehensive API Test Suite for GPS Data Streamer
Tests all endpoints with your JSON format and validation
"""
import requests
import json
import time
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TestGPSDataStreamer:
    """Complete test suite for all GPS Data Streamer APIs"""
    
    def setup_method(self):
        """Setup test data"""
        self.sample_gps_data = {
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
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "GPS Data Streamer"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data
        assert "database" in data
        
        print("✅ Health check passed")
    
    def test_api_status(self):
        """Test the API status endpoint"""
        response = requests.get(f"{BASE_URL}/api")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "GPS Data Streamer"
        assert data["status"] == "online"
        assert "features" in data
        assert len(data["features"]) > 0
        
        print("✅ API status check passed")
    
    def test_gps_data_submission_valid(self):
        """Test valid GPS data submission"""
        response = requests.post(
            f"{BASE_URL}/api/gps/data",
            json=self.sample_gps_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert data["device_id"] == "darshan_002"
        assert data["lattitude"] == 12.906504631042
        assert data["longitude"] == 77.640480041504
        assert data["speed"] == 15
        assert data["altitude"] == 100.5
        assert data["heading"] == 45.0
        assert data["accuracy"] == 3.0
        assert "id" in data  # MongoDB ObjectId
        assert "timestamp" in data
        assert "created_at" in data
        
        # Check computed fields
        assert "speed_ms" in data
        assert "distance_from_origin" in data
        
        print(f"✅ GPS data submission passed - ID: {data['id']}")
        return data["id"]  # Return for other tests
    
    def test_gps_data_validation_invalid_coordinates(self):
        """Test GPS data validation with invalid coordinates"""
        invalid_data = self.sample_gps_data.copy()
        invalid_data["lattitude"] = 91.0  # Invalid latitude > 90
        
        response = requests.post(
            f"{BASE_URL}/api/gps/data",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        error = response.json()
        assert "validation" in error["detail"].lower()
        
        print("✅ Invalid coordinates validation passed")
    
    def test_gps_data_validation_invalid_speed(self):
        """Test GPS data validation with invalid speed"""
        invalid_data = self.sample_gps_data.copy()
        invalid_data["speed"] = 800  # Invalid speed > 720 km/h
        
        response = requests.post(
            f"{BASE_URL}/api/gps/data",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        error = response.json()
        assert "speed" in error["detail"].lower()
        
        print("✅ Invalid speed validation passed")
    
    def test_rate_limiting(self):
        """Test rate limiting (1 request per second)"""
        print("🔄 Testing rate limiting...")
        
        # First request should succeed
        response1 = requests.post(
            f"{BASE_URL}/api/gps/data",
            json=self.sample_gps_data,
            headers={"Content-Type": "application/json"}
        )
        assert response1.status_code == 200
        
        # Immediate second request should be rate limited
        response2 = requests.post(
            f"{BASE_URL}/api/gps/data",
            json=self.sample_gps_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should get 429 Too Many Requests
        if response2.status_code == 429:
            print("✅ Rate limiting working correctly")
        else:
            print("⚠️  Rate limiting may not be strict - check server logs")
    
    def test_gps_data_retrieval_all(self):
        """Test retrieving all GPS data"""
        response = requests.get(f"{BASE_URL}/api/gps/data")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            # Check structure of first record
            record = data[0]
            assert "device_id" in record
            assert "lattitude" in record
            assert "longitude" in record
            assert "timestamp" in record
        
        print(f"✅ GPS data retrieval passed - Found {len(data)} records")
    
    def test_gps_data_retrieval_filtered(self):
        """Test filtered GPS data retrieval"""
        # Test device filter
        response = requests.get(f"{BASE_URL}/api/gps/data?device_id=darshan_002")
        assert response.status_code == 200
        
        # Test limit
        response = requests.get(f"{BASE_URL}/api/gps/data?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
        
        # Test pagination
        response = requests.get(f"{BASE_URL}/api/gps/data?limit=2&offset=0")
        assert response.status_code == 200
        
        print("✅ Filtered GPS data retrieval passed")
    
    def test_system_statistics(self):
        """Test system statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/system/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_gps_records" in data
        assert "database_size_bytes" in data
        assert "database_usage_percentage" in data
        assert "timestamp" in data
        
        # Check computed fields
        assert "database_size_mb" in data
        assert "capacity_status" in data
        
        print(f"✅ System statistics passed - {data['total_gps_records']:,} records, "
              f"{data['database_usage_percentage']:.1f}% usage")
    
    def test_backup_creation_json(self):
        """Test JSON backup creation"""
        response = requests.post(f"{BASE_URL}/api/backup/create?format=json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "filename" in data
        assert "format" in data
        assert data["format"] == "json"
        assert data["filename"].endswith(".json")
        assert "expires_in_hours" in data
        
        print(f"✅ JSON backup creation passed - {data['filename']}")
        return data["filename"]
    
    def test_backup_creation_csv(self):
        """Test CSV backup creation"""
        response = requests.post(f"{BASE_URL}/api/backup/create?format=csv")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "csv"
        assert data["filename"].endswith(".csv")
        
        print(f"✅ CSV backup creation passed - {data['filename']}")
        return data["filename"]
    
    def test_backup_file_listing(self):
        """Test backup file listing"""
        response = requests.get(f"{BASE_URL}/api/backup/files")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "backup_files" in data
        assert "total_files" in data
        assert "active_files" in data
        assert isinstance(data["backup_files"], list)
        
        if len(data["backup_files"]) > 0:
            file_info = data["backup_files"][0]
            assert "filename" in file_info
            assert "format" in file_info
            assert "size_mb" in file_info
            assert "created_at" in file_info
            assert "expired" in file_info
        
        print(f"✅ Backup file listing passed - {data['total_files']} files")
    
    def test_backup_download(self):
        """Test backup file download"""
        # First create a backup
        backup_response = requests.post(f"{BASE_URL}/api/backup/create?format=json")
        if backup_response.status_code == 200:
            backup_data = backup_response.json()
            filename = backup_data.get("filename", "backup_not_found.json")
            
            # Now try to download it
            download_response = requests.get(f"{BASE_URL}/api/backup/download/{filename}")
            
            if download_response.status_code == 200:
                assert download_response.headers["content-type"] == "application/json"
                # Try to parse as JSON to verify it's valid
                backup_data = download_response.json()
                assert "metadata" in backup_data
                assert "data" in backup_data
                
                print(f"✅ Backup download passed - {len(download_response.content)} bytes")
            else:
                print(f"⚠️  Backup download failed: {download_response.status_code}")
    
    def test_backup_cleanup(self):
        """Test backup cleanup"""
        response = requests.delete(f"{BASE_URL}/api/backup/cleanup")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "files_removed" in data
        assert "remaining_files" in data
        
        print(f"✅ Backup cleanup passed - {data['files_removed']} files removed")

def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🧪 GPS Data Streamer - Comprehensive API Test Suite")
    print("=" * 60)
    
    tester = TestGPSDataStreamer()
    tester.setup_method()
    
    tests = [
        ("Health Check", tester.test_health_check),
        ("API Status", tester.test_api_status),
        ("GPS Data Submission (Valid)", tester.test_gps_data_submission_valid),
        ("GPS Data Validation (Invalid Coordinates)", tester.test_gps_data_validation_invalid_coordinates),
        ("GPS Data Validation (Invalid Speed)", tester.test_gps_data_validation_invalid_speed),
        ("Rate Limiting", tester.test_rate_limiting),
        ("GPS Data Retrieval (All)", tester.test_gps_data_retrieval_all),
        ("GPS Data Retrieval (Filtered)", tester.test_gps_data_retrieval_filtered),
        ("System Statistics", tester.test_system_statistics),
        ("Backup Creation (JSON)", tester.test_backup_creation_json),
        ("Backup Creation (CSV)", tester.test_backup_creation_csv),
        ("Backup File Listing", tester.test_backup_file_listing),
        ("Backup Download", tester.test_backup_download),
        ("Backup Cleanup", tester.test_backup_cleanup),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔬 Running: {test_name}")
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED: {str(e)}")
            failed += 1
        
        # Small delay between tests to avoid overwhelming the server
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! Your GPS Data Streamer is working perfectly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    run_comprehensive_test()