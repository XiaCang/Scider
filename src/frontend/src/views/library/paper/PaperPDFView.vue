<template>
  <div class="pdf-viewer-container">
    <!-- 中间 PDF 查看区 -->
    <main class="pdf-main">
      <!-- 工具栏（保持一行，超出滚动） -->
      <header class="pdf-toolbar">
        <!-- 左侧：返回 + 页码信息 + 翻页 + 快速跳转 -->
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

        <!-- 中间：缩放与视图适配 -->
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

        <!-- 右侧：仅搜索按钮 -->
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
        </div>
      </header>

      <!-- 内联搜索栏 -->
      <div class="search-inline-bar" v-show="showSearchInline">
        <PdfSearchPanel 
          :paper-id="paperId" 
          @jump-to-page="jumpToPage" 
        />
      </div>

      <!-- PDF连续滚动区域 -->
      <div class="pdf-content" ref="pagesContainer">
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

    <!-- 右侧笔记栏 -->
    <aside class="note-sidebar" :class="{ mobile: isMobile, visible: showNoteDrawer }">
      <div class="note-header">
        <h3 class="note-section-title">我的笔记</h3>
        <span v-if="note" class="save-status">已自动保存</span>
      </div>
      <div class="note-input-area">
        <el-input
          v-model="noteContent"
          type="textarea"
          :rows="12"
          placeholder="记录你对这篇论文的想法...（内容会自动保存）"
        />
        <div v-if="note" class="note-info">
          <span class="info-text">最后更新：{{ formatTime(note.updatedAt) }}</span>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft, Edit, Document, ZoomIn, ZoomOut, FullScreen, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, onUnmounted, ref, watch, nextTick, shallowRef, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as pdfjsLib from 'pdfjs-dist'

// 配置 PDF.js worker - 使用 CDN 上的 ES module worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.mjs`

import type { PaperNote, PaperPdfInfo } from '../../../types/library'
import {
  fetchPaperPdfInfoApi,
  fetchPaperPdfFileApi,
  fetchPaperNotesApi,
  createNoteApi,
  updateNoteApi
} from '../../../api/library'
import PdfSearchPanel from '../../../components/PdfSearchPanel.vue'

const route = useRoute()
const router = useRouter()
const paperId = computed(() => route.params.paperId as string)

// PDF 信息
const paperTitle = ref('')
const pdfUrl = ref('')
const pageCount = ref(0)

// 连续滚动相关 - 使用 shallowRef 避免 Vue 对 PDF 文档对象进行深度响应式代理
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

// 笔记相关
const note = ref<PaperNote | null>(null)
const noteContent = ref('')
const notePage = ref(1)

// UI 状态
const isMobile = ref(window.innerWidth < 900)
const showNoteDrawer = ref(true)
const pdfLoading = ref(true)
const pdfError = ref('')
let pdfObjectUrl = ''

const showSearchInline = ref(false)
let saveTimer: ReturnType<typeof setTimeout> | null = null

const handleResize = () => {
  isMobile.value = window.innerWidth < 900
}

// ---------- 滚动时计算当前页码（使用 requestAnimationFrame 节流）----------
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

// ---------- 渲染所有页面 ----------
const renderAllPages = async () => {
  const doc = pdfDoc.value
  if (!doc || !pagesContainer.value) return

  pagesContainer.value.innerHTML = ''
  
  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    const page = await doc.getPage(pageNum)
    const viewport = page.getViewport({ scale: zoomScale.value })
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')
    canvas.height = viewport.height
    canvas.width = viewport.width
    canvas.style.display = 'block'
    canvas.style.margin = '0 auto'
    canvas.style.boxShadow = '0 1px 4px rgba(0,0,0,0.1)'
    canvas.style.marginBottom = '16px'
    canvas.style.maxWidth = '100%'
    canvas.style.height = 'auto'

    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    await page.render(renderContext).promise

    const pageWrapper = document.createElement('div')
    pageWrapper.className = 'pdf-page-wrapper'
    pageWrapper.setAttribute('data-page-num', String(pageNum))
    pageWrapper.appendChild(canvas)
    pagesContainer.value.appendChild(pageWrapper)
  }
}

