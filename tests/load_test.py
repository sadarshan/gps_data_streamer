"""
Load Testing and Performance Testing for GPS Data Streamer
"""
import requests
import json
import time
import threading
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8000"

class LoadTester:
    def __init__(self):
        self.results = []
        self.errors = []
        self.start_time = None
        
    def create_test_data(self, device_id: str, sequence_id: int):
        """Create test GPS data with your format"""
        return {
            "id": sequence_id,
            "device_id": device_id,
            "frame_time": datetime.now().strftime("%d/%m/%y %H:%M:%S"),
            "lattitude": 12.906504631042 + (sequence_id * 0.0001),  # Slight variation
            "longitude": 77.640480041504 + (sequence_id * 0.0001),
            "url": f"http://maps.google.com/maps?q=12.906{sequence_id:03d},77.640{sequence_id:03d}",
            "sat_tked": min(12 + (sequence_id % 8), 20),  # Vary satellites 12-20
            "speed": min(15 + (sequence_id % 40), 100),   # Vary speed 15-55 km/h
            "altitude": 100.5 + (sequence_id % 50),       # Vary altitude
            "heading": (sequence_id * 10) % 360,          # Rotate heading
            "accuracy": max(1.0, 5.0 - (sequence_id % 5)), # Vary accuracy 1-5m
            "created_at": "",
            "additional_data": json.dumps({"sequence": sequence_id, "test": True})
        }
    
    def single_request(self, device_id: str, sequence_id: int):
        """Single GPS data submission request"""
        data = self.create_test_data(device_id, sequence_id)
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/gps/data",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                "device_id": device_id,
                "sequence_id": sequence_id,
                "status_code": response.status_code,
                "response_time": response_time,
                "timestamp": datetime.now(),
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                result["response_data"] = response.json()
            else:
                result["error"] = response.text
                
            return result
            
        except Exception as e:
            return {
                "device_id": device_id,
                "sequence_id": sequence_id,
                "status_code": 0,
                "response_time": time.time() - start_time,
                "timestamp": datetime.now(),
                "success": False,
                "error": str(e)
            }
    
    def rate_limit_test(self):
        """Test rate limiting behavior"""
        print("🚦 Testing Rate Limiting...")
        
        device_id = "rate_test_device"
        rapid_requests = 5
        
        print(f"Sending {rapid_requests} requests rapidly...")
        
        results = []
        for i in range(rapid_requests):
            result = self.single_request(device_id, i)
            results.append(result)
            print(f"  Request {i+1}: {result['status_code']} ({result['response_time']:.3f}s)")
        
        successful = sum(1 for r in results if r['success'])
        rate_limited = sum(1 for r in results if r['status_code'] == 429)
        
        print(f"✅ Rate Limiting Results:")
        print(f"   Successful: {successful}/{rapid_requests}")
        print(f"   Rate Limited: {rate_limited}/{rapid_requests}")
        print(f"   Rate limiting {'working' if rate_limited > 0 else 'may need adjustment'}")
    
    def sustained_load_test(self, duration_minutes: int = 2, devices: int = 3):
        """Test sustained load with multiple devices"""
        print(f"⏱️  Sustained Load Test ({duration_minutes} minutes, {devices} devices)...")
        
        self.start_time = time.time()
        end_time = self.start_time + (duration_minutes * 60)
        sequence_counter = 0
        
        print("Starting sustained submissions (respecting rate limits)...")
        
        while time.time() < end_time:
            for device_num in range(devices):
                device_id = f"load_test_device_{device_num:02d}"
                
                result = self.single_request(device_id, sequence_counter)
                self.results.append(result)
                
                if result['success']:
                    print(f"✅ {device_id}: {result['response_time']:.3f}s")
                else:
                    print(f"❌ {device_id}: {result['status_code']} - {result.get('error', 'Unknown')}")
                    self.errors.append(result)
                
                sequence_counter += 1
                
                # Wait to respect rate limiting (1.5s per request)
                time.sleep(1.5)
                
                # Check if we've exceeded time
                if time.time() >= end_time:
                    break
        
        self.print_load_test_results()
    
    def concurrent_load_test(self, total_requests: int = 10, max_workers: int = 3):
        """Test concurrent requests (will hit rate limits)"""
        print(f"🔀 Concurrent Load Test ({total_requests} requests, {max_workers} workers)...")
        
        self.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            futures = []
            for i in range(total_requests):
                device_id = f"concurrent_device_{i % max_workers:02d}"
                future = executor.submit(self.single_request, device_id, i)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)
                
                if result['success']:
                    print(f"✅ {result['device_id']}: {result['response_time']:.3f}s")
                else:
                    print(f"❌ {result['device_id']}: {result['status_code']}")
                    self.errors.append(result)
        
        self.print_load_test_results()
    
    def print_load_test_results(self):
        """Print comprehensive load test results"""
        if not self.results:
            print("No results to analyze")
            return
        
        total_time = time.time() - self.start_time
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        
        print("\n" + "=" * 50)
        print("📊 Load Test Results")
        print("=" * 50)
        
        print(f"⏱️  Total Duration: {total_time:.1f} seconds")
        print(f"📈 Total Requests: {len(self.results)}")
        print(f"✅ Successful: {len(successful_requests)} ({len(successful_requests)/len(self.results)*100:.1f}%)")
        print(f"❌ Failed: {len(failed_requests)} ({len(failed_requests)/len(self.results)*100:.1f}%)")
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            print(f"\n⚡ Response Time Statistics:")
            print(f"   Average: {statistics.mean(response_times):.3f}s")
            print(f"   Median: {statistics.median(response_times):.3f}s")
            print(f"   Min: {min(response_times):.3f}s")
            print(f"   Max: {max(response_times):.3f}s")
            
            # Throughput
            requests_per_second = len(successful_requests) / total_time
            print(f"   Throughput: {requests_per_second:.2f} requests/second")
        
        # Status code breakdown
        status_codes = {}
        for result in self.results:
            code = result['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
        
        print(f"\n🔢 Status Code Breakdown:")
        for code, count in sorted(status_codes.items()):
            print(f"   {code}: {count} ({count/len(self.results)*100:.1f}%)")
        
        # Error analysis
        if failed_requests:
            print(f"\n❌ Error Analysis:")
            error_types = {}
            for result in failed_requests:
                error = result.get('error', f"HTTP {result['status_code']}")
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                print(f"   {error}: {count}")

def test_system_under_load():
    """Test system stats during load"""
    print("📊 Testing system stats under load...")
    
    for i in range(3):
        response = requests.get(f"{BASE_URL}/api/system/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Check {i+1}: {stats['total_gps_records']:,} records, "
                  f"{stats['database_usage_percentage']:.1f}% usage, "
                  f"{stats.get('post_requests_last_minute', 0)} req/min")
        time.sleep(2)

def main():
    """Main load testing function"""
    print("🚀 GPS Data Streamer - Load Testing Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            return
    except:
        print("❌ Cannot connect to server - make sure it's running on localhost:8000")
        return
    
    print("✅ Server is running\n")
    
    tester = LoadTester()
    
    # 1. Rate limit test
    tester.rate_limit_test()
    print()
    
    # 2. Short sustained load test
    tester.results.clear()
    tester.errors.clear()
    tester.sustained_load_test(duration_minutes=1, devices=2)
    print()
    
    # 3. Test system stats
    test_system_under_load()
    print()
    
    # 4. Concurrent test (will hit rate limits)
    print("Note: Concurrent test will hit rate limits - this is expected behavior")
    tester.results.clear()
    tester.errors.clear()
    tester.concurrent_load_test(total_requests=8, max_workers=3)
    
    print("\n🎯 Load Testing Complete!")
    print("💡 Check the dashboard at http://localhost:8000 for real-time updates")

if __name__ == "__main__":
    main()