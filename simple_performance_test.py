"""
Simple Quick Updates Test
Test basic functionality without complex WebSocket testing
"""

import requests
import time

def test_basic_functionality():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing WiseNews with Quick Updates...")
    
    # Test main page
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Main page: {response.status_code}")
    except Exception as e:
        print(f"❌ Main page failed: {e}")
    
    # Test articles page
    try:
        response = requests.get(f"{base_url}/articles", timeout=5)
        print(f"✅ Articles page: {response.status_code}")
    except Exception as e:
        print(f"❌ Articles page failed: {e}")
    
    # Test API endpoints that don't require auth
    try:
        response = requests.get(f"{base_url}/api/news-count", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News count API: {data}")
        else:
            print(f"⚠️ News count API: {response.status_code}")
    except Exception as e:
        print(f"❌ News count API failed: {e}")
    
    # Test live events
    try:
        response = requests.get(f"{base_url}/live-events", timeout=5)
        print(f"✅ Live events page: {response.status_code}")
    except Exception as e:
        print(f"❌ Live events failed: {e}")
    
    print("\n📊 Performance Test - Loading Articles:")
    
    # Test articles loading performance
    times = []
    for i in range(5):
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}/articles", timeout=10)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            times.append(response_time)
            print(f"   Request {i+1}: {response_time:.2f}ms")
        except Exception as e:
            print(f"   Request {i+1}: Failed - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📈 Articles Loading Performance:")
        print(f"   Average: {avg_time:.2f}ms")
        print(f"   Fastest: {min_time:.2f}ms")
        print(f"   Slowest: {max_time:.2f}ms")
        
        if avg_time < 200:
            print("   🟢 EXCELLENT - Very fast loading")
        elif avg_time < 500:
            print("   🟡 GOOD - Acceptable loading speed")
        else:
            print("   🔴 SLOW - Consider optimization")
    
    # Test optimized API endpoints
    print("\n⚡ Testing Optimized API Endpoints:")
    
    # Test fast articles API
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/articles-fast?per_page=20", timeout=10)
        response_time = (time.time() - start_time) * 1000
        if response.status_code == 200:
            print(f"   Fast Articles API: {response_time:.2f}ms ✅")
        else:
            print(f"   Fast Articles API: {response.status_code} ⚠️")
    except Exception as e:
        print(f"   Fast Articles API: Failed - {e}")
    
    # Test fast stats API
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/stats-fast", timeout=10)
        response_time = (time.time() - start_time) * 1000
        if response.status_code == 200:
            print(f"   Fast Stats API: {response_time:.2f}ms ✅")
        else:
            print(f"   Fast Stats API: {response.status_code} ⚠️")
    except Exception as e:
        print(f"   Fast Stats API: Failed - {e}")

if __name__ == "__main__":
    test_basic_functionality()
