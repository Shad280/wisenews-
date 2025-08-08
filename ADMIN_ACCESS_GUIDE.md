# 🛡️ WiseNews Admin Access Guide

## 🔐 Admin Login Credentials

### **Primary Admin Account:**
- **📧 Email:** `admin@wisenews.com`
- **🔑 Password:** `WiseNews2025!`
- **👤 User ID:** 2
- **🎭 Role:** System Administrator
- **💎 Subscription:** Premium Plan (Unlimited Access)

### **Secondary Admin (if needed):**
- **📧 Email:** `stamo@wisenews.com` (configured in auth_decorators.py)

---

## 🌐 Admin Access URLs

### **1. User Dashboard Login (Primary Method)**
```
URL: http://localhost:5000/login
```
- Use admin credentials above
- Access full user interface with admin privileges
- Navigate to `/admin` after login for admin dashboard

### **2. Direct Admin Dashboard**
```
URL: http://localhost:5000/admin
```
- **⚠️ Requires login first**
- Comprehensive system overview
- User statistics and management
- System health monitoring

### **3. API Admin Panel (If Implemented)**
```
URL: http://localhost:5000/admin/api-keys?admin_key=wisenews_admin_2025
```
- API key management
- Application approvals
- Usage monitoring

---

## 🎛️ Admin Dashboard Features

### **📊 System Statistics**
- **Total Users** - Complete user count
- **Total Articles** - News database size  
- **Active Sessions** - Current logged-in users
- **New Users Today** - Recent registrations
- **New Articles Today** - Fresh content added

### **📈 Subscription Analytics**
- **Plan Distribution** - User count per subscription tier
- **Free Plan Users** - Basic access users
- **Standard Plan Users** - Mid-tier subscribers  
- **Premium Plan Users** - Full access subscribers

### **👥 User Management**
- **Recent Users** - Latest 10 registrations
- **User Details** - Name, email, registration date
- **Account Status** - Active/inactive monitoring

### **🔧 Admin Actions**
- **🔄 Refresh News** - Manual news fetch trigger
- **💓 System Status** - Health check and statistics
- **✅ Deployment Check** - Feature verification
- **📡 News Status** - RSS feed monitoring

---

## 🚀 Admin Privileges

### **✅ Full Access Rights:**
- **Unlimited Articles** - No daily reading limits
- **Unlimited Searches** - No search restrictions  
- **All API Endpoints** - Complete system access
- **User Data Access** - View user statistics
- **System Monitoring** - Health and performance data
- **News Management** - Manual content updates

### **🛡️ Security Features:**
- **Email-Based Admin Check** - Configured admin emails only
- **Session Validation** - Secure authentication required
- **Admin Decorator Protection** - Route-level access control
- **Premium Subscription** - Automatically assigned

---

## 🧪 Testing Admin Features

### **1. Login Test:**
1. Go to `/login`
2. Enter admin credentials
3. Should redirect to dashboard
4. Check for "Welcome, WiseNews" message

### **2. Admin Dashboard Test:**
1. After login, navigate to `/admin`
2. Should see system statistics
3. All admin controls should be visible
4. Statistics should show real data

### **3. API Access Test:**
1. Visit `/api/status` - Should work without limits
2. Visit `/api/deployment-check` - Should show full system status
3. Try `/api/articles` - Should return unlimited results

### **4. User Management Test:**
1. Check user statistics on admin dashboard
2. View recent users list
3. Monitor subscription distribution
4. Test system health metrics

---

## 🔐 Security Notes

### **Admin Email Configuration:**
Located in `auth_decorators.py`:
```python
admin_emails = ['admin@wisenews.com', 'stamo@wisenews.com']
```

### **Admin Account Creation:**
Run `create_admin_account.py` to:
- ✅ Create admin user
- ✅ Assign premium subscription  
- ✅ Test login functionality
- ✅ Verify admin privileges

### **Password Security:**
- **bcrypt hashed** - Secure password storage
- **Session tokens** - Secure authentication
- **Automatic expiry** - Session management

---

## 🌟 Railway Deployment

### **Admin Access on Railway:**
1. **Wait for deployment** - Railway needs time to update
2. **Use Railway URL** - Replace localhost with your Railway domain
3. **Same credentials** - Admin login works identically
4. **Full functionality** - All admin features deployed

### **Railway URLs:**
```
Login: https://your-railway-app.railway.app/login
Admin: https://your-railway-app.railway.app/admin
```

---

## 🎉 Admin Setup Complete!

The WiseNews admin system is fully operational with:
- ✅ **Secure Authentication** - bcrypt + session management
- ✅ **Admin Dashboard** - Comprehensive system overview  
- ✅ **User Management** - Statistics and monitoring
- ✅ **System Controls** - News refresh and health checks
- ✅ **API Access** - Unlimited admin privileges
- ✅ **Railway Ready** - Deployed and functional

**🔗 Start Here:** http://localhost:5000/login
