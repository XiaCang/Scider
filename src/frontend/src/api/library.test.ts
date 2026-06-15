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

describe('library API', () => {
  let request: any

  beforeAll(async () => {
    const mod = await import('../network/request')
    request = mod.default
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchLibraryApi', () => {
    it('应发送 GET /papers', async () => {
      const { fetchLibraryApi } = await import('./library')
      request.get.mockResolvedValue({ data: [{ id: 'p-1', title: 'Paper' }] })
      await fetchLibraryApi()
      expect(request.get).toHaveBeenCalledWith('/papers')
    })
  })

  describe('fetchPaperByIdApi', () => {
    it('应发送 GET /papers/{id}', async () => {
      const { fetchPaperByIdApi } = await import('./library')
      const resp = { code: 0, msg: 'ok', data: { id: 'p-1', title: 'Test' } as any }
      request.get.mockResolvedValue(resp)
      const result = await fetchPaperByIdApi('p-1')
      expect(request.get).toHaveBeenCalledWith('/papers/p-1')
      expect(result.data.title).toBe('Test')
    })
  })

  describe('saveKeyPointsApi', () => {
    it('应发送 PATCH /papers/{id}/key-points', async () => {
      const { saveKeyPointsApi } = await import('./library')
      const kp = { background: 'bg', method: 'method', innovation: 'innov', conclusion: 'conc' }
      request.patch.mockResolvedValue({ code: 0, msg: 'ok' })
      await saveKeyPointsApi('p-1', kp)
      expect(request.patch).toHaveBeenCalledWith('/papers/p-1/key-points', { keyPoints: kp })
    })
  })

  describe('deletePaperApi', () => {
    it('应发送 DELETE /papers/{id}', async () => {
      const { deletePaperApi } = await import('./library')
      request.delete.mockResolvedValue({ code: 0, msg: 'ok' })
      await deletePaperApi('p-1')
      expect(request.delete).toHaveBeenCalledWith('/papers/p-1')
    })
  })

  describe('folder CRUD', () => {
    it('fetchFoldersApi — GET /folders/', async () => {
      const { fetchFoldersApi } = await import('./library')
      const resp = { code: 0, msg: 'ok', data: [{ id: 'f-1', name: 'ML' }] as any }
      request.get.mockResolvedValue(resp)
      const result = await fetchFoldersApi()
      expect(request.get).toHaveBeenCalledWith('/folders/')
      expect(result.data![0].name).toBe('ML')
    })

    it('createFolderApi — POST /folders/', async () => {
      const { createFolderApi } = await import('./library')
      const resp = { code: 0, msg: 'ok', data: { id: 'f-2', name: 'New' } as any }
      request.post.mockResolvedValue(resp)
      await createFolderApi({ name: 'New' })
      expect(request.post).toHaveBeenCalledWith('/folders/', { name: 'New' })
    })

    it('fetchFolderDetailApi — GET /folders/{id}', async () => {
      const { fetchFolderDetailApi } = await import('./library')
      request.get.mockResolvedValue({ code: 0, msg: 'ok', data: { id: 'f-1' } as any })
      await fetchFolderDetailApi('f-1')
      expect(request.get).toHaveBeenCalledWith('/folders/f-1')
    })

    it('createSubFolderApi — POST /folders/{id}/subfolders', async () => {
      const { createSubFolderApi } = await import('./library')
      request.post.mockResolvedValue({ id: 'f-1-1', name: 'Sub' } as any)
      await createSubFolderApi('f-1', { name: 'Sub' })
      expect(request.post).toHaveBeenCalledWith('/folders/f-1/subfolders', { name: 'Sub' })
    })

    it('updateFolderApi — PATCH /folders/{id}', async () => {
      const { updateFolderApi } = await import('./library')
      request.patch.mockResolvedValue({ code: 0, msg: 'ok' })
      await updateFolderApi('f-1', { name: 'Renamed' })
      expect(request.patch).toHaveBeenCalledWith('/folders/f-1', { name: 'Renamed' })
    })

    it('deleteFolderApi — DELETE /folders/{id}', async () => {
      const { deleteFolderApi } = await import('./library')
      request.delete.mockResolvedValue({ code: 0, msg: 'ok' })
      await deleteFolderApi('f-1')
      expect(request.delete).toHaveBeenCalledWith('/folders/f-1')
    })

    it('moveFolderApi — PATCH /folders/{id}/move', async () => {
      const { moveFolderApi } = await import('./library')
      request.patch.mockResolvedValue({ code: 0, msg: 'ok' })
      await moveFolderApi('f-1', 'f-2')
      expect(request.patch).toHaveBeenCalledWith('/folders/f-1/move', { parent_id: 'f-2' })
    })

    it('moveFolderApi 移动到根 — parent_id null', async () => {
      const { moveFolderApi } = await import('./library')
      request.patch.mockResolvedValue({ code: 0, msg: 'ok' })
      await moveFolderApi('f-1', null)
      expect(request.patch).toHaveBeenCalledWith('/folders/f-1/move', { parent_id: null })
    })

    it('copyFolderApi — POST /folders/{id}/copy', async () => {
      const { copyFolderApi } = await import('./library')
      request.post.mockResolvedValue({ id: 'f-copy', name: 'Copy' } as any)
      await copyFolderApi('f-1', null)
      expect(request.post).toHaveBeenCalledWith('/folders/f-1/copy', { target_parent_id: null })
    })
  })

  describe('paper-folder关联', () => {
    it('addPaperToFolderApi — POST /folders/{id}/papers', async () => {
      const { addPaperToFolderApi } = await import('./library')
      request.post.mockResolvedValue({ code: 0, msg: 'ok' })
      await addPaperToFolderApi('f-1', 'p-1')
      expect(request.post).toHaveBeenCalledWith('/folders/f-1/papers', { paper_id: 'p-1' })
    })

    it('removePaperFromFolderApi — DELETE /folders/{id}/papers/{paperId}', async () => {
      const { removePaperFromFolderApi } = await import('./library')
      request.delete.mockResolvedValue({ code: 0, msg: 'ok' })
      await removePaperFromFolderApi('f-1', 'p-1')
      expect(request.delete).toHaveBeenCalledWith('/folders/f-1/papers/p-1')
    })

    it('batchAddPapersToFolderApi — POST /folders/{id}/papers/batch', async () => {
      const { batchAddPapersToFolderApi } = await import('./library')
      request.post.mockResolvedValue({ code: 0, msg: 'ok' })
      await batchAddPapersToFolderApi('f-1', ['p-1', 'p-2'])
      expect(request.post).toHaveBeenCalledWith('/folders/f-1/papers/batch', { paper_ids: ['p-1', 'p-2'] })
    })

    it('fetchFolderPapersApi — GET /folders/{id}/papers', async () => {
      const { fetchFolderPapersApi } = await import('./library')
      request.get.mockResolvedValue([{ id: 'p-1' }] as any)
      await fetchFolderPapersApi('f-1')
      expect(request.get).toHaveBeenCalledWith('/folders/f-1/papers')
    })

    it('movePaperToFolderApi — PATCH /papers/{id}/folder', async () => {
      const { movePaperToFolderApi } = await import('./library')
      request.patch.mockResolvedValue({ code: 0, msg: 'ok' })
      await movePaperToFolderApi('p-1', 'f-1')
      expect(request.patch).toHaveBeenCalledWith('/papers/p-1/folder', { folder_id: 'f-1' })
    })
  })

  describe('PDF预览', () => {
    it('fetchPaperPdfInfoApi — GET /papers/{id}/pdf-info', async () => {
      const { fetchPaperPdfInfoApi } = await import('./library')
      const mockInfo = { id: 'p-1', title: 'Test', pdfUrl: '/pdfs/test.pdf', pageCount: 5 }
      request.get.mockResolvedValue(mockInfo)
      const result = await fetchPaperPdfInfoApi('p-1')
      expect(request.get).toHaveBeenCalledWith('/papers/p-1/pdf-info')
      expect(result.title).toBe('Test')
    })

    it('fetchPaperPdfFileApi — GET /papers/{id}/pdf-file blob', async () => {
      const { fetchPaperPdfFileApi } = await import('./library')
      const blob = new Blob(['pdf data'], { type: 'application/pdf' })
      request.get.mockResolvedValue(blob)
      const result = await fetchPaperPdfFileApi('p-1')
      expect(request.get).toHaveBeenCalledWith('/papers/p-1/pdf-file', { responseType: 'blob' })
      expect(result).toBeInstanceOf(Blob)
    })
  })

  describe('笔记操作', () => {
    it('fetchPaperNotesApi — GET /notes/', async () => {
      const { fetchPaperNotesApi } = await import('./library')
      const resp = { code: 0, msg: 'ok', data: { total: 1, items: [{ id: 'n-1' }] as any } }
      request.get.mockResolvedValue(resp)
      const result = await fetchPaperNotesApi('p-1', 1, 20)
      expect(request.get).toHaveBeenCalledWith('/notes/', { params: { paperId: 'p-1', page: 1, pageSize: 20 } })
      expect(result.data.total).toBe(1)
    })

    it('createNoteApi — POST /notes/', async () => {
      const { createNoteApi } = await import('./library')
      const data = { paperId: 'p-1', title: 'Note', contentHtml: '<p>hi</p>', contentFormat: 'html' }
      request.post.mockResolvedValue({ code: 0, msg: 'ok', data: { id: 'n-1' } as any })
      await createNoteApi(data)
      expect(request.post).toHaveBeenCalledWith('/notes/', data)
    })

    it('fetchNoteDetailApi — GET /notes/{id}', async () => {
      const { fetchNoteDetailApi } = await import('./library')
      request.get.mockResolvedValue({ code: 0, msg: 'ok', data: { id: 'n-1', title: 'Note' } as any })
      await fetchNoteDetailApi('n-1')
      expect(request.get).toHaveBeenCalledWith('/notes/n-1')
    })

    it('updateNoteApi — PATCH /notes/{id}', async () => {
      const { updateNoteApi } = await import('./library')
      const data = { title: 'Updated', contentHtml: '<p>new</p>', contentFormat: 'html' }
      request.patch.mockResolvedValue({ code: 0, msg: 'ok', data: { id: 'n-1' } as any })
      await updateNoteApi('n-1', data)
      expect(request.patch).toHaveBeenCalledWith('/notes/n-1', data)
    })

    it('deleteNoteApi — DELETE /notes/{id}', async () => {
      const { deleteNoteApi } = await import('./library')
      request.delete.mockResolvedValue({ code: 0, msg: 'ok', data: null })
      await deleteNoteApi('n-1')
      expect(request.delete).toHaveBeenCalledWith('/notes/n-1')
    })

    it('uploadNoteImageApi — POST /notes/uploads 含 FormData', async () => {
      const { uploadNoteImageApi } = await import('./library')
      const file = new File(['img'], 'img.png', { type: 'image/png' })
      const resp = { code: 0, msg: 'ok', data: { url: '/uploads/img.png' } as any }
      request.post.mockResolvedValue(resp)
      await uploadNoteImageApi('p-1', 'n-1', file)
      expect(request.post).toHaveBeenCalledWith('/notes/uploads?paperId=p-1&noteId=n-1', expect.any(FormData))
    })

    it('fetchNoteImagesApi — GET /notes/{id}/images', async () => {
      const { fetchNoteImagesApi } = await import('./library')
      const resp = { code: 0, msg: 'ok', data: { total: 1, items: [{ id: 'img-1' }] as any } }
      request.get.mockResolvedValue(resp)
      await fetchNoteImagesApi('n-1')
      expect(request.get).toHaveBeenCalledWith('/notes/n-1/images')
    })
  })

  describe('PDF上传', () => {
    it('uploadPaperApi — POST /papers/upload 含 FormData', async () => {
      const { uploadPaperApi } = await import('./library')
      const file = new File(['pdf'], 'paper.pdf', { type: 'application/pdf' })
      const resp = { code: 0, msg: 'ok', data: { paper_id: 'p-1', filename: 'paper.pdf', file_size: 3, md5: 'abc', status: 'ok', task_id: 't-1' } }
      request.post.mockResolvedValue(resp)
      const result = await uploadPaperApi(file)
      expect(request.post).toHaveBeenCalledWith('/papers/upload', expect.any(FormData), {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      expect(result.data.paper_id).toBe('p-1')
    })

    it('batchUploadPapersApi — POST /papers/upload 多文件', async () => {
      const { batchUploadPapersApi } = await import('./library')
      const files = [new File(['a'], 'a.pdf'), new File(['b'], 'b.pdf')]
      request.post.mockResolvedValue({ code: 0, msg: 'ok', data: { total: 2, success_count: 2, results: [] as any[] } })
      await batchUploadPapersApi(files)
      expect(request.post).toHaveBeenCalledWith('/papers/upload', expect.any(FormData), {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    })
  })

  describe('PDF搜索', () => {
    it('searchInPaperApi — POST /papers/{id}/search', async () => {
      const { searchInPaperApi } = await import('./library')
      const data = { keyword: 'transformer', page_number: 1, limit: 10 }
      const resp = { code: 0, msg: 'ok', data: { keyword: 'transformer', total_results: 2, results: [{ page_number: 1, content: 'transformer model', score: 0.9, highlights: ['transformer'] }] } }
      request.post.mockResolvedValue(resp)
      const result = await searchInPaperApi('p-1', data)
      expect(request.post).toHaveBeenCalledWith('/papers/p-1/search', data)
      expect(result.data.total_results).toBe(2)
    })
  })
})
