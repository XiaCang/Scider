<script setup lang="ts">
import { ArrowLeft, Edit, Document, ZoomIn, ZoomOut, FullScreen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VuePdfEmbed from 'vue-pdf-embed'

import type { PaperNote, PaperPdfInfo } from '../../../types/library'
import {
  fetchPaperPdfInfoApi,
  fetchPaperNotesApi,
  createNoteApi,
  updateNoteApi
} from '../../../api/library'

const route = useRoute()
const router = useRouter()

const paperId = computed(() => route.params.paperId as string)

// PDF 信息
const paperTitle = ref('')
const pdfUrl = ref('')
const pageCount = ref(0)

// 笔记相关
const note = ref<PaperNote | null>(null)
const noteContent = ref('')
const notePage = ref(1)

// UI 状态
const zoomLevel = ref(100)
const currentPage = ref(1)
const isMobile = ref(window.innerWidth < 900)
const showNoteDrawer = ref(true)
const pdfLoading = ref(true)
const pdfError = ref('')
const pdfViewerRef = ref<HTMLElement | null>(null)

// 自动保存定时器
let saveTimer: ReturnType<typeof setTimeout> | null = null

const handleResize = () => {
  isMobile.value = window.innerWidth < 900
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadPaperData()
  
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeyDown)
  
  // 清理事件监听器
  if (pdfViewerRef.value) {
    pdfViewerRef.value.removeEventListener('wheel', handleWheelZoom)
  }
})

// 加载论文数据
const loadPaperData = async () => {
  pdfLoading.value = true
  pdfError.value = ''
  try {
    const response = await fetchPaperPdfInfoApi(paperId.value)
    
    // 调试：查看实际返回的数据结构
    console.log('[loadPaperData] API原始响应:', response)
    console.log('[loadPaperData] 响应类型:', typeof response)
    console.log('[loadPaperData] 响应键名:', Object.keys(response || {}))
    
    // 响应拦截器已解包，response 应该是 data 字段的内容
    // 但如果响应拦截器未生效，response 可能是 {code, msg, data} 结构
    let pdfInfo: PaperPdfInfo
    
    if ('code' in response && 'data' in response) {
      // 响应拦截器未解包，手动提取 data
      console.log('[loadPaperData] 检测到完整响应结构，手动提取 data')
      const fullResponse = response as any
      if (fullResponse.code !== 0) {
        throw new Error(fullResponse.msg || '请求失败')
      }
      pdfInfo = fullResponse.data as PaperPdfInfo
    } else {
      // 响应拦截器已解包，直接使用
      console.log('[loadPaperData] 响应已解包，直接使用')
      pdfInfo = response as unknown as PaperPdfInfo
    }
    
    console.log('[loadPaperData] pdfInfo:', pdfInfo)
    console.log('[loadPaperData] pdfInfo.pdfUrl:', pdfInfo?.pdfUrl)

    if (!pdfInfo || !pdfInfo.pdfUrl) {
      throw new Error('PDF信息不完整')
    }

    paperTitle.value = pdfInfo.title || '未命名论文'
    
    // 构建完整的PDF URL（相对路径转绝对路径）
    // 注意：PDF文件在 /uploads 路径下，不在 /api 路径下
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    // 从API基础URL中提取服务器地址（去掉 /api 后缀）
    const serverBaseUrl = apiBaseUrl.replace(/\/api$/, '')
    
    pdfUrl.value = pdfInfo.pdfUrl.startsWith('http') 
      ? pdfInfo.pdfUrl 
      : `${serverBaseUrl}${pdfInfo.pdfUrl}`
    
    pageCount.value = pdfInfo.pageCount || 0
    
    console.log('[loadPaperData] API Base URL:', apiBaseUrl)
    console.log('[loadPaperData] Server Base URL:', serverBaseUrl)
    console.log('[loadPaperData] 最终PDF URL:', pdfUrl.value)
    console.log('[loadPaperData] 论文标题:', paperTitle.value)

    // 获取笔记
    const notesResponse = await fetchPaperNotesApi(paperId.value)
    
    // 同样处理笔记响应
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
    
    console.log('PDF信息加载成功:', {
      title: paperTitle.value,
      pdfUrl: pdfUrl.value,
      pageCount: pageCount.value
    })
  } catch (error) {
    pdfError.value = error instanceof Error ? error.message : '加载失败'
    ElMessage.error('加载论文失败: ' + pdfError.value)
    console.error('加载论文数据失败:', error)
  } finally {
    pdfLoading.value = false
  }
}

// 返回上一页
const handleBack = () => {
  router.back()
}

// PDF加载成功回调
const handlePdfLoaded = (pdfDoc: any) => {
  console.log('[PDF] 加载成功，总页数:', pdfDoc.numPages)
  pageCount.value = pdfDoc.numPages
  pdfLoading.value = false
  
  // 在PDF加载完成后添加滚轮缩放监听
  setTimeout(() => {
    if (pdfViewerRef.value) {
      pdfViewerRef.value.addEventListener('wheel', handleWheelZoom, { passive: false })
    }
  }, 500)
}

// PDF加载失败回调
const handlePdfError = (error: any) => {
  console.error('[PDF] 加载失败:', error)
  pdfError.value = 'PDF文件加载失败，请检查文件是否存在'
  pdfLoading.value = false
  ElMessage.error('PDF加载失败')
}

// 缩放控制
const handleZoomIn = () => {
  if (zoomLevel.value < 300) {
    zoomLevel.value += 10
  }
}

const handleZoomOut = () => {
  if (zoomLevel.value > 25) {
    zoomLevel.value -= 10
  }
}

