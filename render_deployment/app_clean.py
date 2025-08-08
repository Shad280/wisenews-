from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
import hashlib

app = Flask(__name__)
app.secret_key = 'wisenews-secret-key-2025'

# Simple user database (in production, use a real database)
USERS = {
    'admin@wisenews.com': {
        'password_hash': hashlib.sha256('WiseNews2025!'.encode()).hexdigest(),
        'is_admin': True
    }
}

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>WiseNews - Authentication Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="text-center">
            <h1>🎉 WiseNews Authentication Working!</h1>
            <p class="lead">Render deployment with working login system</p>
            
            {% if session.get('user_email') %}
                <div class="alert alert-success">
                    <h3>✅ Login Successful!</h3>
                    <p>Welcome, {{ session.user_email }}!</p>
                    <p>Admin: {{ 'Yes' if session.get('is_admin') else 'No' }}</p>
                    <a href="/logout" class="btn btn-danger">Logout</a>
                </div>
            {% else %}
                <div class="alert alert-info">
                    <strong>Test Credentials:</strong><br>
                    Email: admin@wisenews.com<br>
                    Password: WiseNews2025!
                </div>
                <a href="/login" class="btn btn-primary btn-lg">Test Login Now</a>
            {% endif %}
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in USERS:
            user = USERS[email]
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash == user['password_hash']:
                session['user_email'] = email
                session['is_admin'] = user['is_admin']
                return redirect(url_for('home'))
        
        error = 'Invalid credentials'
    else:
        error = None
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Login - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h2 class="text-center">WiseNews Login</h2>
                        
                        {% if error %}
                            <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        
                        <div class="alert alert-info">
                            <strong>Test Credentials:</strong><br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <input type="email" name="email" class="form-control" 
                                       placeholder="Email" value="admin@wisenews.com" required>
                            </div>
                            <div class="mb-3">
                                <input type="password" name="password" class="form-control" 
                                       placeholder="Password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <a href="/">← Back to Home</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'success',
        'message': 'WiseNews Simple Authentication Working!',
        'version': '1.0.0-simple',
        'authentication': 'ENABLED',
        'test_credentials': 'admin@wisenews.com / WiseNews2025!'
    })

if __name__ == '__main__':
    app.run(debug=True)
