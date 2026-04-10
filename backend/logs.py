"""
NexHost V4 - Log Manager
=========================
Project log management
"""

import os
from datetime import datetime

class LogManager:
    def __init__(self, logs_dir):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
    
    def get_logs(self, project_id, lines=100):
        """Get project logs"""
        log_file = os.path.join(self.logs_dir, f'project_{project_id}.log')
        
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            return [f"Error reading logs: {e}"]
    
    def clear_logs(self, project_id):
        """Clear project logs"""
        log_file = os.path.join(self.logs_dir, f'project_{project_id}.log')
        
        try:
            if os.path.exists(log_file):
                # Backup before clearing
                backup_file = os.path.join(self.logs_dir, f'project_{project_id}.log.old')
                os.rename(log_file, backup_file)
                
                # Create new empty log file
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📝 Logs cleared\n")
            
            return {'success': True, 'message': 'Logs cleared successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_log_size(self, project_id):
        """Get log file size"""
        log_file = os.path.join(self.logs_dir, f'project_{project_id}.log')
        
        if os.path.exists(log_file):
            return os.path.getsize(log_file)
        return 0
