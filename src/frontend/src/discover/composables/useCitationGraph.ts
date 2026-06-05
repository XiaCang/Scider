import { ref, computed } from 'vue'
import { usePaperStore } from '../../store/paper'
import {
  fetchUpstreamByPaperApi,
  fetchDownstreamByPaperApi,
} from '../../api/discover'
import type { LibraryPaper } from '../../types/library'
import type { CitationPaper, CitationResponseData } from '../types'

export function useCitationGraph() {
  const paperStore = usePaperStore()
  const selectedPaperId = ref<string>('')
  const upstreamPapers = ref<CitationPaper[]>([])
  const downstreamPapers = ref<CitationPaper[]>([])
  const upstreamLoading = ref(false)
  const downstreamLoading = ref(false)
  const upstreamError = ref<string | null>(null)
  const downstreamError = ref<string | null>(null)
  const upstreamKeyword = ref('')
  const downstreamKeyword = ref('')

  const libraryPapers = computed<LibraryPaper[]>(() => paperStore.papers)

  const selectedPaper = computed(() =>
    libraryPapers.value.find(p => p.id === selectedPaperId.value) ?? null,
  )

  /** 标准化引文结果字段（API 返回 semantic_id → 映射为 id） */
  function normalizeCitation(item: any): CitationPaper {
    return {
      id: (item.semantic_id as string) || (item.id as string) || '',
      title: (item.title as string) || '',
      authors: (item.authors as string) || '',
      venue: (item.venue as string) || '',
      year: (item.year as number) || 0,
      semantic_id: item.semantic_id as string,
      citation_count: (item.citation_count as number) || 0,
      in_library: !!item.in_library,
      description: (item.abstract as string) || (item.description as string) || '',
      doi: (item.doi as string) || '',
      arxiv_id: (item.arxiv_id as string) || '',
    }
  }

  /** 上游论文：过滤 + 搜索 */
  const filteredUpstreamPapers = computed(() => {
    const kw = upstreamKeyword.value.trim().toLowerCase()
    if (!kw) return upstreamPapers.value
    return upstreamPapers.value.filter(
      p =>
        p.title.toLowerCase().includes(kw) ||
        p.authors.toLowerCase().includes(kw) ||
        (p.description || '').toLowerCase().includes(kw),
    )
  })

  /** 下游论文：过滤 + 搜索 */
  const filteredDownstreamPapers = computed(() => {
    const kw = downstreamKeyword.value.trim().toLowerCase()
    if (!kw) return downstreamPapers.value
    return downstreamPapers.value.filter(
      p =>
        p.title.toLowerCase().includes(kw) ||
        p.authors.toLowerCase().includes(kw) ||
        (p.description || '').toLowerCase().includes(kw),
    )
  })

  /** 选中一篇论文，加载其引用图谱 */
  async function selectPaper(paperId: string) {
    selectedPaperId.value = paperId
    upstreamKeyword.value = ''
    downstreamKeyword.value = ''
    await loadCitationGraph()
  }

  async function loadCitationGraph() {
    await Promise.all([loadUpstream(), loadDownstream()])
  }

  async function loadUpstream() {
    upstreamLoading.value = true
    upstreamError.value = null
    try {
      // 使用 by-paper 端点（通过本地 paper_id 查找 DOI 再调 Semantic Scholar）
      const res = await fetchUpstreamByPaperApi(selectedPaperId.value)
      const citationData = res.data as CitationResponseData
      upstreamPapers.value = (citationData?.data ?? []).map(normalizeCitation)
    } catch (e) {
      upstreamError.value = e instanceof Error ? e.message : '上游论文加载失败'
    } finally {
      upstreamLoading.value = false
    }
  }

  async function loadDownstream() {
    downstreamLoading.value = true
    downstreamError.value = null
    try {
      const res = await fetchDownstreamByPaperApi(selectedPaperId.value)
      const citationData = res.data as CitationResponseData
      downstreamPapers.value = (citationData?.data ?? []).map(normalizeCitation)
    } catch (e) {
      downstreamError.value = e instanceof Error ? e.message : '下游论文加载失败'
    } finally {
      downstreamLoading.value = false
    }
  }

  function clearSelection() {
    selectedPaperId.value = ''
    upstreamPapers.value = []
    downstreamPapers.value = []
    upstreamKeyword.value = ''
    downstreamKeyword.value = ''
  }

  /** 加载文库论文（如果尚未加载） */
  async function ensureLibraryLoaded() {
    if (paperStore.papers.length === 0) {
      await paperStore.loadPapers()
    }
  }

  return {
    selectedPaperId,
    selectedPaper,
    libraryPapers,
    upstreamPapers,
    downstreamPapers,
    upstreamLoading,
    downstreamLoading,
    upstreamError,
    downstreamError,
    upstreamKeyword,
    downstreamKeyword,
    filteredUpstreamPapers,
    filteredDownstreamPapers,
    selectPaper,
    loadCitationGraph,
    clearSelection,
    ensureLibraryLoaded,
  }
}
