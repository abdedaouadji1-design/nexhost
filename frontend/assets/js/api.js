/**
 * NexHost V4 - API Client
 * ========================
 * All API requests and error handling
 */

const API_BASE_URL = window.location.origin + '/api';

// Store token
const TokenManager = {
    getToken() {
        return localStorage.getItem('nexhost_token');
    },
    
    setToken(token) {
        localStorage.setItem('nexhost_token', token);
    },
    
    removeToken() {
        localStorage.removeItem('nexhost_token');
    },
    
    getUser() {
        const userJson = localStorage.getItem('nexhost_user');
        return userJson ? JSON.parse(userJson) : null;
    },
    
    setUser(user) {
        localStorage.setItem('nexhost_user', JSON.stringify(user));
    },
    
    removeUser() {
        localStorage.removeItem('nexhost_user');
    },
    
    isLoggedIn() {
        return !!this.getToken();
    },
    
    isAdmin() {
        const user = this.getUser();
        return user && ['admin', 'superadmin'].includes(user.role);
    },
    
    isSuperAdmin() {
        const user = this.getUser();
        return user && user.role === 'superadmin';
    },
    
    logout() {
        this.removeToken();
        this.removeUser();
        window.location.href = 'login.html';
    }
};

// API Client
const API = {
    // Request helper
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };
        
        // Add auth token if available
        const token = TokenManager.getToken();
        if (token) {
            defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }
        
        const config = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        try {
            showLoading();
            const response = await fetch(url, config);
            hideLoading();
            
            // Handle maintenance mode
            if (response.status === 503) {
                const data = await response.json();
                if (data.maintenance) {
                    showMaintenanceScreen(data.message, data.end_time);
                    return { success: false, error: data.message, maintenance: true };
                }
            }
            
            // Handle unauthorized
            if (response.status === 401) {
                TokenManager.logout();
                return { success: false, error: 'Session expired. Please login again.' };
            }
            
            // Handle forbidden
            if (response.status === 403) {
                return { success: false, error: 'Access denied' };
            }
            
            // Parse JSON response
            const data = await response.json();
            
            if (!response.ok) {
                return { 
                    success: false, 
                    error: data.error || `HTTP ${response.status}` 
                };
            }
            
            return data;
            
        } catch (error) {
            hideLoading();
            console.error('API Error:', error);
            return { 
                success: false, 
                error: 'Network error. Please check your connection.' 
            };
        }
    },
    
    // GET request
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    // POST request
    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // PUT request
    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    // DELETE request
    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },
    
    // File upload
    async uploadFile(endpoint, formData) {
        const url = `${API_BASE_URL}${endpoint}`;
        const token = TokenManager.getToken();
        
        try {
            showLoading();
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });
            hideLoading();
            
            if (response.status === 401) {
                TokenManager.logout();
                return { success: false, error: 'Session expired' };
            }
            
            return await response.json();
            
        } catch (error) {
            hideLoading();
            return { success: false, error: 'Upload failed' };
        }
    }
};

// Auth API
const AuthAPI = {
    async login(username, password) {
        const result = await API.post('/auth/login', { username, password });
        
        if (result.success) {
            TokenManager.setToken(result.token);
            TokenManager.setUser(result.user);
        }
        
        return result;
    },
    
    async logout() {
        await API.post('/auth/logout', {});
        TokenManager.logout();
    },
    
    async getCurrentUser() {
        return await API.get('/auth/me');
    },
    
    async refreshToken() {
        const result = await API.post('/auth/refresh', {});
        
        if (result.success) {
            TokenManager.setToken(result.token);
            TokenManager.setUser(result.user);
        }
        
        return result;
    },
    
    async changeSuperAdminPassword(currentPassword, newPassword) {
        return await API.post('/auth/change-superadmin-password', {
            current_password: currentPassword,
            new_password: newPassword
        });
    }
};

// Projects API
const ProjectsAPI = {
    async getAll() {
        return await API.get('/projects');
    },
    
    async get(projectId) {
        return await API.get(`/projects/${projectId}`);
    },
    
    async create(data) {
        return await API.post('/projects', data);
    },
    
    async delete(projectId) {
        return await API.delete(`/projects/${projectId}`);
    },
    
    async start(projectId) {
        return await API.post(`/projects/${projectId}/start`, {});
    },
    
    async stop(projectId) {
        return await API.post(`/projects/${projectId}/stop`, {});
    },
    
    async restart(projectId) {
        return await API.post(`/projects/${projectId}/restart`, {});
    },
    
    async getStatus(projectId) {
        return await API.get(`/projects/${projectId}/status`);
    },
    
    async hotReload(projectId, filePath, file) {
        const formData = new FormData();
        formData.append('file_path', filePath);
        formData.append('file', file);
        return await API.uploadFile(`/projects/${projectId}/hot-reload`, formData);
    },
    
    async uploadFile(projectId, file) {
        const formData = new FormData();
        formData.append('file', file);
        return await API.uploadFile(`/projects/${projectId}/upload`, formData);
    },
    
    async getFiles(projectId) {
        return await API.get(`/projects/${projectId}/files`);
    },
    
    async getFileContent(projectId, filePath) {
        return await API.get(`/projects/${projectId}/files/${encodeURIComponent(filePath)}`);
    },
    
    async updateFile(projectId, filePath, content) {
        return await API.put(`/projects/${projectId}/files/${encodeURIComponent(filePath)}`, { content });
    },
    
    async deleteFile(projectId, filePath) {
        return await API.delete(`/projects/${projectId}/files/${encodeURIComponent(filePath)}`);
    },
    
    async getEnv(projectId) {
        return await API.get(`/projects/${projectId}/env`);
    },
    
    async updateEnv(projectId, env) {
        return await API.put(`/projects/${projectId}/env`, { env });
    },
    
    async getLogs(projectId, lines = 100) {
        return await API.get(`/projects/${projectId}/logs?lines=${lines}`);
    },
    
    async clearLogs(projectId) {
        return await API.delete(`/projects/${projectId}/logs`);
    }
};

