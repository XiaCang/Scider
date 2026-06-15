import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const mockGetToken = vi.fn(() => 'mock-token')

vi.mock('../utils/auth_storage', () => ({
  authStorage: { getToken: mockGetToken },
}))

/** 创建一个真实类来模拟 WebSocket */
function createMockWsClass() {
  const instances: any[] = []

  class MockWebSocket {
    static OPEN = 1
    static CONNECTING = 0
    static CLOSING = 2
    static CLOSED = 3

    readyState = MockWebSocket.OPEN
    onmessage: any = null
    onopen: any = null
    onclose: any = null
    onerror: any = null
    send = vi.fn()
    close = vi.fn()

    constructor(_url: string) {
      instances.push(this)
    }
  }

  globalThis.WebSocket = MockWebSocket as any
  return {
    getInstance: (index = 0) => instances[index],
  }
}

describe('createChatConnection', () => {
  let originalWebSocket: any

  beforeEach(() => {
    originalWebSocket = globalThis.WebSocket
    mockGetToken.mockReturnValue('mock-token')
  })

  afterEach(() => {
    globalThis.WebSocket = originalWebSocket
  })

  it('无 token 时应返回错误并返回空控制器', async () => {
    mockGetToken.mockReturnValue('')
    const { createChatConnection } = await import('./chat')
    const onError = vi.fn()
    const ctrl = createChatConnection('p-1', {
      onToken: vi.fn(),
      onDone: vi.fn(),
      onError,
    })

    expect(onError).toHaveBeenCalledWith('未登录，请重新登录')
    expect(ctrl.connected).toBe(false)
    expect(() => ctrl.send('hello')).not.toThrow()
    expect(() => ctrl.clear()).not.toThrow()
    expect(() => ctrl.close()).not.toThrow()
  })

  it('应创建 WebSocket 连接并返回控制对象', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const callbacks = { onToken: vi.fn(), onDone: vi.fn(), onError: vi.fn() }
    createChatConnection('p-1', callbacks)

    const ws = getInstance()
    // 实例被创建说明构造函数被调用了
    expect(ws).toBeDefined()
  })

  it('WebSocket URL 应包含必要参数', async () => {
    let capturedUrl = ''
    class UrlCatcher {
      static OPEN = 1; static CONNECTING = 0; static CLOSING = 2; static CLOSED = 3
      readyState = 1; send = vi.fn(); close = vi.fn(); onmessage: any = null; onopen: any = null; onclose: any = null; onerror: any = null
      constructor(url: string) { capturedUrl = url }
    }
    globalThis.WebSocket = UrlCatcher as any

    const { createChatConnection } = await import('./chat')
    createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError: vi.fn() })

    expect(capturedUrl).toContain('/ws/chat')
    expect(capturedUrl).toContain('paper_id=p-1')
    expect(capturedUrl).toContain('token=mock-token')
  })

  it('onmessage 应解析 JSON 并分发 token 事件', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const onToken = vi.fn()
    createChatConnection('p-1', { onToken, onDone: vi.fn(), onError: vi.fn() })

    const ws = getInstance()
    ws.onmessage({ data: JSON.stringify({ type: 'token', content: 'Hello' }) })
    expect(onToken).toHaveBeenCalledWith('Hello')
  })

  it('onmessage 应分发 done 事件', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const onDone = vi.fn()
    createChatConnection('p-1', { onToken: vi.fn(), onDone, onError: vi.fn() })

    const ws = getInstance()
    ws.onmessage({ data: JSON.stringify({ type: 'done', content: '全文总结', sources: [{ title: 'ref1' }] }) })
    expect(onDone).toHaveBeenCalledWith('全文总结', [{ title: 'ref1' }])
  })

  it('onmessage 应分发 error 事件', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const onError = vi.fn()
    createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError })

    const ws = getInstance()
    ws.onmessage({ data: JSON.stringify({ type: 'error', content: 'API 调用失败' }) })
    expect(onError).toHaveBeenCalledWith('API 调用失败')
  })

  it('onmessage 应分发 status 事件', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const onStatus = vi.fn()
    createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError: vi.fn(), onStatus })

    const ws = getInstance()
    ws.onmessage({ data: JSON.stringify({ type: 'status', content: 'processing', data: { progress: 50 } }) })
    expect(onStatus).toHaveBeenCalledWith('processing', { progress: 50 })
  })

  it('non-JSON 消息应被忽略', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError: vi.fn() })

    const ws = getInstance()
    expect(() => ws.onmessage({ data: 'not json' })).not.toThrow()
  })

  it('send 方法应在连接就绪时发送消息', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const ctrl = createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError: vi.fn() })

    const ws = getInstance()
    ctrl.send('What is this paper about?')
    expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
      type: 'question',
      paper_id: 'p-1',
      content: 'What is this paper about?',
    }))
  })

  it('send 方法在连接未就绪时应报错', async () => {
    class ConnectingWs {
      static OPEN = 1; static CONNECTING = 0; static CLOSING = 2; static CLOSED = 3
      readyState = 0; send = vi.fn(); close = vi.fn(); onmessage: any = null; onopen: any = null; onclose: any = null; onerror: any = null
    }
    globalThis.WebSocket = ConnectingWs as any

    const { createChatConnection } = await import('./chat')
    const onError = vi.fn()
    const ctrl = createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError })
    ctrl.send('hello')
    expect(onError).toHaveBeenCalledWith('连接未就绪，请稍后重试')
  })

  it('clear 方法应发送 clear 消息', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const ctrl = createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError: vi.fn() })

    const ws = getInstance()
    ctrl.clear()
    expect(ws.send).toHaveBeenCalledWith(JSON.stringify({ type: 'clear' }))
  })

  it('close 方法应关闭连接', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const ctrl = createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError: vi.fn() })

    const ws = getInstance()
    ctrl.close()
    expect(ws.close).toHaveBeenCalled()
  })

  it('connected getter 应反映 WebSocket 状态', async () => {
    const { getInstance } = createMockWsClass()
    const { createChatConnection } = await import('./chat')
    const ctrl = createChatConnection('p-1', { onToken: vi.fn(), onDone: vi.fn(), onError: vi.fn() })

    getInstance()
    expect(ctrl.connected).toBe(true)
  })
})
