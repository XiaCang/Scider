<template>
  <div class="library-main">
    <!-- 工具栏卡片 -->
    <div class="toolbar-card">
      <header class="library-header">
        <div class="selection-area">
          <template v-if="selectedPaperIds.size === 0">
            <button class="select-all-btn" @click="handleSelectAll">全选</button>
          </template>
          <template v-else>
            <div class="selected-badge">
              <span>已选 {{ selectedPaperIds.size }} 篇</span>
              <button class="clear-all-btn" @click="handleClearAll">
                <el-icon><Close /></el-icon>
                清除
              </button>
            </div>
          </template>
        </div>

        <div class="header-actions">
          <label class="library-search">
            <el-icon><Search /></el-icon>
            <input v-model="searchQuery" type="text" placeholder="按标题搜索..." @input="onSearch" />
          </label>
          <button 
            class="upload-btn" 
            @click="showUploadDialog = true"
            title="上传PDF论文"
          >
            <el-icon><Upload /></el-icon>
            上传PDF
          </button>
          <ParsingProgressPopover 
            ref="parsingProgressRef"
            :papers="filteredPapers"
          />
          <button 
            class="copy-btn" 
            @click="handleBatchCopy" 
            :disabled="selectedPaperIds.size === 0"
            title="复制到文件夹"
          >
            <el-icon><CopyDocument /></el-icon>
            复制到文件夹
          </button>
          <button class="delete-btn" @click="handleBatchDelete" :disabled="selectedPaperIds.size === 0">
            <el-icon><Delete /></el-icon>
            删除
          </button>
        </div>
      </header>
    </div>

    <!-- 论文列表卡片 -->
    <div class="list-card">
      <div class="folder-info-bar">
        <span class="current-folder">{{ currentFolderName }}</span>
        <span class="paper-count">({{ filteredPapers.length }})</span>
      </div>

      <PaperCardList
        :papers="filteredPapers"
        :selectedIds="selectedPaperIds"
        @update:selectedIds="selectedPaperIds = $event"
        @select-paper="handleSelectPaper"
      />
    </div>

    <PaperDetail
      v-model="paperDetailVisible"
      :paper="selectedPaper"
      @save="handleSaveKeyPoints"
      @preview-pdf="handlePreviewPdf"
    />

    <!-- PDF上传对话框（批量） -->
    <PdfUploadDialog
      v-model="showUploadDialog"
      @batch-success="handleBatchUploadSuccess"
    />

    <!-- 复制到文件夹对话框 -->
    <CopyToFolderDialog
      v-model="showCopyDialog"
      :folders="folderStore.folders"
      @confirm="handleConfirmCopy"
    />

    <!-- 页面引导 tour -->
    <GuideTour
      :step="currentStepData"
      :step-number="currentStep + 1"
      :total-steps="totalSteps"
      :is-first="isFirst"
      :is-last="isLast"
      @next="next"
      @prev="prev"
      @skip="skip"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, h, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Delete, Close, Upload, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { LibraryPaper, PaperKeyPoints } from '../../types/library'
import { deletePaperApi, batchAddPapersToFolderApi } from '../../api/library'  
import PaperDetail from './paper/PaperDetail.vue'
import PaperCardList from './paper/PaperListItem.vue'
import PdfUploadDialog from '../../components/PdfUploadDialog.vue'
import ParsingProgressPopover from '../../components/ParsingProgressPopover.vue'
import CopyToFolderDialog from '../../components/CopyToFolderDialog.vue'
import GuideTour from '../../components/GuideTour.vue'
import { useGuide } from '../../hooks/useGuide'
import { usePaperStore } from '../../store/paper'
import { useFolderStore } from '../../store/folder'

const route = useRoute()
const router = useRouter()
const paperStore = usePaperStore()
const folderStore = useFolderStore()

