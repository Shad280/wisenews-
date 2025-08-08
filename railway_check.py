"""
Railway Environment Check for WiseNews 3.0.0
This script checks Railway-specific configurations
"""

import os

def check_railway_env():
    """Check Railway environment variables"""
    print("🚂 Railway Environment Check")
    print("=" * 40)
    
    # Check PORT
    port = os.environ.get('PORT')
    if port:
        print(f"✅ PORT: {port}")
    else:
        print("⚠️ PORT: Not set (using default 5000)")
    
    # Check RAILWAY_ENVIRONMENT
    env = os.environ.get('RAILWAY_ENVIRONMENT')
    if env:
        print(f"✅ RAILWAY_ENVIRONMENT: {env}")
    else:
        print("⚠️ RAILWAY_ENVIRONMENT: Not detected (local mode)")
    
    # Check other useful variables
    service_name = os.environ.get('RAILWAY_SERVICE_NAME')
    if service_name:
        print(f"✅ RAILWAY_SERVICE_NAME: {service_name}")
    
    project_id = os.environ.get('RAILWAY_PROJECT_ID')
    if project_id:
        print(f"✅ RAILWAY_PROJECT_ID: {project_id}")
    
    # Check if we're in production
    is_production = env == 'production'
    print(f"🎯 Production Mode: {'✅ YES' if is_production else '❌ NO (dev/local)'}")
    
    return is_production

def check_app_config():
    """Check app configuration for Railway"""
    print("\n⚙️ App Configuration")
    print("=" * 40)
    
    # Import app to check configuration
    try:
        from app import app
        print(f"✅ Flask app loaded successfully")
        print(f"✅ Debug mode: {app.debug}")
        print(f"✅ Secret key: {'Set' if app.secret_key else 'NOT SET'}")
        
        # Check database configuration  
        db_path = app.config.get('DATABASE', 'wisenews.db')
        print(f"✅ Database path: {db_path}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading app: {e}")
        return False

def main():
    is_production = check_railway_env()
    app_ok = check_app_config()
    
    print("\n" + "=" * 40)
    if app_ok:
        print("✅ Railway configuration looks good!")
        if is_production:
            print("🚀 Running in Railway production environment")
        else:
            print("🔧 Running in local development mode")
    else:
        print("❌ Configuration issues detected")
    
    print("\n🌐 Expected URLs:")
    if is_production:
        print("Production: https://your-railway-domain.railway.app")
    print("Local: http://localhost:5000")

if __name__ == '__main__':
    main()
