import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Search, Send, Image, Mic, Video, FileText,
  CheckCheck, Check, Clock, Phone, MoreVertical,
  Sparkles, RefreshCw, ChevronDown, Archive
} from 'lucide-react'
import { conversationsApi, messagesApi, aiApi } from '../services/api'
import { formatDistanceToNow, format } from 'date-fns'
import toast from 'react-hot-toast'
import { useQueryClient as useQC } from '@tanstack/react-query'

function StatusIcon({ status }) {
  if (status === 'read') return <CheckCheck size={14} className="text-blue-400" />
  if (status === 'delivered') return <CheckCheck size={14} className="text-gray-400" />
  if (status === 'sent') return <Check size={14} className="text-gray-400" />
  return <Clock size={14} className="text-gray-300" />
}

function MediaIcon({ type }) {
  if (type === 'image') return <Image size={14} className="text-gray-400" />
  if (type === 'audio') return <Mic size={14} className="text-gray-400" />
  if (type === 'video') return <Video size={14} className="text-gray-400" />
  if (type === 'document') return <FileText size={14} className="text-gray-400" />
  return null
}

export default function ConversationsPage() {
  const [selectedId, setSelectedId] = useState(null)
  const [search, setSearch] = useState('')
  const [messageText, setMessageText] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const bottomRef = useRef(null)
  const qc = useQueryClient()

  const { data: convsData, isLoading } = useQuery({
    queryKey: ['conversations', statusFilter],
    queryFn: () => conversationsApi.list({ status: statusFilter || undefined }),
    refetchInterval: 10_000,
  })

  const { data: msgsData } = useQuery({
    queryKey: ['messages', selectedId],
    queryFn: () => conversationsApi.getMessages(selectedId),
    enabled: !!selectedId,
    refetchInterval: 5_000,
  })

  const sendMutation = useMutation({
    mutationFn: messagesApi.send,
    onSuccess: () => {
      setMessageText('')
      qc.invalidateQueries({ queryKey: ['messages', selectedId] })
      qc.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: () => toast.error('Failed to send message'),
  })

  const aiMutation = useMutation({
    mutationFn: aiApi.generateReply,
    onSuccess: (data) => {
      if (data.suggested_reply) setMessageText(data.suggested_reply)
      else toast.error('Could not generate reply')
    },
  })

  const resolveMutation = useMutation({
    mutationFn: ({ id, status }) => conversationsApi.updateStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversations'] }),
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [msgsData])

  const conversations = convsData?.conversations || []
  const messages = msgsData?.messages || []
  const filtered = conversations.filter((c) => {
    if (!search) return true
    const name = c.contact?.name?.toLowerCase() || ''
    const phone = c.contact?.phone?.toLowerCase() || ''
    return name.includes(search.toLowerCase()) || phone.includes(search.toLowerCase())
  })

  const selectedConv = conversations.find((c) => c.id === selectedId)

  const handleSend = (e) => {
    e.preventDefault()
    if (!messageText.trim() || !selectedId) return
    sendMutation.mutate({
      conversation_id: selectedId,
      message_type: 'text',
      body: messageText.trim(),
    })
  }

  const handleAiSuggest = () => {
    if (!selectedId) return
    aiMutation.mutate({ conversation_id: selectedId })
  }

  return (
    <div className="flex h-full bg-white">
      {/* Conversation list */}
      <div className={`w-full md:w-80 lg:w-96 border-r border-gray-200 flex flex-col ${selectedId ? 'hidden md:flex' : 'flex'}`}>
        {/* Header */}
        <div className="p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900 mb-3">Conversations</h2>
          <div className="relative mb-3">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-whatsapp-teal"
              placeholder="Search contacts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-1">
            {['', 'open', 'pending', 'resolved'].map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-2.5 py-1 text-xs rounded-full font-medium transition-colors ${
                  statusFilter === s
                    ? 'bg-whatsapp-teal text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {s || 'All'}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="flex gap-3 animate-pulse">
                  <div className="w-10 h-10 bg-gray-200 rounded-full shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 bg-gray-200 rounded w-3/4" />
                    <div className="h-3 bg-gray-200 rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-sm">
              No conversations found
            </div>
          ) : (
            filtered.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setSelectedId(conv.id)}
                className={`w-full p-4 flex items-start gap-3 hover:bg-gray-50 border-b border-gray-50 transition-colors ${
                  selectedId === conv.id ? 'bg-green-50 border-l-2 border-l-whatsapp-teal' : ''
                }`}
              >
                {/* Avatar */}
                <div className="w-10 h-10 rounded-full bg-whatsapp-teal flex items-center justify-center text-white font-medium text-sm shrink-0">
                  {(conv.contact?.name || '?')[0].toUpperCase()}
                </div>

                <div className="flex-1 min-w-0 text-left">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm text-gray-900 truncate">
                      {conv.contact?.name || conv.contact?.phone}
                    </span>
                    <span className="text-xs text-gray-400 shrink-0 ml-2">
                      {conv.last_message_at
                        ? formatDistanceToNow(new Date(conv.last_message_at), { addSuffix: false })
                        : ''}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 mt-0.5">
                    {conv.last_message?.direction === 'outbound' && <StatusIcon status={conv.last_message?.status} />}
                    {conv.last_message?.type !== 'text' && <MediaIcon type={conv.last_message?.type} />}
                    <span className="text-xs text-gray-500 truncate">
                      {conv.last_message?.body || 'No messages yet'}
                    </span>
                  </div>
                </div>

                {conv.unread_count > 0 && (
                  <span className="w-5 h-5 bg-whatsapp-green rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0">
                    {conv.unread_count}
                  </span>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Chat panel */}
      <div className={`flex-1 flex flex-col ${!selectedId ? 'hidden md:flex' : 'flex'}`}>
        {!selectedId ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <MessageIcon />
              </div>
              <p className="font-medium">Select a conversation</p>
              <p className="text-sm mt-1">Choose a conversation to start messaging</p>
            </div>
          </div>
        ) : (
          <>
            {/* Chat header */}
            <div className="px-4 py-3 border-b border-gray-200 bg-white flex items-center gap-3">
              <button className="md:hidden text-gray-600" onClick={() => setSelectedId(null)}>←</button>
              <div className="w-9 h-9 rounded-full bg-whatsapp-teal flex items-center justify-center text-white font-medium text-sm">
                {(selectedConv?.contact?.name || '?')[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-gray-900">{selectedConv?.contact?.name}</p>
                <p className="text-xs text-gray-500">{selectedConv?.contact?.phone}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                  selectedConv?.status === 'open' ? 'bg-green-100 text-green-700' :
                  selectedConv?.status === 'resolved' ? 'bg-gray-100 text-gray-600' :
                  'bg-yellow-100 text-yellow-700'
                }`}>
                  {selectedConv?.status}
                </span>
                <button
                  onClick={() => resolveMutation.mutate({
                    id: selectedId,
                    status: selectedConv?.status === 'resolved' ? 'open' : 'resolved'
                  })}
                  className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                >
                  {selectedConv?.status === 'resolved' ? <RefreshCw size={14} /> : <Archive size={14} />}
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-whatsapp-bg">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={msg.direction === 'outbound' ? 'message-bubble-out' : 'message-bubble-in'}>
                    {/* Media preview */}
                    {msg.media_url && msg.type === 'image' && (
                      <img src={msg.media_url} alt="media" className="rounded-lg max-w-xs mb-2" />
                    )}
                    {msg.media_url && msg.type === 'audio' && (
                      <audio controls src={msg.media_url} className="w-48 mb-2" />
                    )}
                    {msg.media_url && msg.type === 'video' && (
                      <video controls src={msg.media_url} className="rounded-lg max-w-xs mb-2" />
                    )}

                    {msg.body && <p className="text-sm text-gray-800 leading-relaxed">{msg.body}</p>}

                    {msg.ai_generated && (
                      <div className="flex items-center gap-1 mt-1">
                        <Sparkles size={10} className="text-purple-400" />
                        <span className="text-xs text-purple-400">AI</span>
                      </div>
                    )}

                    <div className="flex items-center justify-end gap-1 mt-1">
                      <span className="text-xs text-gray-400">
                        {format(new Date(msg.created_at), 'HH:mm')}
                      </span>
                      {msg.direction === 'outbound' && <StatusIcon status={msg.status} />}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="p-3 bg-white border-t border-gray-200">
              {/* AI suggest button */}
              <div className="flex items-center gap-2 mb-2">
                <button
                  onClick={handleAiSuggest}
                  disabled={aiMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-1 text-xs bg-purple-50 text-purple-600 rounded-full hover:bg-purple-100 transition-colors font-medium"
                >
                  <Sparkles size={12} />
                  {aiMutation.isPending ? 'Generating...' : 'AI Suggest Reply'}
                </button>
              </div>

              <form onSubmit={handleSend} className="flex items-end gap-2">
                <textarea
                  className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-whatsapp-teal min-h-[40px] max-h-32"
                  placeholder="Type a message..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  rows={1}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSend(e)
                    }
                  }}
                />
                <button
                  type="submit"
                  disabled={!messageText.trim() || sendMutation.isPending}
                  className="w-10 h-10 rounded-xl bg-whatsapp-teal text-white flex items-center justify-center hover:bg-whatsapp-dark transition-colors disabled:opacity-50 shrink-0"
                >
                  <Send size={16} />
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function MessageIcon() {
  return (
    <svg width="28" height="28" fill="none" viewBox="0 0 24 24">
      <path d="M20 2H4a2 2 0 00-2 2v18l4-4h14a2 2 0 002-2V4a2 2 0 00-2-2z" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}
