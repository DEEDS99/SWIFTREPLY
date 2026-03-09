import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Zap } from 'lucide-react'
import { authApi } from '../services/api'
import useAuthStore from '../hooks/useAuthStore'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const [form, setForm] = useState({ org_name: '', full_name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }
    setLoading(true)
    try {
      const data = await authApi.register(form)
      login(data.user, data.access_token)
      toast.success('Organisation created! Welcome to SwiftReply 🎉')
      navigate('/settings')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const f = (k) => ({ value: form[k], onChange: (e) => setForm({ ...form, [k]: e.target.value }) })

  return (
    <div className="min-h-screen bg-gradient-to-br from-whatsapp-dark via-whatsapp-teal to-whatsapp-green flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <Zap size={32} className="text-whatsapp-teal" />
          </div>
          <h1 className="text-2xl font-bold text-white">Get Started Free</h1>
          <p className="text-white/70 text-sm mt-1">Set up your organisation in 60 seconds</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Create your organisation</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Organisation Name</label>
              <input type="text" className="input-field" placeholder="Acme Corp" {...f('org_name')} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Your Full Name</label>
              <input type="text" className="input-field" placeholder="Jane Smith" {...f('full_name')} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Work Email</label>
              <input type="email" className="input-field" placeholder="jane@acme.com" {...f('email')} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input type="password" className="input-field" placeholder="Min. 8 characters" {...f('password')} required minLength={8} />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 mt-2">
              {loading ? 'Creating account...' : 'Create Organisation'}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-whatsapp-teal font-medium hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
