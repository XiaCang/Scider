import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useSearch } from './useSearch'
import * as discoverApi from '../../api/discover'

vi.mock('../../api/discover', () => ({
  searchPapersApi: vi.fn(),
  fetchRecommendationsApi: vi.fn(),
}))

const mockSearchResults = {
  data: {
    data: [
      { id: '1', semantic_id: 'sem-1', title: 'Deep Learning', authors: 'Goodfellow', venue: 'NeurIPS', year: 2016, citation_count: 50000, source_type: 'conference' },
      { id: '2', semantic_id: 'sem-2', title: 'Attention Is All You Need', authors: 'Vaswani', venue: 'NeurIPS', year: 2017, citation_count: 80000, source_type: 'conference' },
      { id: '3', semantic_id: 'sem-3', title: 'BERT', authors: 'Devlin', venue: 'ACL', year: 2019, citation_count: 60000, source_type: 'conference' },
    ],
    total: 3,
    offset: 0,
    limit: 10,
  },
}

describe('useSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(discoverApi.fetchRecommendationsApi).mockResolvedValue({ data: [] } as any)
  })

  describe('normalizeResult', () => {
    it('应标准化搜索结果', async () => {
      vi.mocked(discoverApi.searchPapersApi).mockResolvedValue(mockSearchResults as any)
      const search = useSearch()
      search.keyword.value = 'deep'
      await search.search()
      expect(search.results.value).toHaveLength(3)
      expect(search.results.value[0].id).toBe('sem-1')
      expect(search.results.value[0].title).toBe('Deep Learning')
    })
  })

  describe('doSearch with empty keyword', () => {
    it('空关键词应回退到推荐', async () => {
      vi.mocked(discoverApi.fetchRecommendationsApi).mockResolvedValue({ data: [] } as any)
      const search = useSearch()
      search.keyword.value = '  '
      await search.search()
      expect(discoverApi.fetchRecommendationsApi).toHaveBeenCalled()
    })
  })

  describe('error handling', () => {
    it('搜索失败应设置错误信息', async () => {
      vi.mocked(discoverApi.searchPapersApi).mockRejectedValue(new Error('搜索服务不可用'))
      const search = useSearch()
      search.keyword.value = 'test'
      await search.search()
      expect(search.error.value).toBe('搜索服务不可用')
      expect(search.loading.value).toBe(false)
    })
  })

  describe('filteredResults — 客户端过滤逻辑（绕过 watcher 干扰）', () => {
    it('应通过年份过滤', () => {
      const search = useSearch()
      // 直接设置结果（不触发搜索）
      search.results.value = mockSearchResults.data.data.map((item: any) => ({
        id: item.semantic_id || item.id,
        title: item.title,
        authors: item.authors,
        venue: item.venue,
        year: item.year,
        description: '',
      })) as any

      search.selectedYear.value = '2017'
      expect(search.filteredResults.value).toHaveLength(1)
      expect(search.filteredResults.value[0].year).toBe(2017)
    })

    it('应通过来源过滤', () => {
      const search = useSearch()
      search.results.value = mockSearchResults.data.data.map((item: any) => ({
        id: item.semantic_id || item.id,
        title: item.title,
        authors: item.authors,
        venue: item.venue,
        year: item.year,
        description: '',
      })) as any

      search.selectedVenue.value = 'ACL'
      expect(search.filteredResults.value).toHaveLength(1)
      expect(search.filteredResults.value[0].venue).toBe('ACL')
    })

    it('应按 year desc 排序', () => {
      const search = useSearch()
      search.results.value = mockSearchResults.data.data.map((item: any) => ({
        id: item.semantic_id || item.id,
        title: item.title,
        authors: item.authors,
        venue: item.venue,
        year: item.year,
        description: '',
      })) as any

      search.sortBy.value = 'year-desc'
      const years = search.filteredResults.value.map(r => r.year)
      expect(years).toEqual([2019, 2017, 2016])
    })

    it('应按 title asc 排序', () => {
      const search = useSearch()
      search.results.value = mockSearchResults.data.data.map((item: any) => ({
        id: item.semantic_id || item.id,
        title: item.title,
        authors: item.authors,
        venue: item.venue,
        year: item.year,
        description: '',
      })) as any

      search.sortBy.value = 'title-asc'
      const titles = search.filteredResults.value.map(r => r.title)
      expect(titles).toEqual([
        'Attention Is All You Need',
        'BERT',
        'Deep Learning',
      ])
    })

    it('应通过关键词客户端过滤', () => {
      const search = useSearch()
      search.results.value = mockSearchResults.data.data.map((item: any) => ({
        id: item.semantic_id || item.id,
        title: item.title,
        authors: item.authors,
        venue: item.venue,
        year: item.year,
        description: '',
      })) as any

      search.keyword.value = 'Attention'
      expect(search.filteredResults.value).toHaveLength(1)
      expect(search.filteredResults.value[0].title).toBe('Attention Is All You Need')
    })
  })

  describe('clearFilters', () => {
    it('应重置所有筛选条件', () => {
      const search = useSearch()
      search.selectedYear.value = '2024'
      search.selectedVenue.value = 'ACL'
      search.sortBy.value = 'year-desc'
      search.clearFilters()
      expect(search.selectedYear.value).toBe('')
      expect(search.selectedVenue.value).toBe('')
      expect(search.sortBy.value).toBe('relevance')
    })
  })
})
