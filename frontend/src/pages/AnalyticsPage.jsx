import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../services/api'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts'
import { MessageCircle, Users, Zap, TrendingUp, ArrowDown, ArrowUp } from 'lucide-react'

function StatCard({ title, value, icon: Icon, color, sub }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
          <Icon size={18} className="text-white" />
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value?.toLocaleString() || '0'}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

const COLORS = ['#128C7E', '#25D366', '#075E54', '#a78bfa']

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: analyticsApi.summary,
    refetchInterval: 30_000,
  })

  const pieData = data ? [
    { name: 'Inbound', value: data.inbound_week },
    { name: 'Outbound', value: data.outbound_week },
  ] : []

  const barData = [
    { name: 'Conversations', total: data?.total_conversations || 0, open: data?.open_conversations || 0 },
  ]

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-xl font-bold text-gray-900 mb-6">Analytics</h1>

        {isLoading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card p-5 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-2/3 mb-3" />
                <div className="h-7 bg-gray-200 rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard title="Total Conversations" value={data?.total_conversations} icon={MessageCircle} color="bg-whatsapp-teal" sub="All time" />
            <StatCard title="Open Now" value={data?.open_conversations} icon={TrendingUp} color="bg-green-500" sub="Needs attention" />
            <StatCard title="Total Contacts" value={data?.total_contacts} icon={Users} color="bg-blue-500" sub="In your database" />
            <StatCard title="AI Messages (Month)" value={data?.ai_messages_month} icon={Zap} color="bg-purple-500" sub="Auto-replied by Gemini" />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Messages this week */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-800 mb-4">Messages This Week</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-around mt-2 text-center">
              <div>
                <p className="text-2xl font-bold text-whatsapp-teal">{data?.inbound_week || 0}</p>
                <p className="text-xs text-gray-500 flex items-center gap-1 justify-center"><ArrowDown size={12} /> Inbound</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-500">{data?.outbound_week || 0}</p>
                <p className="text-xs text-gray-500 flex items-center gap-1 justify-center"><ArrowUp size={12} /> Outbound</p>
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-800 mb-4">Today's Activity</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <span className="text-sm text-gray-700">Messages Today</span>
                <span className="font-bold text-lg text-whatsapp-teal">{data?.messages_today || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <span className="text-sm text-gray-700">AI Auto-Replies (Month)</span>
                <span className="font-bold text-lg text-purple-600">{data?.ai_messages_month || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <span className="text-sm text-gray-700">Open Conversations</span>
                <span className="font-bold text-lg text-blue-600">{data?.open_conversations || 0}</span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">
                  AI Automation Rate:{' '}
                  <span className="font-bold text-gray-700">
                    {data ? Math.round(((data.ai_messages_month || 0) / Math.max((data.outbound_week || 1), 1)) * 100) : 0}%
                  </span>
                  {' '}of outbound messages this week
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
