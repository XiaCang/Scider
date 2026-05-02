import { ref, computed } from 'vue'
import { searchPapersApi, fetchRecommendationsApi } from '../../api/discover'
import type { SearchResult } from '../types'

export function useSearch() {
  const keyword = ref('')
  const selectedYear = ref('')
  const selectedVenue = ref('')
  const sortBy = ref('relevance')
  const results = ref<SearchResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /** 经过关键词、年份、来源、排序过滤后的结果 */
  const filteredResults = computed(() => {
    let items = results.value

    const kw = keyword.value.trim().toLowerCase()
    if (kw) {
      items = items.filter(
        item =>
          item.title.toLowerCase().includes(kw) ||
          item.authors.toLowerCase().includes(kw) ||
          item.description.toLowerCase().includes(kw),
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

  /** 加载推荐列表 */
  async function search() {
    loading.value = true
    error.value = null
    try {
      const data = await fetchRecommendationsApi()
      results.value = data as SearchResult[]
    } catch (e) {
      error.value = e instanceof Error ? e.message : '推荐服务不可用'
    } finally {
      loading.value = false
    }
  }

  /** 主动搜索论文（对齐 /api/discover/search） */
  async function doSearch() {
    loading.value = true
    error.value = null
    try {
      const res = await searchPapersApi({
        q: keyword.value,
        year_from: selectedYear.value ? parseInt(selectedYear.value) : null,
        year_to: selectedYear.value ? parseInt(selectedYear.value) : null,
        source_type: selectedVenue.value || null,
        sort: sortBy.value === 'relevance' ? 'relevance' : undefined,
      })
      results.value = res.data as SearchResult[]
    } catch (e) {
      error.value = e instanceof Error ? e.message : '搜索服务不可用'
    } finally {
      loading.value = false
    }
  }

  function clearFilters() {
    selectedYear.value = ''
    selectedVenue.value = ''
    sortBy.value = 'relevance'
  }

  // 初始化时加载推荐
  search()

  return {
    keyword,
    selectedYear,
    selectedVenue,
    sortBy,
    results,
    loading,
    error,
    filteredResults,
    search,
    doSearch,
    clearFilters,
  }
}
