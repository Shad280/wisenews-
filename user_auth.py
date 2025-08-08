# WiseNews User Authentication & Data Protection System

import sqlite3
import hashlib
import secrets
import bcrypt
from datetime import datetime, timedelta
from flask import session, request
from functools import wraps
import re
import json

class UserManager:
    def __init__(self, db_path='wisenews.db'):  # Updated to match main app database
        self.db_path = db_path
        self.init_user_tables()
    
    def init_user_tables(self):
        """Initialize user management tables with GDPR compliance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table with GDPR fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                country TEXT,
                date_of_birth DATE,
                phone_number TEXT,
                
                -- GDPR Compliance fields
                gdpr_consent BOOLEAN DEFAULT FALSE,
                marketing_consent BOOLEAN DEFAULT FALSE,
                analytics_consent BOOLEAN DEFAULT FALSE,
                data_processing_consent BOOLEAN DEFAULT FALSE,
                
                -- Account management
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE,
                verification_token TEXT,
                password_reset_token TEXT,
                password_reset_expires DATETIME,
                
                -- Tracking fields
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                login_count INTEGER DEFAULT 0,
                last_ip_address TEXT,
                
                -- Duplicate detection
                email_hash TEXT,
                name_hash TEXT,
                phone_hash TEXT,
                
                -- Data retention
                data_retention_agreed BOOLEAN DEFAULT FALSE,
                account_deletion_requested DATETIME,
                
                -- Security
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until DATETIME,
                two_factor_enabled BOOLEAN DEFAULT FALSE,
                two_factor_secret TEXT
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, preference_key)
            )
        ''')
        
        # Data processing log (GDPR compliance)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT NOT NULL,
                data_type TEXT,
                legal_basis TEXT,
                purpose TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User login history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN,
                failure_reason TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Duplicate detection attempts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS duplicate_signup_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                ip_address TEXT,
                user_agent TEXT,
                attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                detection_method TEXT,
                existing_user_id INTEGER,
                blocked BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email_hash ON users(email_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)')
        
        conn.commit()
        conn.close()
    
    def generate_hash(self, data):
        """Generate hash for duplicate detection"""
        return hashlib.sha256(data.lower().encode()).hexdigest()
    
    def hash_password(self, password):
        """Securely hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    def check_for_duplicates(self, email, first_name, last_name, phone_number=None):
        """Check for duplicate users using multiple methods"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Method 1: Direct email match
        cursor.execute('SELECT id, email FROM users WHERE email = ?', (email.lower(),))
        email_match = cursor.fetchone()
        if email_match:
            conn.close()
            return True, "Email already registered", email_match[0]
        
        # Method 2: Email hash match (case variations)
        email_hash = self.generate_hash(email)
        cursor.execute('SELECT id, email FROM users WHERE email_hash = ?', (email_hash,))
        email_hash_match = cursor.fetchone()
        if email_hash_match:
            conn.close()
            return True, "Email variant already registered", email_hash_match[0]
        
        # Method 3: Name similarity (exact match)
        name_hash = self.generate_hash(f"{first_name}{last_name}")
        cursor.execute('SELECT id, first_name, last_name FROM users WHERE name_hash = ?', (name_hash,))
        name_match = cursor.fetchone()
        if name_match:
            # Additional check: if same name, warn but allow (could be family members)
            pass
        
        # Method 4: Phone number match (if provided)
        if phone_number:
            phone_hash = self.generate_hash(phone_number)
            cursor.execute('SELECT id, phone_number FROM users WHERE phone_hash = ?', (phone_hash,))
            phone_match = cursor.fetchone()
            if phone_match:
                conn.close()
                return True, "Phone number already registered", phone_match[0]
        
        conn.close()
        return False, "No duplicate found", None
    
    def create_admin_user(self, email, password):
        """Create admin user with simplified interface"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if admin already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email.lower(),))
            if cursor.fetchone():
                conn.close()
                return False  # Admin already exists
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create admin user with minimal required fields
            cursor.execute('''
                INSERT INTO users (
                    email, password_hash, first_name, last_name, 
                    gdpr_consent, marketing_consent, analytics_consent, data_processing_consent,
                    is_active, is_verified, is_admin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email.lower(), password_hash, 'Admin', 'User',
                True, False, True, True,  # GDPR consents
                True, True, True  # Active, verified, admin
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Admin creation error: {e}")
            return False

    def log_data_processing(self, user_id, action_type, data_type, legal_basis, purpose, ip_address):
        """Log data processing for GDPR compliance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO data_processing_log 
            (user_id, action_type, data_type, legal_basis, purpose, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, action_type, data_type, legal_basis, purpose, ip_address))
        
        conn.commit()
        conn.close()
    
    def register_user(self, user_data, ip_address):
        """Register new user with GDPR compliance and terms acceptance"""
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'gdpr_consent', 'terms_accepted', 'privacy_policy_accepted', 'age_verification']
        for field in required_fields:
            if not user_data.get(field):
                return False, f"Missing required field: {field}", None
        
        # Validate email
        if not self.validate_email(user_data['email']):
            return False, "Invalid email format", None
        
        # Validate password
        password_valid, password_message = self.validate_password(user_data['password'])
        if not password_valid:
            return False, password_message, None
        
        # Check legal agreements
        if not user_data.get('terms_accepted'):
            return False, "You must accept the Terms and Conditions", None
            
        if not user_data.get('privacy_policy_accepted'):
            return False, "You must accept the Privacy Policy", None
            
        if not user_data.get('age_verification'):
            return False, "Age verification is required", None
        
        # Check GDPR consent
        if not user_data.get('gdpr_consent'):
            return False, "GDPR consent is required", None
        
        # Check for duplicates
        is_duplicate, duplicate_reason, existing_user_id = self.check_for_duplicates(
            user_data['email'], 
            user_data['first_name'], 
            user_data['last_name'],
            user_data.get('phone_number')
        )
        
        if is_duplicate:
            # Log duplicate attempt
            self.log_duplicate_attempt(user_data['email'], ip_address, duplicate_reason, existing_user_id)
            return False, duplicate_reason, existing_user_id
        
        # Hash password and sensitive data
        password_hash = self.hash_password(user_data['password'])
        email_hash = self.generate_hash(user_data['email'])
        name_hash = self.generate_hash(f"{user_data['first_name']}{user_data['last_name']}")
        phone_hash = self.generate_hash(user_data.get('phone_number', '')) if user_data.get('phone_number') else None
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Insert user
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (
                email, password_hash, first_name, last_name, country, date_of_birth, phone_number,
                gdpr_consent, marketing_consent, analytics_consent, data_processing_consent,
                verification_token, email_hash, name_hash, phone_hash, data_retention_agreed,
                last_ip_address
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data['email'].lower(),
            password_hash,
            user_data['first_name'],
            user_data['last_name'],
            user_data.get('country'),
            user_data.get('date_of_birth'),
            user_data.get('phone_number'),
            user_data.get('gdpr_consent', False),
            user_data.get('marketing_consent', False),
            user_data.get('analytics_consent', False),
            user_data.get('data_processing_consent', False),
            verification_token,
            email_hash,
            name_hash,
            phone_hash,
            user_data.get('data_retention_agreed', False),
            ip_address
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log data processing
        self.log_data_processing(
            user_id, 
            'registration', 
            'personal_data', 
            'consent', 
            'account_creation',
            ip_address
        )
        
        return True, "User registered successfully", user_id
    
    def log_duplicate_attempt(self, email, ip_address, detection_method, existing_user_id):
        """Log duplicate signup attempts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO duplicate_signup_attempts 
            (email, ip_address, detection_method, existing_user_id)
            VALUES (?, ?, ?, ?)
        ''', (email, ip_address, detection_method, existing_user_id))
        
        conn.commit()
        conn.close()
    
    def authenticate_user(self, email, password, ip_address):
        """Authenticate user login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user
        cursor.execute('''
            SELECT id, password_hash, is_active, is_verified, failed_login_attempts, account_locked_until
            FROM users WHERE email = ?
        ''', (email.lower(),))
        
        user = cursor.fetchone()
        
        if not user:
            # Log failed attempt
            cursor.execute('''
                INSERT INTO login_history (user_id, ip_address, success, failure_reason)
                VALUES (NULL, ?, FALSE, ?)
            ''', (ip_address, "User not found"))
            conn.commit()
            conn.close()
            return False, "Invalid credentials", None
        
        user_id, password_hash, is_active, is_verified, failed_attempts, locked_until = user
        
        # Check if account is locked
        if locked_until and datetime.now() < datetime.fromisoformat(locked_until):
            cursor.execute('''
                INSERT INTO login_history (user_id, ip_address, success, failure_reason)
                VALUES (?, ?, FALSE, ?)
            ''', (user_id, ip_address, "Account locked"))
            conn.commit()
            conn.close()
            return False, "Account temporarily locked", None
        
        # Check if account is active
        if not is_active:
            cursor.execute('''
                INSERT INTO login_history (user_id, ip_address, success, failure_reason)
                VALUES (?, ?, FALSE, ?)
            ''', (user_id, ip_address, "Account inactive"))
            conn.commit()
            conn.close()
            return False, "Account is inactive", None
        
        # Verify password
        if not self.verify_password(password, password_hash):
            # Increment failed attempts
            failed_attempts += 1
            locked_until = None
            
            if failed_attempts >= 5:
                locked_until = datetime.now() + timedelta(minutes=30)
            
            cursor.execute('''
                UPDATE users SET failed_login_attempts = ?, account_locked_until = ?
                WHERE id = ?
            ''', (failed_attempts, locked_until, user_id))
            
            cursor.execute('''
                INSERT INTO login_history (user_id, ip_address, success, failure_reason)
                VALUES (?, ?, FALSE, ?)
            ''', (user_id, ip_address, "Invalid password"))
            
            conn.commit()
            conn.close()
            return False, "Invalid credentials", None
        
        # Successful login
        # Reset failed attempts
        cursor.execute('''
            UPDATE users SET 
                failed_login_attempts = 0, 
                account_locked_until = NULL,
                last_login = CURRENT_TIMESTAMP,
                login_count = login_count + 1,
                last_ip_address = ?
            WHERE id = ?
        ''', (ip_address, user_id))
        
        # Log successful login
        cursor.execute('''
            INSERT INTO login_history (user_id, ip_address, success)
            VALUES (?, ?, TRUE)
        ''', (user_id, ip_address))
        
        conn.commit()
        conn.close()
        
        # Log data processing
        self.log_data_processing(
            user_id, 
            'login', 
            'authentication_data', 
            'legitimate_interest', 
            'user_authentication',
            ip_address
        )
        
        return True, "Login successful", user_id
    
    def create_session(self, user_id, ip_address, user_agent):
        """Create user session"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=30)  # 30 day session
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_token, ip_address, user_agent, expires_at))
        
        conn.commit()
        conn.close()
        
        return session_token
    
    def validate_session(self, session_token):
        """
        Validate a session token and return user data
        """
        try:
            if not session_token:
                return False, None
            
            # Get database connection with error handling
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                if not conn:
                    return False, None
                
                cursor = conn.cursor()
                
                # Query with proper error handling
                cursor.execute("""
                    SELECT u.id, u.first_name, u.last_name, u.email, u.created_at, u.is_active, 
                           s.created_at as session_created, s.expires_at
                    FROM users u 
                    JOIN user_sessions s ON u.id = s.user_id 
                    WHERE s.session_token = ? AND s.expires_at > datetime('now')
                """, (session_token,))
                
                result = cursor.fetchone()
                
                if result:
                    # Convert date strings to proper format for template
                    created_at = result[4]
                    if created_at:
                        try:
                            from datetime import datetime
                            # Parse SQLite datetime string
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at_formatted = dt.strftime('%B %Y')
                        except:
                            created_at_formatted = created_at[:7] if len(created_at) >= 7 else 'Recently'
                    else:
                        created_at_formatted = 'Recently'
                    
                    user_data = {
                        'id': result[0],
                        'username': f"{result[1]} {result[2]}" if result[1] and result[2] else 'Unknown',
                        'first_name': result[1] or '',
                        'last_name': result[2] or '',
                        'email': result[3] or '',
                        'created_at': created_at_formatted,
                        'is_active': bool(result[5]) if result[5] is not None else False,
                        'session_created': result[6] or '',
                        'session_expires': result[7] or ''
                    }
                    return True, user_data
                else:
                    return False, None
                    
            except sqlite3.Error as e:
                print(f"Database error in validate_session: {e}")
                return False, None
            except Exception as e:
                print(f"Unexpected error in validate_session: {e}")
                return False, None
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            print(f"Critical error in validate_session: {e}")
            return False, None

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            conn = sqlite3.connect('news_database.db', timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                columns = [description[0] for description in cursor.description]
                user_dict = dict(zip(columns, user_data))
                conn.close()
                return user_dict
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    def logout_user(self, session_token):
        """Logout user by invalidating session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions SET is_active = FALSE
            WHERE session_token = ?
        ''', (session_token,))
        
        conn.commit()
        conn.close()
    
    def get_user_data(self, user_id):
        """Get user data for GDPR compliance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, first_name, last_name, country, date_of_birth, phone_number,
                   created_at, last_login, login_count, gdpr_consent, marketing_consent,
                   analytics_consent, data_processing_consent
            FROM users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'email': result[0],
                'first_name': result[1],
                'last_name': result[2],
                'country': result[3],
                'date_of_birth': result[4],
                'phone_number': result[5],
                'created_at': result[6],
                'last_login': result[7],
                'login_count': result[8],
                'gdpr_consent': result[9],
                'marketing_consent': result[10],
                'analytics_consent': result[11],
                'data_processing_consent': result[12]
            }
        
        return None

    def delete_user_account(self, user_id):
        """
        Permanently delete user account and all associated data (GDPR Article 17)
        
        Args:
            user_id (int): User ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Log the deletion before removing data
            self.log_data_processing(
                user_id,
                'account_deletion',
                'All user data permanently deleted under GDPR Article 17'
            )
            
            # Delete all user-related data in correct order (foreign key constraints)
            tables_to_clean = [
                ('user_sessions', 'user_id'),
                ('user_preferences', 'user_id'), 
                ('login_history', 'user_id'),
                ('duplicate_signup_attempts', 'user_id'),
                ('data_processing_log', 'user_id'),
                ('users', 'id')  # This should be last
            ]
            
            for table, column in tables_to_clean:
                cursor.execute(f"DELETE FROM {table} WHERE {column} = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            print(f"User account {user_id} and all associated data permanently deleted")
            return True
            
        except Exception as e:
            print(f"Error deleting user account {user_id}: {e}")
            return False

# Global user manager instance
user_manager = UserManager()
