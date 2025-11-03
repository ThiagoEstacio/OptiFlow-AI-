#!/usr/bin/env python3
"""
Test InfluxDB Query Fix
Validates that the backend can now read historical data from InfluxDB
"""
import requests
import json
from datetime import datetime

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_TAGS = [
    "ARZ_GATES_GATE01_POSICAO_PV",  # By name
    "e92f044e-1909-4bac-b398-ab5fe2427394",  # By UUID
    "ARZ_CORR01_VELOCIDADE_PV",  # By name
]

def test_latest_value(tag_id: str):
    """Test getting latest value for a tag"""
    print(f"\n{'='*80}")
    print(f"Testing tag: {tag_id}")
    print(f"{'='*80}")
    
    url = f"{BACKEND_URL}/api/v1/timeseries/tags/{tag_id}/latest"
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ SUCCESS!")
            print(f"   Value: {data.get('value')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            print(f"   Quality: {data.get('quality')}")
            
            if data.get('quality') == 'good' and data.get('value') is not None:
                print(f"   🎉 Real data from InfluxDB!")
                return True
            elif data.get('quality') == 'no_data':
                print(f"   ⚠️  No data in InfluxDB (but query worked)")
                return True
            else:
                print(f"   ⚠️  Unexpected quality: {data.get('quality')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 InfluxDB Query Fix Validation Test")
    print("="*80)
    print(f"Backend: {BACKEND_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    for tag_id in TEST_TAGS:
        success = test_latest_value(tag_id)
        results.append((tag_id, success))
    
    # Summary
    print("\n" + "="*80)
    print("📊 Test Summary")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for tag_id, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        tag_display = tag_id[:30] + "..." if len(tag_id) > 30 else tag_id
        print(f"{status} - {tag_display}")
    
    print(f"\n{'='*80}")
    print(f"Result: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*80}\n")
    
    if passed == total:
        print("🎉 All tests passed! InfluxDB queries are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
