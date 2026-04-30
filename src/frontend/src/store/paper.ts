// stores/paper.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LibraryPaper, PaperKeyPoints } from '../types/library'
import {
  fetchLibraryApi,
  saveKeyPointsApi,
  movePaperToFolderApi,
} from '../api/library'

export const usePaperStore = defineStore('paper', () => {
  // 全量论文缓存
  const papers = ref<LibraryPaper[]>([])
  const loading = ref(false)

  // 论文ID快速查找
  const paperMap = computed(() => {
    const map = new Map<string, LibraryPaper>()
    papers.value.forEach(p => map.set(p.id, p))
    return map
  })

  // 加载所有论文
  async function loadPapers() {
    loading.value = true
    try {
      const { data } = await fetchLibraryApi()
      papers.value = data
    } finally {
      loading.value = false
    }
  }

  // 保存一篇论文的关键点（同时更新本地）
  async function saveKeyPoints(paperId: string, keyPoints: PaperKeyPoints) {
    await saveKeyPointsApi(paperId, keyPoints)
    const paper = paperMap.value.get(paperId)
    if (paper) {
      paper.keyPoints = { ...keyPoints }
    }
  }

  // 将论文移动到指定文件夹（仅负责调用 API，文件夹的 paperIds 由 folderStore 更新）
  async function movePaperToFolder(paperId: string, folderId: string | null) {
    await movePaperToFolderApi(paperId, folderId)
    // 通知文件夹 Store 更新（通过调用方或事件，此处不直接耦合）
    // 组件中可组合 useFolderStore 并调用其 refresh 方法
  }

  // 根据 ID 列表获取论文对象（供 folderStore 使用）
  function getPapersByIds(ids: string[]): LibraryPaper[] {
    return ids.map(id => paperMap.value.get(id)).filter(Boolean) as LibraryPaper[]
  }

  return {
    papers,
    loading,
    paperMap,
    loadPapers,
    saveKeyPoints,
    movePaperToFolder,
    getPapersByIds,
  }
})