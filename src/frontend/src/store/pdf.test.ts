import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePdfStore } from './pdf'
import * as libraryApi from '../api/library'

vi.mock('../api/library', () => ({
  fetchPaperPdfInfoApi: vi.fn(),
  fetchPaperNotesApi: vi.fn(),
  createNoteApi: vi.fn(),
  updateNoteApi: vi.fn(),
}))

const mockPdfInfo = {
  id: 'p-1',
  title: 'Test Paper',
  pdfUrl: '/pdfs/test.pdf',
  pageCount: 10,
}

const mockNotes = [
  { id: 'n-1', paperId: 'p-1', content: 'Note 1', pageNumber: 1, createdAt: '2024-01-01T00:00:00Z', updatedAt: '2024-01-01T00:00:00Z' },
  { id: 'n-2', paperId: 'p-1', content: 'Note 2', pageNumber: 3, selectedText: 'important text', createdAt: '2024-01-02T00:00:00Z', updatedAt: '2024-01-02T00:00:00Z' },
]

describe('pdfStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应初始化为空', () => {
      const store = usePdfStore()
      expect(store.pdfInfo).toBeNull()
      expect(store.notes).toEqual([])
      expect(store.currentPaperId).toBeNull()
      expect(store.loading).toBe(false)
    })
  })

  describe('loadPdfInfo', () => {
    it('应加载 PDF 信息', async () => {
      vi.mocked(libraryApi.fetchPaperPdfInfoApi).mockResolvedValue(mockPdfInfo as any)
      const store = usePdfStore()
      await store.loadPdfInfo('p-1')
      expect(store.pdfInfo).toEqual(mockPdfInfo)
      expect(store.currentPaperId).toBe('p-1')
      expect(store.loading).toBe(false)
    })

    it('加载完成后 loading 应为 false', async () => {
      vi.mocked(libraryApi.fetchPaperPdfInfoApi).mockResolvedValue(mockPdfInfo as any)
      const store = usePdfStore()
      await store.loadPdfInfo('p-1')
      expect(store.loading).toBe(false)
    })
  })

  describe('loadNotes', () => {
    it('应加载笔记列表', async () => {
      vi.mocked(libraryApi.fetchPaperNotesApi).mockResolvedValue(mockNotes as any)
      const store = usePdfStore()
      await store.loadNotes('p-1')
      expect(store.notes).toHaveLength(2)
    })
  })

  describe('createNote', () => {
    it('应创建笔记并添加到列表', async () => {
      const newNote = { id: 'n-3', paperId: 'p-1', content: 'New Note', pageNumber: 5, createdAt: '2024-02-01T00:00:00Z', updatedAt: '2024-02-01T00:00:00Z' }
      vi.mocked(libraryApi.createNoteApi).mockResolvedValue(newNote as any)
      const store = usePdfStore()
      // 先设置 currentPaperId
      vi.mocked(libraryApi.fetchPaperPdfInfoApi).mockResolvedValue(mockPdfInfo as any)
      await store.loadPdfInfo('p-1')
      const result = await store.createNote('New Note', 5)
      expect(result.id).toBe('n-3')
      expect(store.notes).toHaveLength(1)
      expect(store.notes[0].content).toBe('New Note')
    })

    it('未选择论文时应抛出错误', async () => {
      const store = usePdfStore()
      await expect(store.createNote('No paper', 1)).rejects.toThrow('未选择论文')
    })
  })

  describe('updateNote', () => {
    it('应更新笔记内容', async () => {
      const updatedNote = { id: 'n-1', paperId: 'p-1', content: 'Updated Content', pageNumber: 1, createdAt: '2024-01-01T00:00:00Z', updatedAt: '2024-02-01T00:00:00Z' }
      vi.mocked(libraryApi.fetchPaperNotesApi).mockResolvedValue(mockNotes as any)
      vi.mocked(libraryApi.updateNoteApi).mockResolvedValue(updatedNote as any)
      const store = usePdfStore()
      vi.mocked(libraryApi.fetchPaperPdfInfoApi).mockResolvedValue(mockPdfInfo as any)
      await store.loadPdfInfo('p-1')
      await store.loadNotes('p-1')
      await store.updateNote('n-1', 'Updated Content')
      expect(store.notes[0].content).toBe('Updated Content')
    })

    it('未选择论文时应抛出错误', async () => {
      const store = usePdfStore()
      await expect(store.updateNote('n-1', 'content')).rejects.toThrow('未选择论文')
    })
  })

  describe('resetPdf', () => {
    it('应重置所有 PDF 状态', () => {
      const store = usePdfStore()
      store.pdfInfo = mockPdfInfo as any
      store.notes = mockNotes as any
      store.currentPaperId = 'p-1'
      store.resetPdf()
      expect(store.pdfInfo).toBeNull()
      expect(store.notes).toEqual([])
      expect(store.currentPaperId).toBeNull()
    })
  })
})
