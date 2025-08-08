"""
Quick Updates Performance Test
Test the performance improvements of the new quick updates system
"""

import requests
import time
import json
import asyncio
import websockets
from concurrent.futures import ThreadPoolExecutor
import statistics

class QuickUpdatesPerformanceTest:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.results = {
            'api_response_times': [],
            'websocket_response_times': [],
            'cache_hit_rates': [],
            'database_response_times': []
        }
    
    def test_api_performance(self, num_requests=100):
        """Test API endpoint response times"""
        print(f"🧪 Testing API performance with {num_requests} requests...")
        
        def make_request():
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/quick-updates/performance", timeout=5)
                end_time = time.time()
                if response.status_code == 200:
                    return (end_time - start_time) * 1000  # Convert to ms
            except Exception as e:
                print(f"Request failed: {e}")
            return None
        
        # Test sequential requests
        sequential_times = []
        for i in range(10):
            response_time = make_request()
            if response_time:
                sequential_times.append(response_time)
        
        # Test concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            concurrent_times = [f.result() for f in futures if f.result() is not None]
        
        self.results['api_response_times'] = {
            'sequential_avg': statistics.mean(sequential_times) if sequential_times else 0,
            'concurrent_avg': statistics.mean(concurrent_times) if concurrent_times else 0,
            'concurrent_min': min(concurrent_times) if concurrent_times else 0,
            'concurrent_max': max(concurrent_times) if concurrent_times else 0,
            'success_rate': len(concurrent_times) / num_requests * 100
        }
        
        print(f"✅ API Performance Results:")
        print(f"   Sequential Average: {self.results['api_response_times']['sequential_avg']:.2f}ms")
        print(f"   Concurrent Average: {self.results['api_response_times']['concurrent_avg']:.2f}ms")
        print(f"   Success Rate: {self.results['api_response_times']['success_rate']:.1f}%")
    
    def test_cached_articles_performance(self):
        """Test cached articles vs database performance"""
        print("🧪 Testing cached articles performance...")
        
        # Test cached articles endpoint
        cached_times = []
        for i in range(20):
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/quick-updates/cached-articles?limit=20")
                end_time = time.time()
                if response.status_code == 200:
                    cached_times.append((end_time - start_time) * 1000)
            except Exception as e:
                print(f"Cached request failed: {e}")
        
        # Test regular articles endpoint
        regular_times = []
        for i in range(20):
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/articles?limit=20")
                end_time = time.time()
                if response.status_code == 200:
                    regular_times.append((end_time - start_time) * 1000)
            except Exception as e:
                print(f"Regular request failed: {e}")
        
        cached_avg = statistics.mean(cached_times) if cached_times else 0
        regular_avg = statistics.mean(regular_times) if regular_times else 0
        improvement = ((regular_avg - cached_avg) / regular_avg * 100) if regular_avg > 0 else 0
        
        self.results['cache_performance'] = {
            'cached_avg_ms': cached_avg,
            'regular_avg_ms': regular_avg,
            'improvement_percent': improvement
        }
        
        print(f"✅ Cache Performance Results:")
        print(f"   Cached Articles: {cached_avg:.2f}ms")
        print(f"   Regular Articles: {regular_avg:.2f}ms")
        print(f"   Performance Improvement: {improvement:.1f}%")
    
    async def test_websocket_performance(self):
        """Test WebSocket real-time update performance"""
        print("🧪 Testing WebSocket performance...")
        
        try:
            uri = "ws://127.0.0.1:5000/socket.io/?transport=websocket"
            
            response_times = []
            
            async with websockets.connect(uri) as websocket:
                # Send ping messages and measure response time
                for i in range(20):
                    start_time = time.time()
                    
                    ping_message = json.dumps({
                        "type": "ping",
                        "timestamp": start_time
                    })
                    
                    await websocket.send(ping_message)
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        end_time = time.time()
                        response_times.append((end_time - start_time) * 1000)
                    except asyncio.TimeoutError:
                        print(f"Ping {i} timed out")
            
            if response_times:
                self.results['websocket_response_times'] = {
                    'avg_ms': statistics.mean(response_times),
                    'min_ms': min(response_times),
                    'max_ms': max(response_times),
                    'success_rate': len(response_times) / 20 * 100
                }
                
                print(f"✅ WebSocket Performance Results:")
                print(f"   Average Response: {statistics.mean(response_times):.2f}ms")
                print(f"   Min Response: {min(response_times):.2f}ms")
                print(f"   Max Response: {max(response_times):.2f}ms")
            else:
                print("❌ WebSocket test failed - no responses received")
                
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
    
    def test_update_trigger_performance(self):
        """Test quick update trigger performance"""
        print("🧪 Testing update trigger performance...")
        
        trigger_times = []
        
        for i in range(20):
            start_time = time.time()
            try:
                response = requests.post(f"{self.base_url}/api/quick-updates/trigger", 
                                       json={
                                           'type': 'test_update',
                                           'data': {'test_id': i, 'message': f'Test update {i}'},
                                           'priority': 'normal'
                                       })
                end_time = time.time()
                if response.status_code == 200:
                    trigger_times.append((end_time - start_time) * 1000)
            except Exception as e:
                print(f"Trigger request {i} failed: {e}")
        
        if trigger_times:
            avg_trigger_time = statistics.mean(trigger_times)
            self.results['trigger_performance'] = {
                'avg_ms': avg_trigger_time,
                'min_ms': min(trigger_times),
                'max_ms': max(trigger_times),
                'success_rate': len(trigger_times) / 20 * 100
            }
            
            print(f"✅ Update Trigger Performance:")
            print(f"   Average Trigger Time: {avg_trigger_time:.2f}ms")
            print(f"   Success Rate: {len(trigger_times) / 20 * 100:.1f}%")
        else:
            print("❌ Update trigger test failed")
    
    def get_system_metrics(self):
        """Get current system performance metrics"""
        try:
            response = requests.get(f"{self.base_url}/api/quick-updates/performance")
            if response.status_code == 200:
                metrics = response.json()
                print(f"📊 Current System Metrics:")
                print(f"   Total Updates: {metrics.get('total_updates', 0)}")
                print(f"   Avg Update Time: {metrics.get('avg_update_time_ms', 0):.2f}ms")
                print(f"   Cache Hit Rate: {metrics.get('cache_hit_rate_percent', 0):.1f}%")
                print(f"   Cached Articles: {metrics.get('cached_articles', 0)}")
                print(f"   Active Subscribers: {metrics.get('active_subscribers', 0)}")
                return metrics
        except Exception as e:
            print(f"Failed to get system metrics: {e}")
        return {}
    
    def generate_report(self):
        """Generate a comprehensive performance report"""
        print("\n" + "="*60)
        print("📈 QUICK UPDATES PERFORMANCE REPORT")
        print("="*60)
        
        # Overall performance assessment
        api_avg = self.results.get('api_response_times', {}).get('concurrent_avg', 0)
        cache_improvement = self.results.get('cache_performance', {}).get('improvement_percent', 0)
        
        print(f"\n🎯 PERFORMANCE SUMMARY:")
        print(f"   API Response Time: {api_avg:.2f}ms")
        print(f"   Cache Performance Improvement: {cache_improvement:.1f}%")
        
        if api_avg < 100:
            print("   🟢 EXCELLENT - Sub-100ms response times")
        elif api_avg < 200:
            print("   🟡 GOOD - Sub-200ms response times")
        else:
            print("   🔴 NEEDS IMPROVEMENT - >200ms response times")
        
        if cache_improvement > 50:
            print("   🟢 EXCELLENT - Cache providing significant speedup")
        elif cache_improvement > 20:
            print("   🟡 GOOD - Cache providing moderate speedup")
        else:
            print("   🔴 POOR - Cache not effective")
        
        print(f"\n📋 DETAILED RESULTS:")
        for category, results in self.results.items():
            print(f"   {category.replace('_', ' ').title()}: {results}")
        
        print("\n💡 RECOMMENDATIONS:")
        if api_avg > 150:
            print("   • Consider optimizing database queries")
            print("   • Increase cache size or TTL")
        if cache_improvement < 30:
            print("   • Review cache strategy")
            print("   • Consider pre-warming cache")
        
        print("="*60)

async def main():
    """Run all performance tests"""
    tester = QuickUpdatesPerformanceTest()
    
    print("🚀 Starting Quick Updates Performance Tests...\n")
    
    # Get baseline system metrics
    tester.get_system_metrics()
    print()
    
    # Run API performance tests
    tester.test_api_performance(50)
    print()
    
    # Test cached vs regular performance
    tester.test_cached_articles_performance()
    print()
    
    # Test WebSocket performance
    await tester.test_websocket_performance()
    print()
    
    # Test update triggers
    tester.test_update_trigger_performance()
    print()
    
    # Generate final report
    tester.generate_report()

if __name__ == "__main__":
    print("Quick Updates Performance Testing Tool")
    print("Make sure WiseNews is running on http://127.0.0.1:5000")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
