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

const mockNotesData = {
  total: 2,
  items: [
    { id: 'n-1', paperId: 'p-1', title: 'Note 1', excerpt: 'Note content 1', firstImageUrl: null, updatedAt: '2024-01-01T00:00:00Z' },
    { id: 'n-2', paperId: 'p-1', title: 'Note 2', excerpt: 'Note content 2', firstImageUrl: null, updatedAt: '2024-01-02T00:00:00Z' },
  ],
}

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
      vi.mocked(libraryApi.fetchPaperNotesApi).mockResolvedValue({ data: mockNotesData } as any)
      const store = usePdfStore()
      await store.loadNotes('p-1')
      expect(store.notes).toHaveLength(2)
    })
  })

  describe('createNote', () => {
    it('应创建笔记并添加到列表', async () => {
      const newNoteData = { id: 'n-3', title: 'New Note', contentHtml: 'New content', updatedAt: '2024-02-01T00:00:00Z' }
      vi.mocked(libraryApi.createNoteApi).mockResolvedValue({ data: newNoteData } as any)
      const store = usePdfStore()
      vi.mocked(libraryApi.fetchPaperPdfInfoApi).mockResolvedValue(mockPdfInfo as any)
      await store.loadPdfInfo('p-1')
      const result = await store.createNote('New Note', 'New content')
      expect(result.id).toBe('n-3')
      expect(store.notes).toHaveLength(1)
      expect(store.notes[0].title).toBe('New Note')
    })

    it('未选择论文时应抛出错误', async () => {
      const store = usePdfStore()
      await expect(store.createNote('No paper', 'content')).rejects.toThrow('未选择论文')
    })
  })

  describe('updateNote', () => {
    it('应更新笔记内容', async () => {
      vi.mocked(libraryApi.fetchPaperNotesApi).mockResolvedValue({ data: mockNotesData } as any)
      const updateResp = { id: 'n-1', title: 'Updated', contentHtml: 'Updated Content', updatedAt: '2024-02-01T00:00:00Z' }
      vi.mocked(libraryApi.updateNoteApi).mockResolvedValue({ data: updateResp } as any)
      const store = usePdfStore()
      vi.mocked(libraryApi.fetchPaperPdfInfoApi).mockResolvedValue(mockPdfInfo as any)
      await store.loadPdfInfo('p-1')
      await store.loadNotes('p-1')
      await store.updateNote('n-1', 'Updated', 'Updated Content')
      const note = store.notes.find(n => n.id === 'n-1')
      expect(note?.title).toBe('Updated')
    })

    it('未选择论文时应抛出错误', async () => {
      const store = usePdfStore()
      await expect(store.updateNote('n-1', 'title', 'content')).rejects.toThrow('未选择论文')
    })
  })

  describe('resetPdf', () => {
    it('应重置所有 PDF 状态', () => {
      const store = usePdfStore()
      store.pdfInfo = mockPdfInfo as any
      store.notes = mockNotesData.items as any
      store.currentPaperId = 'p-1'
      store.resetPdf()
      expect(store.pdfInfo).toBeNull()
      expect(store.notes).toEqual([])
      expect(store.currentPaperId).toBeNull()
    })
  })
})
