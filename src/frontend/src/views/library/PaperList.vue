<script setup lang="ts">
import { computed, ref, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { EditPen, Search, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { LibraryPaper, PaperKeyPoints } from '../../types/library'
import PaperDetail from './paper/PaperDetail.vue'
import { usePaperStore } from '../../store/paper'
import { useFolderStore } from '../../store/folder'

const route = useRoute()
const router = useRouter()
const paperStore = usePaperStore()
const folderStore = useFolderStore()

const searchQuery = ref('')
const paperDetailVisible = ref(false)
const selectedPaper = ref<LibraryPaper | null>(null)

// 当前文件夹 ID（来自路由）
const currentFolderId = computed(() => route.params.folderId as string || 'all')

// 当前文件夹的论文列表（利用 store 的计算属性）
const folderPapers = computed(() => {
  if (currentFolderId.value === 'all') return paperStore.papers
  const folder = folderStore.folders.find(f => f.id === currentFolderId.value)
  if (!folder) return []
  return paperStore.getPapersByIds(folder.paperIds)
})

// 搜索过滤
const filteredPapers = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return folderPapers.value
  return folderPapers.value.filter(p => p.title.toLowerCase().includes(keyword))
})

// 当前文件夹名称（用于头部展示）
const currentFolderName = computed(() => {
  if (currentFolderId.value === 'all') return '全部论文'
  const folder = folderStore.folders.find(f => f.id === currentFolderId.value)
  return folder?.name || '未知文件夹'
})

// 操作函数
const handleReview = (paper: LibraryPaper) => {
  selectedPaper.value = paper
  paperDetailVisible.value = true
}

const handleDeletePaper = async (paper: LibraryPaper) => {
  try {
    await ElMessageBox({
      title: '删除论文',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip dialog-warning' }, `确定要删除论文 "${paper.title}" 吗？`),
        h('p', { class: 'dialog-hint' }, '请选择删除范围：')
      ]),
      confirmButtonText: currentFolderId.value !== 'all' ? '从所有位置彻底删除' : '从所有位置删除',
      cancelButtonText: currentFolderId.value !== 'all' ? '仅从当前文件夹移除' : '取消',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      distinguishCancelAndClose: true,
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm' || (action === 'cancel' && currentFolderId.value !== 'all')) {
          done()
        } else {
          done()
        }
      }
    })

    if (currentFolderId.value === 'all') {
      // 全部视图 → 全局删除
      await performGlobalDelete(paper)
    }
  } catch (action) {
    if (action === 'confirm') {
      // 彻底删除
      try {
        await ElMessageBox.confirm('此操作将从所有文件夹中彻底删除该论文,且不可恢复。确定要继续吗?', '警告', {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        })
        await performGlobalDelete(paper)
      } catch { /* 取消 */ }
    } else if (action === 'cancel' && currentFolderId.value !== 'all') {
      // 仅从当前文件夹移除
      await folderStore.removePaperFromFolder(currentFolderId.value, paper.id)
      ElMessage.success('已从当前文件夹移除')
    }
  }
}

const performGlobalDelete = async (paper: LibraryPaper) => {
  // 从所有文件夹中移除
  folderStore.removePaperGlobally(paper.id)
  // 从论文列表中删除
  const idx = paperStore.papers.findIndex(p => p.id === paper.id)
  if (idx !== -1) paperStore.papers.splice(idx, 1)
  ElMessage.success('论文已彻底删除')
}

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

// 状态映射
const statusTextMap: Record<string, string> = {
  Processing: '处理中',
  PendingConfirmation: '未确认',
  Confirmed: '已确认',
}
const statusClassMap: Record<string, string> = {
  Processing: 'is-warning',
  PendingConfirmation: 'is-brand',
  Confirmed: 'is-success',
}
</script>

<template>
  <div class="library-main">
    <header class="library-header">
      <div class="library-header__left">
        <span class="current-folder">{{ currentFolderName }}</span>
      </div>
      <label class="library-search">
        <el-icon><Search /></el-icon>
        <input v-model="searchQuery" type="text" placeholder="Search by title..." />
      </label>
    </header>

    <section class="library-table">
      <el-table :data="filteredPapers" row-key="id">
        <el-table-column prop="title" label="Title" min-width="300" />
        <el-table-column prop="authors" label="Authors" min-width="180" />
        <el-table-column prop="year" label="Year" width="100" />
        <el-table-column label="Status" width="170">
          <template #default="{ row }">
            <span class="status-pill" :class="statusClassMap[row.status]">
              {{ statusTextMap[row.status] }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="Action" width="200">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button text @click="handleReview(row)">
                <el-icon><EditPen /></el-icon>
                详情
              </el-button>
              <el-button text type="danger" @click="handleDeletePaper(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <PaperDetail
      v-model="paperDetailVisible"
      :paper="selectedPaper"
      @save="handleSaveKeyPoints"
      @preview-pdf="handlePreviewPdf"
    />
  </div>
</template>

<style scoped>
/* 保留原 .library-main 及相关样式 */
.library-main {
  flex: 1;
  display: grid;
  gap: 0.9rem;
  padding: 1.2rem 1.5rem 1.5rem;
  min-width: 0;
  margin-left: 280px; /* 配合抽屉面板宽度 */
  transition: margin-left 0.3s;
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid var(--line-soft);
}

.current-folder {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.library-search {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 280px;
  padding: 0.56rem 0.8rem;
  border-radius: 10px;
  border: 1px solid var(--line-soft);
  background: white;
}

.library-search input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
}

.library-table {
  padding: 0.8rem 0;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

/* 状态 pill 样式请根据项目自行补充 */
</style>