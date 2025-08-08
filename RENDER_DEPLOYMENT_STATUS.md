# WiseNews - Production Ready Deployment

## Files Status:
✅ app.py - Simplified Flask application
✅ requirements.txt - Flask==2.3.3, gunicorn==21.2.0  
✅ Procfile - web: gunicorn app:app
✅ templates/ - All HTML templates included

## GitHub Repository: 
https://github.com/Shad280/wisenews-

## Manual Render Configuration:
If automatic deployment fails, use these settings in Render:

**Build Command:** 
pip install -r requirements.txt

**Start Command:** 
gunicorn app:app

**Environment Variables:**
PORT=5000
FLASK_ENV=production

## Alternative Start Commands (if gunicorn fails):
python app.py

## Database:
SQLite database will be created automatically with sample data.

## Expected URLs after deployment:
- Main site: https://wisenews-app.onrender.com
- API health: https://wisenews-app.onrender.com/api/status
- Articles: https://wisenews-app.onrender.com/api/articles

## Troubleshooting 502 Errors:
1. Check Start Command in Render dashboard
2. Verify GitHub Procfile is updated
3. Check Render build logs for errors
4. Ensure gunicorn is in requirements.txt
