import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { UserPlus, Shield, User, Eye, Trash2, X } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'
import useAuthStore from '../hooks/useAuthStore'

const ROLES = [
  { value: 'owner', label: 'Owner', icon: Shield, color: 'text-purple-600 bg-purple-50' },
  { value: 'admin', label: 'Admin', icon: Shield, color: 'text-blue-600 bg-blue-50' },
  { value: 'agent', label: 'Agent', icon: User, color: 'text-green-600 bg-green-50' },
  { value: 'viewer', label: 'Viewer', icon: Eye, color: 'text-gray-600 bg-gray-50' },
]

function InviteModal({ onClose }) {
  const [form, setForm] = useState({ full_name: '', email: '', role: 'agent', password: '' })
  const qc = useQueryClient()
  const mut = useMutation({
    mutationFn: (d) => api.post('/users/invite', d).then(r => r.data),
    onSuccess: () => { toast.success('Team member added!'); qc.invalidateQueries({ queryKey: ['users'] }); onClose() },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to invite'),
  })
  const f = (k) => ({ value: form[k], onChange: (e) => setForm({ ...form, [k]: e.target.value }) })

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold text-gray-900">Invite Team Member</h3>
          <button onClick={onClose}><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 font-medium">Full Name</label>
            <input className="input-field mt-1" placeholder="Jane Smith" {...f('full_name')} required />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Email</label>
            <input type="email" className="input-field mt-1" placeholder="jane@company.com" {...f('email')} required />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Role</label>
            <select className="input-field mt-1" {...f('role')}>
              {ROLES.filter(r => r.value !== 'owner').map(r => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Temporary Password</label>
            <input type="password" className="input-field mt-1" placeholder="Min. 8 characters" {...f('password')} required minLength={8} />
            <p className="text-xs text-gray-400 mt-1">Ask them to change this after first login.</p>
          </div>
          <button
            onClick={() => mut.mutate(form)}
            disabled={!form.full_name || !form.email || !form.password || mut.isPending}
            className="btn-primary w-full mt-2"
          >
            {mut.isPending ? 'Adding...' : 'Add to Team'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function TeamPage() {
  const [showInvite, setShowInvite] = useState(false)
  const { user: currentUser } = useAuthStore()
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users').then(r => r.data),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, ...body }) => api.patch(`/users/${id}`, body).then(r => r.data),
    onSuccess: () => { toast.success('Updated'); qc.invalidateQueries({ queryKey: ['users'] }) },
  })

  const deactivateMut = useMutation({
    mutationFn: (id) => api.delete(`/users/${id}`).then(r => r.data),
    onSuccess: () => { toast.success('User deactivated'); qc.invalidateQueries({ queryKey: ['users'] }) },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  const users = data?.users || []
  const isAdmin = ['owner', 'admin'].includes(currentUser?.role)

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Team</h1>
            <p className="text-sm text-gray-500 mt-1">{users.length} member{users.length !== 1 ? 's' : ''}</p>
          </div>
          {isAdmin && (
            <button onClick={() => setShowInvite(true)} className="btn-primary flex items-center gap-2">
              <UserPlus size={16} /> Invite Member
            </button>
          )}
        </div>

        <div className="card overflow-hidden">
          {isLoading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="px-5 py-3 text-left">Member</th>
                  <th className="px-5 py-3 text-left hidden sm:table-cell">Role</th>
                  <th className="px-5 py-3 text-left hidden md:table-cell">Last Login</th>
                  <th className="px-5 py-3 text-left">Status</th>
                  {isAdmin && <th className="px-5 py-3 text-right">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {users.map((u) => {
                  const roleInfo = ROLES.find(r => r.value === u.role) || ROLES[2]
                  const RoleIcon = roleInfo.icon
                  const isSelf = u.id === currentUser?.id
                  return (
                    <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-whatsapp-teal flex items-center justify-center text-white text-sm font-bold">
                            {u.full_name[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{u.full_name} {isSelf && <span className="text-xs text-gray-400">(you)</span>}</p>
                            <p className="text-xs text-gray-400">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 hidden sm:table-cell">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${roleInfo.color}`}>
                          <RoleIcon size={11} /> {roleInfo.label}
                        </span>
                      </td>
                      <td className="px-5 py-4 hidden md:table-cell text-xs text-gray-400">
                        {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="px-5 py-4">
                        <span className={`inline-flex items-center gap-1 text-xs font-medium ${u.is_active ? 'text-green-600' : 'text-gray-400'}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      {isAdmin && (
                        <td className="px-5 py-4 text-right">
                          {!isSelf && u.role !== 'owner' && (
                            <div className="flex items-center justify-end gap-2">
                              <select
                                value={u.role}
                                onChange={(e) => updateMut.mutate({ id: u.id, role: e.target.value })}
                                className="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-whatsapp-teal"
                              >
                                {ROLES.filter(r => r.value !== 'owner').map(r => (
                                  <option key={r.value} value={r.value}>{r.label}</option>
                                ))}
                              </select>
                              {u.is_active && (
                                <button
                                  onClick={() => {
                                    if (confirm(`Deactivate ${u.full_name}?`)) deactivateMut.mutate(u.id)
                                  }}
                                  className="text-gray-300 hover:text-red-400 transition-colors"
                                >
                                  <Trash2 size={15} />
                                </button>
                              )}
                            </div>
                          )}
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
      {showInvite && <InviteModal onClose={() => setShowInvite(false)} />}
    </div>
  )
}
