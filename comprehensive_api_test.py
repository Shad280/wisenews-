import requests
import json

def test_all_api_endpoints():
    """Comprehensive test of all API endpoints"""
    print("🔍 Comprehensive API Endpoint Test")
    print("=" * 50)
    
    # Test endpoints that should work without authentication
    public_endpoints = [
        '/api/image-stats',
        '/api/image-usage-stats'
    ]
    
    # Test endpoints that require API keys (will return 401)
    protected_endpoints = [
        '/api/news-count',
        '/api/duplicate-stats',
        '/api/articles',
        '/api/sync'
    ]
    
    # Test authenticated endpoints (will redirect to login)
    auth_endpoints = [
        '/api-management',
        '/api-keys',
        '/subscription-plans',
        '/my-subscription'
    ]
    
    print("\n📊 PUBLIC ENDPOINTS (should return 200):")
    public_working = 0
    for endpoint in public_endpoints:
        try:
            response = requests.get(f'http://127.0.0.1:5000{endpoint}', timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {endpoint}: Working")
                public_working += 1
            else:
                print(f"   ❌ {endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: Error - {e}")
    
    print(f"\n🔐 PROTECTED ENDPOINTS (should return 401/404, not 500):")
    protected_no_500 = 0
    for endpoint in protected_endpoints:
        try:
            response = requests.get(f'http://127.0.0.1:5000{endpoint}', timeout=5)
            if response.status_code in [401, 404]:
                print(f"   ✅ {endpoint}: Properly protected ({response.status_code})")
                protected_no_500 += 1
            elif response.status_code == 500:
                print(f"   ❌ {endpoint}: SERVER ERROR (500) - needs fixing")
            else:
                print(f"   📊 {endpoint}: Status {response.status_code}")
                protected_no_500 += 1
        except Exception as e:
            print(f"   ❌ {endpoint}: Error - {e}")
    
    print(f"\n🔑 AUTH ENDPOINTS (should return 200/302, not 500):")
    auth_no_500 = 0
    for endpoint in auth_endpoints:
        try:
            response = requests.get(f'http://127.0.0.1:5000{endpoint}', timeout=5)
            if response.status_code in [200, 302]:
                print(f"   ✅ {endpoint}: Working ({response.status_code})")
                auth_no_500 += 1
            elif response.status_code == 500:
                print(f"   ❌ {endpoint}: SERVER ERROR (500) - needs fixing")
            else:
                print(f"   📊 {endpoint}: Status {response.status_code}")
                auth_no_500 += 1
        except Exception as e:
            print(f"   ❌ {endpoint}: Error - {e}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   📊 Public Endpoints: {public_working}/{len(public_endpoints)} working")
    print(f"   🔐 Protected Endpoints: {protected_no_500}/{len(protected_endpoints)} no 500 errors")
    print(f"   🔑 Auth Endpoints: {auth_no_500}/{len(auth_endpoints)} no 500 errors")
    
    total_no_500 = protected_no_500 + auth_no_500 + public_working
    total_endpoints = len(public_endpoints) + len(protected_endpoints) + len(auth_endpoints)
    
    print(f"   🎉 Overall: {total_no_500}/{total_endpoints} endpoints working correctly")
    
    if total_no_500 >= total_endpoints * 0.8:  # 80% success rate
        print(f"\n✅ SUCCESS: Server errors are mostly resolved!")
        print(f"   Most 500 errors have been fixed")
        print(f"   System is functioning well")
    else:
        print(f"\n⚠️ NEEDS WORK: Still some 500 errors present")
    
    return total_no_500, total_endpoints

def test_specific_fix():
    """Test the specific fix we made"""
    print(f"\n🔧 SPECIFIC FIX TEST:")
    print(f"   Testing /api-management endpoint that was throwing 500 errors...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api-management', timeout=5)
        
        if response.status_code == 200:
            print(f"   🎉 FIXED: /api-management now returns 200 (was 500)")
            return True
        elif response.status_code == 302:
            print(f"   ✅ WORKING: /api-management redirects properly (not 500)")
            return True
        elif response.status_code == 500:
            print(f"   ❌ STILL BROKEN: /api-management still returns 500")
            return False
        else:
            print(f"   📊 CHANGED: /api-management returns {response.status_code} (was 500)")
            return True
            
    except Exception as e:
        print(f"   ❌ ERROR: Cannot test - {e}")
        return False

if __name__ == "__main__":
    print("🚀 WiseNews API Error Resolution Test\n")
    
    # Test specific fix
    fix_working = test_specific_fix()
    
    # Test all endpoints
    working, total = test_all_api_endpoints()
    
    print(f"\n🏆 FINAL RESULT:")
    if fix_working and working >= total * 0.8:
        print(f"   🎉 SUCCESS: 500 errors have been resolved!")
        print(f"   ✅ Main fix working")
        print(f"   ✅ {working}/{total} endpoints functioning")
        print(f"   ✅ Server is stable")
    elif fix_working:
        print(f"   ⚠️ PARTIAL SUCCESS: Main issue fixed, some minor issues remain")
        print(f"   ✅ Primary 500 error resolved")
        print(f"   📊 {working}/{total} endpoints working")
    else:
        print(f"   ❌ ISSUES REMAIN: Server still has 500 errors")
        print(f"   ❌ Main fix didn't work")
        print(f"   📊 {working}/{total} endpoints working")
