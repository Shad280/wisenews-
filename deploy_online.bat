@echo off
echo Deploying WiseNews Online...
echo.

echo Choose deployment platform:
echo 1. Railway (Recommended - Free)
echo 2. Heroku (Popular)
echo 3. Render (Simple)
echo.

set /p choice="Enter choice (1-3): "

if %choice%==1 goto railway
if %choice%==2 goto heroku
if %choice%==3 goto render

:railway
echo.
echo Setting up Railway deployment...
echo.
echo 1. Go to https://railway.app
echo 2. Sign up with GitHub
echo 3. Click "New Project" → "Deploy from GitHub repo"
echo 4. Select your WiseNews repo
echo 5. Railway auto-detects Python and deploys!
echo.
echo Your app will be live at: https://wisenews.railway.app
goto end

:heroku
echo.
echo Setting up Heroku deployment...
echo.
echo 1. Go to https://heroku.com and sign up
echo 2. Install Heroku CLI
echo 3. Run: heroku create wisenews
echo 4. Run: git push heroku main
echo.
echo Your app will be live at: https://wisenews.herokuapp.com
goto end

:render
echo.
echo Setting up Render deployment...
echo.
echo 1. Go to https://render.com and sign up
echo 2. Click "New" → "Web Service"
echo 3. Connect your GitHub repo
echo 4. Render auto-builds and deploys!
echo.
echo Your app will be live at: https://wisenews.onrender.com
goto end

:end
echo.
echo ========================================
echo DEPLOYMENT SETUP COMPLETE!
echo ========================================
echo.
echo After deployment, users can:
echo 1. Visit your public URL
echo 2. Install as app on their phone/computer
echo 3. Use offline when no internet
echo.
echo Files ready for deployment:
echo ✅ Procfile (tells server how to run app)
echo ✅ requirements.txt (Python dependencies)
echo ✅ Dockerfile (containerized deployment)
echo.
pause
