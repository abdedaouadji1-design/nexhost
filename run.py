#!/usr/bin/env python3
"""
NexHost V4 - Run Script
=======================
Main entry point for starting the NexHost V4 server
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███╗   ██╗███████╗██╗  ██╗██╗  ██╗ ██████╗ ███████╗████████╗║
║   ████╗  ██║██╔════╝╚██╗██╔╝██║  ██║██╔═══██╗██╔════╝╚══██╔══╝║
║   ██╔██╗ ██║█████╗   ╚███╔╝ ███████║██║   ██║███████╗   ██║   ║
║   ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══██║██║   ██║╚════██║   ██║   ║
║   ██║ ╚████║███████╗██╔╝ ██╗██║  ██║╚██████╔╝███████║   ██║   ║
║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ║
║                                                              ║
║                    Hosting Panel v4.0                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Create app and get managers
    app, db, auth_manager, settings_manager, process_runner = create_app()
    
    # Initialize database
    print("📦 Initializing database...")
    db.init_database()
    
    # Create default admin
    print("🔑 Checking default admin user...")
    auth_manager.create_default_admin()
    
    # Load settings
    print("⚙️  Loading settings...")
    settings_manager.load_default_settings()
    
    # Restore running processes
    print("🔄 Restoring running processes...")
    process_runner.restore_running_processes()
    
    print("\n" + "=" * 60)
    print("🚀 Starting NexHost V4 Server...")
    print("=" * 60)
    print("╔══════════════════════════════════════════╗")
    print("║        🚀 NexHost V4 Starting...         ║")
    print("╠══════════════════════════════════════════╣")
    print("║  👑 Super Admin: superadmin              ║")
    print("║     Password:   superadmin123            ║")
    print("║  🔧 Admin:      admin                    ║")
    print("║     Password:   admin                    ║")
    print("║                                          ║")
    print("║  ⚠️  غيّر كلمات المرور فوراً!            ║")
    print("╠══════════════════════════════════════════╣")
    print("║  🌐 http://localhost:5000                ║")
    print("║  📱 http://0.0.0.0:5000 (الشبكة)        ║")
    print("╚══════════════════════════════════════════╝")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down NexHost V4...")
        print("🛑 Stopping all running processes...")
        process_runner.stop_all()
        print("✅ Server stopped")
