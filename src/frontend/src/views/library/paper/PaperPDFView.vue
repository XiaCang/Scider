<script setup lang="ts">
import { ArrowLeft, Edit, Document, ZoomIn, ZoomOut, FullScreen, Search, ChatDotSquare, Plus, Delete as DeleteIcon } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, onUnmounted, ref, watch, nextTick, shallowRef, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as pdfjsLib from 'pdfjs-dist'

// 配置 PDF.js worker - 使用 CDN 上的 ES module worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.mjs`

import MarkdownEditor from '../../../components/MarkdownEditor.vue'
import type { PaperNote, NoteListItem, PaperPdfInfo } from '../../../types/library'
import {
  fetchPaperPdfInfoApi,
  fetchPaperPdfFileApi,
  fetchPaperNotesApi,
  createNoteApi,
  updateNoteApi,
  fetchNoteDetailApi,
} from '../../../api/library'
import PdfSearchPanel from '../../../components/PdfSearchPanel.vue'
import AiChatPanel from '../../../components/AiChatPanel.vue'
import PdfContextMenu from '../../../components/PdfContextMenu.vue'

const route = useRoute()
const router = useRouter()
const paperId = computed(() => route.params.paperId as string)

// PDF 信息
const paperTitle = ref('')
const pdfUrl = ref('')
const pageCount = ref(0)

// 连续滚动相关
const pdfDoc = shallowRef<any>(null)
const pagesContainer = ref<HTMLElement | null>(null)
const totalPages = ref(0)
let isScrolling = false
let rafId: number | null = null

// 缩放比例
const zoomScale = ref(1.0)
const zoomLevel = computed({
  get: () => Math.round(zoomScale.value * 100),
  set: (val) => { zoomScale.value = val / 100 }
})

const currentPage = ref(1)
const jumpPageInput = ref('')

// ============ 多笔记支持 ============
const noteList = ref<NoteListItem[]>([])
const activeNoteId = ref<string | null>(null)
const activeNote = ref<PaperNote | null>(null)
const noteContent = ref('')
const noteTitle = ref('')
const noteSaving = ref(false)
let saveTimer: ReturnType<typeof setTimeout> | null = null

// ============ 侧栏显隐 ============
const showNoteSidebar = ref(true)
const showAiSidebar = ref(false)

// UI 状态
const isMobile = ref(window.innerWidth < 900)
const pdfLoading = ref(true)
const pdfError = ref('')
const showSearchInline = ref(false)
let pdfObjectUrl = ''

// 笔记栏宽度调整
const NOTE_SIDEBAR_MIN_WIDTH = 200
const NOTE_SIDEBAR_MAX_WIDTH = 600
const noteSidebarWidth = ref(270)
const isResizing = ref(false)

// AI 侧栏宽度调整
const AI_SIDEBAR_MIN_WIDTH = 240
const AI_SIDEBAR_MAX_WIDTH = 600
const aiSidebarWidth = ref(320)
const isAiResizing = ref(false)
let aiResizeRaf: number | null = null