// ── 引导 tour ──
const guide = useGuide({
  pageKey: 'library',
  steps: [
    {
      selector: '.left-panel',
      title: '文件夹管理',
      description: '左侧文件夹树帮助你分类管理论文。点击右上角 + 按钮可新建文件夹，右键文件夹可进行重命名、移动等操作。',
      placement: 'right',
    },
    {
      selector: '.upload-btn',
      title: '上传 PDF 论文',
      description: '点击这里上传你的 PDF 论文文件，系统会自动解析论文元数据并提取四维度关键点（背景、方法、创新点、结论）。',
      placement: 'bottom',
    },
    {
      selector: '.library-search',
      title: '搜索论文',
      description: '在搜索框中输入关键词，可按标题快速过滤当前文件夹中的论文。',
      placement: 'bottom',
    },
    {
      selector: '.paper-card:first-child',
      title: '查看论文详情',
      description: '点击任意论文卡片，右侧会弹出详情抽屉。你可以在其中查看和编辑论文的四维度关键点，确认后即可预览 PDF。',
      placement: 'left',
    },
    {
      selector: '.select-all-btn',
      title: '批量操作',
      description: '勾选论文后，上方会显示已选数量。你可以批量删除论文，或将它们复制到其他文件夹中。',
      placement: 'bottom',
    },
  ],
})

const { currentStep, isFirst, isLast, currentStepData, totalSteps, next, prev, skip } = guide

const searchQuery = ref('')
const paperDetailVisible = ref(false)
const showUploadDialog = ref(false)
const showCopyDialog = ref(false)
const selectedPaper = ref<LibraryPaper | null>(null)
const selectedPaperIds = ref<Set<string>>(new Set())
const parsingProgressRef = ref<InstanceType<typeof ParsingProgressPopover> | null>(null)

// 自动刷新定时器
let refreshTimer: number | null = null
const REFRESH_INTERVAL = 3000

const currentFolderId = computed(() => route.params.folderId as string || 'all')

const folderPapers = computed(() => {
  if (currentFolderId.value === 'all') return paperStore.papers
  const folder = folderStore.folders.find(f => f.id === currentFolderId.value)
  if (!folder) return []
  return paperStore.getPapersByIds(folder.paperIds ?? [])
})

const filteredPapers = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return folderPapers.value
  return folderPapers.value.filter(p => p.title.toLowerCase().includes(keyword))
})

const terminalStatuses = ['PENDING_CONFIRMATION']  
const hasPendingTasks = computed(() => {
  return paperStore.papers.some(p => !terminalStatuses.includes(p.status))
})

const startAutoRefresh = () => {
  stopAutoRefresh()
  refreshTimer = window.setInterval(async () => {
    if (hasPendingTasks.value) {
      console.log('[Auto Refresh] 检测到待处理任务，刷新论文列表...')
      await paperStore.loadPapers()
      await folderStore.loadFolders()
    } else {
      console.log('[Auto Refresh] 无待处理任务，停止刷新')
      stopAutoRefresh()
    }
  }, REFRESH_INTERVAL)
}

