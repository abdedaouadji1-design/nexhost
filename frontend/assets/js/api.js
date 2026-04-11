/**
 * NexHost V5 - API Client
 * =======================
 * Unified API client for all backend endpoints
 */

const API_BASE = '/api';

// Generic API request handler
const API = {
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    };
    
    // Add auth token if available
    const token = TokenManager.getToken();
    if (token) {
      defaultOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
      const response = await fetch(url, { ...defaultOptions, ...options });
      
      // Check if response is ok
      if (!response.ok) {
        if (response.status === 401) {
          TokenManager.logout();
          return { success: false, error: 'Unauthorized' };
        }
        if (response.status === 403) {
          return { success: false, error: 'Forbidden - Insufficient permissions' };
        }
        if (response.status === 404) {
          return { success: false, error: 'Not found' };
        }
        if (response.status >= 500) {
          return { success: false, error: 'Server error' };
        }
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API Error:', error);
      return { success: false, error: 'Network error' };
    }
  },
  
  // GET request
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },
  
  // POST request
  async post(endpoint, body) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },
  
  // PUT request
  async put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body)
    });
  },
  
  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },
  
  // PATCH request
  async patch(endpoint, body) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body)
    });
  },
  
  // Upload file
  async uploadFile(endpoint, formData) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    const token = TokenManager.getToken();
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: formData
      });
      
      return await response.json();
    } catch (error) {
      console.error('Upload Error:', error);
      return { success: false, error: 'Upload failed' };
    }
  }
};

// Authentication API
const AuthAPI = {
  async login(username, password) {
    return API.post('/auth/login', { username, password });
  },
  
  async logout() {
    return API.post('/auth/logout', {});
  },
  
  async getCurrentUser() {
    return API.get('/auth/me');
  },
  
  async refreshToken() {
    return API.post('/auth/refresh', {});
  }
};

// Projects API
const ProjectsAPI = {
  // Get all projects
  async getAll() {
    return API.get('/projects');
  },
  
  // Get single project
  async get(projectId) {
    return API.get(`/projects/${projectId}`);
  },
  
  // Create new project
  async create(projectData) {
    return API.post('/projects', projectData);
  },
  
  // Update project
  async update(projectId, projectData) {
    return API.put(`/projects/${projectId}`, projectData);
  },
  
  // Delete project
  async delete(projectId) {
    return API.delete(`/projects/${projectId}`);
  },
  
  // Start project
  async start(projectId) {
    return API.post(`/projects/${projectId}/start`, {});
  },
  
  // Stop project
  async stop(projectId) {
    return API.post(`/projects/${projectId}/stop`, {});
  },
  
  // Restart project
  async restart(projectId) {
    return API.post(`/projects/${projectId}/restart`, {});
  },
  
  // Get project logs
  async getLogs(projectId, lines = 100) {
    return API.get(`/projects/${projectId}/logs?lines=${lines}`);
  },
  
  // Get project files
  async getFiles(projectId) {
    return API.get(`/projects/${projectId}/files`);
  },
  
  // Get file content
  async getFileContent(projectId, filename) {
    return API.get(`/projects/${projectId}/files/${encodeURIComponent(filename)}`);
  },
  
  // Update file content
  async updateFile(projectId, filename, content) {
    return API.put(`/projects/${projectId}/files/${encodeURIComponent(filename)}`, { content });
  },
  
  // Delete file
  async deleteFile(projectId, filename) {
    return API.delete(`/projects/${projectId}/files/${encodeURIComponent(filename)}`);
  },
  
  // Get environment variables
  async getEnv(projectId) {
    return API.get(`/projects/${projectId}/env`);
  },
  
  // Update environment variables
  async updateEnv(projectId, env) {
    return API.put(`/projects/${projectId}/env`, env);
  },
  
  // Hot reload project
  async hotReload(projectId, filename, file) {
    const formData = new FormData();
    formData.append('file', file);
    return API.uploadFile(`/projects/${projectId}/hot-reload`, formData);
  }
};

