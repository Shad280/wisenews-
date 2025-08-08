@echo off
echo Installing Flask and web app dependencies...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
)

REM Install web app requirements
echo Installing web application dependencies...
pip install -r requirements.txt

echo.
echo ===============================================
echo  News Aggregator Web App Setup Complete!
echo ===============================================
echo.
echo To run the web application:
echo   1. Make sure your virtual environment is active
echo   2. Run: python app.py
echo   3. Open your browser to: http://localhost:5000
echo.
echo The app will automatically load existing articles
echo and provide a web interface to:
echo   - Browse and search all articles
echo   - View analytics and statistics  
echo   - Run the news scraper from the web interface
echo   - Bookmark and organize articles
echo.
pause
