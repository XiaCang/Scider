// stores/folder.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Folder } from '../types/folder'
import {
  fetchFoldersApi,
  createFolderApi,
  createSubFolderApi,
  updateFolderApi,
  deleteFolderApi,
  moveFolderApi,
  copyFolderApi,
  addPaperToFolderApi,
  removePaperFromFolderApi,
  batchAddPapersToFolderApi,
  fetchFolderPapersApi,
} from '../api/library'
import { usePaperStore } from './paper'
import { testFolders, testPapers } from '../test/test_data'

// 辅助函数：递归查找文件夹
function findFolderById(tree: Folder[], id: string): Folder | undefined {
  for (const node of tree) {
    if (node.id === id) return node
    if (node.children) {
      const found = findFolderById(node.children, id)
      if (found) return found
    }
  }
  return undefined
}

// 辅助函数：从树中移除指定文件夹并返回被移除的节点
function extractFolderFromTree(tree: Folder[], id: string): Folder | undefined {
  const index = tree.findIndex(f => f.id === id)
  if (index !== -1) {
    return tree.splice(index, 1)[0]
  }
  for (const node of tree) {
    if (node.children) {
      const extracted = extractFolderFromTree(node.children, id)
      if (extracted) return extracted
    }
  }
  return undefined
}

// 辅助函数：从树中删除指定文件夹（递归）
function removeFolderFromTree(tree: Folder[], id: string): boolean {
  const index = tree.findIndex(f => f.id === id)
  if (index !== -1) {
    tree.splice(index, 1)
    return true
  }
  for (const node of tree) {
    if (node.children && removeFolderFromTree(node.children, id)) {
      return true
    }
  }
  return false
}

// 辅助函数：从所有文件夹中移除指定论文ID
function removePaperFromAllFolders(tree: Folder[], paperId: string) {
  for (const node of tree) {
    const idx = node.paperIds.indexOf(paperId)
    if (idx !== -1) node.paperIds.splice(idx, 1)
    if (node.children) removePaperFromAllFolders(node.children, paperId)
  }
}

export const useFolderStore = defineStore('folder', () => {
  const folders = ref<Folder[]>([])
  const currentFolderId = ref<string | null>(null)
  const loading = ref(false)

  const currentFolder = computed(() => {
    if (!currentFolderId.value) return null
    return findFolderById(folders.value, currentFolderId.value) || null
  })

  // 当前文件夹下的论文列表（借用 paperStore）
  const currentFolderPapers = computed(() => {
    if (!currentFolder.value) return []
    const paperStore = usePaperStore()
    return paperStore.getPapersByIds(currentFolder.value.paperIds)
  })

  // 加载文件夹树
  async function loadFolders() {
    loading.value = true
    try {
      const data = await fetchFoldersApi()
      folders.value = data
    } finally {
      loading.value = false
    }
  }

  async function createRootFolder(name: string, userId: string) {
    const data = await createFolderApi({ name, user_id: userId })
    folders.value.push(data)
  }

  async function createSubFolder(parentId: string, name: string) {
    const data = await createSubFolderApi(parentId, { name })
    const parent = findFolderById(folders.value, parentId)
    if (parent) {
      if (!parent.children) parent.children = []
      parent.children.push(data)
    }
  }

  async function renameFolder(folderId: string, name: string) {
    await updateFolderApi(folderId, { name })
    const folder = findFolderById(folders.value, folderId)
    if (folder) folder.name = name
  }

  async function deleteFolder(folderId: string) {
    await deleteFolderApi(folderId)
    removeFolderFromTree(folders.value, folderId)
    if (currentFolderId.value === folderId) currentFolderId.value = null
  }

  async function moveFolder(folderId: string, newParentId: string | null) {
    await moveFolderApi(folderId, newParentId)
    const moved = extractFolderFromTree(folders.value, folderId)
    if (moved) {
      if (newParentId) {
        const parent = findFolderById(folders.value, newParentId)
        parent?.children?.push(moved)
      } else {
        folders.value.push(moved)
      }
    }
  }

  async function copyFolder(folderId: string, targetParentId: string | null) {
    const data = await copyFolderApi(folderId, targetParentId)
    if (targetParentId) {
      const parent = findFolderById(folders.value, targetParentId)
      if (parent) {
        if (!parent.children) parent.children = []
        parent.children.push(data)
      }
    } else {
      folders.value.push(data)
    }
  }

  // 论文与文件夹关联
  async function addPaperToFolder(folderId: string, paperId: string) {
    await addPaperToFolderApi(folderId, paperId)
    const folder = findFolderById(folders.value, folderId)
    if (folder && !folder.paperIds.includes(paperId)) {
      folder.paperIds.push(paperId)
    }
  }

  async function removePaperFromFolder(folderId: string, paperId: string) {
    await removePaperFromFolderApi(folderId, paperId)
    const folder = findFolderById(folders.value, folderId)
    if (folder) {
      const idx = folder.paperIds.indexOf(paperId)
      if (idx !== -1) folder.paperIds.splice(idx, 1)
    }
  }

  async function batchAddPapersToFolder(folderId: string, paperIds: string[]) {
    await batchAddPapersToFolderApi(folderId, paperIds)
    const folder = findFolderById(folders.value, folderId)
    if (folder) {
      const set = new Set(folder.paperIds)
      paperIds.forEach(id => set.add(id))
      folder.paperIds = Array.from(set)
    }
  }

  // 移除论文在所有文件夹中的引用（配合 paperStore 的移动）
  function removePaperGlobally(paperId: string) {
    removePaperFromAllFolders(folders.value, paperId)
  }

  // 将论文加入指定文件夹（删除旧关联后添加，内部调用 remove+add）
  async function movePaperIntoFolder(paperId: string, targetFolderId: string | null) {
    removePaperGlobally(paperId)
    if (targetFolderId) {
      await addPaperToFolder(targetFolderId, paperId)
    }
  }

  async function loadFolderPapers(folderId: string) {
    const data = await fetchFolderPapersApi(folderId)
    const paperStore = usePaperStore()
    data.forEach(fp => {
      const idx = paperStore.papers.findIndex(p => p.id === fp.id)
      if (idx === -1) paperStore.papers.push(fp)
      else paperStore.papers[idx] = fp
    })
  }

  function setCurrentFolder(id: string | null) {
    currentFolderId.value = id
  }

  function loadTestData() {
    const paperStore = usePaperStore()
    // 深拷贝测试数据以避免引用污染
    paperStore.papers = JSON.parse(JSON.stringify(testPapers))
    folders.value = JSON.parse(JSON.stringify(testFolders))
    currentFolderId.value = null // 重置选中为“全部”
  }


  return {
    folders,
    currentFolderId,
    loading,
    currentFolder,
    currentFolderPapers,
    loadFolders,
    createRootFolder,
    createSubFolder,
    renameFolder,
    deleteFolder,
    moveFolder,
    copyFolder,
    addPaperToFolder,
    removePaperFromFolder,
    batchAddPapersToFolder,
    removePaperGlobally,
    movePaperIntoFolder,
    loadFolderPapers,
    setCurrentFolder,
    loadTestData
  }
})