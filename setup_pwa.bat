@echo off
echo Setting up WiseNews PWA...

echo Installing Python dependencies...
pip install -r requirements.txt

echo Creating PWA icons...
python create_icons.py

echo.
echo Setup complete!
echo.
echo To start WiseNews:
echo   python app.py
echo.
echo Then open http://localhost:5000 in your browser
echo On mobile: Use "Add to Home Screen" option
echo On desktop: Click the install button when it appears
echo.
pause
