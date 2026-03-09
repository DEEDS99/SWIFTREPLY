import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './hooks/useAuthStore'

import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ConversationsPage from './pages/ConversationsPage'
import ContactsPage from './pages/ContactsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import TemplatesPage from './pages/TemplatesPage'
import SettingsPage from './pages/SettingsPage'
import BroadcastPage from './pages/BroadcastPage'
import TeamPage from './pages/TeamPage'
import AppLayout from './components/dashboard/AppLayout'

function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

function PublicRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

      <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="conversations" element={<ConversationsPage />} />
        <Route path="contacts" element={<ContactsPage />} />
        <Route path="broadcast" element={<BroadcastPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="team" element={<TeamPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
