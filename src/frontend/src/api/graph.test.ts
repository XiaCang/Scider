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

describe('graph API', () => {
  let request: any

  beforeAll(async () => {
    const mod = await import('../network/request')
    request = mod.default
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchSimilarityGraphApi', () => {
    it('应发送 GET /graph/similarity', async () => {
      const { fetchSimilarityGraphApi } = await import('./graph')
      const mockData = { nodes: [] as any[], links: [] as any[], meta: {} }
      const resp = { code: 0, msg: 'ok', data: mockData }
      request.get.mockResolvedValue(resp)
      const result = await fetchSimilarityGraphApi()
      expect(request.get).toHaveBeenCalledWith('/graph/similarity', { params: undefined })
      expect(result.code).toBe(0)
    })

    it('应传递筛选参数', async () => {
      const { fetchSimilarityGraphApi } = await import('./graph')
      const resp = { code: 0, msg: 'ok', data: { nodes: [] as any[], links: [] as any[], meta: {} } }
      request.get.mockResolvedValue(resp)
      await fetchSimilarityGraphApi({ folder_id: 'f-1', max_nodes: 50, min_similarity: 0.5, top_k: 10 })
      expect(request.get).toHaveBeenCalledWith('/graph/similarity', {
        params: { folder_id: 'f-1', max_nodes: 50, min_similarity: 0.5, top_k: 10 },
      })
    })
  })

  describe('fetchLLMGraphApi', () => {
    it('应发送 GET /graph/llm-structure', async () => {
      const { fetchLLMGraphApi } = await import('./graph')
      const mockData = { nodes: [] as any[], links: [] as any[], clusters: [] as any[], meta: {} }
      const resp = { code: 0, msg: 'ok', data: mockData }
      request.get.mockResolvedValue(resp)
      await fetchLLMGraphApi({ folder_id: 'f-1', max_nodes: 30 })
      expect(request.get).toHaveBeenCalledWith('/graph/llm-structure', {
        params: { folder_id: 'f-1', max_nodes: 30 },
      })
    })
  })

  describe('createGraphNode', () => {
    it('应发送 POST /graph/edit/nodes', async () => {
      const { createGraphNode } = await import('./graph')
      const data = { name: 'My Node', node_type: 'custom', category: 0 }
      const resp = { code: 0, msg: 'ok', data: { id: 'n-1', name: 'My Node', node_type: 'custom' as const, category: 0 } }
      request.post.mockResolvedValue(resp)
      const result = await createGraphNode(data)
      expect(request.post).toHaveBeenCalledWith('/graph/edit/nodes', data)
      expect(result.data.name).toBe('My Node')
    })
  })

  describe('updateGraphNode', () => {
    it('应发送 PATCH /graph/edit/nodes/{id}', async () => {
      const { updateGraphNode } = await import('./graph')
      const resp = { code: 0, msg: 'ok', data: { id: 'n-1', name: 'Updated', node_type: 'custom' as const, category: 0 } }
      request.patch.mockResolvedValue(resp)
      await updateGraphNode('n-1', { name: 'Updated' })
      expect(request.patch).toHaveBeenCalledWith('/graph/edit/nodes/n-1', { name: 'Updated' })
    })
  })

  describe('deleteGraphNode', () => {
    it('应发送 DELETE /graph/edit/nodes/{id}', async () => {
      const { deleteGraphNode } = await import('./graph')
      const resp = { code: 0, msg: 'ok', data: { deleted_node_id: 'n-1', deleted_edges_count: 2 } }
      request.delete.mockResolvedValue(resp)
      const result = await deleteGraphNode('n-1')
      expect(request.delete).toHaveBeenCalledWith('/graph/edit/nodes/n-1')
      expect(result.data.deleted_edges_count).toBe(2)
    })
  })

  describe('createGraphEdge', () => {
    it('应发送 POST /graph/edit/edges', async () => {
      const { createGraphEdge } = await import('./graph')
      const data = { source_id: 'n-1', target_id: 'n-2', relation_type: 'related' }
      const resp = { code: 0, msg: 'ok', data: { id: 'e-1', source_id: 'n-1', target_id: 'n-2', relation_type: 'related' as const } }
      request.post.mockResolvedValue(resp)
      await createGraphEdge(data)
      expect(request.post).toHaveBeenCalledWith('/graph/edit/edges', data)
    })
  })

  describe('updateGraphEdge', () => {
    it('应发送 PATCH /graph/edit/edges/{id}', async () => {
      const { updateGraphEdge } = await import('./graph')
      const resp = { code: 0, msg: 'ok', data: { id: 'e-1', source_id: 'n-1', target_id: 'n-2', relation_type: 'applies' as const } }
      request.patch.mockResolvedValue(resp)
      await updateGraphEdge('e-1', { relation_type: 'applies' })
      expect(request.patch).toHaveBeenCalledWith('/graph/edit/edges/e-1', { relation_type: 'applies' })
    })
  })

  describe('deleteGraphEdge', () => {
    it('应发送 DELETE /graph/edit/edges/{id}', async () => {
      const { deleteGraphEdge } = await import('./graph')
      const resp = { code: 0, msg: 'ok', data: { deleted_edge_id: 'e-1' } }
      request.delete.mockResolvedValue(resp)
      await deleteGraphEdge('e-1')
      expect(request.delete).toHaveBeenCalledWith('/graph/edit/edges/e-1')
    })
  })

  describe('getCustomGraph', () => {
    it('应发送 GET /graph/edit/graph', async () => {
      const { getCustomGraph } = await import('./graph')
      const mockData = { nodes: [] as any[], links: [] as any[], meta: { node_count: 0, edge_count: 0 } }
      const resp = { code: 0, msg: 'ok', data: mockData }
      request.get.mockResolvedValue(resp)
      const result = await getCustomGraph()
      expect(request.get).toHaveBeenCalledWith('/graph/edit/graph')
      expect(result.data.meta.node_count).toBe(0)
    })
  })

  describe('askGraphApi', () => {
    it('应发送 POST /graph/ask', async () => {
      const { askGraphApi } = await import('./graph')
      const data = { question: 'What is this paper about?', paper_ids: ['p-1', 'p-2'] }
      const resp = { code: 0, msg: 'ok', data: { answer: 'About ML', paper_count: 2 } }
      request.post.mockResolvedValue(resp)
      const result = await askGraphApi(data)
      expect(request.post).toHaveBeenCalledWith('/graph/ask', data)
      expect(result.data.answer).toBe('About ML')
    })
  })
})
