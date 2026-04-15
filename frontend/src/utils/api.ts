import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  refresh: () => api.post('/auth/refresh'),
  
  me: () => api.get('/auth/me'),
}

// AI API
export const aiApi = {
  chat: (message: string, model: string = 'v3', systemPrompt?: string) =>
    api.post('/ai/chat', { message, model, system_prompt: systemPrompt }),
  
  fixCode: (code: string, errorMessage?: string) =>
    api.post('/ai/code/fix', { code, error_message: errorMessage }),
  
  explainCode: (code: string) =>
    api.post('/ai/code/explain', { code }),
  
  generateBot: (description: string, botType: string = 'telegram', features?: string[]) =>
    api.post('/ai/generate-bot', { description, bot_type: botType, features }),
  
  debugBot: (code: string, errorMessage?: string) =>
    api.post('/ai/debug-bot', { code, error_message: errorMessage }),
  
  status: () => api.get('/ai/status'),
}

// Ready Bots API (Admin)
export const adminBotsApi = {
  create: (data: {
    name: string
    description: string
    bot_type: string
    code: string
    requirements: string
    image_url?: string
    icon?: string
    config_fields?: any[]
    is_premium?: boolean
  }) => api.post('/admin/ready-bots', data),
  
  list: () => api.get('/admin/ready-bots'),
  
  delete: (botId: number) => api.delete(`/admin/ready-bots/${botId}`),
}

// User Bots API
export const userBotsApi = {
  listAvailable: () => api.get('/ready-bots'),
  
  create: (data: {
    template_id: number
    name: string
    config: Record<string, string>
    debug_mode?: boolean
  }) => api.post('/my-bots', data),
  
  list: () => api.get('/my-bots'),
  
  start: (botId: number) => api.post(`/my-bots/${botId}/start`),
  
  stop: (botId: number) => api.post(`/my-bots/${botId}/stop`),
  
  logs: (botId: number, lines: number = 100) =>
    api.get(`/my-bots/${botId}/logs?lines=${lines}`),
  
  delete: (botId: number) => api.delete(`/my-bots/${botId}`),
}

// Users API (Admin)
export const usersApi = {
  list: () => api.get('/admin/users'),
  
  create: (data: {
    username: string
    email: string
    password: string
    role?: string
  }) => api.post('/admin/users', data),
  
  updateQuotas: (userId: number, quotas: {
    max_python_files?: number
    max_php_files?: number
    max_ready_bots?: number
  }) => api.patch(`/admin/users/${userId}/quotas`, quotas),
}

// Health API
export const healthApi = {
  check: () => api.get('/health'),
}

export default api
