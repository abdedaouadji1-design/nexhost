"""
NexHost V4 - Process Runner
============================
Manage Python script execution with subprocess
"""

import subprocess
import os
import signal
import psutil
import time
from datetime import datetime

class ProcessRunner:
    def __init__(self, database, logs_dir):
        self.db = database
        self.logs_dir = logs_dir
        self.running_processes = {}  # project_id -> {process, start_time, log_file}
        
        # Ensure logs directory exists
        os.makedirs(logs_dir, exist_ok=True)
    
    def restore_running_processes(self):
        """Restore running processes on server startup - sync DB with reality"""
        print("🔄 Restoring running processes...")
        running_projects = self.db.get_projects_by_status('running')
        restored_count = 0
        
        for project in running_projects:
            if project.get('pid'):
                try:
                    proc = psutil.Process(project['pid'])
                    if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                        self.running_processes[project['id']] = {
                            'process': proc,
                            'pid': project['pid'],
                            'start_time': datetime.now()
                        }
                        restored_count += 1
                        print(f"  ✓ Restored project {project['id']} (PID: {project['pid']})")
                    else:
                        self.db.update_project_status(project['id'], 'stopped', None)
                        print(f"  ✗ Project {project['id']} zombie process cleaned")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.db.update_project_status(project['id'], 'stopped', None)
                    print(f"  ✗ Project {project['id']} process not found")
        
        print(f"✅ Restored {restored_count} running processes")
        return restored_count
    
    def start_project(self, project_id, project_path, main_file, language='python'):
        """Start a project as a subprocess"""
        try:
            # Check if already running
            if project_id in self.running_processes:
                process_info = self.running_processes[project_id]
                if process_info['process'].poll() is None:
                    return {'success': False, 'error': 'Project is already running'}
                else:
                    # Clean up stopped process
                    del self.running_processes[project_id]
            
            # Check if main file exists
            main_file_path = os.path.join(project_path, main_file)
            if not os.path.exists(main_file_path):
                return {'success': False, 'error': f'Main file not found: {main_file}'}
            
            # Setup log file
            log_file_path = os.path.join(self.logs_dir, f'project_{project_id}.log')
            
            # Load environment variables from .env
            env = os.environ.copy()
            env_path = os.path.join(project_path, '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env[key] = value
            
            # Determine command based on language (Python only for V4)
            if language == 'python':
                # Check for virtual environment
                venv_python = os.path.join(project_path, 'venv', 'bin', 'python')
                if os.path.exists(venv_python):
                    cmd = [venv_python, main_file_path]
                else:
                    cmd = ['python3', main_file_path]
            else:
                return {'success': False, 'error': f'Unsupported language: {language}'}
            
            # Open log file
            log_file = open(log_file_path, 'a', encoding='utf-8')
            
            # Write start marker
            start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_file.write(f"\n{'='*60}\n")
            log_file.write(f"[{start_time}] 🚀 Starting project {project_id}\n")
            log_file.write(f"{'='*60}\n")
            log_file.flush()
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=project_path,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Store process info
            self.running_processes[project_id] = {
                'process': process,
                'start_time': time.time(),
                'log_file': log_file,
                'log_path': log_file_path
            }
            
            # Wait a moment to check if process started successfully
            time.sleep(1)
            
            if process.poll() is not None:
                # Process exited immediately
                exit_code = process.poll()
                log_file.write(f"\n❌ Process exited with code {exit_code}\n")
                log_file.close()
                del self.running_processes[project_id]
                return {'success': False, 'error': f'Process exited immediately with code {exit_code}'}
            
            return {
                'success': True,
                'message': 'Project started successfully',
                'pid': process.pid
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_project(self, project_id):
        """Stop a running project"""
        try:
            if project_id not in self.running_processes:
                # Try to kill by PID from database
                project = self.db.get_project(project_id)
                if project and project.get('pid'):
                    try:
                        os.kill(project['pid'], signal.SIGTERM)
                        return {'success': True, 'message': 'Project stopped'}
                    except ProcessLookupError:
                        return {'success': True, 'message': 'Process not found'}
                return {'success': True, 'message': 'Project was not running'}
            
            process_info = self.running_processes[project_id]
            process = process_info['process']
            log_file = process_info['log_file']
            
            # Write stop marker
            stop_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_file.write(f"\n[{stop_time}] 🛑 Stopping project {project_id}\n")
            
            # Try graceful termination first
            try:
                if os.name != 'nt':
                    # Kill the entire process group
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                # Wait for process to terminate
                process.wait(timeout=5)
                
            except (subprocess.TimeoutExpired, ProcessLookupError):
                # Force kill if graceful termination fails
                try:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait(timeout=2)
                except ProcessLookupError:
                    pass
            
            # Close log file
            log_file.close()
            
            # Remove from running processes
            del self.running_processes[project_id]
            
            return {'success': True, 'message': 'Project stopped successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def is_running(self, project_id):
        """Check if project is running"""
        if project_id not in self.running_processes:
            return False
        
        process = self.running_processes[project_id]['process']
        return process.poll() is None
    
    def get_uptime(self, project_id):
        """Get project uptime in seconds"""
        if project_id not in self.running_processes:
            return 0
        
        start_time = self.running_processes[project_id]['start_time']
        return int(time.time() - start_time)
    
    def get_process_info(self, project_id):
        """Get process information"""
        if project_id not in self.running_processes:
            return None
        
        process_info = self.running_processes[project_id]
        process = process_info['process']
        
        try:
            ps_process = psutil.Process(process.pid)
            return {
                'pid': process.pid,
                'cpu_percent': ps_process.cpu_percent(),
                'memory_info': ps_process.memory_info()._asdict(),
                'uptime': self.get_uptime(project_id),
                'status': 'running' if process.poll() is None else 'stopped'
            }
        except psutil.NoSuchProcess:
            return None
    
    def restart_project(self, project_id, project_path, main_file, language='python'):
        """Restart a project"""
        self.stop_project(project_id)
        time.sleep(1)  # Wait for cleanup
        return self.start_project(project_id, project_path, main_file, language)
    
    def get_all_running(self):
        """Get all running projects"""
        running = []
        for project_id, info in self.running_processes.items():
            if info['process'].poll() is None:
                running.append({
                    'project_id': project_id,
                    'pid': info['process'].pid,
                    'uptime': self.get_uptime(project_id)
                })
        return running
    
    def stop_all(self):
        """Stop all running projects"""
        results = []
        for project_id in list(self.running_processes.keys()):
            result = self.stop_project(project_id)
            results.append({
                'project_id': project_id,
                'result': result
            })
        return results
    
    def cleanup(self):
        """Cleanup stopped processes"""
        to_remove = []
        for project_id, info in self.running_processes.items():
            if info['process'].poll() is not None:
                to_remove.append(project_id)
                try:
                    info['log_file'].close()
                except:
                    pass
        
        for project_id in to_remove:
            del self.running_processes[project_id]
        
        return len(to_remove)
