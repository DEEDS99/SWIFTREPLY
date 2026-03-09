import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sr_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 globally
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('sr_token')
      localStorage.removeItem('sr_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ─── Auth ───────────────────────────────────────────────────────────────────

export const authApi = {
  register: (data) => api.post('/auth/register', data).then((r) => r.data),
  login: (data) => api.post('/auth/login', data).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
}

// ─── Conversations ──────────────────────────────────────────────────────────

export const conversationsApi = {
  list: (params) => api.get('/conversations', { params }).then((r) => r.data),
  getMessages: (id, params) => api.get(`/conversations/${id}/messages`, { params }).then((r) => r.data),
  updateStatus: (id, status) => api.patch(`/conversations/${id}/status`, { status }).then((r) => r.data),
}

// ─── Messages ───────────────────────────────────────────────────────────────

export const messagesApi = {
  send: (data) => api.post('/messages/send', data).then((r) => r.data),
}

// ─── Contacts ───────────────────────────────────────────────────────────────

export const contactsApi = {
  list: (params) => api.get('/contacts', { params }).then((r) => r.data),
  create: (data) => api.post('/contacts', data).then((r) => r.data),
}

// ─── Analytics ──────────────────────────────────────────────────────────────

export const analyticsApi = {
  summary: () => api.get('/analytics/summary').then((r) => r.data),
}

// ─── Templates ──────────────────────────────────────────────────────────────

export const templatesApi = {
  list: () => api.get('/templates').then((r) => r.data),
  create: (data) => api.post('/templates', data).then((r) => r.data),
  delete: (id) => api.delete(`/templates/${id}`).then((r) => r.data),
}

// ─── AI ─────────────────────────────────────────────────────────────────────

export const aiApi = {
  generateReply: (data) => api.post('/ai/generate-reply', data).then((r) => r.data),
}

export default api
