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
      const mockData = { nodes: [], links: [], meta: {} }
      request.get.mockResolvedValue({ data: { code: 0, data: mockData } })
      const result = await fetchSimilarityGraphApi()
      expect(request.get).toHaveBeenCalledWith('/graph/similarity', { params: undefined })
      expect(result.data.code).toBe(0)
    })

    it('应传递筛选参数', async () => {
      const { fetchSimilarityGraphApi } = await import('./graph')
      request.get.mockResolvedValue({ data: { code: 0, data: { nodes: [], links: [], meta: {} } } })
      await fetchSimilarityGraphApi({ folder_id: 'f-1', max_nodes: 50, min_similarity: 0.5, top_k: 10 })
      expect(request.get).toHaveBeenCalledWith('/graph/similarity', {
        params: { folder_id: 'f-1', max_nodes: 50, min_similarity: 0.5, top_k: 10 },
      })
    })
  })

  describe('fetchLLMGraphApi', () => {
    it('应发送 GET /graph/llm-structure', async () => {
      const { fetchLLMGraphApi } = await import('./graph')
      const mockData = { nodes: [], links: [], clusters: [], meta: {} }
      request.get.mockResolvedValue({ data: { code: 0, data: mockData } })
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
      request.post.mockResolvedValue({ data: { code: 0, data: { id: 'n-1', name: 'My Node', node_type: 'custom', category: 0 } } })
      const result = await createGraphNode(data)
      expect(request.post).toHaveBeenCalledWith('/graph/edit/nodes', data)
      expect(result.data.data.name).toBe('My Node')
    })
  })

  describe('updateGraphNode', () => {
    it('应发送 PATCH /graph/edit/nodes/{id}', async () => {
      const { updateGraphNode } = await import('./graph')
      request.patch.mockResolvedValue({ data: { code: 0, data: { id: 'n-1', name: 'Updated' } } })
      await updateGraphNode('n-1', { name: 'Updated' })
      expect(request.patch).toHaveBeenCalledWith('/graph/edit/nodes/n-1', { name: 'Updated' })
    })
  })

  describe('deleteGraphNode', () => {
    it('应发送 DELETE /graph/edit/nodes/{id}', async () => {
      const { deleteGraphNode } = await import('./graph')
      request.delete.mockResolvedValue({ data: { code: 0, data: { deleted_node_id: 'n-1', deleted_edges_count: 2 } } })
      const result = await deleteGraphNode('n-1')
      expect(request.delete).toHaveBeenCalledWith('/graph/edit/nodes/n-1')
      expect(result.data.data.deleted_edges_count).toBe(2)
    })
  })

  describe('createGraphEdge', () => {
    it('应发送 POST /graph/edit/edges', async () => {
      const { createGraphEdge } = await import('./graph')
      const data = { source_id: 'n-1', target_id: 'n-2', relation_type: 'related' }
      request.post.mockResolvedValue({ data: { code: 0, data: { id: 'e-1', source_id: 'n-1', target_id: 'n-2', relation_type: 'related' } } })
      await createGraphEdge(data)
      expect(request.post).toHaveBeenCalledWith('/graph/edit/edges', data)
    })
  })

  describe('updateGraphEdge', () => {
    it('应发送 PATCH /graph/edit/edges/{id}', async () => {
      const { updateGraphEdge } = await import('./graph')
      request.patch.mockResolvedValue({ data: { code: 0, data: { id: 'e-1', relation_type: 'applies' } } })
      await updateGraphEdge('e-1', { relation_type: 'applies' })
      expect(request.patch).toHaveBeenCalledWith('/graph/edit/edges/e-1', { relation_type: 'applies' })
    })
  })

  describe('deleteGraphEdge', () => {
    it('应发送 DELETE /graph/edit/edges/{id}', async () => {
      const { deleteGraphEdge } = await import('./graph')
      request.delete.mockResolvedValue({ data: { code: 0, data: { deleted_edge_id: 'e-1' } } })
      await deleteGraphEdge('e-1')
      expect(request.delete).toHaveBeenCalledWith('/graph/edit/edges/e-1')
    })
  })

  describe('getCustomGraph', () => {
    it('应发送 GET /graph/edit/graph', async () => {
      const { getCustomGraph } = await import('./graph')
      const mockData = { nodes: [], links: [], meta: { node_count: 0, edge_count: 0 } }
      request.get.mockResolvedValue({ data: { code: 0, data: mockData } })
      const result = await getCustomGraph()
      expect(request.get).toHaveBeenCalledWith('/graph/edit/graph')
      expect(result.data.data.meta.node_count).toBe(0)
    })
  })

  describe('askGraphApi', () => {
    it('应发送 POST /graph/ask', async () => {
      const { askGraphApi } = await import('./graph')
      const data = { question: 'What is this paper about?', paper_ids: ['p-1', 'p-2'] }
      request.post.mockResolvedValue({ data: { code: 0, data: { answer: 'About ML', paper_count: 2 } } })
      const result = await askGraphApi(data)
      expect(request.post).toHaveBeenCalledWith('/graph/ask', data)
      expect(result.data.data.answer).toBe('About ML')
    })
  })
})
