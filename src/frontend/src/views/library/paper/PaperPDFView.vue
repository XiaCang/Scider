<script setup lang="ts">
import { ArrowLeft, Edit, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VuePdfEmbed from 'vue-pdf-embed'
import { useVuePdfEmbed } from 'vue-pdf-embed'

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

// 使用 vue-pdf-embed composable 获取文档对象
const { doc } = useVuePdfEmbed({ source: pdfUrl })

// 当文档加载完成后，获取页数
watch(doc, (pdfDoc) => {
  if (pdfDoc) {
    pageCount.value = pdfDoc.numPages
    pdfLoading.value = false
  }
})

// 自动保存定时器
let saveTimer: ReturnType<typeof setTimeout> | null = null

const handleResize = () => {
  isMobile.value = window.innerWidth < 900
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadPaperData()
})

// 加载论文数据
const loadPaperData = async () => {
  try {
    const response = await fetchPaperPdfInfoApi(paperId.value)
    const pdfInfo = response as unknown as PaperPdfInfo

    paperTitle.value = pdfInfo.title
    pdfUrl.value = pdfInfo.pdfUrl
    pageCount.value = pdfInfo.pageCount

    // 获取笔记
    const notesResponse = await fetchPaperNotesApi(paperId.value)
    const notesList = notesResponse as unknown as PaperNote[]
    note.value = notesList.length > 0 ? notesList[0] : null

    if (note.value) {
      noteContent.value = note.value.content
      notePage.value = note.value.pageNumber
    }
  } catch (error) {
    ElMessage.error('加载论文失败')
    console.error('加载论文数据失败:', error)
  }
}

// 返回上一页
const handleBack = () => {
  router.back()
}

// 缩放控制
const handleZoomIn = () => {
  if (zoomLevel.value < 200) {
    zoomLevel.value += 10
  }
}

const handleZoomOut = () => {
  if (zoomLevel.value > 50) {
    zoomLevel.value -= 10
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
            <el-button size="small" @click="handleZoomOut">-</el-button>
            <span class="zoom-level">{{ zoomLevel }}%</span>
            <el-button size="small" @click="handleZoomIn">+</el-button>
          </el-button-group>
        </div>

        <div class="toolbar-right">
          <el-button
            v-if="isMobile"
            text
            @click="showNoteDrawer = !showNoteDrawer"
          >
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button text @click="showNoteDrawer = !showNoteDrawer">
            {{ showNoteDrawer ? '隐藏笔记' : '显示笔记' }}
          </el-button>
        </div>
      </header>

      <!-- PDF 显示区域 -->
      <div class="pdf-content">
        <div v-if="pdfLoading" class="pdf-loading">
          <el-icon :size="48" class="is-loading"><Document /></el-icon>
          <p>正在加载 PDF...</p>
        </div>
        <div v-else class="pdf-viewer" :style="{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }">
          <VuePdfEmbed
            :source="pdfUrl"
            :page="currentPage"
            :scale="zoomLevel / 100"
            text-layer
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
}

.pdf-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--text-secondary);
  gap: 1rem;
}

.pdf-viewer {
  max-width: 800px;
  width: 100%;
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
