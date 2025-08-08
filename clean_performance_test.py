"""
Clean Performance Test
Test the application with only essential optimizations
"""

import requests
import time

def test_clean_performance():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing WiseNews with ESSENTIAL optimizations only...")
    print("=" * 60)
    
    # Test basic endpoints
    endpoints = [
        ("Main page", "/"),
        ("Articles page", "/articles"), 
        ("FAST Articles page", "/articles-fast"),  # Test our new optimized route
        ("Live events", "/live-events"),
        ("News count API", "/api/news-count"),
    ]
    
    print("🌐 Basic Functionality:")
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status_icon = "✅" if response.status_code == 200 else "⚠️"
            print(f"   {status_icon} {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: Failed - {e}")
    
    # Performance test - both regular and fast articles pages
    print(f"\n⚡ Articles Page Performance Comparison:")
    print("-" * 50)
    
    # Test regular articles page
    print("📄 Regular Articles Page:")
    times = []
    for i in range(3):
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/articles", timeout=10)
            response_time = (time.time() - start_time) * 1000
            times.append(response_time)
            
            status_icon = "🟢" if response_time < 200 else "🟡" if response_time < 500 else "🔴"
            print(f"   {status_icon} Request {i+1}: {response_time:.2f}ms")
            
        except Exception as e:
            print(f"   ❌ Request {i+1}: Failed - {e}")
    
    regular_avg = sum(times) / len(times) if times else 0
    
    # Test fast articles page
    print(f"\n⚡ FAST Articles Page:")
    fast_times = []
    for i in range(3):
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/articles-fast", timeout=10)
            response_time = (time.time() - start_time) * 1000
            fast_times.append(response_time)
            
            status_icon = "🟢" if response_time < 200 else "🟡" if response_time < 500 else "🔴"
            print(f"   {status_icon} Request {i+1}: {response_time:.2f}ms")
            
        except Exception as e:
            print(f"   ❌ Request {i+1}: Failed - {e}")
    
    fast_avg = sum(fast_times) / len(fast_times) if fast_times else 0
    
    if times or fast_times:
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print("-" * 30)
        
        if regular_avg > 0:
            print(f"📄 Regular Articles: {regular_avg:.2f}ms average")
        if fast_avg > 0:
            print(f"⚡ Fast Articles: {fast_avg:.2f}ms average")
        
        if regular_avg > 0 and fast_avg > 0:
            improvement = ((regular_avg - fast_avg) / regular_avg) * 100
            print(f"🚀 Speed Improvement: {improvement:.1f}% faster!")
        
        # Use the better performing version for rating
        avg_time = fast_avg if fast_avg > 0 and fast_avg < regular_avg else regular_avg
        min_time = min(fast_times) if fast_times else min(times) if times else 0
        max_time = max(fast_times) if fast_times else max(times) if times else 0
        
        print(f"\n� BEST PERFORMANCE ACHIEVED:")
        print(f"   Average: {avg_time:.2f}ms")
        print(f"   Best: {min_time:.2f}ms") 
        print(f"   Worst: {max_time:.2f}ms")
        
        # Performance rating
        if avg_time < 200:
            rating = "🟢 EXCELLENT"
            message = "Lightning fast! Users will love this."
        elif avg_time < 350:
            rating = "🟡 GOOD" 
            message = "Fast enough for great user experience."
        elif avg_time < 500:
            rating = "🟠 ACCEPTABLE"
            message = "Decent performance, could be better."
        else:
            rating = "🔴 SLOW"
            message = "Still needs optimization work."
        
        print(f"\n🎯 RATING: {rating}")
        print(f"💬 {message}")
        
        # Compare to before optimization
        baseline = 575  # Original performance
        improvement = ((baseline - avg_time) / baseline) * 100
        
        if improvement > 0:
            print(f"📈 IMPROVEMENT: {improvement:.1f}% faster than baseline")
            print(f"   Before: ~{baseline}ms → After: ~{avg_time:.0f}ms")
        
        print(f"\n{'='*60}")
        print("✨ CONCLUSION:")
        if avg_time < 300:
            print("🎉 Essential optimizations were SUCCESSFUL!")
            print("💡 No need for complex optimization layers.")
            print("🚀 Your app is now fast and maintainable.")
        else:
            print("🤔 May need a few more optimizations...")
            print("💡 But keep it simple - avoid over-engineering!")
        
        print(f"{'='*60}")

if __name__ == "__main__":
    test_clean_performance()
