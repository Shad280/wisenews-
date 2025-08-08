"""
WiseNews Deployment Guide
Step-by-step instructions for deploying your app to the internet
"""

import os
import json

def create_deployment_guide():
    print("🚀 WISENEWS DEPLOYMENT GUIDE")
    print("=" * 50)
    
    print("""
📋 DEPLOYMENT OPTIONS (Ranked by Ease):

1. 🟢 RAILWAY.APP (Easiest - Recommended)
   • Free tier available
   • Automatic deployments from GitHub
   • Built-in database hosting
   • Custom domains
   • One-click deploy

2. 🟡 RENDER.COM (Easy)
   • Free tier with limitations
   • GitHub integration
   • Automatic SSL
   • Good for Python apps

3. 🟡 HEROKU (Traditional)
   • Popular platform
   • Git-based deployment
   • Add-ons available
   • Free tier limited

4. 🟠 VERCEL (Frontend-focused)
   • Great for static sites
   • Serverless functions
   • Fast global CDN

5. 🔴 AWS/DigitalOcean (Advanced)
   • Full control
   • More complex setup
   • Better for scaling
   
RECOMMENDED: Railway.app for beginners!
""")

def create_railway_deployment():
    print("\n🚀 RAILWAY.APP DEPLOYMENT (RECOMMENDED)")
    print("-" * 40)
    
    print("""
STEP 1: Prepare Your App
========================
""")
    
    # Create requirements.txt
    requirements = """Flask==2.3.3
Flask-Caching==2.1.0
Flask-SocketIO==5.3.6
requests==2.31.0
python-socketio==5.8.0
python-engineio==4.7.1
gevent==23.7.0
werkzeug==2.3.7
jinja2==3.1.2
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ Created requirements.txt")
    
    # Create Procfile for Railway
    procfile = "web: python app.py"
    with open('Procfile', 'w') as f:
        f.write(procfile)
    
    print("✅ Created Procfile")
    
    # Create railway.json config
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "numReplicas": 1,
            "sleepApplication": False,
            "restartPolicyType": "ON_FAILURE"
        }
    }
    
    with open('railway.json', 'w') as f:
        json.dump(railway_config, f, indent=2)
    
    print("✅ Created railway.json")
    
    print("""
STEP 2: Modify app.py for Production
====================================
""")
    
    production_code = '''
# Add this to the end of your app.py file:

if __name__ == '__main__':
    import os
    
    # Get port from environment (Railway sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Get host from environment
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Initialize database
    init_db()
    
    print(f"🚀 Starting WiseNews on {host}:{port}")
    
    # Run with SocketIO support
    socketio.run(app, 
                host=host, 
                port=port, 
                debug=False,  # Always False in production
                allow_unsafe_werkzeug=True)
'''
    
    with open('production_app_config.py', 'w') as f:
        f.write(production_code)
    
    print("✅ Created production_app_config.py")
    print("   📝 Copy this code to the bottom of your app.py")
    
    print("""
STEP 3: Deploy to Railway
=========================

1. Visit https://railway.app
2. Sign up with GitHub account
3. Click "New Project" 
4. Select "Deploy from GitHub repo"
5. Choose your WiseNews repository
6. Railway will automatically:
   • Detect Python app
   • Install dependencies
   • Deploy your app
   • Give you a public URL

🌐 Your app will be live at: https://your-app.railway.app
""")

def create_render_deployment():
    print("\n🟡 RENDER.COM DEPLOYMENT")
    print("-" * 30)
    
    print("""
STEP 1: Create render.yaml
==========================
""")
    
    render_config = """services:
  - type: web
    name: wisenews
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    plan: free
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: PORT
        value: 10000
"""
    
    with open('render.yaml', 'w') as f:
        f.write(render_config)
    
    print("✅ Created render.yaml")
    
    print("""
STEP 2: Deploy to Render
========================

1. Visit https://render.com
2. Sign up with GitHub
3. Click "New" > "Web Service"
4. Connect your GitHub repo
5. Render will auto-detect Python app
6. Click "Create Web Service"

🌐 Your app will be live in minutes!
""")

def create_github_setup():
    print("\n📂 GITHUB REPOSITORY SETUP")
    print("-" * 30)
    
    gitignore = """# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.pytest_cache/
*.egg-info/
.installed.cfg
*.egg

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Environment variables
.env
.env.local
.env.production

# Cache
cache/
.cache/
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore)
    
    print("✅ Created .gitignore")
    
    print("""
GitHub Commands:
===============

git init
git add .
git commit -m "Initial WiseNews deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/wisenews.git
git push -u origin main

Replace YOUR_USERNAME with your GitHub username!
""")

def create_environment_config():
    print("\n🔧 ENVIRONMENT CONFIGURATION")
    print("-" * 35)
    
    env_example = """# Environment Variables for Production
# Copy this to your hosting platform's environment settings

PORT=5000
HOST=0.0.0.0
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=sqlite:///news_database.db

# Optional: External Database
# DATABASE_URL=postgresql://user:pass@host:port/dbname
# DATABASE_URL=mysql://user:pass@host:port/dbname

# Optional: Redis for caching
# REDIS_URL=redis://host:port

# Security
FLASK_DEBUG=False
TESTING=False
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_example)
    
    print("✅ Created .env.example")
    print("   📝 Configure these in your hosting platform")

def create_quick_deploy_script():
    print("\n⚡ QUICK DEPLOY SCRIPT")
    print("-" * 25)
    
    deploy_script = """#!/bin/bash
# Quick deploy script for WiseNews

echo "🚀 Preparing WiseNews for deployment..."

# Create production files
echo "📝 Creating production files..."

# Update app.py for production
echo "🔧 Configuring for production..."

# Check if git repo exists
if [ ! -d ".git" ]; then
    echo "📂 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial WiseNews deployment"
fi

echo "✅ Ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git remote add origin <your-repo-url>"
echo "2. Deploy to Railway: https://railway.app"
echo "3. Your app will be live in minutes!"
"""
    
    with open('deploy.sh', 'w') as f:
        f.write(deploy_script)
    
    # Make executable on Unix systems
    try:
        os.chmod('deploy.sh', 0o755)
    except:
        pass
    
    print("✅ Created deploy.sh")

if __name__ == "__main__":
    create_deployment_guide()
    create_railway_deployment()
    create_render_deployment()
    create_github_setup()
    create_environment_config()
    create_quick_deploy_script()
    
    print("\n" + "="*50)
    print("🎉 DEPLOYMENT FILES CREATED!")
    print("="*50)
    
    print("""
📁 Files created:
• requirements.txt (Python dependencies)
• Procfile (App startup command)
• railway.json (Railway configuration)  
• render.yaml (Render configuration)
• .gitignore (Git ignore rules)
• .env.example (Environment variables)
• deploy.sh (Quick deploy script)

🚀 RECOMMENDED NEXT STEPS:
1. Push your code to GitHub
2. Deploy to Railway.app (easiest option)
3. Your app will be live on the internet!

💡 Need help? The files contain detailed instructions.
""")
