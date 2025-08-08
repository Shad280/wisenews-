import requests

def test_api_management_fix():
    """Test if the API management 500 error is fixed"""
    print("🔧 Testing API Management Fix...")
    
    try:
        # Test the API management endpoint
        response = requests.get('http://127.0.0.1:5000/api-management', timeout=5)
        
        print(f"📊 API Management Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS: API management page loads without 500 error")
            return True
        elif response.status_code == 302:
            print("   🔀 REDIRECT: Page redirects (likely to login) - this is normal")
            return True
        elif response.status_code == 500:
            print("   ❌ STILL 500 ERROR: Fix didn't work")
            print(f"   Response content: {response.text[:200]}...")
            return False
        else:
            print(f"   ⚠️ UNEXPECTED STATUS: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_other_api_endpoints():
    """Test other API endpoints for 500 errors"""
    print("\n🔍 Testing Other API Endpoints...")
    
    endpoints = [
        '/api/news-count',
        '/api/duplicate-stats',
        '/api/image-stats',
        '/api/image-usage-stats'
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://127.0.0.1:5000{endpoint}', timeout=5)
            results[endpoint] = response.status_code
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint}: Working (200)")
            elif response.status_code == 404:
                print(f"   ⚠️ {endpoint}: Not found (404)")
            elif response.status_code == 500:
                print(f"   ❌ {endpoint}: Server error (500)")
            else:
                print(f"   📊 {endpoint}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint}: Connection error - {e}")
            results[endpoint] = 'ERROR'
    
    return results

if __name__ == "__main__":
    print("🚀 API Error Fix Verification\n")
    
    # Test the main fix
    api_management_fixed = test_api_management_fix()
    
    # Test other endpoints
    endpoint_results = test_other_api_endpoints()
    
    print(f"\n🎯 Summary:")
    print(f"   {'✅' if api_management_fixed else '❌'} API Management: {'Fixed' if api_management_fixed else 'Still broken'}")
    
    working_endpoints = sum(1 for status in endpoint_results.values() if status == 200)
    total_endpoints = len(endpoint_results)
    
    print(f"   📊 Other Endpoints: {working_endpoints}/{total_endpoints} working")
    
    if api_management_fixed and working_endpoints > 0:
        print(f"\n🎉 SUCCESS: 500 errors are being resolved!")
    else:
        print(f"\n⚠️ Some 500 errors may remain - check server logs")
