"""
WiseNews Admin Test Account Creator & Access Guide
=================================================

This script creates a test admin user and shows you how to access admin features.
"""

import sqlite3
import bcrypt
from datetime import datetime
import secrets

def create_test_admin():
    """Create a test admin account for testing WiseNews features"""
    
    print("🌟 Creating WiseNews Test Admin Account...")
    
    # Admin credentials
    admin_email = "admin@wisenews.com"
    admin_password = "WiseNews2025!"
    admin_first_name = "WiseNews"
    admin_last_name = "Administrator"
    
    # Hash password
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        conn = sqlite3.connect('wisenews.db')  # Updated to match main app database
        cursor = conn.cursor()
        
        # Check if admin already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (admin_email,))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print("✅ Admin account already exists!")
            admin_id = existing_admin[0]
        else:
            # Create admin user
            cursor.execute('''
                INSERT INTO users (
                    email, password_hash, first_name, last_name, 
                    is_active, is_verified, gdpr_consent, data_processing_consent,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                admin_email, password_hash, admin_first_name, admin_last_name,
                True, True, True, True, datetime.now().isoformat()
            ))
            
            admin_id = cursor.lastrowid
            print("✅ Admin account created successfully!")
        
        # Make sure admin has a premium subscription
        cursor.execute('SELECT id FROM user_subscriptions WHERE user_id = ?', (admin_id,))
        existing_sub = cursor.fetchone()
        
        if not existing_sub:
            # Get premium plan ID (plan_id = 3 for premium)
            cursor.execute('''
                INSERT INTO user_subscriptions (
                    user_id, plan_id, status, 
                    subscription_start_date, subscription_end_date,
                    auto_renew
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                admin_id, 3, 'active',  # Plan ID 3 is Premium
                datetime.now().isoformat(), '2026-12-31',
                True
            ))
            print("✅ Admin premium subscription created!")
        
        conn.commit()
        conn.close()
        
        print("\n🌟 WiseNews Test Admin Account Ready!")
        print("=" * 50)
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print(f"🆔 User ID: {admin_id}")
        print("=" * 50)
        
        return admin_email, admin_password, admin_id
        
    except Exception as e:
        print(f"❌ Error creating admin account: {e}")
        return None, None, None

def show_access_guide(admin_email, admin_password):
    """Show how to access WiseNews admin features"""
    
    print("\n🚀 How to Access WiseNews Admin Features:")
    print("=" * 60)
    
    print("\n1️⃣ **User Dashboard Login:**")
    print("   URL: http://127.0.0.1:5000/login")
    print(f"   Email: {admin_email}")
    print(f"   Password: {admin_password}")
    print("   → Access full user dashboard with admin privileges")
    
    print("\n2️⃣ **API Admin Panel:**")
    print("   URL: http://127.0.0.1:5000/admin/api-keys?admin_key=wisenews_admin_2025")
    print("   → Manage API keys, approve applications, monitor usage")
    
    print("\n3️⃣ **Test User-Friendly Messages:**")
    print("   → Login to dashboard first")
    print("   → Navigate to different sections")
    print("   → Try making multiple rapid requests to test rate limiting")
    print("   → Check API endpoints for friendly error messages")
    
    print("\n4️⃣ **Features to Test:**")
    print("   ✅ Article browsing with unlimited access")
    print("   ✅ API key management")
    print("   ✅ User-friendly rate limit messages")
    print("   ✅ Premium subscription features")
    print("   ✅ Live feeds and notifications")
    print("   ✅ Social media integration")
    
    print("\n5️⃣ **Rate Limiting Test:**")
    print("   → Use the test scripts we created earlier")
    print("   → Now you'll see WiseNews-branded friendly messages!")
    
    print("\n🌟 WiseNews Brand Messages Include:")
    print("   • Emojis and friendly tone")
    print("   • 'WiseNews' brand mentions")
    print("   • Encouraging upgrade messages")
    print("   • Professional but approachable language")

def test_admin_login():
    """Test if admin can login successfully"""
    print("\n🧪 Testing Admin Login...")
    
    from user_auth import user_manager
    
    admin_email = "admin@wisenews.com"
    admin_password = "WiseNews2025!"
    
    # Test authentication
    success, message, user_id = user_manager.authenticate_user(admin_email, admin_password, "127.0.0.1")
    
    if success:
        print("✅ Admin login test successful!")
        print(f"   User ID: {user_id}")
        print(f"   Message: {message}")
        return True
    else:
        print(f"❌ Admin login test failed: {message}")
        return False

if __name__ == "__main__":
    print("🌟 WiseNews Admin Setup & Testing Guide")
    print("=" * 50)
    
    # Create admin account
    admin_email, admin_password, admin_id = create_test_admin()
    
    if admin_email:
        # Show access guide
        show_access_guide(admin_email, admin_password)
        
        # Test login
        test_admin_login()
        
        print("\n🎉 Setup Complete! You can now test WiseNews admin features.")
        print("🔗 Start by visiting: http://127.0.0.1:5000/login")
    else:
        print("❌ Setup failed. Check the error messages above.")
