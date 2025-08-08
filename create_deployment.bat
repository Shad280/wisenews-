@echo off
echo 🚀 WiseNews Deployment Package Creator
echo =====================================
echo.

echo ✅ Creating deployment folder...
if not exist "deployment" mkdir deployment

echo ✅ Copying essential files...
copy app_minimal.py deployment\ >nul 2>&1
copy requirements_minimal.txt deployment\ >nul 2>&1
copy Procfile deployment\ >nul 2>&1
copy runtime.txt deployment\ >nul 2>&1

echo ✅ Copying templates folder...
if exist "templates" (
    if not exist "deployment\templates" mkdir deployment\templates
    copy templates\*.html deployment\templates\ >nul 2>&1
)

echo.
echo 🎉 Deployment package ready!
echo.
echo 📁 Files in deployment folder:
dir deployment /b
echo.
echo 📋 Next Steps:
echo 1. Go to your hosting platform (Railway, Render, Heroku)
echo 2. Choose "Upload files" or "Deploy from local"
echo 3. Upload all files from the 'deployment' folder
echo 4. Deploy and enjoy your live WiseNews app!
echo.
pause
