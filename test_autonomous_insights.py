#!/usr/bin/env python3
"""
Test Autonomous Insights System
Validates the autonomous agent endpoints
"""
import requests
import json
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8000"
TEST_USER = {"username": "admin@optiflow.com", "password": "admin123"}

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def login():
    """Login and get token"""
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        data=TEST_USER
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def test_autonomous_summary(token):
    """Test autonomous insights summary"""
    print_section("1. Autonomous Insights Summary")
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/ai/insights/autonomous/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Summary retrieved")
        print(f"\n📊 Monitoring Status:")
        print(f"   Active: {data.get('monitoring_active')}")
        print(f"   Interval: {data.get('monitoring_interval')}s")
        print(f"   Total Insights: {data.get('total_insights')}")
        
        if data.get('by_category'):
            print(f"\n📂 By Category:")
            for cat, count in data['by_category'].items():
                print(f"   {cat}: {count}")
        
        if data.get('by_severity'):
            print(f"\n🚨 By Severity:")
            for sev, count in data['by_severity'].items():
                icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢', 'info': '🔵'}.get(sev, '⚪')
                print(f"   {icon} {sev}: {count}")
        
        if data.get('latest_insight'):
            latest = data['latest_insight']
            print(f"\n🆕 Latest Insight:")
            print(f"   Title: {latest.get('title')}")
            print(f"   Category: {latest.get('category')}")
            print(f"   Severity: {latest.get('severity')}")
        
        return True
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return False

def test_trigger_monitoring(token):
    """Test manual trigger of monitoring cycle"""
    print_section("2. Trigger Monitoring Cycle")
    
    print("⏳ Triggering monitoring cycle...")
    response = requests.post(
        f"{BACKEND_URL}/api/v1/ai/insights/autonomous/trigger",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Monitoring cycle completed")
        print(f"   Status: {data.get('status')}")
        print(f"   Insights Generated: {data.get('insights_generated')}")
        return True
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return False

def test_get_insights(token):
    """Test getting insights with filters"""
    print_section("3. Get Autonomous Insights")
    
    # Test without filters
    response = requests.get(
        f"{BACKEND_URL}/api/v1/ai/insights/autonomous?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {data.get('total')} insights\n")
        
        for i, insight in enumerate(data.get('insights', [])[:3], 1):
            print(f"{i}. {insight.get('title')}")
            print(f"   Category: {insight.get('category')} | Severity: {insight.get('severity')}")
            print(f"   Description: {insight.get('description')[:80]}...")
            if insight.get('recommendations'):
                print(f"   Recommendations: {len(insight['recommendations'])} actions")
            print()
        
        return True
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return False

def test_realtime_insight(token):
    """Test real-time insight for a tag"""
    print_section("4. Real-time Tag Insight")
    
    # First, get a tag ID
    tags_response = requests.get(
        f"{BACKEND_URL}/api/v1/tags?limit=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if tags_response.status_code != 200:
        print("❌ Could not get tags")
        return False
    
    tags = tags_response.json()
    if not tags:
        print("❌ No tags available")
        return False
    
    tag = tags[0]
    tag_id = tag['id']
    print(f"📊 Analyzing tag: {tag['name']}\n")
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/ai/insights/realtime/{tag_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Real-time insight generated")
        print(f"\n📈 Current Value:")
        if data.get('current_value'):
            cv = data['current_value']
            print(f"   Value: {cv.get('value')}")
            print(f"   Unit: {cv.get('unit')}")
            print(f"   Quality: {cv.get('quality')}")
        
        if data.get('statistics'):
            stats = data['statistics']
            print(f"\n📊 Statistics (1h):")
            print(f"   Mean: {stats.get('mean')}")
            print(f"   StdDev: {stats.get('stddev')}")
            print(f"   Min: {stats.get('min')} | Max: {stats.get('max')}")
        
        if data.get('anomalies'):
            anom = data['anomalies']
            print(f"\n🔍 Anomalies:")
            print(f"   Count: {anom.get('anomaly_count')}")
            print(f"   Insight: {anom.get('insight')}")
        
        if data.get('recommendations'):
            print(f"\n💡 Recommendations:")
            for rec in data['recommendations']:
                print(f"   • {rec}")
        
        return True
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return False

def test_process_analysis(token):
    """Test complete process analysis"""
    print_section("5. Complete Process Analysis")
    
    print("⏳ Analyzing complete process (this may take a moment)...\n")
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/ai/insights/analyze-process?duration=1h",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Process analysis completed")
        print(f"   Tags Analyzed: {data.get('tags_analyzed')}")
        print(f"   Duration: {data.get('duration')}")
        
        health = data.get('process_health', {})
        print(f"\n🏥 Process Health:")
        print(f"   Score: {health.get('score')}/100")
        print(f"   Status: {health.get('status').upper()}")
        if health.get('factors'):
            print(f"   Factors:")
            for factor in health['factors']:
                print(f"      • {factor}")
        
        if data.get('anomalies'):
            print(f"\n🔍 Anomalies Detected: {len(data['anomalies'])}")
            for anom in data['anomalies'][:3]:
                print(f"   • {anom.get('tag')}: {anom.get('count')} anomalies")
        
        if data.get('performance'):
            print(f"\n⚙️  Performance Metrics: {len(data['performance'])}")
            for perf in data['performance'][:3]:
                print(f"   • {perf.get('tag')}: {perf.get('performance'):.1f}% ({perf.get('status')})")
        
        if data.get('recommendations'):
            print(f"\n💡 Recommendations:")
            for rec in data['recommendations']:
                print(f"   • {rec}")
        
        return True
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🤖 Autonomous Insights System - Test Suite")
    print("="*80)
    print(f"Backend: {BACKEND_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Login
    token = login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return 1
    
    # Run tests
    tests = [
        ("Autonomous Summary", lambda: test_autonomous_summary(token)),
        ("Trigger Monitoring", lambda: test_trigger_monitoring(token)),
        ("Get Insights", lambda: test_get_insights(token)),
        ("Realtime Insight", lambda: test_realtime_insight(token)),
        ("Process Analysis", lambda: test_process_analysis(token)),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            time.sleep(1)  # Small delay between tests
        except Exception as e:
            print(f"❌ Exception in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("📊 Test Results Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*80}")
    print(f"Final Score: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*80}\n")
    
    if passed == total:
        print("🎉 All tests passed! Autonomous Insights System is operational!")
        print("\n✅ System Capabilities Validated:")
        print("   • Autonomous monitoring running")
        print("   • Insights generation working")
        print("   • Real-time analysis functional")
        print("   • Process health assessment active")
        print("   • Recommendations engine operational")
        return 0
    else:
        print("⚠️  Some tests failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    exit(main())