const stopAutoRefresh = () => {
  if (refreshTimer !== null) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const handleTaskCompleted = async (event: Event) => {
  const customEvent = event as CustomEvent
  const { paperId, status } = customEvent.detail
  console.log(`[Task Completed] 论文 ${paperId.substring(0, 8)}... 状态: ${status}`)
  await paperStore.loadPapers()
  await folderStore.loadFolders()
  if (status === 'SUCCESS') {
    ElMessage.success('论文解析完成！')
  } else if (status === 'FAILURE') {
    ElMessage.warning('论文解析失败，请重试')
  }
}

const initData = async () => {
  console.log('[PaperList] 组件挂载，开始加载数据...')
  try {
    await Promise.all([
      paperStore.loadPapers(),
      folderStore.loadFolders()
    ])
    console.log(`[PaperList] 数据加载完成，论文数量: ${paperStore.papers.length}`)
  } catch (e: any) {
    if (!e.message?.includes('未认证') && !e.message?.includes('Token')) {
      ElMessage.error('加载数据失败，请检查网络连接')
    }
  }
}

onMounted(async () => {
  await initData()
  startAutoRefresh()
  window.addEventListener('task-completed', handleTaskCompleted as EventListener)
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('task-completed', handleTaskCompleted as EventListener)
})

const currentFolderName = computed(() => {
  if (currentFolderId.value === 'all') return '全部论文'
  const folder = folderStore.folders.find(f => f.id === currentFolderId.value)
  return folder?.name || '未知文件夹'
})

const handleSelectAll = () => {
  const allIds = filteredPapers.value.map(p => p.id)
  selectedPaperIds.value = new Set(allIds)
}

const handleClearAll = () => {
  selectedPaperIds.value = new Set()
}

const handleSelectPaper = (paper: LibraryPaper) => {
  selectedPaper.value = paper
  paperDetailVisible.value = true
}

const handleBatchDelete = async () => {
  if (selectedPaperIds.value.size === 0) {
    ElMessage.warning('请先选择要删除的论文')
    return
  }
  const paperCount = selectedPaperIds.value.size
  const isAllView = currentFolderId.value === 'all'

  try {
    await ElMessageBox({
      title: '批量删除论文',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip dialog-warning' }, `您选择了 ${paperCount} 篇论文。`),
        h('p', { class: 'dialog-hint' }, isAllView ? '此操作将彻底删除这些论文，不可恢复。' : '请选择操作范围：')
      ]),
      confirmButtonText: isAllView ? '彻底删除' : '从所有位置彻底删除',
      cancelButtonText: isAllView ? '取消' : '仅从当前文件夹移除',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      distinguishCancelAndClose: true,
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm' || (action === 'cancel' && !isAllView)) {
          done()
        } else {
          done()
        }
      }
    })

    if (isAllView) {
      await performGlobalBatchDelete()
    } else {
      // 非全部视图，用户选择了“仅从当前文件夹移除”时，cancel分支会在catch中处理
    }
  } catch (action) {
    if (action === 'confirm') {
      try {
        await ElMessageBox.confirm(`此操作将从所有文件夹中彻底删除 ${paperCount} 篇论文，且不可恢复。确定要继续吗？`, '警告', {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        })
        await performGlobalBatchDelete()
      } catch { /* 取消 */ }
    } else if (action === 'cancel' && !isAllView) {
      await removePapersFromCurrentFolder()
    }
  }
}

const performGlobalBatchDelete = async () => {
  const idsToDelete = Array.from(selectedPaperIds.value)
  try {
    for (const paperId of idsToDelete) {
      await deletePaperApi(paperId)
    }
    for (const paperId of idsToDelete) {
      folderStore.removePaperGlobally(paperId)
      const idx = paperStore.papers.findIndex(p => p.id === paperId)
      if (idx !== -1) paperStore.papers.splice(idx, 1)
    }
    selectedPaperIds.value.clear()
    ElMessage.success(`已彻底删除 ${idsToDelete.length} 篇论文`)
  } catch (error) {
    console.error('[performGlobalBatchDelete] 删除失败:', error)
    ElMessage.error('删除失败，请重试')
  }
}

const removePapersFromCurrentFolder = async () => {
  const folderId = currentFolderId.value
  const idsToRemove = Array.from(selectedPaperIds.value)
  try {
    for (const paperId of idsToRemove) {
      await folderStore.removePaperFromFolder(folderId, paperId)
    }
    selectedPaperIds.value.clear()
    ElMessage.success(`已从当前文件夹移除 ${idsToRemove.length} 篇论文`)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '移除论文失败')
  }
}

const handleBatchCopy = () => {
  if (selectedPaperIds.value.size === 0) {
    ElMessage.warning('请先选择要复制的论文')
    return
  }
  showCopyDialog.value = true
}

const handleConfirmCopy = async (folderId: string) => {
  const paperIds = Array.from(selectedPaperIds.value)
  try {
    await batchAddPapersToFolderApi(folderId, paperIds)
    await folderStore.loadFolders()
    selectedPaperIds.value.clear()
    ElMessage.success(`已将 ${paperIds.length} 篇论文复制到文件夹`)
  } catch (error) {
    console.error('[handleConfirmCopy] 复制失败:', error)
    ElMessage.error('复制失败，请重试')
  }
}

