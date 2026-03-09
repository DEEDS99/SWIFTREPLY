import React, { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  Activity, MessageCircle, Users, BarChart3, FileText,
  Settings, LogOut, Menu, X, Zap, Megaphone, UserCheck
} from 'lucide-react'
import useAuthStore from '../../hooks/useAuthStore'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

const nav = [
  { to: '/dashboard',      icon: Activity,     label: 'Live Dashboard', live: true },
  { to: '/conversations',  icon: MessageCircle, label: 'Conversations' },
  { to: '/contacts',       icon: Users,         label: 'Contacts' },
  { to: '/broadcast',      icon: Megaphone,     label: 'Broadcast' },
  { to: '/analytics',      icon: BarChart3,     label: 'Analytics' },
  { to: '/templates',      icon: FileText,      label: 'Templates' },
  { to: '/team',           icon: UserCheck,     label: 'Team' },
  { to: '/settings',       icon: Settings,      label: 'Settings' },
]

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-30 w-60 bg-whatsapp-dark text-white flex flex-col
        transform transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/10">
          <div className="w-8 h-8 bg-whatsapp-green rounded-lg flex items-center justify-center shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="font-bold text-sm">SwiftReply</h1>
            <p className="text-xs text-white/50 truncate">{user?.organisation_name}</p>
          </div>
          <button className="ml-auto lg:hidden" onClick={() => setSidebarOpen(false)}>
            <X size={16} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label, live }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-white/15 text-white'
                    : 'text-white/65 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <Icon size={17} />
              <span className="flex-1">{label}</span>
              {live && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="p-2 border-t border-white/10">
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg">
            <div className="w-7 h-7 bg-whatsapp-green rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0">
              {user?.full_name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-white/50 capitalize">{user?.role}</p>
            </div>
            <button onClick={handleLogout} className="text-white/40 hover:text-white transition-colors" title="Logout">
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile header */}
        <header className="lg:hidden bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
          <button onClick={() => setSidebarOpen(true)}>
            <Menu size={20} />
          </button>
          <span className="font-semibold text-whatsapp-dark">SwiftReply</span>
        </header>
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
