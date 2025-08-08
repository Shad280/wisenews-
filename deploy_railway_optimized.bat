@echo off
echo 🚀 Deploying WiseNews Railway Optimized Version
echo.

echo 📝 Backing up current Procfile...
copy Procfile Procfile_backup
copy Procfile_optimized Procfile

echo 🔄 Committing optimized version...
git add .
git commit -m "Railway Optimized: Reduced memory usage, simplified news fetching"

echo 🚀 Pushing to Railway...
git push

echo.
echo ✅ Railway Optimized deployment complete!
echo 🌐 Check: https://web-production-1f6d.up.railway.app
echo.
echo Key optimizations:
echo - Reduced news sources from 18 to 3
echo - Removed background processes
echo - Simplified database operations
echo - Added memory-efficient news fetching
echo.
pause
