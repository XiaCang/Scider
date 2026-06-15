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

describe('discover API', () => {
  let request: any

  beforeAll(async () => {
    const mod = await import('../network/request')
    request = mod.default
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('searchPapersApi', () => {
    it('应发送 GET /discover/search 包含查询参数', async () => {
      const { searchPapersApi } = await import('./discover')
      const params = { q: 'deep learning', offset: 0, limit: 10 }
      const resp = { code: 0, msg: 'ok', data: { data: [], total: 0, offset: 0, limit: 10 } }
      request.get.mockResolvedValue(resp)
      const result = await searchPapersApi(params)
      expect(request.get).toHaveBeenCalledWith('/discover/search', { params })
      expect(result.code).toBe(0)
    })

    it('应支持可选筛选参数', async () => {
      const { searchPapersApi } = await import('./discover')
      const params = { q: 'transformer', year_from: 2020, year_to: 2024, source_type: 'conference', sort: 'citation_count' }
      const resp = { code: 0, msg: 'ok', data: { data: [], total: 0, offset: 0, limit: 10 } }
      request.get.mockResolvedValue(resp)
      await searchPapersApi(params)
      expect(request.get).toHaveBeenCalledWith('/discover/search', { params })
    })
  })

  describe('fetchRecommendationsApi', () => {
    it('应发送 GET /discover/recommendations', async () => {
      const { fetchRecommendationsApi } = await import('./discover')
      request.get.mockResolvedValue({ data: [] })
      await fetchRecommendationsApi()
      expect(request.get).toHaveBeenCalledWith('/discover/recommendations', { params: { direction: undefined } })
    })

    it('应传递 direction 参数', async () => {
      const { fetchRecommendationsApi } = await import('./discover')
      request.get.mockResolvedValue({ data: [] })
      await fetchRecommendationsApi('upstream')
      expect(request.get).toHaveBeenCalledWith('/discover/recommendations', { params: { direction: 'upstream' } })
    })
  })

  describe('fetchUpstreamPapersApi', () => {
    it('应发送 GET /discover/references/{semantic_id}', async () => {
      const { fetchUpstreamPapersApi } = await import('./discover')
      request.get.mockResolvedValue({ code: 0, msg: 'ok', data: { data: [] as any[] } })
      await fetchUpstreamPapersApi('sem-1')
      expect(request.get).toHaveBeenCalledWith('/discover/references/sem-1')
    })
  })

  describe('fetchDownstreamPapersApi', () => {
    it('应发送 GET /discover/citations/{semantic_id}', async () => {
      const { fetchDownstreamPapersApi } = await import('./discover')
      request.get.mockResolvedValue({ code: 0, msg: 'ok', data: { data: [] as any[] } })
      await fetchDownstreamPapersApi('sem-1')
      expect(request.get).toHaveBeenCalledWith('/discover/citations/sem-1')
    })
  })

  describe('fetchUpstreamByPaperApi', () => {
    it('应发送 GET /discover/references/by-paper/{paper_id} 含超时', async () => {
      const { fetchUpstreamByPaperApi } = await import('./discover')
      request.get.mockResolvedValue({ code: 0, msg: 'ok', data: { data: [] as any[] } })
      await fetchUpstreamByPaperApi('p-1')
      expect(request.get).toHaveBeenCalledWith('/discover/references/by-paper/p-1', { timeout: 120000 })
    })
  })

  describe('fetchDownstreamByPaperApi', () => {
    it('应发送 GET /discover/citations/by-paper/{paper_id} 含超时', async () => {
      const { fetchDownstreamByPaperApi } = await import('./discover')
      request.get.mockResolvedValue({ code: 0, msg: 'ok', data: { data: [] as any[] } })
      await fetchDownstreamByPaperApi('p-1')
      expect(request.get).toHaveBeenCalledWith('/discover/citations/by-paper/p-1', { timeout: 120000 })
    })
  })

  describe('fetchCitationGraphApi', () => {
    it('应发送 GET /discover/citations 含 paper_id 参数', async () => {
      const { fetchCitationGraphApi } = await import('./discover')
      request.get.mockResolvedValue({ nodes: [], links: [] })
      await fetchCitationGraphApi('p-1')
      expect(request.get).toHaveBeenCalledWith('/discover/citations', { params: { paper_id: 'p-1' } })
    })
  })

  describe('importPaperApi', () => {
    it('应发送 POST /discover/import', async () => {
      const { importPaperApi } = await import('./discover')
      const data = { semantic_id: 'sem-1', title: 'Paper', authors: 'Author', year: 2024, abstract: 'abstract', venue: 'NeurIPS', source_type: 'conference', citation_count: 10, reference_count: 5, url: 'http://example.com', pdf_url: 'http://example.com/pdf' }
      const resp = { code: 0, msg: 'ok', data: { paper_id: 'p-1', task_id: 't-1', status: 'imported' } }
      request.post.mockResolvedValue(resp)
      const result = await importPaperApi(data)
      expect(request.post).toHaveBeenCalledWith('/discover/import', data)
      expect(result.data.paper_id).toBe('p-1')
    })
  })

  describe('bulkImportPapersApi', () => {
    it('应发送 POST /discover/import/bulk', async () => {
      const { bulkImportPapersApi } = await import('./discover')
      const data = { papers: [{ semantic_id: 'sem-1', title: 'Paper', authors: 'Author', year: 2024, abstract: '', venue: '', source_type: 'conference', citation_count: 0, reference_count: 0, url: '', pdf_url: '' }] }
      request.post.mockResolvedValue({ code: 0, msg: 'ok', data: null })
      await bulkImportPapersApi(data)
      expect(request.post).toHaveBeenCalledWith('/discover/import/bulk', data)
    })
  })

  describe('downloadDiscoverPdfApi', () => {
    it('应发送 GET /discover/pdf-proxy 含 blob responseType', async () => {
      const { downloadDiscoverPdfApi } = await import('./discover')
      const blob = new Blob(['pdf content'])
      request.get.mockResolvedValue(blob)
      const result = await downloadDiscoverPdfApi('http://example.com/paper.pdf')
      expect(request.get).toHaveBeenCalledWith('/discover/pdf-proxy', {
        params: { pdf_url: 'http://example.com/paper.pdf', arxiv_id: undefined },
        responseType: 'blob',
        timeout: 120000,
      })
      expect(result).toBeInstanceOf(Blob)
    })

    it('应传递 arxiv_id 参数', async () => {
      const { downloadDiscoverPdfApi } = await import('./discover')
      request.get.mockResolvedValue(new Blob())
      await downloadDiscoverPdfApi('http://arxiv.org/pdf/2301.001', '2301.001')
      expect(request.get).toHaveBeenCalledWith('/discover/pdf-proxy', expect.objectContaining({
        params: expect.objectContaining({ arxiv_id: '2301.001' }),
      }))
    })
  })
})
