"""
NexHost V4 - Database Manager
==============================
SQLite database operations with threading support
"""

import sqlite3
import os
import threading
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._local = threading.local()
    
    def get_connection(self):
        """Get database connection with threading support"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn
    
    def init_database(self):
        """Initialize database with tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table - Added is_active field
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # Super Admin table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS super_admin (
                id INTEGER PRIMARY KEY DEFAULT 1,
                username TEXT NOT NULL DEFAULT 'superadmin',
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CHECK (id = 1)
            )
        ''')
        
        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                name TEXT NOT NULL,
                description TEXT,
                language TEXT DEFAULT 'python',
                main_file TEXT DEFAULT 'main.py',
                status TEXT DEFAULT 'stopped',
                pid INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                auto_restart INTEGER DEFAULT 1,
                start_on_boot INTEGER DEFAULT 1
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Activity logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Login attempts table (for security)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                ip_address TEXT,
                success INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Broadcast messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                created_by INTEGER REFERENCES users(id),
                expires_at DATETIME,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Quick links table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                icon TEXT DEFAULT '🔗',
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                color TEXT DEFAULT 'cyan',
                visible_to TEXT DEFAULT 'all',
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        
        # Initialize super admin if not exists
        self._init_super_admin(cursor)
        
        conn.commit()
        print("✅ Database initialized successfully")
    
    def _init_super_admin(self, cursor):
        """Initialize super admin if not exists"""
        cursor.execute('SELECT COUNT(*) as count FROM super_admin')
        result = cursor.fetchone()
        
        if result['count'] == 0:
            # Import bcrypt here to avoid circular import
            import bcrypt
            password_hash = bcrypt.hashpw('superadmin123'.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
            cursor.execute('''
                INSERT INTO super_admin (username, password_hash)
                VALUES ('superadmin', ?)
            ''', (password_hash,))
            print("👑 Super Admin created: superadmin / superadmin123")
    
    # User operations
    def create_user(self, username, email, password_hash, role='user'):
        """Create new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            conn.commit()
            user_id = cursor.lastrowid
            return {'success': True, 'user_id': user_id}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Username already exists'}
    
    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        return dict(user) if user else None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    
    def get_all_users(self):
        """Get all users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, role, is_active, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        users = [dict(row) for row in cursor.fetchall()]
        return users
    
    def update_user(self, user_id, data):
        """Update user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['username', 'email', 'role', 'is_active']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])
        
        if 'password_hash' in data:
            updates.append('password_hash = ?')
            values.append(data['password_hash'])
        
        if updates:
            values.append(user_id)
            cursor.execute(f'''
                UPDATE users SET {', '.join(updates)} WHERE id = ?
            ''', values)
            conn.commit()
        
        return {'success': True}
    
    def delete_user(self, user_id):
        """Delete user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        return {'success': True}
    
    def update_last_login(self, user_id):
        """Update last login time"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now().isoformat(), user_id))
        conn.commit()
    
    def toggle_user_status(self, user_id, is_active):
        """Toggle user active status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET is_active = ? WHERE id = ?
        ''', (1 if is_active else 0, user_id))
        conn.commit()
        return {'success': True}
    
    # Super Admin operations
    def get_super_admin(self):
        """Get super admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM super_admin WHERE id = 1')
        admin = cursor.fetchone()
        return dict(admin) if admin else None
    
    def update_super_admin_password(self, password_hash):
        """Update super admin password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE super_admin SET password_hash = ? WHERE id = 1
        ''', (password_hash,))
        conn.commit()
        return {'success': True}
    
    # Project operations
    def create_project(self, user_id, name, description, language, main_file):
        """Create new project"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO projects (user_id, name, description, language, main_file)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, name, description, language, main_file))
        conn.commit()
        project_id = cursor.lastrowid
        return {'success': True, 'project_id': project_id}
    
    def get_project(self, project_id):
        """Get project by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        project = cursor.fetchone()
        return dict(project) if project else None
    
    def get_projects_by_user(self, user_id):
        """Get all projects for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.username as owner_name
            FROM projects p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
        ''', (user_id,))
        projects = [dict(row) for row in cursor.fetchall()]
        return projects
    
    def get_all_projects(self):
        """Get all projects (admin)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.username as owner_name
            FROM projects p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
        ''')
        projects = [dict(row) for row in cursor.fetchall()]
        return projects
    
    def get_projects_by_status(self, status):
        """Get projects by status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE status = ?', (status,))
        projects = [dict(row) for row in cursor.fetchall()]
        return projects
    
    def update_project_status(self, project_id, status, pid=None):
        """Update project status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if pid is not None:
            cursor.execute('''
                UPDATE projects SET status = ?, pid = ? WHERE id = ?
            ''', (status, pid, project_id))
        else:
            cursor.execute('''
                UPDATE projects SET status = ? WHERE id = ?
            ''', (status, project_id))
        conn.commit()
    
    def update_project(self, project_id, data):
        """Update project"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['name', 'description', 'language', 'main_file', 
                         'auto_restart', 'start_on_boot']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])
        
        if updates:
            values.append(project_id)
            cursor.execute(f'''
                UPDATE projects SET {', '.join(updates)} WHERE id = ?
            ''', values)
            conn.commit()
        
        return {'success': True}
    
    def delete_project(self, project_id):
        """Delete project"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit()
        return {'success': True}
    
    def count_user_projects(self, user_id):
        """Count projects for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM projects WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result['count']
    
    # Settings operations
    def get_setting(self, key):
        """Get setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result['value'] if result else None
    
    def set_setting(self, key, value):
        """Set setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
        conn.commit()
    
    def get_all_settings(self):
        """Get all settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM settings')
        settings = {row['key']: row['value'] for row in cursor.fetchall()}
        return settings
    
    # Activity logs
    def log_activity(self, user_id, action, details=None, ip_address=None):
        """Log user activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_logs (user_id, action, details, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, details, ip_address))
        conn.commit()
    
    def get_activity_logs(self, limit=100):
        """Get activity logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, u.username
            FROM activity_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT ?
        ''', (limit,))
        logs = [dict(row) for row in cursor.fetchall()]
        return logs
    
    # Login attempts
    def log_login_attempt(self, username, ip_address, success=False):
        """Log login attempt"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO login_attempts (username, ip_address, success)
            VALUES (?, ?, ?)
        ''', (username, ip_address, 1 if success else 0))
        conn.commit()
    
    def get_recent_failed_attempts(self, username, minutes=30):
        """Get recent failed login attempts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM login_attempts
            WHERE username = ? AND success = 0
            AND created_at > datetime('now', '-{} minutes')
        '''.format(minutes), (username,))
        result = cursor.fetchone()
        return result['count']
    
    # Broadcast operations
    def create_broadcast(self, message, type_, created_by, expires_at=None):
        """Create broadcast message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO broadcasts (message, type, created_by, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (message, type_, created_by, expires_at))
        conn.commit()
        return {'success': True, 'id': cursor.lastrowid}
    
    def get_active_broadcast(self):
        """Get active broadcast message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM broadcasts 
            WHERE is_active = 1 
            AND (expires_at IS NULL OR expires_at > datetime('now'))
            ORDER BY created_at DESC LIMIT 1
        ''')
        broadcast = cursor.fetchone()
        return dict(broadcast) if broadcast else None
    
    def get_broadcast_history(self, limit=50):
        """Get broadcast history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.*, u.username as created_by_name
            FROM broadcasts b
            LEFT JOIN users u ON b.created_by = u.id
            ORDER BY b.created_at DESC
            LIMIT ?
        ''', (limit,))
        broadcasts = [dict(row) for row in cursor.fetchall()]
        return broadcasts
    
    def deactivate_broadcast(self, broadcast_id):
        """Deactivate broadcast"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE broadcasts SET is_active = 0 WHERE id = ?
        ''', (broadcast_id,))
        conn.commit()
        return {'success': True}
    
    # Quick Links operations
    def create_quick_link(self, title, icon, type_, content, color='cyan', visible_to='all', sort_order=0):
        """Create quick link"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO quick_links (title, icon, type, content, color, visible_to, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, icon, type_, content, color, visible_to, sort_order))
        conn.commit()
        return {'success': True, 'id': cursor.lastrowid}
    
    def get_quick_links(self, visible_to=None):
        """Get quick links"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if visible_to:
            cursor.execute('''
                SELECT * FROM quick_links 
                WHERE is_active = 1 AND (visible_to = 'all' OR visible_to = ?)
                ORDER BY sort_order ASC
            ''', (visible_to,))
        else:
            cursor.execute('''
                SELECT * FROM quick_links 
                WHERE is_active = 1
                ORDER BY sort_order ASC
            ''')
        
        links = [dict(row) for row in cursor.fetchall()]
        return links
    
    def get_all_quick_links(self):
        """Get all quick links (admin)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM quick_links ORDER BY sort_order ASC
        ''')
        links = [dict(row) for row in cursor.fetchall()]
        return links
    
    def update_quick_link(self, link_id, data):
        """Update quick link"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['title', 'icon', 'type', 'content', 'color', 'visible_to', 'sort_order', 'is_active']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])
        
        if updates:
            values.append(link_id)
            cursor.execute(f'''
                UPDATE quick_links SET {', '.join(updates)} WHERE id = ?
            ''', values)
            conn.commit()
        
        return {'success': True}
    
    def delete_quick_link(self, link_id):
        """Delete quick link"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM quick_links WHERE id = ?', (link_id,))
        conn.commit()
        return {'success': True}
    
    def reorder_quick_links(self, order_list):
        """Reorder quick links"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for index, link_id in enumerate(order_list):
            cursor.execute('''
                UPDATE quick_links SET sort_order = ? WHERE id = ?
            ''', (index, link_id))
        
        conn.commit()
        return {'success': True}