const startAiResize = (e: MouseEvent) => {
  e.preventDefault()
  isAiResizing.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  const startX = e.clientX
  const startWidth = aiSidebarWidth.value

  const onMouseMove = (ev: MouseEvent) => {
    if (aiResizeRaf !== null) cancelAnimationFrame(aiResizeRaf)
    aiResizeRaf = requestAnimationFrame(() => {
      const delta = ev.clientX - startX
      aiSidebarWidth.value = Math.min(
        AI_SIDEBAR_MAX_WIDTH,
        Math.max(AI_SIDEBAR_MIN_WIDTH, startWidth + delta)
      )
      aiResizeRaf = null
    })
  }

  const onMouseUp = () => {
    isAiResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    if (aiResizeRaf !== null) cancelAnimationFrame(aiResizeRaf)
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// 右键菜单
const contextMenu = ref({ visible: false, x: 0, y: 0, text: '' })
const aiChatRef = ref<InstanceType<typeof AiChatPanel> | null>(null)

// ============ 笔记栏拖拽调整宽度 ============
const startResize = (e: MouseEvent) => {
  e.preventDefault()
  isResizing.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  const startX = e.clientX
  const startWidth = noteSidebarWidth.value

  const onMouseMove = (ev: MouseEvent) => {
    const delta = startX - ev.clientX
    const newWidth = Math.min(NOTE_SIDEBAR_MAX_WIDTH, Math.max(NOTE_SIDEBAR_MIN_WIDTH, startWidth + delta))
    noteSidebarWidth.value = newWidth
  }

  const onMouseUp = () => {
    isResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// ============ 笔记操作 ============
const loadNotes = async () => {
  try {
    const resp = await fetchPaperNotesApi(paperId.value)
    const data = ('data' in resp ? (resp as any).data : resp) as any
    noteList.value = data.items || []
    if (noteList.value.length > 0) {
      await selectNote(noteList.value[0].id)
    } else {
      activeNoteId.value = null
      activeNote.value = null
      noteContent.value = ''
      noteTitle.value = ''
    }
  } catch (e) {
    console.error('加载笔记列表失败:', e)
  }
}

const selectNote = async (noteId: string) => {
  activeNoteId.value = noteId
  try {
    const resp = await fetchNoteDetailApi(noteId)
    const data = ('data' in resp ? (resp as any).data : resp) as any
    const note = data.data || data
    activeNote.value = note
    noteContent.value = note.contentHtml || ''
    noteTitle.value = note.title || ''
  } catch (e) {
    console.error('加载笔记详情失败:', e)
    // 降级：从 noteList 中获取 excerpt
    const item = noteList.value.find(n => n.id === noteId)
    if (item) {
      noteContent.value = item.excerpt || ''
      noteTitle.value = item.title || ''
    }
  }
}

const createNote = async () => {
  try {
    const resp = await createNoteApi({
      paperId: paperId.value,
      title: '新笔记',
      contentHtml: '',
      contentFormat: 'markdown',
    })
    const data = ('data' in resp ? (resp as any).data : resp) as any
    const newNote = data.data || data
    noteList.value.unshift({
      id: newNote.id,
      paperId: paperId.value,
      title: newNote.title || '新笔记',
      excerpt: '',
      firstImageUrl: null,
      updatedAt: newNote.updatedAt || new Date().toISOString(),
    })
    await selectNote(newNote.id)
    ElMessage.success('已创建新笔记')
  } catch (e) {
    ElMessage.error('创建笔记失败')
    console.error(e)
  }
}

const deleteNote = async (noteId: string) => {
  try {
    await ElMessageBox.confirm('确定删除此笔记？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    // API 暂未提供删除接口，前端先移除
    noteList.value = noteList.value.filter(n => n.id !== noteId)
    if (activeNoteId.value === noteId) {
      if (noteList.value.length > 0) {
        await selectNote(noteList.value[0].id)
      } else {
        activeNoteId.value = null
        activeNote.value = null
        noteContent.value = ''
        noteTitle.value = ''
      }
    }
    ElMessage.success('笔记已删除')
  } catch {
    // 用户取消
  }
}

const autoSaveNote = async () => {
  if (!activeNoteId.value || !noteContent.value.trim()) return
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    noteSaving.value = true
    try {
      await updateNoteApi(activeNoteId.value!, {
        title: noteTitle.value || '笔记',
        contentHtml: noteContent.value,
        contentFormat: 'markdown',
      })
      // 更新 noteList 中的标题和摘录
      const item = noteList.value.find(n => n.id === activeNoteId.value)
      if (item) {
        item.title = noteTitle.value || '笔记'
        item.excerpt = noteContent.value.slice(0, 100)
        item.updatedAt = new Date().toISOString()
      }
    } catch (e) {
      ElMessage.error('自动保存失败')
      console.error(e)
    } finally {
      noteSaving.value = false
    }
  }, 500)
}
watch(noteContent, () => autoSaveNote())
watch(noteTitle, () => autoSaveNote())

// ============ 侧栏切换 ============
const toggleNoteSidebar = () => {
  showNoteSidebar.value = !showNoteSidebar.value
}
const toggleAiSidebar = () => {
  showAiSidebar.value = !showAiSidebar.value
}

// ============ 右键菜单 ============
const handlePdfContextMenu = (e: MouseEvent) => {
  // 检查是否选中了文字
  const selection = window.getSelection()
  const text = selection?.toString().trim() || ''
  if (text) {
    contextMenu.value = {
      visible: true,
      x: e.clientX,
      y: e.clientY,
      text,
    }
    e.preventDefault()
  }
}

const handleAskAiFromContext = (text: string) => {
  // 打开 AI 侧栏并发送文本
  showAiSidebar.value = true
  nextTick(() => {
    aiChatRef.value?.askWithContext(text)
  })
}

const closeContextMenu = () => {
  contextMenu.value.visible = false
}

// ============ 原有功能（缩放、滚动、渲染等保持不变）============
const handleResize = () => {
  isMobile.value = window.innerWidth < 900
}

const updateCurrentPageFromScroll = () => {
  if (!pagesContainer.value) return
  const containerRect = pagesContainer.value.getBoundingClientRect()
  const containerCenter = containerRect.top + containerRect.height / 2
  let minDistance = Infinity
  let closestPage = 1
  const wrappers = pagesContainer.value.querySelectorAll('.pdf-page-wrapper')
  wrappers.forEach((wrapper, idx) => {
    const rect = wrapper.getBoundingClientRect()
    const pageCenter = rect.top + rect.height / 2
    const distance = Math.abs(containerCenter - pageCenter)
    if (distance < minDistance) {
      minDistance = distance
      closestPage = idx + 1
    }
  })
  if (closestPage !== currentPage.value) {
    currentPage.value = closestPage
  }
}

const handleScroll = () => {
  if (isScrolling) return
  if (rafId !== null) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(() => {
    updateCurrentPageFromScroll()
    rafId = null
  })
}

// ============ 渲染任务管理 ============
let renderGeneration = 0

const renderAllPagesWithScale = async (targetScale: number) => {
  const doc = pdfDoc.value
  if (!doc || !pagesContainer.value || totalPages.value === 0) return

  const gen = ++renderGeneration
  const renderScale = Math.max(1, targetScale)

  const existingWrappers = pagesContainer.value.querySelectorAll('.pdf-page-wrapper')
  if (existingWrappers.length !== totalPages.value) {
    pagesContainer.value.innerHTML = ''
    for (let i = 1; i <= totalPages.value; i++) {
      const wrapper = document.createElement('div')
      wrapper.className = 'pdf-page-wrapper'
      wrapper.setAttribute('data-page-num', String(i))
      wrapper.style.display = 'flex'
      wrapper.style.justifyContent = 'center'
      wrapper.style.marginBottom = '24px'
      pagesContainer.value.appendChild(wrapper)
    }
  } else {
    pagesContainer.value.querySelectorAll('.pdf-page-inner').forEach(el => el.remove())
  }

  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    if (gen !== renderGeneration) return

    const page = await doc.getPage(pageNum)
    if (gen !== renderGeneration) { page.cleanup(); return }

    const orig = page.getViewport({ scale: 1 })
    const displayW = orig.width * targetScale
    const displayH = orig.height * targetScale
    const renderVP = page.getViewport({ scale: renderScale })
    const displayVP = page.getViewport({ scale: targetScale })

    const wrapper = pagesContainer.value.querySelector(
      `.pdf-page-wrapper[data-page-num="${pageNum}"]`
    ) as HTMLElement

    const container = document.createElement('div')
    container.className = 'pdf-page-inner'
    container.style.width = `${displayW}px`
    container.style.height = `${displayH}px`
    container.style.position = 'relative'
    container.style.overflow = 'hidden'
    container.style.boxShadow = '0 2px 12px rgba(0,0,0,0.1)'
    container.style.background = 'white'
    container.style.borderRadius = '2px'
    container.style.setProperty('--scale-factor', String(targetScale))
    // 自定义属性记录页码，供右键菜单使用
    container.dataset.pageNum = String(pageNum)
    wrapper.appendChild(container)

    const canvas = document.createElement('canvas')
    canvas.width = renderVP.width
    canvas.height = renderVP.height
    canvas.style.width = `${displayW}px`
    canvas.style.height = `${displayH}px`
    canvas.style.display = 'block'
    container.appendChild(canvas)

    const ctx = canvas.getContext('2d')!

    try {
      await page.render({ canvasContext: ctx, viewport: renderVP }).promise
    } catch (err: any) {
      if (err?.name === 'RenderingCancelledException' || gen !== renderGeneration) {
        page.cleanup()
        return
      }
      console.warn(`Page ${pageNum} canvas failed:`, err)
      page.cleanup()
      continue
    }

    if (gen !== renderGeneration) { page.cleanup(); return }

    try {
      const textContent = await page.getTextContent()
      page.cleanup()

      const textDiv = document.createElement('div')
      textDiv.className = 'textLayer'
      container.appendChild(textDiv)

      const textLayer = new pdfjsLib.TextLayer({
        textContentSource: textContent,
        container: textDiv,
        viewport: displayVP,
      })
      await textLayer.render()
    } catch (e) {
      page.cleanup()
    }
  }
}

const scrollToPage = async (pageNum: number, behavior: ScrollBehavior = 'smooth') => {
  if (!pagesContainer.value) return
  const targetWrapper = pagesContainer.value.querySelector(`.pdf-page-wrapper[data-page-num="${pageNum}"]`)
  if (targetWrapper) {
    isScrolling = true
    targetWrapper.scrollIntoView({ behavior, block: 'center', inline: 'center' })
    setTimeout(() => { isScrolling = false }, 500)
    currentPage.value = pageNum
  }
}

const handleJumpToPage = () => {
  const page = parseInt(jumpPageInput.value)
  if (!isNaN(page) && page >= 1 && page <= totalPages.value) {
    scrollToPage(page)
    jumpPageInput.value = ''
  } else {
    ElMessage.warning(`请输入 1-${totalPages.value} 之间的页码`)
  }
}

const goToPrevPage = () => {
  if (currentPage.value > 1) scrollToPage(currentPage.value - 1)
}
const goToNextPage = () => {
  if (currentPage.value < totalPages.value) scrollToPage(currentPage.value + 1)
}

// ============ 缩放控制 ============
let zoomTimer: ReturnType<typeof setTimeout> | null = null

const applyZoom = (immediate = false) => {
  if (zoomTimer) clearTimeout(zoomTimer)
  if (immediate) {
    zoomTimer = null
    doRender()
  } else {
    zoomTimer = setTimeout(doRender, 100)
  }
}

const doRender = async () => {
  zoomTimer = null
  const pageBefore = currentPage.value
  await renderAllPagesWithScale(zoomScale.value)
  await nextTick()
  scrollToPage(pageBefore, 'auto')
}

const handleZoomIn = () => {
  if (zoomScale.value < 3) { zoomScale.value += 0.1; applyZoom() }
}
const handleZoomOut = () => {
  if (zoomScale.value > 0.25) { zoomScale.value -= 0.1; applyZoom() }
}
const handleResetZoom = () => {
  zoomScale.value = 1.0; applyZoom(true)
}

const handleFitWidth = async () => {
  if (!pagesContainer.value || !pdfDoc.value) return;
  const firstPage = await pdfDoc.value.getPage(1);
  const originalWidth = firstPage.getViewport({ scale: 1 }).width;
  const containerWidth = pagesContainer.value.clientWidth - 40;
  let newScale = containerWidth / originalWidth;
  newScale = Math.min(3, Math.max(0.25, newScale));
  zoomScale.value = newScale;
  applyZoom(true);
};

const handleFitHeight = async () => {
  if (!pagesContainer.value || !pdfDoc.value) return;
  const firstPage = await pdfDoc.value.getPage(1);
  const originalHeight = firstPage.getViewport({ scale: 1 }).height;
  const containerHeight = pagesContainer.value.clientHeight - 100;
  let newScale = containerHeight / originalHeight;
  newScale = Math.min(3, Math.max(0.25, newScale));
  zoomScale.value = newScale;
  applyZoom(true);
};

const handleWheelZoom = (event: WheelEvent) => {
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault()
    if (event.deltaY < 0) handleZoomIn()
    else handleZoomOut()
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
    event.preventDefault(); toggleSearchInline()
  }
  if (event.key === 'Escape') {
    showSearchInline.value = false
    contextMenu.value.visible = false
    event.preventDefault()
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === '=' || event.key === '+')) {
    event.preventDefault(); handleZoomIn()
  }
  if ((event.ctrlKey || event.metaKey) && event.key === '-') {
    event.preventDefault(); handleZoomOut()
  }
  if ((event.ctrlKey || event.metaKey) && event.key === '0') {
    event.preventDefault(); handleResetZoom()
  }
}

