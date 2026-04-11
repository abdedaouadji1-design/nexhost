"""
NexHost V4 - Settings Manager
==============================
System settings and backup management with Maintenance Mode
"""

import os
import json
import shutil
import zipfile
from datetime import datetime, timedelta

class SettingsManager:
    def __init__(self, database, data_dir):
        self.db = database
        self.data_dir = data_dir
        self.backup_dir = os.path.join(data_dir, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Default settings
        self.default_settings = {
            'panel_name': 'NexHost',
            'panel_version': '4.0.0',
            'language': 'ar',
            'timezone': 'Asia/Riyadh',
            'max_projects_per_user': '10',
            'session_timeout': '8',
            'enable_2fa': 'false',
            'log_login_attempts': 'true',
            'lock_after_failed': 'true',
            'max_failed_attempts': '5',
            'auto_backup': 'true',
            'backup_time': '03:00',
            'backup_retention_days': '30',
            'notify_on_crash': 'true',
            'notify_on_high_cpu': 'true',
            'notify_on_disk_full': 'true',
            'notification_email': 'admin@nexhost.local',
            'cpu_threshold': '80',
            'disk_threshold': '90',
            # Maintenance Mode settings
            'maintenance_mode': 'false',
            'maintenance_message': 'النظام تحت الصيانة، سيعود قريباً 🔧',
            'maintenance_end_time': '',
            'maintenance_started_at': ''
        }
    
    def load_default_settings(self):
        """Load default settings if not exists"""
        current_settings = self.db.get_all_settings()
        
        for key, value in self.default_settings.items():
            if key not in current_settings:
                self.db.set_setting(key, value)
        
        print("✅ Settings loaded successfully")
    
    def get_settings(self):
        """Get all settings"""
        settings = self.db.get_all_settings()
        
        # Add computed values
        settings['backup_dir'] = self.backup_dir
        
        # Get backup size
        backup_size = self._get_backup_dir_size()
        settings['backup_size'] = backup_size
        settings['backup_size_formatted'] = self._format_size(backup_size)
        
        return settings
    
    def get_maintenance_status(self):
        """Get maintenance mode status"""
        return {
            'maintenance': self.db.get_setting('maintenance_mode') == 'true',
            'message': self.db.get_setting('maintenance_message') or 'النظام تحت الصيانة، سيعود قريباً 🔧',
            'end_time': self.db.get_setting('maintenance_end_time') or '',
            'started_at': self.db.get_setting('maintenance_started_at') or ''
        }
    
    def set_maintenance_mode(self, enabled, message=None, end_time=None):
        """Set maintenance mode"""
        try:
            self.db.set_setting('maintenance_mode', 'true' if enabled else 'false')
            
            if message is not None:
                self.db.set_setting('maintenance_message', message)
            
            if end_time is not None:
                self.db.set_setting('maintenance_end_time', end_time)
            
            if enabled:
                self.db.set_setting('maintenance_started_at', datetime.now().isoformat())
            else:
                self.db.set_setting('maintenance_started_at', '')
            
            return {
                'success': True,
                'message': 'Maintenance mode ' + ('enabled' if enabled else 'disabled')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_settings(self, new_settings):
        """Update settings"""
        try:
            for key, value in new_settings.items():
                if key in self.default_settings or key.startswith('custom_'):
                    self.db.set_setting(key, str(value))
            
            return {
                'success': True,
                'message': 'Settings updated successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_backup(self):
        """Create system backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'backup_{timestamp}.zip'
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup database
                db_path = os.path.join(self.data_dir, 'nexhost.db')
                if os.path.exists(db_path):
                    zipf.write(db_path, 'nexhost.db')
                
                # Backup uploads
                uploads_dir = os.path.join(self.data_dir, 'uploads')
                if os.path.exists(uploads_dir):
                    for root, dirs, files in os.walk(uploads_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.data_dir)
                            zipf.write(file_path, arcname)
                
                # Backup settings
                settings = self.get_settings()
                settings_json = json.dumps(settings, indent=2, ensure_ascii=False)
                zipf.writestr('settings.json', settings_json)
            
            # Clean old backups
            self._cleanup_old_backups()
            
            backup_size = os.path.getsize(backup_path)
            
            return {
                'success': True,
                'message': 'Backup created successfully',
                'backup': {
                    'name': backup_name,
                    'path': backup_path,
                    'size': backup_size,
                    'size_formatted': self._format_size(backup_size),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_backups(self):
        """Get list of backups"""
        backups = []
        
        if os.path.exists(self.backup_dir):
            for filename in sorted(os.listdir(self.backup_dir), reverse=True):
                if filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    stat = os.stat(file_path)
                    
                    backups.append({
                        'name': filename,
                        'size': stat.st_size,
                        'size_formatted': self._format_size(stat.st_size),
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'path': file_path
                    })
        
        return backups
    
    def restore_backup(self, backup_name):
        """Restore from backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': 'Backup not found'
                }
            
            # Create temporary restore directory
            restore_dir = os.path.join(self.data_dir, 'restore_temp')
            os.makedirs(restore_dir, exist_ok=True)
            
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            # Restore database (requires restart)
            db_backup = os.path.join(restore_dir, 'nexhost.db')
            if os.path.exists(db_backup):
                db_target = os.path.join(self.data_dir, 'nexhost.db')
                # Backup current database first
                if os.path.exists(db_target):
                    shutil.copy2(db_target, f"{db_target}.pre_restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Restore uploads
            uploads_backup = os.path.join(restore_dir, 'uploads')
            if os.path.exists(uploads_backup):
                uploads_target = os.path.join(self.data_dir, 'uploads')
                if os.path.exists(uploads_target):
                    shutil.rmtree(uploads_target)
                shutil.copytree(uploads_backup, uploads_target)
            
            # Cleanup
            shutil.rmtree(restore_dir)
            
            return {
                'success': True,
                'message': 'Backup restored successfully. Please restart the server.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_backup(self, backup_name):
        """Delete a backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
                return {
                    'success': True,
                    'message': 'Backup deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Backup not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        try:
            retention_days = int(self.db.get_setting('backup_retention_days') or '30')
            cutoff = datetime.now() - timedelta(days=retention_days)
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff:
                        os.remove(file_path)
                        print(f"🗑️ Deleted old backup: {filename}")
                        
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
    
    def _get_backup_dir_size(self):
        """Get total size of backup directory"""
        total_size = 0
        if os.path.exists(self.backup_dir):
            for dirpath, dirnames, filenames in os.walk(self.backup_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
        return total_size
    
    def _format_size(self, size_bytes):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        try:
            for key, value in self.default_settings.items():
                self.db.set_setting(key, value)
            
            return {
                'success': True,
                'message': 'Settings reset to defaults'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
