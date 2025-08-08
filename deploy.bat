@echo off
echo 🚀 WiseNews Deployment Helper
echo =============================
echo.

echo Checking deployment files...
if exist requirements.txt (
    echo ✅ requirements.txt found
) else (
    echo ❌ requirements.txt missing
    goto :error
)

if exist Procfile (
    echo ✅ Procfile found  
) else (
    echo ❌ Procfile missing
    goto :error
)

if exist app.py (
    echo ✅ app.py found
) else (
    echo ❌ app.py missing
    goto :error
)

echo.
echo 🎉 All deployment files ready!
echo.
echo Next steps:
echo 1. Create GitHub repository at https://github.com/new
echo 2. Run these commands:
echo.
echo    git init
echo    git add .
echo    git commit -m "WiseNews deployment ready"
echo    git branch -M main
echo    git remote add origin https://github.com/YOUR_USERNAME/wisenews.git
echo    git push -u origin main
echo.
echo 3. Deploy to Railway.app:
echo    - Go to https://railway.app
echo    - Sign up with GitHub
echo    - Click "New Project" → "Deploy from GitHub repo"
echo    - Select your repository
echo    - Wait for deployment to complete
echo.
echo 🌐 Your app will be live on the internet!
echo.
pause
goto :end

:error
echo.
echo ❌ Missing deployment files. Please check your setup.
pause

:end