const toggleSearchInline = () => { showSearchInline.value = !showSearchInline.value }

const jumpToPage = (pageNumber: number) => {
  if (pageNumber >= 1 && pageNumber <= totalPages.value) {
    scrollToPage(pageNumber)
    showSearchInline.value = false
  }
}

const loadPdfDocument = async () => {
  pdfLoading.value = true
  pdfError.value = ''
  try {
    const loadingTask = pdfjsLib.getDocument({url:pdfUrl.value,useSystemFonts:false})
    const doc = await loadingTask.promise
    pdfDoc.value = markRaw(doc)
    totalPages.value = pdfDoc.value.numPages
    pageCount.value = totalPages.value

    const firstPage = await doc.getPage(1)
    const origWidth = firstPage.getViewport({ scale: 1 }).width
    const containerWidth = (pagesContainer.value?.clientWidth ?? 800) - 40
    let fitScale = containerWidth / origWidth
    fitScale = Math.min(3, Math.max(0.25, fitScale))
    zoomScale.value = fitScale
    firstPage.cleanup()

    await renderAllPagesWithScale(zoomScale.value)

    if (pagesContainer.value) {
      pagesContainer.value.addEventListener('scroll', handleScroll)
      pagesContainer.value.addEventListener('wheel', handleWheelZoom, { passive: false })
      // 右键菜单
      pagesContainer.value.addEventListener('contextmenu', handlePdfContextMenu)
    }
  } catch (err) {
    console.error('PDF 加载失败:', err)
    pdfError.value = 'PDF 文件加载失败，请检查文件是否有效'
  } finally {
    pdfLoading.value = false
  }
}

