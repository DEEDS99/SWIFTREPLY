import React, { useState } from 'react'
import { Settings, Key, MessageSquare, Bot, Save, Server, ExternalLink } from 'lucide-react'
import useAuthStore from '../hooks/useAuthStore'
import toast from 'react-hot-toast'
import api from '../services/api'

function Section({ title, icon: Icon, badge, children }) {
  return (
    <div className="card p-6 mb-5">
      <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
        <Icon size={18} className="text-whatsapp-teal" />
        {title}
        {badge && <span className="ml-auto text-xs px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full font-medium">{badge}</span>}
      </h3>
      {children}
    </div>
  )
}

export default function SettingsPage() {
  const { user } = useAuthStore()
  const [evo, setEvo] = useState({ url: '', api_key: '', instance: 'swiftreply' })
  const [ai, setAi] = useState({
    gemini_key: '',
    system_prompt: 'You are a helpful business assistant. Reply professionally and concisely.',
    ai_enabled: true,
  })
  const [saving, setSaving] = useState('')

  const save = async (field, data) => {
    setSaving(field)
    try {
      await api.patch('/auth/organisation', data)
      toast.success('Saved!')
    } catch {
      toast.error('Failed to save')
    } finally {
      setSaving('')
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-xl font-bold text-gray-900 mb-6">Settings</h1>

        <Section title="Account" icon={Settings}>
          <div className="space-y-3">
            <div><label className="text-xs text-gray-500">Organisation</label>
              <p className="text-sm font-medium mt-0.5">{user?.organisation_name}</p></div>
            <div><label className="text-xs text-gray-500">Email</label>
              <p className="text-sm mt-0.5">{user?.email}</p></div>
            <div><label className="text-xs text-gray-500">Plan</label>
              <span className="inline-block mt-0.5 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full capitalize">{user?.plan || 'starter'}</span></div>
          </div>
        </Section>

        <Section title="Evolution API (WhatsApp)" icon={Server} badge="Recommended">
          <div className="space-y-4">
            <div className="p-3 bg-emerald-50 rounded-lg text-xs text-emerald-800 border border-emerald-200">
              <p className="font-semibold mb-1">✅ ToS-Compliant WhatsApp Connection</p>
              <p>Evolution API uses the WhatsApp Web protocol — no Meta Business verification or webhook approval needed. Self-host it or use a provider.</p>
              <a href="https://github.com/EvolutionAPI/evolution-api" target="_blank" rel="noopener" className="flex items-center gap-1 mt-2 text-emerald-600 hover:underline font-medium">
                <ExternalLink size={11} /> View Evolution API on GitHub
              </a>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg text-xs text-blue-700">
              <p className="font-semibold mb-1">Webhook URL (set this in Evolution API)</p>
              <code className="bg-blue-100 px-1.5 py-0.5 rounded font-mono">
                {window.location.origin.replace('5173', '8000')}/api/evolution/webhook
              </code>
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">Evolution API Server URL</label>
              <input className="input-field mt-1" placeholder="https://evo.yourserver.com"
                value={evo.url} onChange={e => setEvo({...evo, url: e.target.value})} />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">Global API Key</label>
              <input type="password" className="input-field mt-1" placeholder="Your Evolution API key"
                value={evo.api_key} onChange={e => setEvo({...evo, api_key: e.target.value})} />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">Instance Name</label>
              <input className="input-field mt-1" placeholder="swiftreply"
                value={evo.instance} onChange={e => setEvo({...evo, instance: e.target.value})} />
              <p className="text-xs text-gray-400 mt-1">Each organisation has one Evolution instance. After saving, go to Live Dashboard → Pair to scan QR code.</p>
            </div>
            <button onClick={() => save('evo', {evolution_url: evo.url, evolution_api_key: evo.api_key, evolution_instance: evo.instance})}
              disabled={saving === 'evo'} className="btn-primary flex items-center gap-2">
              <Save size={14} /> {saving === 'evo' ? 'Saving...' : 'Save Evolution Settings'}
            </button>
          </div>
        </Section>

        <Section title="AI Configuration (Google Gemini)" icon={Bot}>
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
              <input type="checkbox" id="ai_on" checked={ai.ai_enabled}
                onChange={e => setAi({...ai, ai_enabled: e.target.checked})} className="w-4 h-4 text-purple-600" />
              <label htmlFor="ai_on" className="text-sm text-purple-700 font-medium cursor-pointer">
                Enable AI Auto-Reply (text, image, audio, video)
              </label>
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">Gemini API Key</label>
              <input type="password" className="input-field mt-1" placeholder="AIzaSy..."
                value={ai.gemini_key} onChange={e => setAi({...ai, gemini_key: e.target.value})} />
              <p className="text-xs text-gray-400 mt-1">
                Get your key at <a href="https://aistudio.google.com" target="_blank" className="text-whatsapp-teal hover:underline">aistudio.google.com</a>
              </p>
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">AI System Prompt</label>
              <textarea className="input-field mt-1 min-h-24" value={ai.system_prompt}
                onChange={e => setAi({...ai, system_prompt: e.target.value})} />
            </div>
            <button onClick={() => save('ai', {gemini_api_key: ai.gemini_key, ai_system_prompt: ai.system_prompt, ai_enabled: ai.ai_enabled})}
              disabled={saving === 'ai'} className="btn-primary flex items-center gap-2">
              <Save size={14} /> {saving === 'ai' ? 'Saving...' : 'Save AI Settings'}
            </button>
          </div>
        </Section>
      </div>
    </div>
  )
}
