#!/usr/bin/env python3
"""Test API management route functionality."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from user_auth import user_manager
from api_security import api_manager

def test_api_management():
    """Test the functions used in API management route."""
    print("🧪 Testing API management functions...")
    
    try:
        # Test user_manager.get_user_by_id
        print("\n1. Testing user_manager.get_user_by_id(1)...")
        user_data = user_manager.get_user_by_id(1)
        print(f"   ✅ Success: {user_data}")
        
        if user_data and 'email' in user_data:
            email = user_data['email']
            print(f"   Email: {email}")
            
            # Test api_manager.get_user_keys
            print(f"\n2. Testing api_manager.get_user_keys('{email}')...")
            api_keys = api_manager.get_user_keys(email)
            print(f"   ✅ Success: {len(api_keys)} keys found")
            for key in api_keys:
                print(f"   - {key['key_name']}: {key['status']}")
        else:
            print("   ❌ No user data or email found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_management()
#!/usr/bin/env python3
"""Test API management route functionality."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from user_auth import user_manager
from api_security import api_manager

def test_api_management():
    """Test the functions used in API management route."""
    print("🧪 Testing API management functions...")
    
    try:
        # Test user_manager.get_user_by_id
        print("\n1. Testing user_manager.get_user_by_id(1)...")
        user_data = user_manager.get_user_by_id(1)
        print(f"   ✅ Success: {user_data}")
        
        if user_data and 'email' in user_data:
            email = user_data['email']
            print(f"   Email: {email}")
            
            # Test api_manager.get_user_keys
            print(f"\n2. Testing api_manager.get_user_keys('{email}')...")
            api_keys = api_manager.get_user_keys(email)
            print(f"   ✅ Success: {len(api_keys)} keys found")
            for key in api_keys:
                print(f"   - {key['key_name']}: {key['status']}")
        else:
            print("   ❌ No user data or email found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_management()
