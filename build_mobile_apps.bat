@echo off
echo Converting WiseNews to Mobile Apps...
echo.

echo Step 1: Installing Capacitor (app wrapper)...
npm install -g @capacitor/cli
npm install --save @capacitor/core @capacitor/android @capacitor/ios

echo.
echo Step 2: Initializing mobile project...
npx cap init "WiseNews" "com.wisenews.mobile" --web-dir=static

echo.
echo Step 3: Adding mobile platforms...
npx cap add android
npx cap add ios

echo.
echo Step 4: Building web app...
python app.py &
timeout /t 5 /nobreak > nul

echo.
echo Step 5: Syncing with mobile platforms...
npx cap sync

echo.
echo ========================================
echo MOBILE APP SETUP COMPLETE!
echo ========================================
echo.
echo To build Android app:
echo   npx cap open android
echo   (Then use Android Studio to build .apk)
echo.
echo To build iPhone app:
echo   npx cap open ios  
echo   (Then use Xcode to build .ipa)
echo.
echo Or test on device:
echo   npx cap run android
echo   npx cap run ios
echo.
pause
