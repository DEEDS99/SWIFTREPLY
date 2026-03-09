import React, { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Megaphone, Send, Users, Image, FileText,
  CheckCircle, XCircle, Loader2, Plus, X, Radio
} from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

function ProgressBar({ sent, failed, total }) {
  const pct = total > 0 ? Math.round(((sent + failed) / total) * 100) : 0
  return (
    <div className="mt-2">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{sent} sent · {failed} failed · {total} total</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full flex">
          <div className="bg-green-500 transition-all duration-500" style={{ width: `${(sent/total)*100}%` }} />
          <div className="bg-red-400 transition-all duration-500" style={{ width: `${(failed/total)*100}%` }} />
        </div>
      </div>
    </div>
  )
}

export default function BroadcastPage() {
  const [form, setForm] = useState({
    name: '',
    message_body: '',
    message_type: 'text',
    media_url: '',
  })
  const [activeCampaigns, setActiveCampaigns] = useState([])
  const qc = useQueryClient()

  const { data: recentData } = useQuery({
    queryKey: ['broadcasts'],
    queryFn: () => api.get('/broadcasts').then(r => r.data),
    refetchInterval: 5000,
  })

  const { data: contactsData } = useQuery({
    queryKey: ['contacts-count'],
    queryFn: () => api.get('/contacts').then(r => r.data),
  })

  const sendMutation = useMutation({
    mutationFn: (data) => api.post('/broadcasts', data).then(r => r.data),
    onSuccess: (data) => {
      toast.success(`Broadcast started — ${data.total_recipients} recipients`)
      setActiveCampaigns(prev => [...prev, {
        id: data.campaign_id,
        name: form.name,
        total: data.total_recipients,
        sent: 0,
        failed: 0,
        status: 'running',
      }])
      setForm({ name: '', message_body: '', message_type: 'text', media_url: '' })
      qc.invalidateQueries({ queryKey: ['broadcasts'] })

      // Poll progress
      const interval = setInterval(async () => {
        try {
          const r = await api.get(`/broadcasts/${data.campaign_id}/progress`)
          const p = r.data
          setActiveCampaigns(prev => prev.map(c =>
            c.id === data.campaign_id ? { ...c, ...p } : c
          ))
          if (p.status === 'completed') clearInterval(interval)
        } catch { clearInterval(interval) }
      }, 2000)
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Broadcast failed'),
  })

  const contactCount = contactsData?.contacts?.length || 0
  const f = (k) => ({ value: form[k], onChange: (e) => setForm({ ...form, [k]: e.target.value }) })

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
            <Megaphone size={20} className="text-orange-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Broadcast Campaigns</h1>
            <p className="text-sm text-gray-500">Send bulk messages to all or filtered contacts</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Compose */}
          <div className="lg:col-span-3 card p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Plus size={16} className="text-whatsapp-teal" /> New Broadcast
            </h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-500 font-medium">Campaign Name</label>
                <input className="input-field mt-1" placeholder="Flash Sale — November" {...f('name')} />
              </div>
              <div>
                <label className="text-xs text-gray-500 font-medium">Message Type</label>
                <div className="flex gap-2 mt-1">
                  {['text', 'image', 'video', 'document'].map(t => (
                    <button key={t}
                      onClick={() => setForm({ ...form, message_type: t })}
                      className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors capitalize ${
                        form.message_type === t
                          ? 'bg-whatsapp-teal text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {form.message_type !== 'text' && (
                <div>
                  <label className="text-xs text-gray-500 font-medium">Media URL</label>
                  <input className="input-field mt-1" placeholder="https://..." {...f('media_url')} />
                </div>
              )}

              <div>
                <label className="text-xs text-gray-500 font-medium">
                  Message Body {form.message_type !== 'text' && '(caption)'}
                </label>
                <textarea
                  className="input-field mt-1 min-h-28 resize-none"
                  placeholder="Type your message here..."
                  {...f('message_body')}
                />
                <p className="text-xs text-gray-400 mt-1">{form.message_body.length} characters</p>
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700">
                <p className="font-semibold mb-0.5">⚠️ Rate limiting enabled</p>
                <p>Messages are sent at ~1/second to protect your WhatsApp account from bans.</p>
              </div>

              <button
                onClick={() => sendMutation.mutate(form)}
                disabled={!form.name || !form.message_body || sendMutation.isPending}
                className="btn-primary w-full flex items-center justify-center gap-2 py-2.5"
              >
                {sendMutation.isPending ? (
                  <><Loader2 size={16} className="animate-spin" /> Starting...</>
                ) : (
                  <><Send size={16} /> Send to {contactCount} contacts</>
                )}
              </button>
            </div>
          </div>

          {/* Status panel */}
          <div className="lg:col-span-2 space-y-4">
            {/* Active campaigns */}
            {activeCampaigns.length > 0 && (
              <div className="card p-4">
                <h4 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <Radio size={14} className="text-green-500" /> Active
                </h4>
                <div className="space-y-4">
                  {activeCampaigns.map(c => (
                    <div key={c.id}>
                      <div className="flex items-center gap-2">
                        {c.status === 'completed'
                          ? <CheckCircle size={14} className="text-green-500" />
                          : <Loader2 size={14} className="text-blue-500 animate-spin" />
                        }
                        <span className="text-sm font-medium text-gray-800 truncate">{c.name}</span>
                      </div>
                      <ProgressBar sent={c.sent || 0} failed={c.failed || 0} total={c.total || 1} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Contacts summary */}
            <div className="card p-4">
              <h4 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <Users size={14} className="text-blue-500" /> Audience
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Total contacts</span>
                  <span className="font-semibold">{contactCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Eligible (not blocked)</span>
                  <span className="font-semibold text-green-600">{contactCount}</span>
                </div>
              </div>
            </div>

            {/* Recent campaigns */}
            {(recentData?.campaigns?.length > 0) && (
              <div className="card p-4">
                <h4 className="text-sm font-semibold text-gray-800 mb-3">Recent</h4>
                <div className="space-y-3">
                  {recentData.campaigns.slice(-5).reverse().map(c => (
                    <div key={c.id} className="text-xs">
                      <div className="flex items-center gap-1.5">
                        {c.status === 'completed'
                          ? <CheckCircle size={11} className="text-green-500" />
                          : c.status === 'running'
                          ? <Loader2 size={11} className="text-blue-500 animate-spin" />
                          : <XCircle size={11} className="text-gray-300" />
                        }
                        <span className="text-gray-600 capitalize">{c.status}</span>
                        <span className="text-gray-400 ml-auto">{c.sent || 0}/{c.total || 0}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