const handleSaveKeyPoints = async (paperId: string, keyPoints: PaperKeyPoints) => {
  try {
    await paperStore.saveKeyPoints(paperId, keyPoints)
    ElMessage.success('关键点已确认')
  } catch (error) {
    console.error('[handleSaveKeyPoints] 保存失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '保存失败')
  }
}

const handlePreviewPdf = (paperId: string) => {
  router.push({ name: 'paper-pdf', params: { paperId } })
}

const onSearch = () => {
  selectedPaperIds.value.clear()
}

// 批量上传成功处理
const handleBatchUploadSuccess = (results: Array<{ paper_id: string; task_id: string; filename: string }>) => {
  console.log('批量上传成功，论文列表：', results)
  if (parsingProgressRef.value) {
    for (const item of results) {
      parsingProgressRef.value.addTask(item.paper_id, item.task_id, item.filename)
    }
  }
  // 刷新列表（可选，会由解析完成事件自动刷新，但为了即时显示论文占位，可以主动刷新一次）
  paperStore.loadPapers()
  folderStore.loadFolders()
}
</script>

<style scoped>
/* 样式保持不变 */
.library-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 20px 20px;
  min-width: 0;
  overflow-y: auto;
}
.toolbar-card {
  padding: 8px 12px;
  border-radius: 14px;
  background: transparent;
  flex-shrink: 0;
}
.list-card {
  flex: 1;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  padding: 12px 0 4px;
  overflow: hidden;
}
.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.selection-area {
  flex-shrink: 0;
}
.select-all-btn {
  background: none;
  border: none;
  font-size: 0.8rem;
  color: var(--text-secondary, #526071);
  cursor: pointer;
  padding: 0;
  font-weight: 500;
  transition: color 0.2s;
}
.select-all-btn:hover {
  color: var(--text-primary, #101828);
}
.selected-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: #f5f0ea;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #6b7280;
}
.clear-all-btn {
  background: none;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0 0 0 4px;
  transition: color 0.2s;
}
.clear-all-btn:hover {
  color: #ef4444;
}
.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid #4a9d9a;
  border-radius: 8px;
  background: #4a9d9a;
  color: white;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.upload-btn:hover {
  background: #3d8b88;
  border-color: #3d8b88;
  box-shadow: 0 2px 8px rgba(74, 157, 154, 0.3);
}
.library-search {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 220px;
  padding: 4px 12px;
  border-radius: 40px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #faf8f5;
  transition: 0.2s;
}
.library-search:focus-within {
  border-color: #4a9d9a;
  box-shadow: 0 0 0 2px rgba(74, 157, 154, 0.12);
}
.library-search input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 0.8rem;
}
.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid #4a9d9a;
  border-radius: 8px;
  background: white;
  color: #4a9d9a;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.copy-btn:hover:not(:disabled) {
  background: #4a9d9a;
  color: white;
  box-shadow: 0 2px 8px rgba(74, 157, 154, 0.3);
}
.copy-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  border-color: #cbd5e1;
  color: #94a3b8;
}
.delete-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: none;
  background: none;
  color: var(--text-secondary, #526071);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
}
.delete-btn:hover:not(:disabled) {
  color: #dc2626;
}
.delete-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.folder-info-bar {
  display: flex;
  gap: 6px;
  align-items: baseline;
  padding: 0 16px 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  margin-bottom: 4px;
}
.current-folder {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1f2937;
}
.paper-count {
  font-size: 0.75rem;
  color: #9ca3af;
}
.library-main::-webkit-scrollbar {
  width: 6px;
}
.library-main::-webkit-scrollbar-track {
  background: #f5f0ea;
  border-radius: 8px;
}
.library-main::-webkit-scrollbar-thumb {
  background: #d4cfc9;
  border-radius: 8px;
}
</style>