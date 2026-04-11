"""
NexHost V4 - User Manager
==========================
User management for administrators with Super Admin protection
"""

import bcrypt
from datetime import datetime

class UserManager:
    def __init__(self, database):
        self.db = database
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def get_all_users(self):
        """Get all users with additional stats"""
        users = self.db.get_all_users()
        
        # Add project count for each user
        for user in users:
            user['project_count'] = self.db.count_user_projects(user['id'])
            
            # Format last login
            if user.get('last_login'):
                try:
                    last_login = datetime.fromisoformat(user['last_login'])
                    user['last_login_formatted'] = last_login.strftime('%Y-%m-%d %H:%M')
                except:
                    user['last_login_formatted'] = user['last_login']
            else:
                user['last_login_formatted'] = 'Never'
            
            # Add active status text
            user['status_text'] = 'Active' if user.get('is_active', 1) == 1 else 'Disabled'
        
        return users
    
    def create_user(self, username, email, password, role='user'):
        """Create new user"""
        # Validate inputs
        if not username or len(username) < 3:
            return {'success': False, 'error': 'Username must be at least 3 characters'}
        
        if not password or len(password) < 6:
            return {'success': False, 'error': 'Password must be at least 6 characters'}
        
        # Validate role
        valid_roles = ['admin', 'user', 'viewer']
        if role not in valid_roles:
            return {'success': False, 'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user
        result = self.db.create_user(username, email, password_hash, role)
        
        if result['success']:
            return {
                'success': True,
                'message': f'User "{username}" created successfully',
                'user_id': result['user_id']
            }
        else:
            return result
    
    def update_user(self, user_id, data, current_user_role=None):
        """Update user information"""
        # Check if user exists
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Protect super admin (cannot be modified by regular admin)
        if user.get('role') == 'superadmin' or user_id == 0:
            return {'success': False, 'error': 'Cannot modify Super Admin'}
        
        # Prevent changing own role (to avoid locking yourself out)
        if 'role' in data and user['role'] == 'admin':
            # Count admin users
            all_users = self.db.get_all_users()
            admin_count = sum(1 for u in all_users if u['role'] == 'admin')
            
            if admin_count <= 1 and data['role'] != 'admin':
                return {'success': False, 'error': 'Cannot change role of the only admin'}
        
        # Update user
        result = self.db.update_user(user_id, data)
        
        if result['success']:
            return {
                'success': True,
                'message': 'User updated successfully'
            }
        else:
            return result
    
    def delete_user(self, user_id, current_user_id=None, current_user_role=None):
        """Delete user"""
        # Check if user exists
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Protect super admin
        if user.get('role') == 'superadmin' or user_id == 0:
            return {'success': False, 'error': 'Cannot delete Super Admin'}
        
        # Prevent deleting yourself
        if current_user_id and user_id == current_user_id:
            return {'success': False, 'error': 'Cannot delete your own account'}
        
        # Prevent deleting the only admin
        if user['role'] == 'admin':
            all_users = self.db.get_all_users()
            admin_count = sum(1 for u in all_users if u['role'] == 'admin')
            
            if admin_count <= 1:
                return {'success': False, 'error': 'Cannot delete the only admin user'}
        
        # Delete user's projects first
        projects = self.db.get_projects_by_user(user_id)
        for project in projects:
            self.db.delete_project(project['id'])
        
        # Delete user
        result = self.db.delete_user(user_id)
        
        if result['success']:
            return {
                'success': True,
                'message': f'User "{user["username"]}" deleted successfully'
            }
        else:
            return result
    
    def change_password(self, user_id, new_password):
        """Change user password"""
        if not new_password or len(new_password) < 6:
            return {'success': False, 'error': 'Password must be at least 6 characters'}
        
        password_hash = self.hash_password(new_password)
        result = self.db.update_user(user_id, {'password_hash': password_hash})
        
        if result['success']:
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
        else:
            return result
    
    def toggle_user_status(self, user_id, current_user_role=None):
        """Enable/disable user account"""
        # Check if user exists
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Protect super admin
        if user.get('role') == 'superadmin' or user_id == 0:
            return {'success': False, 'error': 'Cannot modify Super Admin status'}
        
        # Prevent disabling the only admin
        if user['role'] == 'admin' and user.get('is_active', 1) == 1:
            all_users = self.db.get_all_users()
            active_admins = sum(1 for u in all_users if u['role'] == 'admin' and u.get('is_active', 1) == 1)
            if active_admins <= 1:
                return {'success': False, 'error': 'Cannot disable the only active admin'}
        
        # Toggle status
        new_status = 0 if user.get('is_active', 1) == 1 else 1
        result = self.db.toggle_user_status(user_id, new_status == 1)
        
        if result['success']:
            status_text = 'enabled' if new_status == 1 else 'disabled'
            return {
                'success': True,
                'message': f'User account {status_text}',
                'is_active': new_status
            }
        else:
            return result
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return None
        
        projects = self.db.get_projects_by_user(user_id)
        
        # Count running projects
        running_count = sum(1 for p in projects if p['status'] == 'running')
        
        return {
            'user_id': user_id,
            'username': user['username'],
            'role': user['role'],
            'is_active': user.get('is_active', 1),
            'total_projects': len(projects),
            'running_projects': running_count,
            'created_at': user['created_at'],
            'last_login': user.get('last_login')
        }
    
    def search_users(self, query):
        """Search users by username or email"""
        all_users = self.get_all_users()
        query_lower = query.lower()
        
        results = []
        for user in all_users:
            if (query_lower in user['username'].lower() or 
                (user.get('email') and query_lower in user['email'].lower())):
                results.append(user)
        
        return results
