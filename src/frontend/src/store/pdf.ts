// stores/pdf.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { PaperPdfInfo, PaperNote } from '../types/library'
import {
  fetchPaperPdfInfoApi,
  fetchPaperNotesApi,
  createNoteApi,
  updateNoteApi,
} from '../api/library'

export const usePdfStore = defineStore('pdf', () => {
  const pdfInfo = ref<PaperPdfInfo | null>(null)
  const notes = ref<PaperNote[]>([])
  const currentPaperId = ref<string | null>(null)   // 当前正在阅读的论文 ID
  const loading = ref(false)

  // 根据论文加载 PDF 信息
  async function loadPdfInfo(paperId: string) {
    loading.value = true
    currentPaperId.value = paperId
    try {
      const data = await fetchPaperPdfInfoApi(paperId)
      pdfInfo.value = data
    } finally {
      loading.value = false
    }
  }

  // 加载该论文的所有笔记
  async function loadNotes(paperId: string) {
    const data = await fetchPaperNotesApi(paperId)
    notes.value = data
  }

  // 创建笔记
  async function createNote(content: string, pageNumber: number, selectedText?: string) {
    if (!currentPaperId.value) throw new Error('未选择论文')
    const data = await createNoteApi(currentPaperId.value, {
      content,
      pageNumber,
      selectedText,
    })
    notes.value.push(data)
    return data
  }

  // 更新笔记
  async function updateNote(noteId: string, content: string) {
    if (!currentPaperId.value) throw new Error('未选择论文')
    const data = await updateNoteApi(currentPaperId.value, noteId, { content })
    const idx = notes.value.findIndex(n => n.id === noteId)
    if (idx !== -1) notes.value[idx] = data
    return data
  }

  // 清空（切换论文时重置）
  function resetPdf() {
    pdfInfo.value = null
    notes.value = []
    currentPaperId.value = null
  }

  return {
    pdfInfo,
    notes,
    currentPaperId,
    loading,
    loadPdfInfo,
    loadNotes,
    createNote,
    updateNote,
    resetPdf,
  }
})