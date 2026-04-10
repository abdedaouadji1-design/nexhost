"""
NexHost V4 - Admin Manager
===========================
Admin endpoints for Maintenance Mode, Broadcast Messages, and Quick Links
"""

from datetime import datetime, timedelta

class AdminManager:
    def __init__(self, database, settings_manager):
        self.db = database
        self.settings_manager = settings_manager
    
    # ==================== MAINTENANCE MODE ====================
    
    def get_maintenance_status(self):
        """Get maintenance mode status (public endpoint)"""
        return self.settings_manager.get_maintenance_status()
    
    def toggle_maintenance(self, enabled, message=None, end_time=None, user_role=None):
        """Toggle maintenance mode"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        return self.settings_manager.set_maintenance_mode(enabled, message, end_time)
    
    # ==================== BROADCAST MESSAGES ====================
    
    def create_broadcast(self, message, type_='info', duration_minutes=None, created_by=None, user_role=None):
        """Create new broadcast message"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        if not message or len(message.strip()) == 0:
            return {'success': False, 'error': 'Message is required'}
        
        # Validate type
        valid_types = ['info', 'warning', 'error', 'success']
        if type_ not in valid_types:
            type_ = 'info'
        
        # Calculate expiration
        expires_at = None
        if duration_minutes and duration_minutes > 0:
            expires_at = (datetime.now() + timedelta(minutes=duration_minutes)).isoformat()
        
        # Deactivate any existing active broadcasts
        active = self.db.get_active_broadcast()
        if active:
            self.db.deactivate_broadcast(active['id'])
        
        # Create new broadcast
        result = self.db.create_broadcast(message, type_, created_by, expires_at)
        
        if result['success']:
            return {
                'success': True,
                'message': 'Broadcast created successfully',
                'broadcast_id': result['id']
            }
        return result
    
    def get_active_broadcast(self):
        """Get active broadcast message"""
        broadcast = self.db.get_active_broadcast()
        
        if broadcast:
            return {
                'success': True,
                'broadcast': {
                    'id': broadcast['id'],
                    'message': broadcast['message'],
                    'type': broadcast['type'],
                    'created_at': broadcast['created_at'],
                    'expires_at': broadcast['expires_at']
                }
            }
        
        return {'success': True, 'broadcast': None}
    
    def get_broadcast_history(self, user_role=None, limit=50):
        """Get broadcast history"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        broadcasts = self.db.get_broadcast_history(limit)
        return {
            'success': True,
            'broadcasts': broadcasts
        }
    
    def deactivate_broadcast(self, broadcast_id, user_role=None):
        """Deactivate a broadcast"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        return self.db.deactivate_broadcast(broadcast_id)
    
    # ==================== QUICK LINKS ====================
    
    def create_quick_link(self, title, icon, type_, content, color='cyan', visible_to='all', user_role=None):
        """Create new quick link"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        if not title or len(title.strip()) == 0:
            return {'success': False, 'error': 'Title is required'}
        
        if not content or len(content.strip()) == 0:
            return {'success': False, 'error': 'Content is required'}
        
        # Validate type
        valid_types = ['url', 'message', 'telegram_channel', 'telegram_contact']
        if type_ not in valid_types:
            return {'success': False, 'error': f'Invalid type. Must be one of: {", ".join(valid_types)}'}
        
        # Validate color
        valid_colors = ['cyan', 'purple', 'green', 'yellow', 'red']
        if color not in valid_colors:
            color = 'cyan'
        
        # Validate visible_to
        valid_visible = ['all', 'admin', 'user']
        if visible_to not in valid_visible:
            visible_to = 'all'
        
        # Get next sort order
        all_links = self.db.get_all_quick_links()
        sort_order = len(all_links)
        
        result = self.db.create_quick_link(title, icon, type_, content, color, visible_to, sort_order)
        
        if result['success']:
            return {
                'success': True,
                'message': 'Quick link created successfully',
                'link_id': result['id']
            }
        return result
    
    def get_quick_links(self, user_role='user'):
        """Get quick links for user"""
        visible_to = 'all'
        if user_role == 'admin' or user_role == 'superadmin':
            visible_to = 'admin'
        
        links = self.db.get_quick_links(visible_to)
        return {
            'success': True,
            'links': links
        }
    
    def get_all_quick_links(self, user_role=None):
        """Get all quick links (admin only)"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        links = self.db.get_all_quick_links()
        return {
            'success': True,
            'links': links
        }
    
    def update_quick_link(self, link_id, data, user_role=None):
        """Update quick link"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        # Validate type if provided
        if 'type' in data:
            valid_types = ['url', 'message', 'telegram_channel', 'telegram_contact']
            if data['type'] not in valid_types:
                return {'success': False, 'error': f'Invalid type'}
        
        # Validate color if provided
        if 'color' in data:
            valid_colors = ['cyan', 'purple', 'green', 'yellow', 'red']
            if data['color'] not in valid_colors:
                data['color'] = 'cyan'
        
        # Validate visible_to if provided
        if 'visible_to' in data:
            valid_visible = ['all', 'admin', 'user']
            if data['visible_to'] not in valid_visible:
                data['visible_to'] = 'all'
        
        return self.db.update_quick_link(link_id, data)
    
    def delete_quick_link(self, link_id, user_role=None):
        """Delete quick link"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        return self.db.delete_quick_link(link_id)
    
    def reorder_quick_links(self, order_list, user_role=None):
        """Reorder quick links"""
        if user_role not in ['admin', 'superadmin']:
            return {'success': False, 'error': 'Admin access required'}
        
        return self.db.reorder_quick_links(order_list)
