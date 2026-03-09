import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('sr_user') || 'null'),
  token: localStorage.getItem('sr_token') || null,
  isAuthenticated: !!localStorage.getItem('sr_token'),

  login: (user, token) => {
    localStorage.setItem('sr_token', token)
    localStorage.setItem('sr_user', JSON.stringify(user))
    set({ user, token, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('sr_token')
    localStorage.removeItem('sr_user')
    set({ user: null, token: null, isAuthenticated: false })
  },

  updateUser: (updates) => {
    set((state) => {
      const updated = { ...state.user, ...updates }
      localStorage.setItem('sr_user', JSON.stringify(updated))
      return { user: updated }
    })
  },
}))

export default useAuthStore
