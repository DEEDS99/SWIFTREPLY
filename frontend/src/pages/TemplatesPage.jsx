import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi } from '../services/api'
import { Plus, Trash2, FileText, X } from 'lucide-react'
import toast from 'react-hot-toast'

function CreateTemplateModal({ onClose }) {
  const [form, setForm] = useState({ name: '', body: '', category: 'UTILITY', language: 'en', header: '', footer: '' })
  const qc = useQueryClient()
  const mut = useMutation({
    mutationFn: templatesApi.create,
    onSuccess: () => { toast.success('Template saved'); qc.invalidateQueries({ queryKey: ['templates'] }); onClose() },
    onError: () => toast.error('Failed to save template'),
  })
  const f = (k) => ({ value: form[k], onChange: (e) => setForm({ ...form, [k]: e.target.value }) })

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">New Template</h3>
          <button onClick={onClose}><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 font-medium">Template Name *</label>
              <input className="input-field mt-1" placeholder="order_confirmation" {...f('name')} />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">Category</label>
              <select className="input-field mt-1" {...f('category')}>
                <option>UTILITY</option>
                <option>MARKETING</option>
                <option>AUTHENTICATION</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Header (optional)</label>
            <input className="input-field mt-1" placeholder="Welcome to Acme!" {...f('header')} />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Body *</label>
            <textarea
              className="input-field mt-1 min-h-24"
              placeholder="Hi {{1}}, your order {{2}} is confirmed..."
              {...f('body')}
            />
            <p className="text-xs text-gray-400 mt-1">Use {'{{1}}'}, {'{{2}}'} for variables</p>
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">Footer (optional)</label>
            <input className="input-field mt-1" placeholder="Reply STOP to unsubscribe" {...f('footer')} />
          </div>
          <button onClick={() => mut.mutate(form)} disabled={!form.name || !form.body || mut.isPending} className="btn-primary w-full">
            {mut.isPending ? 'Saving...' : 'Save Template'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function TemplatesPage() {
  const [showCreate, setShowCreate] = useState(false)
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['templates'], queryFn: templatesApi.list })
  const delMut = useMutation({
    mutationFn: templatesApi.delete,
    onSuccess: () => { toast.success('Template deleted'); qc.invalidateQueries({ queryKey: ['templates'] }) },
  })
  const templates = data?.templates || []

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Message Templates</h1>
            <p className="text-sm text-gray-500 mt-1">Pre-approved templates for outbound messaging</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
            <Plus size={16} /> New Template
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-12 text-gray-400">Loading...</div>
        ) : templates.length === 0 ? (
          <div className="card p-12 text-center">
            <FileText size={36} className="text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No templates yet. Create your first template.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {templates.map((t) => (
              <div key={t.id} className="card p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">{t.name}</span>
                      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                        t.status === 'approved' ? 'bg-green-100 text-green-700' :
                        t.status === 'rejected' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {t.status}
                      </span>
                      <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{t.category}</span>
                    </div>
                    {t.header && <p className="text-xs text-gray-500 font-medium mb-1">{t.header}</p>}
                    <p className="text-sm text-gray-700">{t.body}</p>
                    {t.footer && <p className="text-xs text-gray-400 mt-1">{t.footer}</p>}
                    {t.variables?.length > 0 && (
                      <div className="flex gap-1 mt-2">
                        {t.variables.map((v, i) => (
                          <span key={i} className="text-xs bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded">{v}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => delMut.mutate(t.id)}
                    className="text-gray-300 hover:text-red-400 transition-colors shrink-0"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      {showCreate && <CreateTemplateModal onClose={() => setShowCreate(false)} />}
    </div>
  )
}
