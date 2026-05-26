import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCitationGraph } from './useCitationGraph'
import { usePaperStore } from '../../store/paper'
import * as discoverApi from '../../api/discover'

vi.mock('../../api/discover', () => ({
  fetchUpstreamByPaperApi: vi.fn(),
  fetchDownstreamByPaperApi: vi.fn(),
}))

const mockUpstreamData = {
  data: {
    data: [
      { id: 'up-1', semantic_id: 'sem-up-1', title: 'Upstream Paper', authors: 'Author A', venue: 'NeurIPS', year: 2020, citation_count: 100, in_library: false },
      { id: 'up-2', semantic_id: 'sem-up-2', title: 'Earlier Work', authors: 'Author B', venue: 'ICML', year: 2018, citation_count: 50, in_library: true },
    ],
  },
}

const mockDownstreamData = {
  data: {
    data: [
      { id: 'down-1', semantic_id: 'sem-down-1', title: 'Downstream Paper', authors: 'Author C', venue: 'ACL', year: 2023, citation_count: 30, in_library: false },
    ],
  },
}

describe('useCitationGraph', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // 给 paperStore 预置一些论文使 selectPaper 能正常工作
    const paperStore = usePaperStore()
    paperStore.papers = [
      { id: 'p-1', title: 'Base Paper', authors: 'Author', year: 2022, status: 'CONFIRMED', source: 'arXiv', keyPoints: { background: '', method: '', innovation: '', conclusion: '' } },
    ]
  })

  describe('selectPaper', () => {
    it('应加载引用图谱', async () => {
      vi.mocked(discoverApi.fetchUpstreamByPaperApi).mockResolvedValue(mockUpstreamData as any)
      vi.mocked(discoverApi.fetchDownstreamByPaperApi).mockResolvedValue(mockDownstreamData as any)

      const graph = useCitationGraph()
      await graph.selectPaper('p-1')

      expect(graph.selectedPaperId.value).toBe('p-1')
      expect(graph.upstreamPapers.value).toHaveLength(2)
      expect(graph.downstreamPapers.value).toHaveLength(1)
      expect(graph.upstreamPapers.value[0].title).toBe('Upstream Paper')
      expect(graph.downstreamPapers.value[0].title).toBe('Downstream Paper')
    })

    it('应重置关键词', async () => {
      vi.mocked(discoverApi.fetchUpstreamByPaperApi).mockResolvedValue(mockUpstreamData as any)
      vi.mocked(discoverApi.fetchDownstreamByPaperApi).mockResolvedValue(mockDownstreamData as any)

      const graph = useCitationGraph()
      graph.upstreamKeyword.value = 'test'
      await graph.selectPaper('p-1')
      expect(graph.upstreamKeyword.value).toBe('')
      expect(graph.downstreamKeyword.value).toBe('')
    })
  })

  describe('filteredUpstreamPapers', () => {
    it('应过滤上游论文', async () => {
      vi.mocked(discoverApi.fetchUpstreamByPaperApi).mockResolvedValue(mockUpstreamData as any)
      vi.mocked(discoverApi.fetchDownstreamByPaperApi).mockResolvedValue(mockDownstreamData as any)

      const graph = useCitationGraph()
      await graph.selectPaper('p-1')
      graph.upstreamKeyword.value = 'Earlier'
      expect(graph.filteredUpstreamPapers.value).toHaveLength(1)
      expect(graph.filteredUpstreamPapers.value[0].title).toBe('Earlier Work')
    })
  })

  describe('filteredDownstreamPapers', () => {
    it('应过滤下游论文', async () => {
      vi.mocked(discoverApi.fetchUpstreamByPaperApi).mockResolvedValue(mockUpstreamData as any)
      vi.mocked(discoverApi.fetchDownstreamByPaperApi).mockResolvedValue(mockDownstreamData as any)

      const graph = useCitationGraph()
      await graph.selectPaper('p-1')
      graph.downstreamKeyword.value = 'Downstream'
      expect(graph.filteredDownstreamPapers.value).toHaveLength(1)
    })
  })

  describe('clearSelection', () => {
    it('应清除当前选择', async () => {
      vi.mocked(discoverApi.fetchUpstreamByPaperApi).mockResolvedValue(mockUpstreamData as any)
      vi.mocked(discoverApi.fetchDownstreamByPaperApi).mockResolvedValue(mockDownstreamData as any)

      const graph = useCitationGraph()
      await graph.selectPaper('p-1')
      graph.clearSelection()
      expect(graph.selectedPaperId.value).toBe('')
      expect(graph.upstreamPapers.value).toEqual([])
      expect(graph.downstreamPapers.value).toEqual([])
    })
  })

  describe('ensureLibraryLoaded', () => {
    it('paperStore 已有论文时不应重复加载', async () => {
      const graph = useCitationGraph()
      const paperStore = usePaperStore()
      const loadSpy = vi.spyOn(paperStore, 'loadPapers')
      await graph.ensureLibraryLoaded()
      expect(loadSpy).not.toHaveBeenCalled()
    })
  })

  describe('selectedPaper', () => {
    it('应返回当前已选论文信息', () => {
      const graph = useCitationGraph()
      graph.selectedPaperId.value = 'p-1'
      expect(graph.selectedPaper.value?.id).toBe('p-1')
      expect(graph.selectedPaper.value?.title).toBe('Base Paper')
    })

    it('未选择时应返回 null', () => {
      const graph = useCitationGraph()
      expect(graph.selectedPaper.value).toBeNull()
    })

    it('不存在的论文 ID 应返回 null', () => {
      const graph = useCitationGraph()
      graph.selectedPaperId.value = 'non-existent'
      expect(graph.selectedPaper.value).toBeNull()
    })
  })
})