// Users API
const UsersAPI = {
  // Get all users (admin only)
  async getAll() {
    return API.get('/users');
  },
  
  // Get single user
  async get(userId) {
    return API.get(`/users/${userId}`);
  },
  
  // Create new user (admin only)
  async create(userData) {
    return API.post('/users', userData);
  },
  
  // Update user (admin only)
  async update(userId, userData) {
    return API.put(`/users/${userId}`, userData);
  },
  
  // Delete user (admin only)
  async delete(userId) {
    return API.delete(`/users/${userId}`);
  },
  
  // Toggle user status (admin only)
  async toggleStatus(userId) {
    return API.post(`/users/${userId}/toggle-status`, {});
  },
  
  // Change user password (admin only)
  async changePassword(userId, newPassword) {
    return API.post(`/users/${userId}/change-password`, { password: newPassword });
  },
  
  // Change own password
  async changeMyPassword(currentPassword, newPassword) {
    return API.post('/users/me/change-password', { current_password: currentPassword, new_password: newPassword });
  },
  
  // Delete own account
  async deleteMe() {
    return API.delete('/users/me');
  }
};

// System API
const SystemAPI = {
  // Get system stats
  async getStats() {
    return API.get('/system/stats');
  },
  
  // Get system info
  async getInfo() {
    return API.get('/system/info');
  },
  
  // Check health
  async checkHealth() {
    return API.get('/health');
  }
};

// Admin API
const AdminAPI = {
  // Get all quick links
  async getAllQuickLinks() {
    return API.get('/admin/quick-links');
  },
  
  // Create quick link
  async createQuickLink(linkData) {
    return API.post('/admin/quick-links', linkData);
  },
  
  // Update quick link
  async updateQuickLink(linkId, linkData) {
    return API.put(`/admin/quick-links/${linkId}`, linkData);
  },
  
  // Delete quick link
  async deleteQuickLink(linkId) {
    return API.delete(`/admin/quick-links/${linkId}`);
  },
  
  // Create broadcast message
  async createBroadcast(message, type = 'info', durationMinutes = null) {
    return API.post('/admin/broadcast', { message, type, duration_minutes: durationMinutes });
  },
  
  // Get maintenance status
  async getMaintenanceStatus() {
    return API.get('/admin/maintenance/status');
  },
  
  // Toggle maintenance mode
  async toggleMaintenance(enabled, message = '', endTime = null) {
    return API.post('/admin/maintenance/toggle', { enabled, message, end_time: endTime });
  },
  
  // Get all settings
  async getSettings() {
    return API.get('/admin/settings');
  },
  
  // Update settings
  async updateSettings(settings) {
    return API.put('/admin/settings', settings);
  }
};

// Activity API
const ActivityAPI = {
  // Get all activity logs
  async getAll(limit = 50) {
    return API.get(`/activity?limit=${limit}`);
  },
  
  // Get user activity
  async getUserActivity(userId, limit = 50) {
    return API.get(`/activity/user/${userId}?limit=${limit}`);
  },
  
  // Clear activity logs
  async clear() {
    return API.delete('/activity');
  }
};

// Token Manager
const TokenManager = {
  TOKEN_KEY: 'nexhost_token',
  USER_KEY: 'nexhost_user',
  
  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  },
  
  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },
  
  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },
  
  getUser() {
    const user = localStorage.getItem(this.USER_KEY);
    return user ? JSON.parse(user) : null;
  },
  
  isLoggedIn() {
    return !!this.getToken();
  },
  
  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    window.location.href = 'login.html';
  },
  
  async refresh() {
    const result = await AuthAPI.refreshToken();
    if (result.success && result.token) {
      this.setToken(result.token);
      return true;
    }
    return false;
  }
};

// Admin check helper
function requireAdmin() {
  const user = TokenManager.getUser();
  if (!user || !['admin', 'superadmin'].includes(user.role)) {
    showToast('لا تملك صلاحية الوصول', 'error');
    window.location.href = 'hosting-panel.html';
    return false;
  }
  return true;
}

// Super admin check helper
function requireSuperAdmin() {
  const user = TokenManager.getUser();
  if (!user || user.role !== 'superadmin') {
    showToast('لا تملك صلاحية الوصول - يحتاج Super Admin', 'error');
    window.location.href = 'hosting-panel.html';
    return false;
  }
  return true;
}