const loadPaperData = async () => {
  pdfLoading.value = true
  pdfError.value = ''
  try {
    const response = await fetchPaperPdfInfoApi(paperId.value)
    let pdfInfo: PaperPdfInfo
    if ('code' in response && 'data' in response) {
      const fullResponse = response as any
      if (fullResponse.code !== 0) throw new Error(fullResponse.msg || '请求失败')
      pdfInfo = fullResponse.data as PaperPdfInfo
    } else {
      pdfInfo = response as unknown as PaperPdfInfo
    }
    if (!pdfInfo || !pdfInfo.pdfUrl) throw new Error('PDF信息不完整')
    paperTitle.value = pdfInfo.title || '未命名论文'
    try {
      if (pdfObjectUrl) URL.revokeObjectURL(pdfObjectUrl)
      const pdfBlob = await fetchPaperPdfFileApi(paperId.value)
      const pdfBlobTyped = new Blob([pdfBlob], { type: 'application/pdf' })
      pdfObjectUrl = URL.createObjectURL(pdfBlobTyped)
      pdfUrl.value = pdfObjectUrl
    } catch (err) {
      console.error('PDF文件流加载失败:', err)
      pdfError.value = 'PDF文件加载失败'
      pdfLoading.value = false
      return
    }
    await loadPdfDocument()
    // 加载笔记列表
    await loadNotes()
  } catch (error) {
    pdfError.value = error instanceof Error ? error.message : '加载失败'
    ElMessage.error('加载论文失败: ' + pdfError.value)
    console.error(error)
  } finally {
    pdfLoading.value = false
  }
}

