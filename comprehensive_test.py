#!/usr/bin/env python3
"""Comprehensive test to verify API and live events fixes."""

import requests
import time
import sqlite3

def test_api_routes():
    """Test API routes for 500 errors."""
    print("🧪 Testing API routes...")
    
    base_url = "http://127.0.0.1:5000"
    test_routes = [
        "/api-management",
        "/api-keys", 
        "/subscription-plans",
        "/my-subscription",
        "/export-user-data"
    ]
    
    results = {}
    
    for route in test_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            results[route] = {
                'status_code': response.status_code,
                'status': 'OK' if response.status_code != 500 else 'ERROR'
            }
            print(f"  {route}: {response.status_code} - {'✅' if response.status_code != 500 else '❌'}")
        except Exception as e:
            results[route] = {
                'status_code': 'CONNECTION_ERROR',
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"  {route}: Connection error - ❌")
    
    return results

def test_live_events_duplicates():
    """Test live events for duplicates."""
    print("\n🧪 Testing live events duplicates...")
    
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    # Check for duplicates in last 5 minutes
    cursor.execute('''
        SELECT event_name, COUNT(*) as count 
        FROM live_events 
        WHERE start_time >= datetime('now', '-5 minutes')
        GROUP BY event_name 
        HAVING count > 1 
        ORDER BY count DESC
    ''')
    
    recent_duplicates = cursor.fetchall()
    
    print(f"  Recent duplicates (last 5 min): {len(recent_duplicates)}")
    for dup in recent_duplicates:
        print(f"    - {dup[0][:50]}: {dup[1]} instances")
    
    # Check active events count
    cursor.execute("SELECT COUNT(*) FROM live_events WHERE status IN ('active', 'live')")
    active_count = cursor.fetchone()[0]
    print(f"  Active events: {active_count}")
    
    # Check very old events that should be cleaned up
    cursor.execute("SELECT COUNT(*) FROM live_events WHERE start_time < datetime('now', '-10 minutes') AND status IN ('active', 'live')")
    old_active_count = cursor.fetchone()[0]
    print(f"  Old active events (>10 min): {old_active_count}")
    
    conn.close()
    
    return {
        'recent_duplicates': len(recent_duplicates),
        'active_events': active_count,
        'old_active_events': old_active_count
    }

def check_server_logs():
    """Check for errors in server output."""
    print("\n🧪 Checking server status...")
    
    try:
        # Test basic server connectivity
        response = requests.get("http://127.0.0.1:5000/", timeout=5)
        server_status = "UP" if response.status_code == 200 else f"Error {response.status_code}"
        print(f"  Server status: {server_status}")
        return {'server_status': server_status}
    except Exception as e:
        print(f"  Server status: DOWN - {e}")
        return {'server_status': 'DOWN', 'error': str(e)}

def main():
    """Run comprehensive tests."""
    print("🔍 Running comprehensive system tests...\n")
    
    # Test API routes
    api_results = test_api_routes()
    
    # Test live events
    live_events_results = test_live_events_duplicates()
    
    # Check server
    server_results = check_server_logs()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)
    
    # API Results
    api_errors = sum(1 for r in api_results.values() if r['status'] == 'ERROR')
    print(f"API Routes: {len(api_results) - api_errors}/{len(api_results)} working - {'✅' if api_errors == 0 else '❌'}")
    
    # Live Events Results
    live_events_good = (live_events_results['recent_duplicates'] == 0 and 
                       live_events_results['old_active_events'] == 0)
    print(f"Live Events: {'✅' if live_events_good else '❌'}")
    print(f"  - Recent duplicates: {live_events_results['recent_duplicates']}")
    print(f"  - Old active events: {live_events_results['old_active_events']}")
    
    # Server Status
    server_good = server_results['server_status'] in ['UP', 'Error 302', 'Error 200']
    print(f"Server Status: {server_results['server_status']} - {'✅' if server_good else '❌'}")
    
    # Overall Status
    overall_good = api_errors == 0 and live_events_good and server_good
    print(f"\nOverall System Status: {'✅ HEALTHY' if overall_good else '❌ ISSUES DETECTED'}")
    
    if not overall_good:
        print("\n🔧 Recommendations:")
        if api_errors > 0:
            print("  - Check API route authentication and dependencies")
        if not live_events_good:
            print("  - Live events cleanup needed")
        if not server_good:
            print("  - Server connectivity issues")

if __name__ == "__main__":
    main()
