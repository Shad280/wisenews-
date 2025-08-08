@echo off
REM WiseNews Server Optimization and Startup Script for Windows
REM Optimizes current server for production use

echo ========================================
echo WiseNews Server Optimization Script
echo ========================================

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache

echo [1/6] Setting up environment...
set FLASK_ENV=production
set PYTHONOPTIMIZE=2

echo [2/6] Running database optimization...
python server_optimizer.py

echo [3/6] Testing optimized database connections...
python -c "from server_optimizer import optimizer; print('Database pool test:', len(optimizer.db_pool))"

echo [4/6] Clearing old cache files...
if exist "cache\*" del /q cache\*

echo [5/6] Starting optimized production server...
echo.
echo Server Configuration:
echo - Database: SQLite with WAL mode and connection pooling
echo - Caching: Filesystem cache with 5-minute TTL
echo - Compression: Gzip for responses > 1KB
echo - Memory: Optimized for 16GB RAM system
echo - Protection: Anti-scraping with rate limiting
echo.

REM Start the server with optimizations
python -c "
import os
os.environ['FLASK_ENV'] = 'production'
from app import app
from server_optimizer import optimizer

# Initialize optimizations
print('Initializing server optimizations...')
optimizer.run_full_optimization()

print('Starting Flask development server with optimizations...')
print('Access your optimized WiseNews at: http://localhost:5000')
print('Press Ctrl+C to stop the server')
print('')

# Start Flask with threading and optimizations
app.run(
    host='0.0.0.0',
    port=5000,
    debug=False,
    threaded=True,
    use_reloader=False,
    processes=1
)
"

echo [6/6] Server stopped. Cleaning up...
echo Optimization complete!
pause
