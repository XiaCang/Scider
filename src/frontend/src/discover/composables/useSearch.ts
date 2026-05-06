import { ref, computed, watch } from 'vue'
import { searchPapersApi, fetchRecommendationsApi } from '../../api/discover'
import type { SearchResult, SearchResponseData } from '../types'

const DEBOUNCE_MS = 400

export function useSearch() {
  const keyword = ref('')
  const selectedYear = ref('')
  const selectedVenue = ref('')
  const sortBy = ref('relevance')
  const results = ref<SearchResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  /** 标准化搜索结果的字段名（API 返回 semantic_id → 映射为 id） */
  function normalizeResult(item: any): SearchResult {
    return {
      id: (item.semantic_id as string) || (item.id as string) || '',
      title: (item.title as string) || '',
      authors: (item.authors as string) || '',
      venue: (item.venue as string) || '',
      year: (item.year as number) || 0,
      semantic_id: item.semantic_id as string,
      citation_count: item.citation_count as number,
      source_type: item.source_type as string,
      pdf_url: item.pdf_url as string,
      reason: item.reason as string,
      description: item.description as string,
    }
  }

  /** 经过关键词、年份、来源、排序过滤后的结果 */
  const filteredResults = computed(() => {
    let items = results.value

    const kw = keyword.value.trim().toLowerCase()
    if (kw) {
      items = items.filter(
        item =>
          item.title.toLowerCase().includes(kw) ||
          item.authors.toLowerCase().includes(kw) ||
          (item.description || '').toLowerCase().includes(kw),
      )
    }

    if (selectedYear.value) {
      items = items.filter(item => String(item.year) === selectedYear.value)
    }

    if (selectedVenue.value) {
      items = items.filter(item => item.venue === selectedVenue.value)
    }

    switch (sortBy.value) {
      case 'year-desc':
        items = [...items].sort((a, b) => b.year - a.year)
        break
      case 'year-asc':
        items = [...items].sort((a, b) => a.year - b.year)
        break
      case 'title-asc':
        items = [...items].sort((a, b) => a.title.localeCompare(b.title))
        break
    }

    return items
  })

  /** 加载推荐列表（初始状态下无关键词时调用） */
  async function loadRecommendations() {
    loading.value = true
    error.value = null
    try {
      const data = await fetchRecommendationsApi()
      // 兼容推荐接口返回格式（可能是数组或 ApiResponse）
      const raw = Array.isArray(data) ? data : (data as any)?.data ?? []
      results.value = (raw as any[]).map(normalizeResult)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '推荐服务不可用'
    } finally {
      loading.value = false
    }
  }

  /** 主动搜索论文（调用后端真实搜索接口） */
  async function doSearch() {
    const q = keyword.value.trim()
    if (!q) {
      // 关键词为空时，回退到推荐
      await loadRecommendations()
      return
    }

    loading.value = true
    error.value = null
    try {
      const res = await searchPapersApi({
        q,
        year_from: selectedYear.value ? parseInt(selectedYear.value) : null,
        year_to: selectedYear.value ? parseInt(selectedYear.value) : null,
        source_type: selectedVenue.value || null,
        sort: sortBy.value === 'relevance' ? 'relevance' : undefined,
      })
      // res: ApiResponse<SearchResponseData>
      // res.data = { total, offset, limit, data: [...] }
      const responseData = res.data as SearchResponseData
      results.value = (responseData?.data ?? []).map(normalizeResult)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '搜索服务不可用'
    } finally {
      loading.value = false
    }
  }

  /** 防抖触发搜索 */
  function triggerDebouncedSearch() {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      doSearch()
    }, DEBOUNCE_MS)
  }

  // 监听关键词变化，自动触发防抖搜索
  watch(keyword, () => {
    triggerDebouncedSearch()
  })

  // 监听筛选条件变化，重新搜索
  watch([selectedYear, selectedVenue, sortBy], () => {
    if (keyword.value.trim()) {
      doSearch()
    }
  })

  function clearFilters() {
    selectedYear.value = ''
    selectedVenue.value = ''
    sortBy.value = 'relevance'
  }

  // 初始化时加载推荐
  loadRecommendations()

  return {
    keyword,
    selectedYear,
    selectedVenue,
    sortBy,
    results,
    loading,
    error,
    filteredResults,
    search: doSearch,
    loadRecommendations,
    clearFilters,
  }
}
