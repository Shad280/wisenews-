@echo off
echo Setting up Git repository for WiseNews...
echo.

cd /d "c:\Users\Stamo\news scrapper\render_deployment"

echo Initializing Git repository...
git init

echo Adding files...
git add .

echo Creating first commit...
git commit -m "Initial WiseNews deployment"

echo.
echo ============================================
echo Git repository created successfully!
echo ============================================
echo.
echo Next steps:
echo 1. Create a new repository on GitHub.com
echo 2. Copy the repository URL
echo 3. Run: git remote add origin YOUR_GITHUB_URL
echo 4. Run: git push -u origin main
echo.
echo Then connect your GitHub repo to Render for automatic deployments!
echo.
pause
