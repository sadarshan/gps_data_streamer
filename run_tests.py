#!/usr/bin/env python3
"""
GPS Data Streamer - Test Runner
Run all tests to verify your API is working correctly
"""
import subprocess
import sys
import time
import requests
import os

def check_server():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_test_file(test_file, description):
    """Run a specific test file"""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              text=True, 
                              timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 GPS Data Streamer - Complete Test Suite")
    print("="*60)
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    if not check_server():
        print("❌ Server is not running!")
        print("\n📋 To start the server:")
        print("   1. Open a terminal")
        print("   2. Navigate to the GPS_streamer directory")
        print("   3. Run: python main.py")
        print("   4. Wait for 'MongoDB connected successfully' message")
        print("   5. Then run this test script again")
        return
    
    print("✅ Server is running and responding")
    
    # Test files to run
    tests = [
        ("tests/test_your_format.py", "Your JSON Format Tests"),
        ("tests/test_all_apis.py", "Complete API Test Suite"),
        ("tests/load_test.py", "Load and Performance Tests"),
        ("tests/websocket_test.py", "WebSocket Real-time Tests"),
    ]
    
    results = []
    
    for test_file, description in tests:
        if os.path.exists(test_file):
            success = run_test_file(test_file, description)
            results.append((description, success))
            
            # Wait between tests
            time.sleep(2)
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append((description, False))
    
    # Print final summary
    print("\n" + "="*60)
    print("🎯 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Your GPS Data Streamer is working perfectly.")
        print("\n🌐 Next steps:")
        print("   • Open http://localhost:8000 to view the dashboard")
        print("   • Check http://localhost:8000/docs for API documentation")
        print("   • Your system is ready for production!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()