const handleBack = () => router.back()

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeyDown)
  loadPaperData()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeyDown)
  if (pagesContainer.value) {
    pagesContainer.value.removeEventListener('scroll', handleScroll)
    pagesContainer.value.removeEventListener('wheel', handleWheelZoom)
    pagesContainer.value.removeEventListener('contextmenu', handlePdfContextMenu)
  }
  if (pdfDoc.value) pdfDoc.value.destroy()
  if (pdfObjectUrl) URL.revokeObjectURL(pdfObjectUrl)
  if (rafId !== null) cancelAnimationFrame(rafId)
})

</script>

<template>
  <div class="pdf-viewer-container">
    <!-- 左侧 AI 对话栏 -->
    <aside
      v-if="showAiSidebar"
      class="ai-sidebar"
      :class="{ 'is-resizing': isAiResizing }"
      :style="{ width: aiSidebarWidth + 'px' }"
    >
      <AiChatPanel
        ref="aiChatRef"
        :paper-id="paperId"
      />
    </aside>

    <!-- AI 侧栏拖拽分隔条 -->
    <div
      v-if="showAiSidebar"
      class="ai-resizer"
      :class="{ 'is-active': isAiResizing }"
      @mousedown="startAiResize"
    />

    <!-- 中间 PDF 查看区 -->
    <main class="pdf-main">
      <!-- 工具栏 -->
      <header class="pdf-toolbar">
        <div class="toolbar-left">
          <el-button text @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>

          <div class="page-nav-group" v-if="totalPages > 0">
            <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
            <div class="nav-buttons">
              <el-button size="small" :disabled="currentPage <= 1" @click="goToPrevPage">上一页</el-button>
              <el-button size="small" :disabled="currentPage >= totalPages" @click="goToNextPage">下一页</el-button>
            </div>
            <div class="page-jump">
              <el-input
                v-model="jumpPageInput"
                size="small"
                placeholder="页码"
                style="width: 70px"
                @keyup.enter="handleJumpToPage"
              />
              <el-button size="small" @click="handleJumpToPage">跳转</el-button>
            </div>
          </div>
        </div>

        <div class="toolbar-center">
          <el-button-group>
            <el-tooltip content="缩小 (Ctrl + -)" placement="bottom">
              <el-button size="small" @click="handleZoomOut">
                <el-icon><ZoomOut /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="重置缩放 (Ctrl + 0)" placement="bottom">
              <el-button size="small" @click="handleResetZoom">
                {{ zoomLevel }}%
              </el-button>
            </el-tooltip>
            <el-tooltip content="放大 (Ctrl + +)" placement="bottom">
              <el-button size="small" @click="handleZoomIn">
                <el-icon><ZoomIn /></el-icon>
              </el-button>
            </el-tooltip>
          </el-button-group>

          <div class="divider"></div>

          <el-button-group>
            <el-tooltip content="适应宽度" placement="bottom">
              <el-button size="small" @click="handleFitWidth">
                <el-icon><FullScreen /></el-icon>
                适应宽度
              </el-button>
            </el-tooltip>
            <el-tooltip content="适应高度" placement="bottom">
              <el-button size="small" @click="handleFitHeight">
                <el-icon><FullScreen /></el-icon>
                适应高度
              </el-button>
            </el-tooltip>
          </el-button-group>
        </div>

        <div class="toolbar-right">
          <el-tooltip content="搜索 (Ctrl + F)" placement="bottom">
            <el-button
              size="small"
              :type="showSearchInline ? 'primary' : ''"
              @click="toggleSearchInline"
            >
              <el-icon><Search /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="AI 对话" placement="bottom">
            <el-button
              size="small"
              :type="showAiSidebar ? 'primary' : ''"
              @click="toggleAiSidebar"
            >
              <el-icon><ChatDotSquare /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="笔记" placement="bottom">
            <el-button
              size="small"
              :type="showNoteSidebar ? 'primary' : ''"
              @click="toggleNoteSidebar"
            >
              <el-icon><Edit /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </header>

      <!-- 浮动搜索浮层（不占布局空间） -->
      <div v-if="showSearchInline" class="pdf-search-float">
        <PdfSearchPanel
          ref="searchPanelRef"
          :paper-id="paperId"
          @jump-to-page="jumpToPage"
          @close="showSearchInline = false"
        />
      </div>

      <!-- PDF连续滚动区域 -->
      <div class="pdf-content" ref="pagesContainer" v-once>
        <div v-if="pdfLoading" class="pdf-loading">
          <el-icon class="is-loading" :size="48"><Document /></el-icon>
          <p>正在加载PDF...</p>
        </div>
        <div v-else-if="pdfError" class="pdf-error">
          <el-icon :size="48"><Document /></el-icon>
          <p>{{ pdfError }}</p>
          <el-button type="primary" @click="loadPaperData">重试</el-button>
        </div>
        <div v-else-if="!pdfUrl" class="pdf-empty">
          <el-icon :size="48"><Document /></el-icon>
          <p>暂无PDF文件</p>
        </div>
      </div>
    </main>

    <!-- 笔记栏拖拽分隔条 -->
    <div
      class="resizer"
      :class="{ 'is-active': isResizing }"
      @mousedown="startResize"
    />

    <!-- 右侧笔记栏 -->
    <aside
      v-if="showNoteSidebar"
      class="note-sidebar"
      :class="{ 'is-resizing': isResizing }"
      :style="{ width: noteSidebarWidth + 'px' }"
    >
      <div class="note-header">
        <h3 class="note-section-title">笔记</h3>
        <div class="note-header-actions">
          <span v-if="noteSaving" class="save-status">保存中...</span>
          <span v-else-if="activeNoteId" class="save-status">已保存</span>
          <el-button size="small" text @click="createNote">
            <el-icon :size="14"><Plus /></el-icon>
            新建
          </el-button>
        </div>
      </div>

      <!-- 笔记列表 -->
      <div class="note-list" v-if="noteList.length > 0">
        <div
          v-for="item in noteList"
          :key="item.id"
          class="note-list-item"
          :class="{ active: item.id === activeNoteId }"
          @click="selectNote(item.id)"
        >
          <div class="note-list-item-title">{{ item.title || '无标题' }}</div>
          <div class="note-list-item-excerpt">{{ item.excerpt || '空笔记' }}</div>
          <div class="note-list-item-meta">
            <span>{{ formatTime(item.updatedAt) }}</span>
            <el-button
              size="small"
              text
              @click.stop="deleteNote(item.id)"
            >
              <el-icon :size="12"><DeleteIcon /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 当前笔记编辑器 -->
      <div v-if="activeNoteId" class="note-input-area">
        <el-input
          v-model="noteTitle"
          size="small"
          placeholder="笔记标题"
          class="note-title-input"
        />
        <MarkdownEditor
          v-model="noteContent"
          placeholder="记录你对这篇论文的想法...（支持 Markdown，内容会自动保存）"
        />
      </div>
      <div v-else class="note-input-area note-empty">
        <p>暂无笔记，点击"新建"创建</p>
      </div>
    </aside>

    <!-- 右键上下文菜单 -->
    <PdfContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :selected-text="contextMenu.text"
      @ask-ai="handleAskAiFromContext"
      @close="closeContextMenu"
    />
  </div>
