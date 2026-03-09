import { useEffect, useRef, useCallback } from 'react'
import useAuthStore from './useAuthStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

export function useWebSocket(onMessage) {
  const ws = useRef(null)
  const user = useAuthStore((s) => s.user)
  const pingInterval = useRef(null)

  const connect = useCallback(() => {
    if (!user?.organisation_id) return
    if (ws.current?.readyState === WebSocket.OPEN) return

    const url = `${WS_URL}/${user.organisation_id}`
    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      console.log('WS connected')
      pingInterval.current = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send('ping')
        }
      }, 30_000)
    }

    ws.current.onmessage = (event) => {
      if (event.data === 'pong') return
      try {
        const data = JSON.parse(event.data)
        onMessage?.(data)
      } catch (e) {}
    }

    ws.current.onclose = () => {
      clearInterval(pingInterval.current)
      // Reconnect after 3s
      setTimeout(connect, 3000)
    }

    ws.current.onerror = () => {
      ws.current?.close()
    }
  }, [user?.organisation_id, onMessage])

  useEffect(() => {
    connect()
    return () => {
      clearInterval(pingInterval.current)
      ws.current?.close()
    }
  }, [connect])
}
