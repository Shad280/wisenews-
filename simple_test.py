#!/usr/bin/env python3
"""
Simple Railway App Test
Quick test of WiseNews startup
"""

import sys
import os

print("🧪 SIMPLE RAILWAY APP TEST")
print("=" * 40)

print("1. Testing Python imports...")
try:
    import flask
    print("   ✅ Flask available")
except ImportError:
    print("   ❌ Flask not available")

try:
    import gunicorn
    print("   ✅ Gunicorn available")
except ImportError:
    print("   ❌ Gunicorn not available")

try:
    import bcrypt
    print("   ✅ Bcrypt available")
except ImportError:
    print("   ❌ Bcrypt not available")

print("\n2. Testing file structure...")
files = ['app.py', 'Procfile', 'requirements.txt', 'user_auth.py', 'auth_decorators.py']
for file in files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} missing")

print("\n3. Testing Procfile...")
if os.path.exists('Procfile'):
    with open('Procfile', 'r') as f:
        content = f.read().strip()
    print(f"   Content: {content}")
    if content == "web: gunicorn app:app":
        print("   ✅ Procfile correct")
    else:
        print("   ❌ Procfile incorrect")

print("\n4. Testing app.py syntax...")
try:
    with open('app.py', 'r', encoding='utf-8') as f:
        code = f.read()
    compile(code, 'app.py', 'exec')
    print("   ✅ app.py syntax valid")
except Exception as e:
    print(f"   ❌ app.py syntax error: {e}")

print("\n🎯 CONCLUSION:")
print("If all above tests pass, Railway deployment should work.")
print("The issue is likely that Railway is still building/starting.")
print("\n⏰ Wait 5-10 minutes, then try your Railway URL again!")
print("\n📋 If still not working:")
print("1. Check Railway dashboard for deployment logs")
print("2. Install Railway CLI: npm install -g @railway/cli")
print("3. Run: railway logs")