// 重置缩放
const handleResetZoom = () => {
  zoomLevel.value = 100
}

// 适应宽度
const handleFitWidth = () => {
  if (pdfViewerRef.value) {
    const containerWidth = pdfViewerRef.value.clientWidth - 40 // 减去padding
    // 假设PDF标准宽度为595pt (A4)
    const standardPdfWidth = 595
    const calculatedZoom = Math.floor((containerWidth / standardPdfWidth) * 100)
    zoomLevel.value = Math.max(25, Math.min(300, calculatedZoom))
  }
}

// 适应高度
const handleFitHeight = () => {
  if (pdfViewerRef.value) {
    const containerHeight = window.innerHeight - 200 // 减去工具栏等
    // 假设PDF标准高度为842pt (A4)
    const standardPdfHeight = 842
    const calculatedZoom = Math.floor((containerHeight / standardPdfHeight) * 100)
    zoomLevel.value = Math.max(25, Math.min(300, calculatedZoom))
  }
}

// 鼠标滚轮缩放（按住Ctrl键）
const handleWheelZoom = (event: WheelEvent) => {
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault()
    
    if (event.deltaY < 0) {
      // 向上滚动，放大
      handleZoomIn()
    } else {
      // 向下滚动，缩小
      handleZoomOut()
    }
  }
}

// 键盘快捷键
const handleKeyDown = (event: KeyboardEvent) => {
  // Ctrl/Cmd + '+' 放大
  if ((event.ctrlKey || event.metaKey) && (event.key === '=' || event.key === '+')) {
    event.preventDefault()
    handleZoomIn()
  }
  
  // Ctrl/Cmd + '-' 缩小
  if ((event.ctrlKey || event.metaKey) && event.key === '-') {
    event.preventDefault()
    handleZoomOut()
  }
  
  // Ctrl/Cmd + '0' 重置缩放
  if ((event.ctrlKey || event.metaKey) && event.key === '0') {
    event.preventDefault()
    handleResetZoom()
  }
}

// 翻页控制
const goToPrevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const goToNextPage = () => {
  if (currentPage.value < pageCount.value) currentPage.value++
}

// 自动保存笔记（防抖）
const autoSaveNote = async () => {
  if (saveTimer) clearTimeout(saveTimer)

  saveTimer = setTimeout(async () => {
    if (!noteContent.value.trim()) return

    try {
      if (note.value) {
        await updateNoteApi(paperId.value, note.value.id, {
          content: noteContent.value
        })
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
      console.error('自动保存失败:', error)
    }
  }, 500)
}

watch(noteContent, () => { autoSaveNote() })

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="pdf-viewer-container">
    <!-- 中间 PDF 查看区 -->
    <main class="pdf-main">
      <!-- 工具栏 -->
      <header class="pdf-toolbar">
        <div class="toolbar-left">
          <el-button text @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <span class="page-info" v-if="pageCount > 0">
            第 {{ currentPage }} / {{ pageCount }} 页
          </span>
          <div class="nav-buttons" v-if="pageCount > 0">
            <el-button size="small" :disabled="currentPage <= 1" @click="goToPrevPage">上一页</el-button>
            <el-button size="small" :disabled="currentPage >= pageCount" @click="goToNextPage">下一页</el-button>
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
          
          <el-button-group style="margin-left: 12px;">
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
          <el-tooltip content="提示：按住 Ctrl + 滚轮可快速缩放" placement="bottom">
            <el-button size="small" text>
              <el-icon><Edit /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </header>

      <!-- PDF显示区域 -->
      <div class="pdf-content" ref="pdfViewerRef">
        <div 
          v-if="pdfLoading" 
          class="pdf-loading"
        >
          <el-icon class="is-loading" :size="48"><Document /></el-icon>
          <p>正在加载PDF...</p>
        </div>
        
        <div 
          v-else-if="pdfError" 
          class="pdf-error"
        >
          <el-icon :size="48"><Document /></el-icon>
          <p>{{ pdfError }}</p>
          <el-button type="primary" @click="loadPaperData">重试</el-button>
        </div>
        
        <div 
          v-else-if="!pdfUrl" 
          class="pdf-empty"
        >
          <el-icon :size="48"><Document /></el-icon>
          <p>暂无PDF文件</p>
        </div>
        
        <div 
          v-else 
          class="pdf-viewer" 
          :style="{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }"
        >
          <VuePdfEmbed
            :source="pdfUrl"
            :page="currentPage"
            :scale="zoomLevel / 100"
            text-layer
            @loaded="handlePdfLoaded"
            @error="handlePdfError"
          />
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

.pdf-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 1rem;
  background-color: white;
  border-bottom: 1px solid var(--line-soft);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.toolbar-center {
  display: flex;
  align-items: center;
}

.page-info {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.nav-buttons {
  display: flex;
  gap: 0.25rem;
}

.zoom-level {
  min-width: 48px;
  text-align: center;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-primary);
}

.pdf-content {
  flex: 1;
  overflow: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #f5f5f5;
}

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
  transition: transform 0.15s ease-out;
  transform-origin: top center;
}

.pdf-viewer-wrapper :deep(.vue-pdf-embed) {
  width: 100%;
}

.pdf-viewer-wrapper :deep(canvas) {
  width: 100% !important;
  height: auto !important;
  display: block;
}

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

@media (max-width: 1200px) {
  .note-sidebar {
    width: 240px;
  }
}

@media (max-width: 900px) {
  .pdf-main {
    min-width: auto;
  }
}
</style>
