<!-- PaperList.vue（原 LibraryMain 视图，顶栏控件重构） -->
<script setup lang="ts">
import { computed, ref, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Delete, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { LibraryPaper, PaperKeyPoints } from '../../types/library'  
import PaperDetail from './paper/PaperDetail.vue'
import PaperCardList from './paper/PaperListItem.vue'
import { usePaperStore } from '../../store/paper'
import { useFolderStore } from '../../store/folder'

const route = useRoute()
const router = useRouter()
const paperStore = usePaperStore()
const folderStore = useFolderStore()

const searchQuery = ref('')
const paperDetailVisible = ref(false)
const selectedPaper = ref<LibraryPaper | null>(null)
const selectedPaperIds = ref<Set<string>>(new Set())  // 选中的论文ID

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

const currentFolderName = computed(() => {
  if (currentFolderId.value === 'all') return '全部论文'
  const folder = folderStore.folders.find(f => f.id === currentFolderId.value)
  return folder?.name || '未知文件夹'
})

// 全选当前筛选结果
const handleSelectAll = () => {
  const allIds = filteredPapers.value.map(p => p.id)
  selectedPaperIds.value = new Set(allIds)
}

// 清除所有选中
const handleClearAll = () => {
  selectedPaperIds.value = new Set()
}

// 处理单个论文预览（点击卡片主体）
const handleSelectPaper = (paper: LibraryPaper) => {
  selectedPaper.value = paper
  paperDetailVisible.value = true
}

// 批量删除
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
      // 全部视图 → 全局删除
      await performGlobalBatchDelete()
    } else {
      // 非全部视图，用户选择了“仅从当前文件夹移除”（cancel分支）会在catch中处理
    }
  } catch (action) {
    if (action === 'confirm') {
      // 彻底删除（全部视图下 confirm 就是彻底删除；非全部视图下 confirm 也是彻底删除）
      try {
        await ElMessageBox.confirm(`此操作将从所有文件夹中彻底删除 ${paperCount} 篇论文，且不可恢复。确定要继续吗？`, '警告', {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        })
        await performGlobalBatchDelete()
      } catch { /* 取消 */ }
    } else if (action === 'cancel' && !isAllView) {
      // 仅从当前文件夹移除
      await removePapersFromCurrentFolder()
    }
  }
}

// 彻底删除选中的论文（全局）
const performGlobalBatchDelete = async () => {
  const idsToDelete = Array.from(selectedPaperIds.value)
  for (const paperId of idsToDelete) {
    folderStore.removePaperGlobally(paperId)
    const idx = paperStore.papers.findIndex(p => p.id === paperId)
    if (idx !== -1) paperStore.papers.splice(idx, 1)
  }
  selectedPaperIds.value.clear()
  ElMessage.success(`已彻底删除 ${idsToDelete.length} 篇论文`)
}

// 仅从当前文件夹移除（不删除论文本体）
const removePapersFromCurrentFolder = async () => {
  const folderId = currentFolderId.value
  const idsToRemove = Array.from(selectedPaperIds.value)
  for (const paperId of idsToRemove) {
    await folderStore.removePaperFromFolder(folderId, paperId)
  }
  selectedPaperIds.value.clear()
  ElMessage.success(`已从当前文件夹移除 ${idsToRemove.length} 篇论文`)
}

// 保存关键点（单篇）
const handleSaveKeyPoints = async (paperId: string, keyPoints: PaperKeyPoints) => {
  try {
    await paperStore.saveKeyPoints(paperId, keyPoints)
    ElMessage.success('关键点已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

const handlePreviewPdf = (paperId: string) => {
  router.push({ name: 'paper-pdf', params: { paperId } })
}

// 监听搜索时清空选中
const onSearch = () => {
  selectedPaperIds.value.clear()
}
</script>

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
  </div>
</template>

<style scoped>
.library-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 20px 20px;
  min-width: 0;
  overflow-y: auto;
}

/* ── 工具栏卡片 ── */
.toolbar-card {
  padding: 8px 12px;
  border-radius: 14px;
  background: transparent;
  flex-shrink: 0;
}

/* ── 论文列表卡片 ── */
.list-card {
  flex: 1;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(148, 163, 184, 0.08);
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
  padding: 12px 0 4px;
  overflow: hidden;
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0;
  /* border removed */
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
  background-color: #f1f5f9;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #475569;
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

.library-search {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 220px;
  padding: 4px 12px;
  border-radius: 40px;
  border: 1px solid rgba(148, 163, 184, 0.15);
  background: transparent;
  transition: 0.2s;
}

.library-search:focus-within {
  border-color: var(--text-tertiary, #8a94a6);
  box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.12);
}

.library-search input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 0.8rem;
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
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
  margin-bottom: 4px;
}

.current-folder {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
}

.paper-count {
  font-size: 0.75rem;
  color: #5b6e8c;
}

/* 滚动条 */
.library-main::-webkit-scrollbar {
  width: 6px;
}
.library-main::-webkit-scrollbar-track {
  background: #e2e8f0;
  border-radius: 8px;
}
.library-main::-webkit-scrollbar-thumb {
  background: #94a3b8;
  border-radius: 8px;
}
</style>