import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useFolderStore } from './folder'
import { usePaperStore } from './paper'
import * as libraryApi from '../api/library'

vi.mock('../api/library', () => ({
  fetchFoldersApi: vi.fn(),
  createFolderApi: vi.fn(),
  createSubFolderApi: vi.fn(),
  updateFolderApi: vi.fn(),
  deleteFolderApi: vi.fn(),
  moveFolderApi: vi.fn(),
  copyFolderApi: vi.fn(),
  addPaperToFolderApi: vi.fn(),
  removePaperFromFolderApi: vi.fn(),
  batchAddPapersToFolderApi: vi.fn(),
  fetchFolderPapersApi: vi.fn(),
}))

const mockFolders = [
  {
    id: 'f-1',
    name: '机器学习',
    created_at: '2024-01-01T00:00:00Z',
    children: [
      { id: 'f-1-1', name: '深度学习', created_at: '2024-01-02T00:00:00Z' },
    ],
  },
  { id: 'f-2', name: '自然语言处理', created_at: '2024-01-03T00:00:00Z' },
]

describe('folderStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // 辅助：深拷贝 mock 数据以避免测试间突变
  function cloneFolders() {
    return JSON.parse(JSON.stringify(mockFolders))
  }

  describe('初始状态', () => {
    it('应初始化为空', () => {
      const store = useFolderStore()
      expect(store.folders).toEqual([])
      expect(store.currentFolderId).toBeNull()
      expect(store.loading).toBe(false)
    })
  })

  describe('loadFolders', () => {
    it('应加载文件夹树', async () => {
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: mockFolders } as any)
      const store = useFolderStore()
      await store.loadFolders()
      expect(store.folders).toHaveLength(2)
      expect(store.loading).toBe(false)
    })

    it('加载失败应抛出错误', async () => {
      vi.mocked(libraryApi.fetchFoldersApi).mockRejectedValue(new Error('Network Error'))
      const store = useFolderStore()
      await expect(store.loadFolders()).rejects.toThrow('Network Error')
      expect(store.loading).toBe(false)
    })
  })

  describe('currentFolder', () => {
    it('未设置时应返回 null', () => {
      const store = useFolderStore()
      expect(store.currentFolder).toBeNull()
    })

    it('应返回当前选中的文件夹', async () => {
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: mockFolders } as any)
      const store = useFolderStore()
      await store.loadFolders()
      store.setCurrentFolder('f-1')
      expect(store.currentFolder?.name).toBe('机器学习')
    })

    it('不存在的 ID 应返回 null', () => {
      const store = useFolderStore()
      store.setCurrentFolder('not-exists')
      expect(store.currentFolder).toBeNull()
    })
  })

  describe('createRootFolder', () => {
    it('应创建根文件夹并加入列表', async () => {
      const newFolder = { id: 'f-3', name: '新文件夹', created_at: '2024-02-01T00:00:00Z' }
      vi.mocked(libraryApi.createFolderApi).mockResolvedValue({ data: newFolder } as any)
      const store = useFolderStore()
      await store.createRootFolder('新文件夹')
      expect(store.folders).toHaveLength(1)
      expect(store.folders[0].name).toBe('新文件夹')
    })
  })

  describe('createSubFolder', () => {
    it('应创建子文件夹', async () => {
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: cloneFolders() } as any)
      vi.mocked(libraryApi.createSubFolderApi).mockResolvedValue({ id: 'f-1-2', name: 'CNN', created_at: '2024-02-01T00:00:00Z' } as any)
      const store = useFolderStore()
      await store.loadFolders()
      await store.createSubFolder('f-1', 'CNN')
      const parent = store.folders[0]
      expect(parent.children).toHaveLength(2)
      expect(parent.children![1].name).toBe('CNN')
    })
  })

  describe('renameFolder', () => {
    it('应重命名文件夹', async () => {
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: cloneFolders() } as any)
      vi.mocked(libraryApi.updateFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()
      await store.renameFolder('f-1', 'ML')
      expect(store.folders[0].name).toBe('ML')
    })
  })

  describe('deleteFolder', () => {
    it('应删除文件夹并从树中移除', async () => {
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: cloneFolders() } as any)
      vi.mocked(libraryApi.deleteFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()
      await store.deleteFolder('f-2')
      expect(store.folders).toHaveLength(1)
    })

    it('删除当前打开的文件夹应重置 currentFolderId', async () => {
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: cloneFolders() } as any)
      vi.mocked(libraryApi.deleteFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()
      store.setCurrentFolder('f-1')
      await store.deleteFolder('f-1')
      expect(store.currentFolderId).toBeNull()
    })
  })

  describe('moveFolder', () => {
    it('应移动文件夹到新的父文件夹', async () => {
      const folders = cloneFolders()
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: folders } as any)
      vi.mocked(libraryApi.moveFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()

      expect(store.folders).toHaveLength(2)
      await store.moveFolder('f-2', 'f-1')
      expect(store.folders).toHaveLength(1)
      expect(store.folders[0].children).toHaveLength(2)
    })

    it('移动到 null 应将文件夹移到根级别', async () => {
      const nestedFolders = [
        { id: 'root', name: 'Root', created_at: '', paperIds: [] as string[], children: [{ id: 'child', name: 'Child', created_at: '', paperIds: [] as string[] }] },
      ]
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: nestedFolders } as any)
      vi.mocked(libraryApi.moveFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()
      await store.moveFolder('child', null)
      expect(store.folders).toHaveLength(2)
      expect(store.folders[1].id).toBe('child')
    })
  })

  describe('addPaperToFolder', () => {
    it('应将论文 ID 添加到文件夹', async () => {
      const folders = cloneFolders()
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: folders } as any)
      vi.mocked(libraryApi.addPaperToFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()
      await store.addPaperToFolder('f-1', 'p-1')
      expect(store.folders[0].paperIds).toContain('p-1')
    })

    it('重复添加不应产生重复 ID', async () => {
      const folders = cloneFolders()
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: folders } as any)
      vi.mocked(libraryApi.addPaperToFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()
      await store.addPaperToFolder('f-1', 'p-1')
      await store.addPaperToFolder('f-1', 'p-1')
      expect(store.folders[0].paperIds).toHaveLength(1)
    })
  })

  describe('removePaperFromFolder', () => {
    it('应从文件夹移除论文 ID', async () => {
      const foldersWithPaper = [
        { id: 'f-1', name: 'Test', created_at: '', paperIds: ['p-1', 'p-2'] },
      ]
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: foldersWithPaper } as any)
      vi.mocked(libraryApi.removePaperFromFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()
      await store.removePaperFromFolder('f-1', 'p-1')
      expect(store.folders[0].paperIds).toEqual(['p-2'])
    })
  })

  describe('removePaperGlobally', () => {
    it('应从所有文件夹移除指定论文', () => {
      const foldersWithPaper = [
        {
          id: 'f-1', name: 'A', created_at: '',
          paperIds: ['p-1', 'p-2'],
          children: [{ id: 'f-1-1', name: 'A1', created_at: '', paperIds: ['p-1'] }],
        },
        { id: 'f-2', name: 'B', created_at: '', paperIds: ['p-1', 'p-3'] },
      ]
      const store = useFolderStore()
      store.folders = foldersWithPaper as any
      store.removePaperGlobally('p-1')
      expect(store.folders[0].paperIds).toEqual(['p-2'])
      expect(store.folders[0].children![0].paperIds).toEqual([])
      expect(store.folders[1].paperIds).toEqual(['p-3'])
    })
  })

  describe('batchAddPapersToFolder', () => {
    it('应批量添加论文到文件夹', async () => {
      const folders = cloneFolders()
      vi.mocked(libraryApi.fetchFoldersApi).mockResolvedValue({ data: folders } as any)
      vi.mocked(libraryApi.batchAddPapersToFolderApi).mockResolvedValue({} as any)
      const store = useFolderStore()
      await store.loadFolders()
      await store.batchAddPapersToFolder('f-1', ['p-1', 'p-2', 'p-3'])
      expect(store.folders[0].paperIds).toHaveLength(3)
    })
  })
})
