# 🚀 Railway CLI Installation Guide

## 📱 **Install Node.js & Railway CLI**

### **Step 1: Install Node.js**
1. **Download Node.js:**
   - Go to: https://nodejs.org/
   - Click "Download for Windows" (LTS version recommended)
   - Run the installer (.msi file)
   - Follow installation wizard (accept defaults)

2. **Verify Installation:**
   Open PowerShell and run:
   ```powershell
   node --version
   npm --version
   ```
   Should show version numbers if installed correctly.

### **Step 2: Install Railway CLI**
In PowerShell, run:
```powershell
npm install -g @railway/cli
```

### **Step 3: Login to Railway**
```powershell
railway login
```
This will open your browser to authenticate.

### **Step 4: Check WiseNews Logs**
```powershell
railway logs
```
This will show the **actual error** causing the 502!

---

## 🔍 **What to Look For in Logs**

### **Common Error Patterns:**
- `ImportError: No module named 'xyz'` - Missing dependency
- `ModuleNotFoundError` - Package not in requirements.txt
- `SyntaxError` - Code syntax issue
- `MemoryError` - App using too much memory
- `Address already in use` - Port binding issue
- `sqlite3.OperationalError` - Database problem

### **Expected Log Output:**
```
Building...
Installing dependencies...
Starting gunicorn...
🗞️ WiseNews starting on 0.0.0.0:PORT
📊 Database: wisenews.db
🚀 Version: 3.0.0 - Railway Ready
```

If you see errors instead, that's what we need to fix!

---

## ⚡ **Quick Alternative (No Node.js)**

If you can't install Node.js right now:

1. **Railway Dashboard Logs:**
   - Go to: https://railway.app/dashboard
   - Click your WiseNews project
   - Go to "Deployments" tab
   - Click latest deployment
   - Check "Build Logs" and "Deploy Logs"

2. **Test Locally First:**
   ```powershell
   cd "c:\Users\Stamo\news scrapper"
   python app.py
   ```
   See if WiseNews starts locally without errors.

---

## 🎯 **After Getting Logs**

Once you see the actual error, we can:
1. **Fix the specific issue** (import, dependency, etc.)
2. **Update the code** accordingly
3. **Push to Railway** for redeployment
4. **Test the working app**

**The logs will tell us exactly what's wrong - no more guessing!** 🎯
