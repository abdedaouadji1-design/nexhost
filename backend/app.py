"""
NexHost V5 - Flask Backend
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, sys
from datetime import datetime

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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'backups'), exist_ok=True)


def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }})

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

    # ── MAINTENANCE ───────────────────────────────────────────
    @app.before_request
    def check_maintenance():
        allowed = ['/api/auth/login', '/api/admin/maintenance/status', '/api/health']
        if any(request.path.startswith(p) for p in allowed):
            return
        if not request.path.startswith('/api/'):
            return
        if settings_manager.db.get_setting('maintenance_mode') == 'true':
            user = None
            token = request.headers.get('Authorization', '').replace('Bearer ', '') or None
            if token:
                r = auth_manager.get_user_from_token(token)
                if r['success']:
                    user = r['user']
            if not user or user['role'] not in ['admin', 'superadmin']:
                return jsonify({
                    'success': False, 'maintenance': True,
                    'message': settings_manager.db.get_setting('maintenance_message') or 'النظام تحت الصيانة 🔧',
                    'end_time': settings_manager.db.get_setting('maintenance_end_time') or '',
                    'started_at': settings_manager.db.get_setting('maintenance_started_at') or ''
                }), 503

    # ── HELPERS ───────────────────────────────────────────────
    def get_token():
        return request.headers.get('Authorization', '').replace('Bearer ', '') or None

    def require_auth():
        token = get_token()
        if not token:
            return None, jsonify({'success': False, 'error': 'Authentication required'}), 401
        r = auth_manager.get_user_from_token(token)
        if not r['success']:
            return None, jsonify(r), 401
        return r['user'], None, None

    def require_admin():
        user, err, status = require_auth()
        if err:
            return None, err, status
        if user['role'] not in ['admin', 'superadmin']:
            return None, jsonify({'success': False, 'error': 'Admin access required'}), 403
        return user, None, None

    def require_superadmin():
        user, err, status = require_auth()
        if err:
            return None, err, status
        if user['role'] != 'superadmin':
            return None, jsonify({'success': False, 'error': 'Super Admin required'}), 403
        return user, None, None

    # ── AUTH ──────────────────────────────────────────────────
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        result = auth_manager.login(username, password)
        if result['success']:
            uid = result['user']['id']
            if uid != 0:
                db.log_activity(uid, 'login', f"تسجيل دخول: {username}")
        return jsonify(result), 200 if result['success'] else 401

    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        return jsonify({'success': True})

    @app.route('/api/auth/me', methods=['GET'])
    def get_current_user():
        token = get_token()
        if not token:
            return jsonify({'success': False, 'error': 'No token'}), 401
        result = auth_manager.get_user_from_token(token)
        return jsonify(result), 200 if result['success'] else 401

    @app.route('/api/auth/refresh', methods=['POST'])
    def refresh_token():
        token = get_token()
        if not token:
            return jsonify({'success': False, 'error': 'No token'}), 401
        result = auth_manager.refresh_token(token)
        return jsonify(result), 200 if result['success'] else 401

    @app.route('/api/auth/change-superadmin-password', methods=['POST'])
    def change_superadmin_password():
        user, err, status = require_superadmin()
        if err:
            return err, status
        data = request.get_json() or {}
        cp = data.get('current_password', '')
        np = data.get('new_password', '')
        if not cp or not np:
            return jsonify({'success': False, 'error': 'Passwords required'}), 400
        if len(np) < 6:
            return jsonify({'success': False, 'error': 'Min 6 characters'}), 400
        result = auth_manager.change_superadmin_password(cp, np)
        return jsonify(result), 200 if result['success'] else 400

    # ── PROJECTS ──────────────────────────────────────────────
    @app.route('/api/projects', methods=['GET'])
    def get_projects():
        user, err, status = require_auth()
        if err:
            return err, status
        return jsonify({'success': True, 'projects': project_manager.get_projects(user['id'], user['role'])}), 200

    @app.route('/api/projects', methods=['POST'])
    def create_project():
        user, err, status = require_auth()
        if err:
            return err, status
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'Name required'}), 400
        result = project_manager.create_project(
            user_id=user['id'], name=name,
            description=data.get('description', ''),
            language=data.get('language', 'python'),
            main_file=data.get('main_file', 'main.py')
        )
        return jsonify(result), 201 if result['success'] else 400

    @app.route('/api/projects/<int:pid>', methods=['GET'])
    def get_project(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        result = project_manager.get_project(pid, user['id'], user['role'])
        return jsonify(result), 200 if result['success'] else 404

    @app.route('/api/projects/<int:pid>', methods=['DELETE'])
    def delete_project(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        process_runner.stop_project(pid)
        result = project_manager.delete_project(pid, user['id'], user['role'])
        return jsonify(result), 200 if result['success'] else 403

    @app.route('/api/projects/<int:pid>/start', methods=['POST'])
    def start_project(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        p = r['project']
        path = os.path.join(UPLOADS_DIR, str(p['user_id']), str(pid))
        result = process_runner.start_project(project_id=pid, project_path=path, main_file=p['main_file'], language=p['language'])
        if result['success']:
            project_manager.update_status(pid, 'running', result.get('pid'))
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/projects/<int:pid>/stop', methods=['POST'])
    def stop_project(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        result = process_runner.stop_project(pid)
        if result['success']:
            project_manager.update_status(pid, 'stopped')
        return jsonify(result), 200

    @app.route('/api/projects/<int:pid>/restart', methods=['POST'])
    def restart_project(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        process_runner.stop_project(pid)
        project_manager.update_status(pid, 'stopped')
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        p = r['project']
        path = os.path.join(UPLOADS_DIR, str(p['user_id']), str(pid))
        result = process_runner.start_project(project_id=pid, project_path=path, main_file=p['main_file'], language=p['language'])
        if result['success']:
            project_manager.update_status(pid, 'running', result.get('pid'))
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/projects/<int:pid>/status', methods=['GET'])
    def get_project_status(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        p = r['project']
        running = process_runner.is_running(pid)
        return jsonify({'success': True, 'status': 'running' if running else p['status'],
                        'pid': p.get('pid'), 'uptime': process_runner.get_uptime(pid) if running else None}), 200

    @app.route('/api/projects/<int:pid>/hot-reload', methods=['POST'])
    def hot_reload(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        file_path = request.form.get('file_path', '')
        new_file = request.files.get('file')
        if not file_path or not new_file:
            return jsonify({'success': False, 'error': 'File required'}), 400
        try:
            content = new_file.read().decode('utf-8')
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        result = project_manager.hot_reload(project_id=pid, user_id=user['id'], user_role=user['role'],
                                             file_path=file_path, new_file_content=content, process_runner=process_runner)
        return jsonify(result), 200 if result['success'] else 400

    # ── FILES ─────────────────────────────────────────────────
    @app.route('/api/projects/<int:pid>/upload', methods=['POST'])
    def upload_file(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        p = r['project']
        proj_path = os.path.join(UPLOADS_DIR, str(p['user_id']), str(pid))
        os.makedirs(proj_path, exist_ok=True)
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file'}), 400
        f = request.files['file']
        if not f.filename:
            return jsonify({'success': False, 'error': 'No filename'}), 400
        f.save(os.path.join(proj_path, f.filename))
        return jsonify({'success': True, 'message': 'Uploaded', 'filename': f.filename}), 200

    @app.route('/api/projects/<int:pid>/files', methods=['GET'])
    def get_files(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        p = r['project']
        proj_path = os.path.join(UPLOADS_DIR, str(p['user_id']), str(pid))
        files = []
        if os.path.exists(proj_path):
            for item in os.listdir(proj_path):
                ip = os.path.join(proj_path, item)
                st = os.stat(ip)
                files.append({'name': item, 'is_dir': os.path.isdir(ip),
                               'size': st.st_size if os.path.isfile(ip) else None,
                               'modified': datetime.fromtimestamp(st.st_mtime).isoformat()})
        return jsonify({'success': True, 'files': files}), 200

    @app.route('/api/projects/<int:pid>/files/<path:fp>', methods=['GET'])
    def get_file_content(pid, fp):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        full = os.path.join(UPLOADS_DIR, str(r['project']['user_id']), str(pid), fp)
        if not os.path.isfile(full):
            return jsonify({'success': False, 'error': 'Not found'}), 404
        try:
            return jsonify({'success': True, 'content': open(full, encoding='utf-8').read()}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/projects/<int:pid>/files/<path:fp>', methods=['PUT'])
    def update_file(pid, fp):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        full = os.path.join(UPLOADS_DIR, str(r['project']['user_id']), str(pid), fp)
        data = request.get_json() or {}
        try:
            with open(full, 'w', encoding='utf-8') as f:
                f.write(data.get('content', ''))
            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/projects/<int:pid>/files/<path:fp>', methods=['DELETE'])
    def delete_file(pid, fp):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        full = os.path.join(UPLOADS_DIR, str(r['project']['user_id']), str(pid), fp)
        try:
            if os.path.isdir(full):
                import shutil; shutil.rmtree(full)
            else:
                os.remove(full)
            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ── ENV ───────────────────────────────────────────────────
    @app.route('/api/projects/<int:pid>/env', methods=['GET'])
    def get_env(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        env_path = os.path.join(UPLOADS_DIR, str(r['project']['user_id']), str(pid), '.env')
        env_vars = {}
        if os.path.exists(env_path):
            for line in open(env_path, encoding='utf-8'):
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    env_vars[k] = v
        return jsonify({'success': True, 'env': env_vars}), 200

    @app.route('/api/projects/<int:pid>/env', methods=['PUT'])
    def update_env(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        env_path = os.path.join(UPLOADS_DIR, str(r['project']['user_id']), str(pid), '.env')
        data = request.get_json() or {}
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                for k, v in data.get('env', {}).items():
                    f.write(f'{k}={v}\n')
            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ── LOGS ──────────────────────────────────────────────────
    @app.route('/api/projects/<int:pid>/logs', methods=['GET'])
    def get_logs(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        lines = request.args.get('lines', 100, type=int)
        return jsonify({'success': True, 'logs': log_manager.get_logs(pid, lines)}), 200

    @app.route('/api/projects/<int:pid>/logs', methods=['DELETE'])
    def clear_logs(pid):
        user, err, status = require_auth()
        if err:
            return err, status
        r = project_manager.get_project(pid, user['id'], user['role'])
        if not r['success']:
            return jsonify(r), 404
        return jsonify(log_manager.clear_logs(pid)), 200

    # ── SYSTEM ────────────────────────────────────────────────
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'success': True, 'status': 'online', 'version': '5.0.0'}), 200

    @app.route('/api/system/stats', methods=['GET'])
    def system_stats():
        user, err, status = require_auth()
        if err:
            return err, status
        return jsonify({'success': True, 'stats': system_monitor.get_stats()}), 200

    @app.route('/api/system/info', methods=['GET'])
    def system_info():
        user, err, status = require_auth()
        if err:
            return err, status
        return jsonify({'success': True, 'info': system_monitor.get_info()}), 200

    # ── USERS ─────────────────────────────────────────────────
    @app.route('/api/users', methods=['GET'])
    def get_users():
        admin, err, status = require_admin()
        if err:
            return err, status
        return jsonify({'success': True, 'users': user_manager.get_all_users()}), 200

    @app.route('/api/users', methods=['POST'])
    def create_user():
        admin, err, status = require_admin()
        if err:
            return err, status
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        result = user_manager.create_user(username, data.get('email', ''), password, data.get('role', 'user'))
        return jsonify(result), 201 if result['success'] else 400

    @app.route('/api/users/me', methods=['GET'])
    def get_me():
        user, err, status = require_auth()
        if err:
            return err, status
        if user['role'] == 'superadmin':
            return jsonify({'success': True, 'user': user}), 200
        u = db.get_user_by_id(user['id'])
        if not u:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return jsonify({'success': True, 'user': {'id': u['id'], 'username': u['username'], 'email': u.get('email', ''), 'role': u['role']}}), 200

    @app.route('/api/users/me', methods=['DELETE'])
    def delete_me():
        user, err, status = require_auth()
        if err:
            return err, status
        if user['role'] in ['admin', 'superadmin']:
            return jsonify({'success': False, 'error': 'Admins cannot delete their account'}), 403
        return jsonify(db.delete_user(user['id'])), 200

    @app.route('/api/users/me/change-password', methods=['POST'])
    def change_my_password():
        user, err, status = require_auth()
        if err:
            return err, status
        data = request.get_json() or {}
        cp = data.get('current_password', '')
        np = data.get('new_password', '')
        if not cp or not np:
            return jsonify({'success': False, 'error': 'Passwords required'}), 400
        if len(np) < 6:
            return jsonify({'success': False, 'error': 'Min 6 characters'}), 400
        if user['role'] == 'superadmin':
            result = auth_manager.change_superadmin_password(cp, np)
        else:
            u = db.get_user_by_id(user['id'])
            if not u or not auth_manager.verify_password(cp, u['password_hash']):
                return jsonify({'success': False, 'error': 'Wrong current password'}), 400
            result = auth_manager.change_password(user['id'], np)
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/users/<int:uid>', methods=['PUT'])
    def update_user(uid):
        admin, err, status = require_admin()
        if err:
            return err, status
        data = request.get_json() or {}
        result = user_manager.update_user(uid, data, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/users/<int:uid>', methods=['DELETE'])
    def delete_user(uid):
        admin, err, status = require_admin()
        if err:
            return err, status
        result = user_manager.delete_user(uid, admin.get('id'), admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/users/<int:uid>/password', methods=['PUT'])
    def change_user_password(uid):
        admin, err, status = require_admin()
        if err:
            return err, status
        data = request.get_json() or {}
        pw = data.get('password', '').strip()
        if not pw:
            return jsonify({'success': False, 'error': 'Password required'}), 400
        result = user_manager.change_password(uid, pw)
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/users/<int:uid>/toggle', methods=['POST'])
    def toggle_user(uid):
        admin, err, status = require_admin()
        if err:
            return err, status
        result = user_manager.toggle_user_status(uid, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    # ── ACTIVITY ──────────────────────────────────────────────
    @app.route('/api/activity', methods=['GET'])
    def get_activity():
        admin, err, status = require_admin()
        if err:
            return err, status
        limit = request.args.get('limit', 50, type=int)
        return jsonify({'success': True, 'logs': db.get_activity_logs(limit)}), 200

    @app.route('/api/activity', methods=['DELETE'])
    def clear_activity():
        admin, err, status = require_admin()
        if err:
            return err, status
        conn = db.get_connection()
        conn.cursor().execute('DELETE FROM activity_logs')
        conn.commit()
        return jsonify({'success': True}), 200

    # ── SETTINGS ──────────────────────────────────────────────
    @app.route('/api/settings', methods=['GET'])
    def get_settings():
        user, err, status = require_auth()
        if err:
            return err, status
        return jsonify({'success': True, 'settings': settings_manager.get_settings()}), 200

    @app.route('/api/settings', methods=['PUT'])
    def update_settings():
        admin, err, status = require_admin()
        if err:
            return err, status
        result = settings_manager.update_settings(request.get_json() or {})
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/settings/backup', methods=['POST'])
    def create_backup():
        admin, err, status = require_admin()
        if err:
            return err, status
        result = settings_manager.create_backup()
        return jsonify(result), 200 if result['success'] else 500

    @app.route('/api/settings/backups', methods=['GET'])
    def get_backups():
        admin, err, status = require_admin()
        if err:
            return err, status
        return jsonify({'success': True, 'backups': settings_manager.get_backups()}), 200

    @app.route('/api/admin/settings', methods=['GET'])
    def get_admin_settings():
        admin, err, status = require_admin()
        if err:
            return err, status
        return jsonify({'success': True, 'settings': settings_manager.get_settings()}), 200

    # ── ADMIN ─────────────────────────────────────────────────
    @app.route('/api/admin/maintenance/status', methods=['GET'])
    def maintenance_status():
        return jsonify(admin_manager.get_maintenance_status()), 200

    @app.route('/api/admin/maintenance/toggle', methods=['POST'])
    def toggle_maintenance():
        admin, err, status = require_admin()
        if err:
            return err, status
        data = request.get_json() or {}
        result = admin_manager.toggle_maintenance(
            data.get('enabled', False), data.get('message'), data.get('end_time'), admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/admin/broadcast/active', methods=['GET'])
    def active_broadcast():
        user, err, status = require_auth()
        if err:
            return err, status
        return jsonify(admin_manager.get_active_broadcast()), 200

    @app.route('/api/admin/broadcast', methods=['POST'])
    def create_broadcast():
        admin, err, status = require_admin()
        if err:
            return err, status
        data = request.get_json() or {}
        result = admin_manager.create_broadcast(
            data.get('message', ''), data.get('type', 'info'),
            data.get('duration_minutes'), admin.get('id'), admin['role'])
        return jsonify(result), 201 if result['success'] else 400

    @app.route('/api/admin/broadcast/history', methods=['GET'])
    def broadcast_history():
        admin, err, status = require_admin()
        if err:
            return err, status
        return jsonify(admin_manager.get_broadcast_history(admin['role'])), 200

    @app.route('/api/admin/broadcast/<int:bid>', methods=['DELETE'])
    def deactivate_broadcast(bid):
        admin, err, status = require_admin()
        if err:
            return err, status
        result = admin_manager.deactivate_broadcast(bid, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/quick-links', methods=['GET'])
    def quick_links():
        user, err, status = require_auth()
        if err:
            return err, status
        return jsonify(admin_manager.get_quick_links(user['role'])), 200

    @app.route('/api/admin/quick-links', methods=['GET'])
    def all_quick_links():
        admin, err, status = require_admin()
        if err:
            return err, status
        return jsonify(admin_manager.get_all_quick_links(admin['role'])), 200

    @app.route('/api/admin/quick-links', methods=['POST'])
    def create_quick_link():
        admin, err, status = require_admin()
        if err:
            return err, status
        data = request.get_json() or {}
        result = admin_manager.create_quick_link(
            data.get('title', ''), data.get('icon', '🔗'), data.get('type', 'url'),
            data.get('content', ''), data.get('color', 'cyan'), data.get('visible_to', 'all'), admin['role'])
        return jsonify(result), 201 if result['success'] else 400

    @app.route('/api/admin/quick-links/<int:lid>', methods=['PUT'])
    def update_quick_link(lid):
        admin, err, status = require_admin()
        if err:
            return err, status
        result = admin_manager.update_quick_link(lid, request.get_json() or {}, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/admin/quick-links/<int:lid>', methods=['DELETE'])
    def delete_quick_link(lid):
        admin, err, status = require_admin()
        if err:
            return err, status
        result = admin_manager.delete_quick_link(lid, admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    @app.route('/api/admin/quick-links/reorder', methods=['POST'])
    def reorder_quick_links():
        admin, err, status = require_admin()
        if err:
            return err, status
        data = request.get_json() or {}
        result = admin_manager.reorder_quick_links(data.get('order', []), admin['role'])
        return jsonify(result), 200 if result['success'] else 400

    # ── FRONTEND ──────────────────────────────────────────────
    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'login.html')

    @app.route('/<path:filename>')
    def serve_static(filename):
        fp = os.path.join(FRONTEND_DIR, filename)
        if os.path.isfile(fp):
            return send_from_directory(os.path.dirname(fp), os.path.basename(fp))
        return send_from_directory(FRONTEND_DIR, 'login.html')

    # ── ERRORS ────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return send_from_directory(FRONTEND_DIR, 'login.html')

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'error': 'Server error'}), 500

    return app, db, auth_manager, settings_manager, process_runner


# ── GUNICORN ENTRY ────────────────────────────────────────────
def _init_app():
    _app, _db, _auth, _settings, _runner = create_app()
    _db.init_database()
    _auth.create_default_admin()
    _settings.load_default_settings()
    _runner.restore_running_processes()
    return _app

app = _init_app()
