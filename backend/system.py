"""
NexHost V4 - System Monitor
============================
System resource monitoring
"""

import psutil
import platform
import socket
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        pass
    
    def get_stats(self):
        """Get system stats (CPU, RAM, Disk)"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memory
        memory = psutil.virtual_memory()
        memory_used_gb = round(memory.used / (1024**3), 2)
        memory_total_gb = round(memory.total / (1024**3), 2)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_used_gb = round(disk.used / (1024**3), 2)
        disk_total_gb = round(disk.total / (1024**3), 2)
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'frequency': cpu_freq.current if cpu_freq else None
            },
            'memory': {
                'percent': memory.percent,
                'used_gb': memory_used_gb,
                'total_gb': memory_total_gb,
                'available_gb': round(memory.available / (1024**3), 2)
            },
            'disk': {
                'percent': disk.percent,
                'used_gb': disk_used_gb,
                'total_gb': disk_total_gb,
                'free_gb': round(disk.free / (1024**3), 2)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_info(self):
        """Get system information"""
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': socket.gethostname(),
            'python_version': platform.python_version(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    
    def get_process_list(self):
        """Get list of running processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes
