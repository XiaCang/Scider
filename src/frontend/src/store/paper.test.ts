import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePaperStore } from './paper'
import * as libraryApi from '../api/library'

vi.mock('../api/library', () => ({
  fetchLibraryApi: vi.fn(),
  saveKeyPointsApi: vi.fn(),
  movePaperToFolderApi: vi.fn(),
}))

const mockPapers = [
  { id: 'p-1', title: 'Paper A', authors: 'Author A', year: 2024, status: 'CONFIRMED', source: 'arXiv', keyPoints: { background: '', method: '', innovation: '', conclusion: '' } },
  { id: 'p-2', title: 'Paper B', authors: 'Author B', year: 2023, status: 'PENDING_PARSING', source: 'ACL', keyPoints: { background: '', method: '', innovation: '', conclusion: '' } },
  { id: 'p-3', title: 'Paper C', authors: 'Author C', year: 2025, status: 'CONFIRMED', source: 'NeurIPS', keyPoints: { background: '', method: '', innovation: '', conclusion: '' } },
]

describe('paperStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应初始化为空', () => {
      const store = usePaperStore()
      expect(store.papers).toEqual([])
      expect(store.loading).toBe(false)
    })
  })

  describe('loadPapers', () => {
    it('应加载论文列表', async () => {
      vi.mocked(libraryApi.fetchLibraryApi).mockResolvedValue({ data: mockPapers } as any)
      const store = usePaperStore()
      await store.loadPapers()
      expect(store.papers).toHaveLength(3)
      expect(store.loading).toBe(false)
    })

    it('加载失败时应打印错误但不抛出', async () => {
      vi.mocked(libraryApi.fetchLibraryApi).mockRejectedValue(new Error('Network Error'))
      const store = usePaperStore()
      await store.loadPapers()
      expect(store.papers).toEqual([])
      expect(store.loading).toBe(false)
    })
  })

  describe('paperMap', () => {
    it('应根据 papers 生成快速查找映射', async () => {
      vi.mocked(libraryApi.fetchLibraryApi).mockResolvedValue({ data: mockPapers } as any)
      const store = usePaperStore()
      await store.loadPapers()
      expect(store.paperMap.get('p-1')?.title).toBe('Paper A')
      expect(store.paperMap.get('not-exists')).toBeUndefined()
    })
  })

  describe('saveKeyPoints', () => {
    it('应保存关键点并更新论文状态为 CONFIRMED', async () => {
      vi.mocked(libraryApi.fetchLibraryApi).mockResolvedValue({ data: mockPapers } as any)
      vi.mocked(libraryApi.saveKeyPointsApi).mockResolvedValue({} as any)
      const store = usePaperStore()
      await store.loadPapers()

      const newKeyPoints = { background: 'bg', method: 'method', innovation: 'innov', conclusion: 'conc' }
      await store.saveKeyPoints('p-1', newKeyPoints)
      expect(store.papers[0].keyPoints.background).toBe('bg')
      expect(store.papers[0].status).toBe('CONFIRMED')
    })

    it('不存在的 paperId 应仅打印警告不报错', async () => {
      vi.mocked(libraryApi.saveKeyPointsApi).mockResolvedValue({} as any)
      const store = usePaperStore()
      // 不应抛出错误
      await expect(store.saveKeyPoints('nonexistent', { background: '', method: '', innovation: '', conclusion: '' })).resolves.not.toThrow()
    })
  })

  describe('getPapersByIds', () => {
    it('应根据 ID 列表获取论文', async () => {
      vi.mocked(libraryApi.fetchLibraryApi).mockResolvedValue({ data: mockPapers } as any)
      const store = usePaperStore()
      await store.loadPapers()
      const result = store.getPapersByIds(['p-1', 'p-3'])
      expect(result).toHaveLength(2)
      expect(result[0].id).toBe('p-1')
      expect(result[1].id).toBe('p-3')
    })

    it('不存在的 ID 应被过滤掉', () => {
      const store = usePaperStore()
      const result = store.getPapersByIds(['not-exists'])
      expect(result).toEqual([])
    })
  })
})
