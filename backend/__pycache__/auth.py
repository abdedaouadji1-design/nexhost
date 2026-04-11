"""
NexHost V4 - Authentication Manager
====================================
JWT-based authentication with bcrypt password hashing
Supports Super Admin and regular users
"""

import jwt
import bcrypt
import json
import os
import secrets
from datetime import datetime, timedelta

# Base directory for config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class AuthManager:
    def __init__(self, database):
        self.db = database
        self.secret_key = os.environ.get(
            'JWT_SECRET_KEY',
            self._load_or_create_secret()
        )
        self.token_expiry = 24  # hours
    
    def _load_or_create_secret(self):
        """Load JWT secret from config.json or create new one"""
        config_path = os.path.join(BASE_DIR, 'config.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                return config.get('jwt_secret')
            except:
                pass
        
        # Create new secret
        secret = secrets.token_hex(32)
        config = {'jwt_secret': secret}
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config.json: {e}")
        
        return secret
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password, password_hash):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def generate_token(self, user_id, username, role):
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def decode_token(self, token):
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {'success': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            return {'success': False, 'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'error': 'Invalid token'}
    
    def login(self, username, password):
        """Authenticate user and return token"""
        # Check if it's the super admin
        if username == 'superadmin':
            return self._login_super_admin(password)
        
        # Regular user login
        return self._login_regular_user(username, password)
    
    def _login_super_admin(self, password):
        """Login as super admin"""
        super_admin = self.db.get_super_admin()
        
        if not super_admin:
            return {'success': False, 'error': 'Super admin not found'}
        
        # Verify password
        if not self.verify_password(password, super_admin['password_hash']):
            return {'success': False, 'error': 'Invalid username or password'}
        
        # Generate token with superadmin role
        token = self.generate_token(0, 'superadmin', 'superadmin')
        
        return {
            'success': True,
            'token': token,
            'user': {
                'id': 0,
                'username': 'superadmin',
                'email': 'superadmin@nexhost.local',
                'role': 'superadmin'
            }
        }
    
    def _login_regular_user(self, username, password):
        """Login as regular user"""
        # Get user from database
        user = self.db.get_user_by_username(username)
        
        if not user:
            return {'success': False, 'error': 'Invalid username or password'}
        
        # Check if user is active
        if user.get('is_active') == 0:
            return {'success': False, 'error': 'Account is disabled. Contact administrator.'}
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Invalid username or password'}
        
        # Update last login
        self.db.update_last_login(user['id'])
        
        # Generate token
        token = self.generate_token(user['id'], user['username'], user['role'])
        
        return {
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }
    
    def get_user_from_token(self, token):
        """Get user info from token"""
        result = self.decode_token(token)
        
        if not result['success']:
            return result
        
        payload = result['payload']
        
        # Check if it's super admin
        if payload['role'] == 'superadmin':
            return {
                'success': True,
                'user': {
                    'id': 0,
                    'username': 'superadmin',
                    'email': 'superadmin@nexhost.local',
                    'role': 'superadmin'
                }
            }
        
        # Regular user
        user = self.db.get_user_by_id(payload['user_id'])
        
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        return {
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }
    
    def refresh_token(self, token):
        """Refresh expired token"""
        try:
            # Decode without verification to get payload
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'], options={'verify_exp': False})
            
            # Check if it's super admin
            if payload['role'] == 'superadmin':
                new_token = self.generate_token(0, 'superadmin', 'superadmin')
                return {
                    'success': True,
                    'token': new_token,
                    'user': {
                        'id': 0,
                        'username': 'superadmin',
                        'email': 'superadmin@nexhost.local',
                        'role': 'superadmin'
                    }
                }
            
            # Check if user still exists
            user = self.db.get_user_by_id(payload['user_id'])
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Generate new token
            new_token = self.generate_token(user['id'], user['username'], user['role'])
            
            return {
                'success': True,
                'token': new_token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }
            }
        except jwt.InvalidTokenError:
            return {'success': False, 'error': 'Invalid token'}
    
    def create_default_admin(self):
        """Create default admin user if no users exist"""
        users = self.db.get_all_users()
        
        if not users:
            # Create default admin
            password_hash = self.hash_password('admin')
            result = self.db.create_user(
                username='admin',
                email='admin@nexhost.local',
                password_hash=password_hash,
                role='admin'
            )
            
            if result['success']:
                print("=" * 60)
                print("🔑 Default admin user created:")
                print("   Username: admin")
                print("   Password: admin")
                print("=" * 60)
            
            return result
        
        return {'success': True, 'message': 'Users already exist'}
    
    def change_password(self, user_id, new_password):
        """Change user password"""
        password_hash = self.hash_password(new_password)
        result = self.db.update_user(user_id, {'password_hash': password_hash})
        return result
    
    def change_superadmin_password(self, current_password, new_password):
        """Change super admin password"""
        super_admin = self.db.get_super_admin()
        
        if not super_admin:
            return {'success': False, 'error': 'Super admin not found'}
        
        # Verify current password
        if not self.verify_password(current_password, super_admin['password_hash']):
            return {'success': False, 'error': 'Current password is incorrect'}
        
        # Update password
        password_hash = self.hash_password(new_password)
        return self.db.update_super_admin_password(password_hash)
    
    def check_permission(self, user_role, required_role='user'):
        """Check if user has required permission"""
        roles = {'viewer': 0, 'user': 1, 'admin': 2, 'superadmin': 3}
        user_level = roles.get(user_role, 0)
        required_level = roles.get(required_role, 1)
        return user_level >= required_level
    
    def is_superadmin(self, user_role):
        """Check if user is super admin"""
        return user_role == 'superadmin'
    
    def is_admin_or_superadmin(self, user_role):
        """Check if user is admin or super admin"""
        return user_role in ['admin', 'superadmin']
