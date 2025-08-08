@echo off
echo ========================================
echo WiseNews - Custom Domain Deployment
echo ========================================
echo.

echo Choose your deployment platform:
echo.
echo 1. Railway (Free custom domain)
echo 2. Vercel (Free custom domain) 
echo 3. Netlify (Free custom domain)
echo 4. Heroku (Custom domain with plan)
echo 5. DigitalOcean (VPS with full control)
echo.

set /p choice="Enter choice (1-5): "

if %choice%==1 goto railway
if %choice%==2 goto vercel
if %choice%==3 goto netlify
if %choice%==4 goto heroku
if %choice%==5 goto digitalocean

:railway
echo.
echo ========================================
echo Railway Deployment (Recommended)
echo ========================================
echo.
echo 1. Go to https://railway.app
echo 2. Connect your GitHub account
echo 3. Import WiseNews repository
echo 4. Railway auto-deploys Python apps
echo 5. Get URL: https://wisenews.railway.app
echo.
echo For Custom Domain:
echo 6. Go to Settings -> Domains
echo 7. Add custom domain: wisenews.com
echo 8. Update DNS: CNAME -> your-app.railway.app
echo.
echo Result: https://wisenews.com (FREE!)
goto end

:vercel
echo.
echo ========================================
echo Vercel Deployment
echo ========================================
echo.
echo 1. Install Vercel CLI: npm i -g vercel
echo 2. Run: vercel --prod
echo 3. Connect to your GitHub repo
echo 4. Get URL: https://wisenews.vercel.app
echo.
echo For Custom Domain:
echo 5. Go to Vercel Dashboard -> Domains
echo 6. Add: wisenews.com
echo 7. Update DNS records as shown
echo.
echo Result: https://wisenews.com (FREE!)
goto end

:netlify
echo.
echo ========================================
echo Netlify Deployment
echo ========================================
echo.
echo 1. Go to https://netlify.com
echo 2. Connect GitHub repository
echo 3. Build command: python app.py
echo 4. Get URL: https://wisenews.netlify.app
echo.
echo For Custom Domain:
echo 5. Site Settings -> Domain Management
echo 6. Add custom domain: wisenews.com
echo 7. Update DNS: CNAME -> your-site.netlify.app
echo.
echo Result: https://wisenews.com (FREE!)
goto end

:heroku
echo.
echo ========================================
echo Heroku Deployment
echo ========================================
echo.
echo 1. Install Heroku CLI
echo 2. heroku create wisenews
echo 3. git push heroku main
echo 4. Get URL: https://wisenews.herokuapp.com
echo.
echo For Custom Domain (Requires paid plan):
echo 5. heroku domains:add wisenews.com
echo 6. Update DNS: CNAME -> your-app.herokuapp.com
echo.
echo Cost: $7/month for custom domain
goto end

:digitalocean
echo.
echo ========================================
echo DigitalOcean VPS Deployment
echo ========================================
echo.
echo 1. Create DigitalOcean Droplet ($5/month)
echo 2. Install Python and dependencies
echo 3. Configure Nginx reverse proxy
echo 4. Set up SSL with Let's Encrypt
echo 5. Point domain to server IP
echo.
echo Full control but requires technical setup
echo Cost: $5/month + domain ($12/year)
goto end

:end
echo.
echo ========================================
echo Google Search Visibility Setup
echo ========================================
echo.
echo After deployment:
echo 1. Register domain: wisenews.com (~$12/year)
echo 2. Set up Google Search Console
echo 3. Submit sitemap: /sitemap.xml
echo 4. Add to Google Analytics
echo 5. Create social media accounts
echo.
echo Expected Google visibility:
echo - Direct searches: 1-3 days
echo - Keyword searches: 2-4 weeks
echo - App store visibility: 1-2 weeks
echo.
echo Your WiseNews will be searchable as:
echo "wisenews.com" or "WiseNews app"
echo.
pause