// 跳转到指定页面并居中
const scrollToPage = async (pageNum: number, behavior: ScrollBehavior = 'smooth') => {
  if (!pagesContainer.value) return
  const targetWrapper = pagesContainer.value.querySelector(`.pdf-page-wrapper[data-page-num="${pageNum}"]`)
  if (targetWrapper) {
    isScrolling = true
    targetWrapper.scrollIntoView({
      behavior,
      block: 'center',
      inline: 'center'
    })
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

// 缩放控制
const handleZoomIn = () => {
  if (zoomScale.value < 3) {
    zoomScale.value += 0.1
    applyZoom()
  }
}
const handleZoomOut = () => {
  if (zoomScale.value > 0.25) {
    zoomScale.value -= 0.1
    applyZoom()
  }
}
const handleResetZoom = () => {
  zoomScale.value = 1.0
  applyZoom()
}

const applyZoom = async () => {
  const currentPageBefore = currentPage.value
  await renderAllPages()
  await nextTick()
  scrollToPage(currentPageBefore, 'auto')
}

const handleFitWidth = async () => {
  if (!pagesContainer.value || !pdfDoc.value) return
  const firstPage = await pdfDoc.value.getPage(1)
  const originalWidth = firstPage.getViewport({ scale: 1 }).width
  const containerWidth = pagesContainer.value.clientWidth - 40
  let newScale = containerWidth / originalWidth
  newScale = Math.min(3, Math.max(0.25, newScale))
  zoomScale.value = newScale
  await applyZoom()
}

const handleFitHeight = async () => {
  if (!pagesContainer.value || !pdfDoc.value) return
  const firstPage = await pdfDoc.value.getPage(1)
  const originalHeight = firstPage.getViewport({ scale: 1 }).height
  const containerHeight = pagesContainer.value.clientHeight - 100
  let newScale = containerHeight / originalHeight
  newScale = Math.min(3, Math.max(0.25, newScale))
  zoomScale.value = newScale
  await applyZoom()
}

const handleWheelZoom = (event: WheelEvent) => {
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault()
    if (event.deltaY < 0) handleZoomIn()
    else handleZoomOut()
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
    event.preventDefault()
    toggleSearchInline()
  }
  if (event.key === 'Escape' && showSearchInline.value) {
    showSearchInline.value = false
    event.preventDefault()
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === '=' || event.key === '+')) {
    event.preventDefault()
    handleZoomIn()
  }
  if ((event.ctrlKey || event.metaKey) && event.key === '-') {
    event.preventDefault()
    handleZoomOut()
  }
  if ((event.ctrlKey || event.metaKey) && event.key === '0') {
    event.preventDefault()
    handleResetZoom()
  }
}

const toggleSearchInline = () => {
  showSearchInline.value = !showSearchInline.value
}

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
    const loadingTask = pdfjsLib.getDocument(pdfUrl.value)
    const doc = await loadingTask.promise
    pdfDoc.value = markRaw(doc)
    totalPages.value = pdfDoc.value.numPages
    pageCount.value = totalPages.value

    await renderAllPages()
    if (pagesContainer.value) {
      pagesContainer.value.addEventListener('scroll', handleScroll)
      pagesContainer.value.addEventListener('wheel', handleWheelZoom, { passive: false })
    }
    await handleFitWidth()
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
    const notesResponse = await fetchPaperNotesApi(paperId.value)
    let notesList: PaperNote[]
    if ('code' in notesResponse && 'data' in notesResponse) {
      const fullResponse = notesResponse as any
      notesList = fullResponse.code === 0 ? fullResponse.data : []
    } else {
      notesList = notesResponse as unknown as PaperNote[]
    }
    note.value = notesList.length > 0 ? notesList[0] : null
    if (note.value) {
      noteContent.value = note.value.content
      notePage.value = note.value.pageNumber || 1
    }
    await loadPdfDocument()
  } catch (error) {
    pdfError.value = error instanceof Error ? error.message : '加载失败'
    ElMessage.error('加载论文失败: ' + pdfError.value)
    console.error(error)
  } finally {
    pdfLoading.value = false
  }
}

const handleBack = () => router.back()

const autoSaveNote = async () => {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    if (!noteContent.value.trim()) return
    try {
      if (note.value) {
        await updateNoteApi(paperId.value, note.value.id, { content: noteContent.value })
        note.value.content = noteContent.value
        note.value.updatedAt = new Date().toISOString()
      } else {
        const response = await createNoteApi(paperId.value, {
          content: noteContent.value,
          pageNumber: notePage.value,
        })
        note.value = response as unknown as PaperNote
      }
    } catch (error) {
      ElMessage.error('自动保存失败')
      console.error(error)
    }
  }, 500)
}
watch(noteContent, () => autoSaveNote())

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
  }
  if (pdfDoc.value) pdfDoc.value.destroy()
  if (pdfObjectUrl) URL.revokeObjectURL(pdfObjectUrl)
  if (rafId !== null) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.pdf-viewer-container {
  display: flex;
  height: calc(100vh - 60px);
  background-color: var(--bg-primary);
  overflow: hidden;
}
.pdf-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 600px;
  background-color: var(--bg-primary);
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

/* 滚动容器样式 */
.pdf-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background-color: #f5f5f5;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: #c0c4cc #e9ecef;
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

.pdf-page-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}
.pdf-page-wrapper canvas {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  background: white;
  border-radius: 2px;
  max-width: 100%;
  height: auto !important;
  display: block;
}

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

/* 笔记栏 */
.note-sidebar {
  width: 270px;
  background-color: var(--bg-secondary);
  border-left: 1px solid var(--line-soft);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
}
.note-header {
  padding: 0.55rem 0.8rem;
  border-bottom: 1px solid var(--line-soft);
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.search-inline-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 8px 0;
  background-color: #fff;
  border-bottom: 1px solid var(--line-soft);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  z-index: 10;
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
@media (max-width: 768px) {
  .search-drawer {
    width: 100%;
    max-width: 100vw;
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    height: 100vh;
  }
}
</style>