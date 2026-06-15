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

describe('settings API', () => {
  let request: any

  beforeAll(async () => {
    const mod = await import('../network/request')
    request = mod.default
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getProvidersApi', () => {
    it('应发送 GET /user/llm-providers', async () => {
      const { getProvidersApi } = await import('./settings')
      const mockProviders = [
        { id: '1', name: 'DeepSeek', provider: 'deepseek', base_url: 'https://api.deepseek.com', api_key_masked: 'sk-xxx', default_model: 'deepseek-chat', enabled: true, user_id: null },
      ]
      const resp = { code: 0, msg: 'ok', data: mockProviders }
      request.get.mockResolvedValue(resp)
      const result = await getProvidersApi()
      expect(request.get).toHaveBeenCalledWith('/user/llm-providers')
      expect(result.data[0].name).toBe('DeepSeek')
    })
  })

  describe('createProviderApi', () => {
    it('应发送 POST /user/llm-providers', async () => {
      const { createProviderApi } = await import('./settings')
      const payload = { name: 'Qwen', provider: 'qwen', base_url: 'https://dashscope.aliyuncs.com', api_key: 'sk-yyy', default_model: 'qwen-plus', enabled: true }
      const resp = { code: 0, msg: 'ok', data: { id: '2', name: 'Qwen', provider: 'qwen', base_url: 'https://dashscope.aliyuncs.com', api_key_masked: 'sk-yyy', default_model: 'qwen-plus', enabled: true, user_id: null as string | null } }
      request.post.mockResolvedValue(resp)
      const result = await createProviderApi(payload)
      expect(request.post).toHaveBeenCalledWith('/user/llm-providers', payload)
      expect(result.data.name).toBe('Qwen')
    })
  })

  describe('updateProviderApi', () => {
    it('应发送 PATCH /user/llm-providers/{id}', async () => {
      const { updateProviderApi } = await import('./settings')
      request.patch.mockResolvedValue({ code: 0, msg: 'ok', data: { id: '1' } })
      await updateProviderApi('1', { enabled: false })
      expect(request.patch).toHaveBeenCalledWith('/user/llm-providers/1', { enabled: false })
    })
  })

  describe('deleteProviderApi', () => {
    it('应发送 DELETE /user/llm-providers/{id}', async () => {
      const { deleteProviderApi } = await import('./settings')
      request.delete.mockResolvedValue({ code: 0, msg: 'ok', data: null })
      await deleteProviderApi('1')
      expect(request.delete).toHaveBeenCalledWith('/user/llm-providers/1')
    })
  })
})
