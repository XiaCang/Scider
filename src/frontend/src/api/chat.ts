import { authStorage } from '../utils/auth_storage'

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || import.meta.env.VITE_API_BASE_URL?.replace(/^http/, 'ws') || 'ws://39.107.252.200:8000/api'

export interface ChatEventCallbacks {
  onToken: (token: string) => void
  onDone: (fullContent: string, sources: any[]) => void
  onError: (error: string) => void
  onStatus?: (status: string, data?: any) => void
}

/**
 * 创建 WebSocket AI 聊天连接
 * 返回控制对象：send / close / connected
 */
export function createChatConnection(paperId: string, callbacks: ChatEventCallbacks) {
  const token = authStorage.getToken()
  if (!token) {
    callbacks.onError('未登录，请重新登录')
    return { send: () => {}, clear: () => {}, close: () => {}, connected: false }
  }

  const url = `${WS_BASE}/ws/chat?token=${encodeURIComponent(token)}&paper_id=${encodeURIComponent(paperId)}`
  let ws: WebSocket | null = null
  let reconnecting = false
  let closed = false

  function connect() {
    if (closed) return
    try {
      ws = new WebSocket(url)
    } catch (e: any) {
      callbacks.onError(`WebSocket 连接失败: ${e.message}`)
      return
    }

    ws.onopen = () => {
      reconnecting = false
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        switch (msg.type) {
          case 'token':
            callbacks.onToken(msg.content)
            break
          case 'done':
            callbacks.onDone(msg.content, msg.sources || [])
            break
          case 'error':
            callbacks.onError(msg.content)
            break
          case 'status':
            callbacks.onStatus?.(msg.content, msg.data)
            break
        }
      } catch {
        // ignore non-JSON messages
      }
    }

    ws.onclose = () => {
      if (!closed && !reconnecting) {
        reconnecting = true
        setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      // onclose 会接着触发，所以只在这里记录
      if (!reconnecting) {
        callbacks.onError('连接异常，正在重连...')
      }
    }
  }

  connect()

  return {
    send(question: string) {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'question',
          paper_id: paperId,
          content: question,
        }))
      } else {
        callbacks.onError('连接未就绪，请稍后重试')
      }
    },
    clear() {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'clear' }))
      }
    },
    close() {
      closed = true
      ws?.close()
      ws = null
    },
    get connected() {
      return ws?.readyState === WebSocket.OPEN
    },
  }
}
