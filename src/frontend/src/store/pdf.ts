import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { PaperPdfInfo, NoteListItem } from '../types/library'
import {
  fetchPaperPdfInfoApi,
  fetchPaperNotesApi,
  createNoteApi,
  updateNoteApi,
} from '../api/library'

export const usePdfStore = defineStore('pdf', () => {
  const pdfInfo = ref<PaperPdfInfo | null>(null)
  const notes = ref<NoteListItem[]>([])
  const currentPaperId = ref<string | null>(null)
  const loading = ref(false)

  async function loadPdfInfo(paperId: string) {
    loading.value = true
    currentPaperId.value = paperId
    try {
      const data = await fetchPaperPdfInfoApi(paperId)
      pdfInfo.value = data as any
    } finally {
      loading.value = false
    }
  }

  async function loadNotes(paperId: string) {
    const resp = await fetchPaperNotesApi(paperId)
    const data = (resp as any).data || resp
    notes.value = data.items || []
  }

  async function createNote(title: string, contentHtml: string) {
    if (!currentPaperId.value) throw new Error('未选择论文')
    const resp = await createNoteApi({
      paperId: currentPaperId.value,
      title,
      contentHtml,
      contentFormat: 'markdown',
    })
    const data = (resp as any).data || resp
    notes.value.unshift({
      id: data.id,
      paperId: currentPaperId.value,
      title: data.title || title,
      excerpt: contentHtml.slice(0, 100),
      firstImageUrl: null,
      updatedAt: data.updatedAt || new Date().toISOString(),
    })
    return data
  }

  async function updateNote(noteId: string, title: string, contentHtml: string) {
    if (!currentPaperId.value) throw new Error('未选择论文')
    const resp = await updateNoteApi(noteId, { title, contentHtml, contentFormat: 'markdown' })
    const data = (resp as any).data || resp
    const idx = notes.value.findIndex(n => n.id === noteId)
    if (idx !== -1) {
      notes.value[idx].title = title
      notes.value[idx].excerpt = contentHtml.slice(0, 100)
      notes.value[idx].updatedAt = data.updatedAt || new Date().toISOString()
    }
    return data
  }

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