</template>


<style scoped>
.pdf-viewer-container {
  display: flex;
  height: calc(100vh - 64px);
  background-color: var(--bg-primary);
  overflow: hidden;
}
.pdf-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 600px;
  min-height: 0;
  position: relative;
  background-color: var(--bg-primary);
}

.pdf-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 1rem;
  background-color: #f5f5f5;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: #c0c4cc #e9ecef;
}

/* 工具栏样式优化：强制一行，超出滚动 */
.pdf-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 1rem;
  background-color: white;
  border-bottom: 1px solid var(--line-soft);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  gap: 1rem;
  flex-wrap: nowrap;          /* 禁止换行 */
  overflow-x: auto;           /* 超出宽度时水平滚动 */
  white-space: nowrap;
  scrollbar-width: thin;
}

/* 确保内部容器也不换行 */
.toolbar-left,
.toolbar-center,
.toolbar-right,
.page-nav-group,
.nav-buttons,
.page-jump,
.el-button-group {
  flex-shrink: 0;            /* 防止被压缩 */
  white-space: nowrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.page-nav-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #f8f9fa;
  padding: 0.2rem 0.8rem;
  border-radius: 20px;
}
.page-info {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-primary);
}
.nav-buttons {
  display: flex;
  gap: 0.25rem;
}
.page-jump {
  display: flex;
  align-items: center;
  gap: 4px;
}
.toolbar-center {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.divider {
  width: 1px;
  height: 24px;
  background-color: #e4e7ed;
  margin: 0 4px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pdf-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
.pdf-content::-webkit-scrollbar-track {
  background: #e9ecef;
  border-radius: 4px;
}
.pdf-content::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 4px;
  transition: background 0.2s;
}
.pdf-content::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

/* 动态创建的 DOM 元素样式见 renderAllPagesWithScale 中的 inline style */
/* (Vue scoped CSS 不作用于动态创建的 DOM 元素) */

/* 加载/错误状态 */
.pdf-loading,
.pdf-error,
.pdf-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--text-secondary);
  gap: 1rem;
}
.error-detail {
  font-size: 0.875rem;
  color: var(--text-tertiary);
  max-width: 500px;
  text-align: center;
  word-break: break-word;
}

