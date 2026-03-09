import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contactsApi } from '../services/api'
import { Search, UserPlus, Phone, Building, Tag, X } from 'lucide-react'
import toast from 'react-hot-toast'

function AddContactModal({ onClose }) {
  const [form, setForm] = useState({ phone_number: '', display_name: '', email: '', company: '' })
  const qc = useQueryClient()
  const mut = useMutation({
    mutationFn: contactsApi.create,
    onSuccess: () => { toast.success('Contact added'); qc.invalidateQueries({ queryKey: ['contacts'] }); onClose() },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to add contact'),
  })
  const f = (k) => ({ value: form[k], onChange: (e) => setForm({ ...form, [k]: e.target.value }) })
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Add Contact</h3>
          <button onClick={onClose}><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 font-medium">Phone Number (E.164 format) *</label>
            <input className="input-field mt-1" placeholder="+260971234567" {...f('phone_number')} required />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Full Name</label>
            <input className="input-field mt-1" placeholder="Jane Smith" {...f('display_name')} />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Email</label>
            <input type="email" className="input-field mt-1" placeholder="jane@company.com" {...f('email')} />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Company</label>
            <input className="input-field mt-1" placeholder="Acme Corp" {...f('company')} />
          </div>
          <button
            onClick={() => mut.mutate(form)}
            disabled={!form.phone_number || mut.isPending}
            className="btn-primary w-full mt-2"
          >
            {mut.isPending ? 'Adding...' : 'Add Contact'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function ContactsPage() {
  const [search, setSearch] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const { data, isLoading } = useQuery({
    queryKey: ['contacts', search],
    queryFn: () => contactsApi.list({ search: search || undefined }),
    debounce: 300,
  })
  const contacts = data?.contacts || []

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900">Contacts</h1>
          <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2">
            <UserPlus size={16} /> Add Contact
          </button>
        </div>

        <div className="relative mb-4">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-whatsapp-teal bg-white"
            placeholder="Search by name or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="card overflow-hidden">
          {isLoading ? (
            <div className="p-8 text-center text-gray-400 text-sm">Loading...</div>
          ) : contacts.length === 0 ? (
            <div className="p-12 text-center">
              <UserPlus size={32} className="text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No contacts yet. Add your first contact or they'll appear automatically when they message you.</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3 text-left">Contact</th>
                  <th className="px-4 py-3 text-left hidden sm:table-cell">Phone</th>
                  <th className="px-4 py-3 text-left hidden md:table-cell">Company</th>
                  <th className="px-4 py-3 text-left hidden lg:table-cell">Tags</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {contacts.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-whatsapp-teal flex items-center justify-center text-white text-xs font-bold">
                          {(c.display_name || c.phone_number)[0].toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{c.display_name || '—'}</p>
                          <p className="text-xs text-gray-400 sm:hidden">{c.phone_number}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <span className="text-sm text-gray-600 flex items-center gap-1">
                        <Phone size={12} className="text-gray-400" /> {c.phone_number}
                      </span>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className="text-sm text-gray-600">{c.company || '—'}</span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <div className="flex gap-1 flex-wrap">
                        {(c.tags || []).map((tag) => (
                          <span key={tag} className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-full">{tag}</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
      {showAdd && <AddContactModal onClose={() => setShowAdd(false)} />}
    </div>
  )
}
