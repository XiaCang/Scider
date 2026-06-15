import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'

vi.mock('../network/request', () => {
  const mockAxios = {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  }
  return { default: mockAxios }
})

describe('tasks API', () => {
  let request: any

  beforeAll(async () => {
    const mod = await import('../network/request')
    request = mod.default
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchTaskResultApi', () => {
    it('应发送 GET /tasks/{task_id}', async () => {
      const { fetchTaskResultApi } = await import('./tasks')
      const resp = { code: 0, msg: 'ok', data: { status: 'SUCCESS', result: {} } }
      request.get.mockResolvedValue(resp)
      const result = await fetchTaskResultApi('task-1')
      expect(request.get).toHaveBeenCalledWith('/tasks/task-1')
      expect(result.code).toBe(0)
    })
  })

  describe('pingTaskApi', () => {
    it('应发送 POST /tasks/ping', async () => {
      const { pingTaskApi } = await import('./tasks')
      const resp = { code: 0, msg: 'ok', data: { pong: true } }
      request.post.mockResolvedValue(resp)
      const result = await pingTaskApi()
      expect(request.post).toHaveBeenCalledWith('/tasks/ping')
      expect(result.code).toBe(0)
    })
  })
})
