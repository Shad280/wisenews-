# News Aggregator Deployment Guide

## Option 1: Progressive Web App (PWA) - RECOMMENDED
This is the easiest approach that works on all devices.

### Setup Steps:
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create PWA icons:
   ```
   python create_icons.py
   ```

3. Run the app:
   ```
   python app.py
   ```

4. Access the app:
   - Open http://localhost:5000 in your browser
   - On mobile: Add to Home Screen from browser menu
   - On desktop: Install button will appear in the browser

### Deploy to Cloud (Heroku/Railway/Render):
1. Create Procfile:
   ```
   web: python app.py
   ```

2. Set environment variables:
   - PORT (auto-set by platform)
   - Any API keys you use

3. Deploy and access via your custom URL

## Option 2: Desktop App with Electron
For a native desktop application.

### Requirements:
- Node.js installed
- Python Flask app running

### Setup:
1. Install Electron:
   ```
   npm install electron --save-dev
   ```

2. Create electron-main.js (see files below)

3. Package the app:
   ```
   npm run build
   ```

## Option 3: Mobile App with Capacitor
For native mobile apps on iOS/Android.

### Requirements:
- Node.js
- Android Studio (for Android)
- Xcode (for iOS, Mac only)

### Setup:
1. Install Capacitor:
   ```
   npm install @capacitor/core @capacitor/cli
   ```

2. Initialize Capacitor project
3. Build and deploy to app stores

## Option 4: Docker Container
For consistent deployment across platforms.

### Setup:
1. Build Docker image:
   ```
   docker build -t news-aggregator .
   ```

2. Run container:
   ```
   docker run -p 5000:5000 news-aggregator
   ```

## Recommended Approach:
Start with the PWA option as it:
- Works on all devices
- No app store approval needed
- Easy to deploy and update
- Costs minimal to host
- Provides offline functionality
