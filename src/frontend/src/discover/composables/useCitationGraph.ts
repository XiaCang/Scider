import { ref, computed } from 'vue'
import { usePaperStore } from '../../store/paper'
import { useAuthStore } from '../../store/auth'
import { fetchUpstreamPapersApi, fetchDownstreamPapersApi } from '../../api/discover'
import type { LibraryPaper } from '../../types/library'
import type { CitationPaper } from '../types'

export function useCitationGraph() {
  const paperStore = usePaperStore()
  const authStore = useAuthStore()
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

  /** 上游论文：过滤 + 搜索 */
  const filteredUpstreamPapers = computed(() => {
    const kw = upstreamKeyword.value.trim().toLowerCase()
    if (!kw) return upstreamPapers.value
    return upstreamPapers.value.filter(
      p =>
        p.title.toLowerCase().includes(kw) ||
        p.authors.toLowerCase().includes(kw) ||
        p.description.toLowerCase().includes(kw),
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
        p.description.toLowerCase().includes(kw),
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
      const userId = authStore.user?.userId || ''
      const res = await fetchUpstreamPapersApi(selectedPaperId.value, userId)
      upstreamPapers.value = res.data as CitationPaper[]
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
      const userId = authStore.user?.userId || ''
      const res = await fetchDownstreamPapersApi(selectedPaperId.value, userId)
      downstreamPapers.value = res.data as CitationPaper[]
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
