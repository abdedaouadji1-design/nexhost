"""
NexHost V5 - Flask Backend Application
=======================================
Main application entry point with all API routes
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from auth import AuthManager
from projects import ProjectManager
from runner import ProcessRunner
from logs import LogManager
from users import UserManager
from system import SystemMonitor
from settings import SettingsManager
from admin import AdminManager

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def create_app():
    """Create and configure Flask application"""

    # Flask app with static_folder pointing to frontend
    app = Flask(__name__,
                static_folder=FRONTEND_DIR,
                static_url_path='')

    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Initialize managers
    db_path = os.environ.get('DB_PATH', os.path.join(DATA_DIR, 'nexhost.db'))
    db = Database(db_path)
    auth_manager = AuthManager(db)
    project_manager = ProjectManager(db, UPLOADS_DIR)
    process_runner = ProcessRunner(db, LOGS_DIR)
    log_manager = LogManager(LOGS_DIR)
    user_manager = UserManager(db)
    system_monitor = SystemMonitor()
    settings_manager = SettingsManager(db, DATA_DIR)
    admin_manager = AdminManager(db, settings_manager)

    # =============================================================================
    # MAINTENANCE MIDDLEWARE
    # =============================================================================

    @app.before_request
    def check_maintenance():
        allowed_paths = ['/api/auth/login', '/api/admin/maintenance/status', '/api/health']
        if any(request.path.startswith(p) for p in allowed_paths):
            return
        if not request.path.startswith('/api/'):
            return
        if settings_manager.db.get_setting('maintenance_mode') == 'true':
            user = None
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
            if token:
                result = auth_manager.get_user_from_token(token)
                if result['success']:
                    user = result['user']
            if not user or user['role'] not in ['admin', 'superadmin']:
                return jsonify({
                    'success': False,
                    'maintenance': True,
                    'message': settings_manager.db.get_setting('maintenance_message') or 'Ø§Ù„Ù†Ø¸Ø§Ù… ØªØ­Øª Ø§Ù„ØµÙŠØ§Ù†Ø© ðŸ”§',
                    'end_time': settings_manager.db.get_setting('maintenance_end_time') or '',
                    'started_at': settings_manager.db.get_setting('maintenance_started_at') or ''
                }), 503

    # =============================================================================
    # HELPER FUNCTIONS
    # =============================================================================

    def require_auth():
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
        if not token:
            return None, jsonify({'success': False, 'error': 'Authentication required'}), 401
        result = auth_manager.get_user_from_token(token)
        if not result['success']:
            return None, jsonify(result), 401
        return result['user'], None, None

    def require_admin():
        user, error_response, status = require_auth()
        if error_response:
            return None, error_response, status
        if user['role'] not in ['admin', 'superadmin']:
            return None, jsonify({'success': False, 'error': 'Admin access required'}), 403
        return user, None, None

    def require_superadmin():
        user, error_response, status = require_auth()
        if error_response:
            return None, error_response, status
        if user['role'] != 'superadmin':
            return None, jsonify({'success': False, 'error': 'Super Admin access required'}), 403
        return user, None, None

    # =============================================================================
    # AUTH ROUTES
    # =============================================================================

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        result = auth_manager.login(username, password)
        if result['success']:
            user_id = result['user']['id']
            if user_id != 0:
                db.log_activity(user_id, 'login', f"ØªØ³Ø¬ÙŠÙ„ Ø¯Ø®ÙˆÙ„: {username}")
            return jsonify(result), 200
        return jsonify(result), 401

    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        return jsonify({'success': True, 'message': 'Logged out successfully'})

    @app.route('/api/auth/me', methods=['GET'])
    def get_current_user():
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
        if not token:
            return jsonify({'success': False, 'error': 'No token provided'}), 401
        result = auth_manager.get_user_from_token(token)
        return jsonify(result), 200 if result['success'] else 401

    @app.route('/api/auth/refresh', methods=['POST'])
    def refresh_token():
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
        if not token:
            return jsonify({'success': False, 'error': 'No token provided'}), 401
        result = auth_manager.refresh_token(token)
        return jsonify(result), 200 if result['success'] else 401

    @app.route('/api/auth/change-superadmin-password', methods=['POST'])
    def change_superadmin_password():
        user, error_response, status = require_superadmin()
        if error_response:
            return error_response, status
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Current and new password required'}), 400
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
        result = auth_manager.change_superadmin_password(current_password, new_password)
        return jsonify(result), 200 if result['success'] else 400

    # =============================================================================
    # PROJECT ROUTES
    # =============================================================================

    @app.route('/api/projects', methods=['GET'])
    def get_projects():
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        projects = project_manager.get_projects(user['id'], user['role'])
        return jsonify({'success': True, 'projects': projects}), 200

    @app.route('/api/projects', methods=['POST'])
    def create_project():
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        language = data.get('language', 'python')
        main_file = data.get('main_file', 'main.py')
        if not name:
            return jsonify({'success': False, 'error': 'Project name required'}), 400
        result = project_manager.create_project(user_id=user['id'], name=name, description=description, language=language, main_file=main_file)
        return jsonify(result), 201 if result['success'] else 400

    @app.route('/api/projects/<int:project_id>', methods=['GET'])
    def get_project(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        return jsonify(result), 200 if result['success'] else 404

    @app.route('/api/projects/<int:project_id>', methods=['DELETE'])
    def delete_project(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        process_runner.stop_project(project_id)
        result = project_manager.delete_project(project_id, user['id'], user['role'])
        return jsonify(result), 200 if result['success'] else 403

    @app.route('/api/projects/<int:project_id>/start', methods=['POST'])
    def start_project(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        project_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id))
        result = process_runner.start_project(project_id=project_id, project_path=project_path, main_file=project['main_file'], language=project['language'])
        if result['success']:
            project_manager.update_status(project_id, 'running', result.get('pid'))
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/projects/<int:project_id>/stop', methods=['POST'])
    def stop_project(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        result = process_runner.stop_project(project_id)
        if result['success']:
            project_manager.update_status(project_id, 'stopped')
        return jsonify(result), 200

    @app.route('/api/projects/<int:project_id>/restart', methods=['POST'])
    def restart_project(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        process_runner.stop_project(project_id)
        project_manager.update_status(project_id, 'stopped')
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        project_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id))
        result = process_runner.start_project(project_id=project_id, project_path=project_path, main_file=project['main_file'], language=project['language'])
        if result['success']:
            project_manager.update_status(project_id, 'running', result.get('pid'))
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/projects/<int:project_id>/status', methods=['GET'])
    def get_project_status(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        is_running = process_runner.is_running(project_id)
        return jsonify({'success': True, 'status': 'running' if is_running else project['status'], 'pid': project.get('pid'), 'uptime': process_runner.get_uptime(project_id) if is_running else None}), 200

    @app.route('/api/projects/<int:project_id>/hot-reload', methods=['POST'])
    def hot_reload(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        file_path = request.form.get('file_path', '')
        new_file = request.files.get('file')
        if not file_path or not new_file:
            return jsonify({'success': False, 'error': 'File path and file required'}), 400
        try:
            new_content = new_file.read().decode('utf-8')
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to read file: {str(e)}'}), 400
        result = project_manager.hot_reload(project_id=project_id, user_id=user['id'], user_role=user['role'], file_path=file_path, new_file_content=new_content, process_runner=process_runner)
        return jsonify(result), 200 if result['success'] else 400

    # =============================================================================
    # FILE ROUTES
    # =============================================================================

    @app.route('/api/projects/<int:project_id>/upload', methods=['POST'])
    def upload_file(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        project_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id))
        os.makedirs(project_path, exist_ok=True)
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        file_path = os.path.join(project_path, file.filename)
        file.save(file_path)
        return jsonify({'success': True, 'message': 'File uploaded successfully', 'filename': file.filename}), 200

    @app.route('/api/projects/<int:project_id>/files', methods=['GET'])
    def get_files(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        project_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id))
        files = []
        if os.path.exists(project_path):
            for item in os.listdir(project_path):
                item_path = os.path.join(project_path, item)
                stat = os.stat(item_path)
                files.append({'name': item, 'is_dir': os.path.isdir(item_path), 'size': stat.st_size if os.path.isfile(item_path) else None, 'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()})
        return jsonify({'success': True, 'files': files}), 200

    @app.route('/api/projects/<int:project_id>/files/<path:file_path>', methods=['GET'])
    def get_file_content(project_id, file_path):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        full_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id), file_path)
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'success': True, 'content': content}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/projects/<int:project_id>/files/<path:file_path>', methods=['PUT'])
    def update_file(project_id, file_path):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        full_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id), file_path)
        data = request.get_json()
        content = data.get('content', '')
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return jsonify({'success': True, 'message': 'File updated successfully'}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/projects/<int:project_id>/files/<path:file_path>', methods=['DELETE'])
    def delete_file(project_id, file_path):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        full_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id), file_path)
        try:
            if os.path.isdir(full_path):
                import shutil
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            return jsonify({'success': True, 'message': 'File deleted successfully'}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # =============================================================================
    # ENV ROUTES
    # =============================================================================

    @app.route('/api/projects/<int:project_id>/env', methods=['GET'])
    def get_env(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        env_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id), '.env')
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        return jsonify({'success': True, 'env': env_vars}), 200

    @app.route('/api/projects/<int:project_id>/env', methods=['PUT'])
    def update_env(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        project = result['project']
        env_path = os.path.join(UPLOADS_DIR, str(project['user_id']), str(project_id), '.env')
        data = request.get_json()
        env_vars = data.get('env', {})
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    f.write(f'{key}={value}\n')
            return jsonify({'success': True, 'message': 'Environment variables updated'}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # =============================================================================
    # LOGS ROUTES
    # =============================================================================

    @app.route('/api/projects/<int:project_id>/logs', methods=['GET'])
    def get_logs(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        lines = request.args.get('lines', 100, type=int)
        logs = log_manager.get_logs(project_id, lines)
        return jsonify({'success': True, 'logs': logs}), 200

    @app.route('/api/projects/<int:project_id>/logs', methods=['DELETE'])
    def clear_logs(project_id):
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = project_manager.get_project(project_id, user['id'], user['role'])
        if not result['success']:
            return jsonify(result), 404
        result = log_manager.clear_logs(project_id)
        return jsonify(result), 200

    # =============================================================================
    # SYSTEM ROUTES
    # =============================================================================

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'success': True, 'status': 'online', 'version': '5.0.0'}), 200

    @app.route('/api/system/stats', methods=['GET'])
    def get_system_stats():
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        stats = system_monitor.get_stats()
        return jsonify({'success': True, 'stats': stats}), 200

    @app.route('/api/system/info', methods=['GET'])
    def get_system_info():
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        info = system_monitor.get_info()
        return jsonify({'success': True, 'info': info}), 200

    # =============================================================================
    # USERS ROUTES
    # =============================================================================

    @app.route('/api/users', methods=['GET'])
    def get_users():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        users = user_manager.get_all_users()
        return jsonify({'success': True, 'users': users}), 200

    @app.route('/api/users', methods=['POST'])
    def create_user():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'user')
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        result = user_manager.create_user(username, email, password, role)
        return jsonify(result), 201 if result['success'] else 400

    @app.route('/api/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        result = user_manager.update_user(user_id, data, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        result = user_manager.delete_user(user_id, admin.get('id'), admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/users/<int:user_id>/password', methods=['PUT'])
    def change_user_password(user_id):
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        new_password = data.get('password', '').strip()
        if not new_password:
            return jsonify({'success': False, 'error': 'Password required'}), 400
        result = user_manager.change_password(user_id, new_password)
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/users/<int:user_id>/toggle', methods=['POST'])
    def toggle_user_status(user_id):
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        result = user_manager.toggle_user_status(user_id, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    # =============================================================================
    # ACTIVITY ROUTES
    # =============================================================================

    @app.route('/api/activity', methods=['GET'])
    def get_activity_logs():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        limit = request.args.get('limit', 50, type=int)
        logs = db.get_activity_logs(limit)
        return jsonify({'success': True, 'logs': logs}), 200

    @app.route('/api/activity', methods=['DELETE'])
    def clear_activity_logs():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM activity_logs')
        conn.commit()
        return jsonify({'success': True, 'message': 'Activity logs cleared'}), 200

    # =============================================================================
    # SETTINGS ROUTES
    # =============================================================================

    @app.route('/api/settings', methods=['GET'])
    def get_settings():
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        settings = settings_manager.get_settings()
        return jsonify({'success': True, 'settings': settings}), 200

    @app.route('/api/settings', methods=['PUT'])
    def update_settings():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        result = settings_manager.update_settings(data)
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/settings/backup', methods=['POST'])
    def create_backup():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        result = settings_manager.create_backup()
        return jsonify(result), 200 if result['success'] else 500

    @app.route('/api/settings/backups', methods=['GET'])
    def get_backups():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        backups = settings_manager.get_backups()
        return jsonify({'success': True, 'backups': backups}), 200

    # =============================================================================
    # ADMIN ROUTES
    # =============================================================================

    @app.route('/api/admin/maintenance/status', methods=['GET'])
    def get_maintenance_status():
        status = admin_manager.get_maintenance_status()
        return jsonify(status), 200

    @app.route('/api/admin/maintenance/toggle', methods=['POST'])
    def toggle_maintenance():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        enabled = data.get('enabled', False)
        message = data.get('message')
        end_time = data.get('end_time')
        result = admin_manager.toggle_maintenance(enabled, message, end_time, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/admin/broadcast/active', methods=['GET'])
    def get_active_broadcast():
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = admin_manager.get_active_broadcast()
        return jsonify(result), 200

    @app.route('/api/admin/broadcast', methods=['POST'])
    def create_broadcast():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        message = data.get('message', '')
        type_ = data.get('type', 'info')
        duration_minutes = data.get('duration_minutes')
        result = admin_manager.create_broadcast(message, type_, duration_minutes, admin.get('id'), admin['role'])
        return jsonify(result), 201 if result['success'] else 400

    @app.route('/api/admin/broadcast/history', methods=['GET'])
    def get_broadcast_history():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        result = admin_manager.get_broadcast_history(admin['role'])
        return jsonify(result), 200

    @app.route('/api/admin/broadcast/<int:broadcast_id>', methods=['DELETE'])
    def deactivate_broadcast(broadcast_id):
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        result = admin_manager.deactivate_broadcast(broadcast_id, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/quick-links', methods=['GET'])
    def get_quick_links():
        user, error_response, status = require_auth()
        if error_response:
            return error_response, status
        result = admin_manager.get_quick_links(user['role'])
        return jsonify(result), 200

    @app.route('/api/admin/quick-links', methods=['GET'])
    def get_all_quick_links():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        result = admin_manager.get_all_quick_links(admin['role'])
        return jsonify(result), 200

    @app.route('/api/admin/quick-links', methods=['POST'])
    def create_quick_link():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        title = data.get('title', '')
        icon = data.get('icon', 'ðŸ”—')
        type_ = data.get('type', 'url')
        content = data.get('content', '')
        color = data.get('color', 'cyan')
        visible_to = data.get('visible_to', 'all')
        result = admin_manager.create_quick_link(title, icon, type_, content, color, visible_to, admin['role'])
        return jsonify(result), 201 if result['success'] else 400

    @app.route('/api/admin/quick-links/<int:link_id>', methods=['PUT'])
    def update_quick_link(link_id):
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        result = admin_manager.update_quick_link(link_id, data, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/admin/quick-links/<int:link_id>', methods=['DELETE'])
    def delete_quick_link(link_id):
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        result = admin_manager.delete_quick_link(link_id, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/admin/quick-links/reorder', methods=['POST'])
    def reorder_quick_links():
        admin, error_response, status = require_admin()
        if error_response:
            return error_response, status
        data = request.get_json()
        order = data.get('order', [])
        result = admin_manager.reorder_quick_links(order, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    # =============================================================================
    # FRONTEND ROUTES
    # =============================================================================

    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'login.html')

    # =============================================================================
    # ERROR HANDLERS
    # =============================================================================

    @app.errorhandler(404)
    def not_found(error):
        return send_from_directory(FRONTEND_DIR, 'login.html')

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    return app, db, auth_manager, settings_manager, process_runner


# Gunicorn entry point
def _init_app():
    _app, _db, _auth, _settings, _runner = create_app()
    _db.init_database()
    _auth.create_default_admin()
    _settings.load_default_settings()
    _runner.restore_running_processes()
    return _app

app = _init_app()