.pdf-viewer {
  max-width: 900px;
  width: 100%;
  transition: transform 0.2s ease;
}

.pdf-viewer :deep(.vue-pdf-embed) {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* canvas 尺寸完全由外层容器 scale 控制 */
.pdf-viewer :deep(canvas) {
  display: block;
  max-width: 100%;
}

/* ── 拖拽分隔条 ── */
.resizer {
  width: 5px;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  transition: background 0.15s ease;
}

.resizer:hover,
.resizer.is-active {
  background: var(--brand);
}

/* ── AI 侧栏拖拽分隔条 ── */
.ai-resizer {
  width: 5px;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  transition: background 0.15s ease;
}

.ai-resizer:hover,
.ai-resizer.is-active {
  background: var(--brand);
}

.ai-sidebar.is-resizing {
  transition: none;
}

/* ── AI 侧栏 ── */
.ai-sidebar {
  background: white;
  border-right: 1px solid var(--line-soft);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

/* ── 笔记列表 ── */
.note-list {
  max-height: 200px;
  overflow-y: auto;
  border-bottom: 1px solid var(--line-soft);
  flex-shrink: 0;
}

.note-list-item {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.12s;
}

.note-list-item:hover {
  background: #f5f7fa;
}

.note-list-item.active {
  background: #ecf5ff;
  border-left: 3px solid var(--brand);
  padding-left: 9px;
}

.note-list-item-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-list-item-excerpt {
  font-size: 0.72rem;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-list-item-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.65rem;
  color: #ccc;
  margin-top: 2px;
}

.note-title-input {
  margin-bottom: 6px;
}

.note-title-input :deep(.el-input__inner) {
  font-size: 0.85rem;
  font-weight: 600;
}

.note-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  font-size: 0.82rem;
}

.note-sidebar {
  background-color: var(--bg-secondary);
  border-left: 1px solid var(--line-soft);
  display: flex;
  flex-direction: column;
}

.note-sidebar.is-resizing {
  transition: none;
}

.note-header {
  padding: 0.55rem 0.8rem;
  border-bottom: 1px solid var(--line-soft);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.note-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.export-btn {
  color: var(--text-tertiary);
  transition: color 0.15s ease;
}

.export-btn:hover {
  color: var(--brand);
}

.note-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.save-status {
  font-size: 0.7rem;
  color: var(--brand);
  opacity: 0.8;
}
.note-input-area {
  flex: 1;
  padding: 0.55rem 0.8rem;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.note-input-area :deep(.md-editor) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 分栏模式 */
.note-input-area :deep(.mode-split .md-preview-section) {
  flex: 1;
  min-height: 0;
}

.note-input-area :deep(.mode-split .md-preview) {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* 实时预览模式 */
.note-input-area :deep(.mode-live .md-live) {
  flex: 1;
  min-height: 0;
}
.note-info {
  padding-top: 0.35rem;
  border-top: 1px solid var(--line-soft);
  margin-top: auto;
}
.info-text {
  font-size: 0.7rem;
  color: var(--text-tertiary);
}
.note-sidebar.mobile {
  position: fixed;
  top: 60px;
  right: 0;
  bottom: 0;
  z-index: 100;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
  transform: translateX(100%);
}
.note-sidebar.mobile.visible {
  transform: translateX(0);
}

/* 浮动搜索浮层 */
.pdf-search-float {
  position: absolute;
  top: 52px;
  right: 12px;
  z-index: 100;
}

/* 响应式：小屏幕时仅让工具栏可滚动，内部不再换行 */
@media (max-width: 900px) {
  .pdf-toolbar {
    overflow-x: auto;
    overflow-y: hidden;
  }
  .pdf-main {
    min-width: auto;
  }
}
@media (max-width: 1200px) {
  .note-sidebar {
    width: 240px;
  }
}
</style>

<style>
/* PDF.js 文字选择层 — 全局样式（动态创建的元素） */
.textLayer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  line-height: 1;
  text-align: initial;
  z-index: 2;
}

.textLayer span,
.textLayer br {
  color: transparent !important;
  position: absolute;
  white-space: pre;
  cursor: text;
  transform-origin: 0% 0%;
}

.textLayer .highlight {
  margin: -1px;
  padding: 1px;
  background-color: rgba(180, 0, 170, 0.3);
  border-radius: 4px;
}

.textLayer .highlight.selected {
  background-color: rgba(0, 100, 0, 0.3);
}

/* 选择高亮 */
.textLayer ::selection {
  background-color: rgba(0, 0, 255, 0.2);
}

/* ── 工具栏按钮 hover 颜色改为品牌色（替代 Element Plus 默认蓝色）── */
.pdf-toolbar .el-button:not(.el-button--primary):not(:disabled):hover {
  color: #4a9d9a !important;
  background-color: rgba(74, 157, 154, 0.08) !important;
  border-color: transparent;
}

.pdf-toolbar .el-button.is-text:not(:disabled):hover {
  color: #4a9d9a !important;
  background-color: rgba(74, 157, 154, 0.08) !important;
}
</style>
