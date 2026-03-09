import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import {
  Wifi, WifiOff, QrCode, Zap, MessageCircle, Users,
  TrendingUp, Activity, RefreshCw, CheckCircle, XCircle,
  Loader2, Radio, Eye, BarChart2, Circle
} from 'lucide-react'
import { analyticsApi } from '../../services/api'
import useAuthStore from '../../hooks/useAuthStore'
import api from '../../services/api'

// ── Live Status Dot ────────────────────────────────────────────────────────

function PulseDot({ color = 'green', size = 'sm' }) {
  const sz = size === 'lg' ? 'w-3 h-3' : 'w-2 h-2'
  const pulse = size === 'lg' ? 'w-3 h-3' : 'w-2 h-2'
  const colors = {
    green: 'bg-emerald-400',
    yellow: 'bg-amber-400',
    red: 'bg-red-400',
    gray: 'bg-gray-400',
  }
  return (
    <span className="relative flex items-center justify-center">
      <span className={`animate-ping absolute inline-flex ${pulse} rounded-full ${colors[color]} opacity-60`} />
      <span className={`relative inline-flex rounded-full ${sz} ${colors[color]}`} />
    </span>
  )
}

// ── Connection Status Card ─────────────────────────────────────────────────

function ConnectionCard({ status, onRefresh, onShowQR }) {
  const stateMap = {
    open: { label: 'Connected', color: 'green', icon: Wifi },
    connecting: { label: 'Connecting...', color: 'yellow', icon: Loader2 },
    close: { label: 'Disconnected', color: 'red', icon: WifiOff },
    qr: { label: 'Scan QR Code', color: 'yellow', icon: QrCode },
  }
  const s = stateMap[status] || stateMap.close
  const Icon = s.icon

  return (
    <div className={`relative overflow-hidden rounded-2xl p-5 border ${
      s.color === 'green' ? 'bg-emerald-950/40 border-emerald-500/30' :
      s.color === 'yellow' ? 'bg-amber-950/40 border-amber-500/30' :
      'bg-red-950/40 border-red-500/30'
    }`}>
      {/* Glow */}
      <div className={`absolute inset-0 opacity-10 ${
        s.color === 'green' ? 'bg-gradient-to-br from-emerald-400' :
        s.color === 'yellow' ? 'bg-gradient-to-br from-amber-400' :
        'bg-gradient-to-br from-red-400'
      }`} />

      <div className="relative flex items-center gap-3">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${
          s.color === 'green' ? 'bg-emerald-500/20' :
          s.color === 'yellow' ? 'bg-amber-500/20' :
          'bg-red-500/20'
        }`}>
          <Icon size={20} className={
            s.color === 'green' ? 'text-emerald-400' :
            s.color === 'yellow' ? `text-amber-400 ${status === 'connecting' ? 'animate-spin' : ''}` :
            'text-red-400'
          } />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <PulseDot color={s.color} />
            <span className={`text-sm font-semibold ${
              s.color === 'green' ? 'text-emerald-300' :
              s.color === 'yellow' ? 'text-amber-300' :
              'text-red-300'
            }`}>{s.label}</span>
          </div>
          <p className="text-xs text-white/40 mt-0.5">Evolution API · WhatsApp Web</p>
        </div>
        <div className="flex gap-2">
          {status !== 'open' && (
            <button
              onClick={onShowQR}
              className="text-xs px-2.5 py-1 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 transition-colors flex items-center gap-1"
            >
              <QrCode size={12} /> Pair
            </button>
          )}
          <button
            onClick={onRefresh}
            className="text-xs px-2.5 py-1 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 transition-colors"
          >
            <RefreshCw size={12} />
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Live Metric Card ───────────────────────────────────────────────────────

function LiveMetric({ label, value, delta, icon: Icon, accent, live }) {
  const [displayed, setDisplayed] = useState(value)
  const [flash, setFlash] = useState(false)

  useEffect(() => {
    if (value !== displayed) {
      setFlash(true)
      setDisplayed(value)
      setTimeout(() => setFlash(false), 600)
    }
  }, [value])

  return (
    <div className="relative overflow-hidden rounded-2xl bg-white/4 border border-white/8 p-5 hover:bg-white/6 transition-colors">
      <div className={`absolute inset-0 transition-opacity duration-500 ${flash ? 'opacity-100' : 'opacity-0'}`}
        style={{ background: `radial-gradient(circle at 50% 0%, ${accent}22 0%, transparent 70%)` }}
      />
      <div className="relative">
        <div className="flex items-center justify-between mb-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${accent}22` }}>
            <Icon size={17} style={{ color: accent }} />
          </div>
          {live && (
            <span className="flex items-center gap-1.5 text-xs" style={{ color: accent }}>
              <PulseDot color="green" /> LIVE
            </span>
          )}
        </div>
        <p className={`text-3xl font-bold text-white tabular-nums transition-all duration-300 ${flash ? 'scale-110' : 'scale-100'}`}
          style={{ fontFamily: "'DM Mono', monospace" }}>
          {displayed?.toLocaleString() ?? '—'}
        </p>
        <p className="text-xs text-white/40 mt-1 font-medium tracking-wide uppercase">{label}</p>
        {delta !== undefined && (
          <p className={`text-xs mt-1 font-medium ${delta >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {delta >= 0 ? '↑' : '↓'} {Math.abs(delta)} today
          </p>
        )}
      </div>
    </div>
  )
}

// ── Live Activity Feed ─────────────────────────────────────────────────────

function ActivityFeed({ events }) {
  const listRef = useRef(null)

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = 0
    }
  }, [events.length])

  const typeIcons = {
    text: '💬',
    image: '🖼️',
    audio: '🎵',
    video: '📹',
    document: '📄',
  }

  return (
    <div className="rounded-2xl bg-white/4 border border-white/8 overflow-hidden">
      <div className="px-5 py-4 border-b border-white/8 flex items-center gap-2">
        <Radio size={15} className="text-emerald-400" />
        <span className="text-sm font-semibold text-white/80">Live Activity</span>
        <PulseDot color="green" />
      </div>
      <div ref={listRef} className="h-64 overflow-y-auto">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-white/20 text-sm gap-2">
            <Activity size={24} />
            <span>Waiting for messages...</span>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {events.map((e, i) => (
              <div key={i} className={`px-5 py-3 flex items-center gap-3 ${i === 0 ? 'bg-emerald-500/5' : ''}`}>
                <span className="text-base">{typeIcons[e.message_type] || '💬'}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-white/80 truncate">{e.contact_name || e.contact_phone}</span>
                    {e.ai_replied && (
                      <span className="text-xs px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 flex items-center gap-1 shrink-0">
                        <Zap size={9} /> AI
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-white/40 truncate mt-0.5">
                    {e.body || `[${e.message_type}]`}
                  </p>
                </div>
                <span className="text-xs text-white/25 shrink-0 tabular-nums">{e.time}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── QR Code Modal ──────────────────────────────────────────────────────────

function QRModal({ instanceName, onClose }) {
  const [qrData, setQrData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetch = async () => {
      try {
        const r = await api.get(`/evolution/qr/${instanceName}`)
        setQrData(r.data)
      } catch {
        setError('Could not fetch QR code. Check Evolution API connection.')
      } finally {
        setLoading(false)
      }
    }
    fetch()
    const interval = setInterval(fetch, 20_000) // refresh QR every 20s
    return () => clearInterval(interval)
  }, [instanceName])

  const qrBase64 = qrData?.base64 || qrData?.qrcode?.base64 || ''

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0d1117] border border-white/10 rounded-3xl p-8 w-full max-w-sm text-center shadow-2xl">
        <div className="flex items-center justify-center gap-2 mb-2">
          <QrCode size={18} className="text-emerald-400" />
          <h3 className="text-white font-semibold">Scan to Connect</h3>
        </div>
        <p className="text-white/40 text-xs mb-6">Open WhatsApp → Linked Devices → Link a Device</p>

        {loading ? (
          <div className="w-48 h-48 mx-auto rounded-2xl bg-white/5 flex items-center justify-center">
            <Loader2 size={32} className="text-emerald-400 animate-spin" />
          </div>
        ) : error ? (
          <div className="w-48 h-48 mx-auto rounded-2xl bg-red-500/10 flex flex-col items-center justify-center gap-2">
            <XCircle size={24} className="text-red-400" />
            <p className="text-red-300 text-xs px-3">{error}</p>
          </div>
        ) : qrBase64 ? (
          <div className="w-48 h-48 mx-auto rounded-2xl bg-white p-2">
            <img
              src={qrBase64.startsWith('data:') ? qrBase64 : `data:image/png;base64,${qrBase64}`}
              alt="WhatsApp QR Code"
              className="w-full h-full object-contain"
            />
          </div>
        ) : (
          <div className="w-48 h-48 mx-auto rounded-2xl bg-white/5 flex items-center justify-center">
            <p className="text-white/30 text-xs">No QR available</p>
          </div>
        )}

        <p className="text-white/25 text-xs mt-4">Auto-refreshes every 20 seconds</p>
        <button onClick={onClose} className="mt-4 w-full py-2 rounded-xl bg-white/10 text-white/60 hover:bg-white/20 transition-colors text-sm">
          Close
        </button>
      </div>
    </div>
  )
}

// ── Mini Bar Chart ─────────────────────────────────────────────────────────

function MiniBar({ inbound, outbound }) {
  const total = Math.max(inbound + outbound, 1)
  return (
    <div className="rounded-2xl bg-white/4 border border-white/8 p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-semibold text-white/80">This Week</span>
        <BarChart2 size={15} className="text-white/30" />
      </div>
      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-white/40">Inbound</span>
            <span className="text-emerald-400 font-mono">{inbound}</span>
          </div>
          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full transition-all duration-700"
              style={{ width: `${(inbound / total) * 100}%` }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-white/40">Outbound</span>
            <span className="text-blue-400 font-mono">{outbound}</span>
          </div>
          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-700"
              style={{ width: `${(outbound / total) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main Live GUI ──────────────────────────────────────────────────────────

export default function LiveDashboard() {
  const { user } = useAuthStore()
  const [connectionState, setConnectionState] = useState('connecting')
  const [liveEvents, setLiveEvents] = useState([])
  const [showQR, setShowQR] = useState(false)
  const instanceName = user?.evolution_instance || os.getenv?.('EVOLUTION_INSTANCE') || 'swiftreply'
  const qc = useQueryClient()

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: analyticsApi.summary,
    refetchInterval: 15_000,
  })

  // Poll Evolution connection state
  const checkConnection = useCallback(async () => {
    try {
      const r = await api.get(`/evolution/status/${instanceName}`)
      const state = r.data?.instance?.state || r.data?.state || 'close'
      setConnectionState(state.toLowerCase())
    } catch {
      setConnectionState('close')
    }
  }, [instanceName])

  useEffect(() => {
    checkConnection()
    const interval = setInterval(checkConnection, 10_000)
    return () => clearInterval(interval)
  }, [checkConnection])

  // WebSocket for live events
  useEffect(() => {
    if (!user?.organisation_id) return
    const wsUrl = `${(import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws')}/${user.organisation_id}`
    let ws
    let retryTimer

    const connect = () => {
      ws = new WebSocket(wsUrl)
      ws.onmessage = (e) => {
        if (e.data === 'pong') return
        try {
          const data = JSON.parse(e.data)
          if (data.type === 'new_message') {
            const event = {
              ...data,
              time: new Date().toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' }),
            }
            setLiveEvents((prev) => [event, ...prev].slice(0, 50))
            qc.invalidateQueries({ queryKey: ['conversations'] })
            qc.invalidateQueries({ queryKey: ['analytics-summary'] })
          }
          if (data.type === 'connection_update') {
            setConnectionState(data.state?.toLowerCase() || 'close')
            if (data.qr) setShowQR(true)
          }
        } catch {}
      }
      ws.onclose = () => {
        retryTimer = setTimeout(connect, 3000)
      }
      ws.onerror = () => ws.close()
      const ping = setInterval(() => ws.readyState === 1 && ws.send('ping'), 30_000)
      ws._pingInterval = ping
    }

    connect()
    return () => {
      clearTimeout(retryTimer)
      if (ws._pingInterval) clearInterval(ws._pingInterval)
      ws?.close()
    }
  }, [user?.organisation_id])

  const aiRate = stats
    ? Math.round(((stats.ai_messages_month || 0) / Math.max(stats.outbound_week || 1, 1)) * 100)
    : 0

  return (
    <div className="h-full overflow-y-auto bg-[#080c10] text-white">
      {/* Google Font for mono numbers */}
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
      * { font-family: 'DM Sans', sans-serif; }`}</style>

      <div className="max-w-5xl mx-auto p-6 space-y-5">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <Zap size={14} className="text-emerald-400" />
              </span>
              Live Dashboard
            </h1>
            <p className="text-xs text-white/30 mt-0.5">{user?.organisation_name} · Evolution API</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-white/30">
            <Circle size={6} className="text-emerald-400 fill-emerald-400 animate-pulse" />
            Real-time
          </div>
        </div>

        {/* Connection */}
        <ConnectionCard
          status={connectionState}
          onRefresh={checkConnection}
          onShowQR={() => setShowQR(true)}
        />

        {/* Key Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <LiveMetric
            label="Open Conversations"
            value={stats?.open_conversations}
            icon={MessageCircle}
            accent="#22d3ee"
            live
          />
          <LiveMetric
            label="Messages Today"
            value={stats?.messages_today}
            icon={Activity}
            accent="#a78bfa"
            live
          />
          <LiveMetric
            label="Contacts"
            value={stats?.total_contacts}
            icon={Users}
            accent="#fb923c"
          />
          <LiveMetric
            label="AI Rate"
            value={aiRate}
            icon={Zap}
            accent="#4ade80"
          />
        </div>

        {/* Live feed + bar chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <ActivityFeed events={liveEvents} />
          </div>
          <div>
            <MiniBar
              inbound={stats?.inbound_week || 0}
              outbound={stats?.outbound_week || 0}
            />
          </div>
        </div>

        {/* Evolution instance info */}
        <div className="rounded-2xl bg-white/4 border border-white/8 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Eye size={15} className="text-white/40" />
            <span className="text-sm font-semibold text-white/80">Evolution API Instance</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-white/4 rounded-xl">
              <p className="text-white/30 mb-1">Instance Name</p>
              <p className="text-white/80 font-mono">{instanceName}</p>
            </div>
            <div className="p-3 bg-white/4 rounded-xl">
              <p className="text-white/30 mb-1">Protocol</p>
              <p className="text-emerald-400 font-medium">WhatsApp Web (ToS ✓)</p>
            </div>
            <div className="p-3 bg-white/4 rounded-xl">
              <p className="text-white/30 mb-1">AI Engine</p>
              <p className="text-purple-300 font-medium">Gemini 1.5 Pro</p>
            </div>
            <div className="p-3 bg-white/4 rounded-xl">
              <p className="text-white/30 mb-1">Webhook</p>
              <p className="text-white/60 font-mono truncate">/api/evolution/webhook</p>
            </div>
          </div>
        </div>

      </div>

      {/* QR Modal */}
      {showQR && (
        <QRModal instanceName={instanceName} onClose={() => setShowQR(false)} />
      )}
    </div>
  )
}
