@echo off
echo ========================================
echo WiseNews - Railway Deployment Setup
echo ========================================
echo.

echo Checking Git repository...
if not exist .git (
    echo Initializing Git repository...
    git init
    echo.
) else (
    echo Git repository already exists ✓
    echo.
)

echo Checking .gitignore...
if not exist .gitignore (
    echo Creating .gitignore...
    echo __pycache__/> .gitignore
    echo *.pyc>> .gitignore
    echo .env>> .gitignore
    echo .vscode/>> .gitignore
    echo *.log>> .gitignore
    echo.
) else (
    echo .gitignore already exists ✓
    echo.
)

echo Adding all files to Git...
git add .
git commit -m "WiseNews - Ready for Railway deployment"
echo.

echo ========================================
echo Railway Deployment Ready! 🚀
echo ========================================
echo.
echo Next steps:
echo 1. Go to https://railway.app
echo 2. Click "Start a New Project"
echo 3. Choose "GitHub Repo" 
echo 4. Select this WiseNews repository
echo 5. Click "Deploy"
echo.
echo Your app will be live in 2-3 minutes!
echo URL will be: https://wisenews-production-xyz.up.railway.app
echo.
echo For detailed instructions, see: RAILWAY_DEPLOYMENT.md
echo.
pause