// Users API (Admin only)
const UsersAPI = {
    async getAll() {
        return await API.get('/users');
    },
    
    async create(data) {
        return await API.post('/users', data);
    },
    
    async update(userId, data) {
        return await API.put(`/users/${userId}`, data);
    },
    
    async delete(userId) {
        return await API.delete(`/users/${userId}`);
    },
    
    async changePassword(userId, password) {
        return await API.put(`/users/${userId}/password`, { password });
    },
    
    async toggleStatus(userId) {
        return await API.post(`/users/${userId}/toggle`, {});
    }
};

// System API
const SystemAPI = {
    async getStats() {
        return await API.get('/system/stats');
    },
    
    async getInfo() {
        return await API.get('/system/info');
    }
};

// Activity API (Admin only)
const ActivityAPI = {
    async getAll(limit = 50) {
        return await API.get(`/activity?limit=${limit}`);
    },
    async clear() {
        return await API.delete('/activity');
    }
};

// Settings API
const SettingsAPI = {
    async getAll() {
        return await API.get('/settings');
    },
    
    async update(settings) {
        return await API.put('/settings', settings);
    },
    
    async createBackup() {
        return await API.post('/settings/backup', {});
    },
    
    async getBackups() {
        return await API.get('/settings/backups');
    }
};

// Admin API (Maintenance, Broadcast, Quick Links)
const AdminAPI = {
    // Maintenance
    async getMaintenanceStatus() {
        return await API.get('/admin/maintenance/status');
    },
    
    async toggleMaintenance(enabled, message, endTime) {
        return await API.post('/admin/maintenance/toggle', {
            enabled,
            message,
            end_time: endTime
        });
    },
    
    // Broadcast
    async getActiveBroadcast() {
        return await API.get('/admin/broadcast/active');
    },
    
    async createBroadcast(message, type, durationMinutes) {
        return await API.post('/admin/broadcast', {
            message,
            type,
            duration_minutes: durationMinutes
        });
    },
    
    async getBroadcastHistory() {
        return await API.get('/admin/broadcast/history');
    },
    
    async deactivateBroadcast(broadcastId) {
        return await API.delete(`/admin/broadcast/${broadcastId}`);
    },
    
    // Quick Links
    async getQuickLinks() {
        return await API.get('/quick-links');
    },
    
    async getAllQuickLinks() {
        return await API.get('/admin/quick-links');
    },
    
    async createQuickLink(data) {
        return await API.post('/admin/quick-links', data);
    },
    
    async updateQuickLink(linkId, data) {
        return await API.put(`/admin/quick-links/${linkId}`, data);
    },
    
    async deleteQuickLink(linkId) {
        return await API.delete(`/admin/quick-links/${linkId}`);
    },
    
    async reorderQuickLinks(order) {
        return await API.post('/admin/quick-links/reorder', { order });
    }
};

// Loading indicator
let loadingCount = 0;

function showLoading() {
    loadingCount++;
    let overlay = document.getElementById('loadingOverlay');
    
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <div style="color: var(--text); font-size: 14px;">جاري التحميل...</div>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    
    overlay.style.display = 'flex';
}

function hideLoading() {
    loadingCount--;
    
    if (loadingCount <= 0) {
        loadingCount = 0;
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
}

// Toast notifications (fallback if utils.js not loaded)
if (typeof showToast !== 'function') {
    function showToast(message, type = 'info', duration = 3000) {
        let container = document.getElementById('toastContainer');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `
            <span>${icons[type] || 'ℹ️'}</span>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(-100%)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// Format utilities
const FormatUtils = {
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    formatDuration(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    },
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ar-SA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    formatRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'الآن';
        if (diff < 3600) return `منذ ${Math.floor(diff / 60)}د`;
        if (diff < 86400) return `منذ ${Math.floor(diff / 3600)}س`;
        if (diff < 604800) return `منذ ${Math.floor(diff / 86400)}ي`;
        return this.formatDate(dateString);
    }
};

// Check auth on page load
function checkAuth() {
    const publicPages = ['login.html', 'register.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (publicPages.includes(currentPage)) {
        return;
    }
    
    if (!TokenManager.isLoggedIn()) {
        window.location.href = 'login.html';
        return;
    }
    
    // Update user info in sidebar
    const user = TokenManager.getUser();
    if (user) {
        const userNameEl = document.querySelector('.user-name');
        const userPlanEl = document.querySelector('.user-plan');
        const avatarEl = document.querySelector('.avatar');
        
        if (userNameEl) userNameEl.textContent = user.username;
        if (userPlanEl) userPlanEl.textContent = user.role.toUpperCase();
        if (avatarEl) avatarEl.textContent = user.username.charAt(0).toUpperCase();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// Export for use in other scripts
window.TokenManager = TokenManager;
window.API = API;
window.AuthAPI = AuthAPI;
window.ProjectsAPI = ProjectsAPI;
window.UsersAPI = UsersAPI;
window.SystemAPI = SystemAPI;
window.ActivityAPI = ActivityAPI;
window.SettingsAPI = SettingsAPI;
window.AdminAPI = AdminAPI;
window.showToast = showToast;
window.FormatUtils = FormatUtils;
