<script setup lang="ts">
import { EditPen, FolderOpened, Search, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, ref, h } from 'vue'
import { useRouter } from 'vue-router'

import type { LibraryPaper, PaperKeyPoints } from '../../api/library'
import { saveKeyPointsApi } from '../../api/library'
import LibraryFolder from './LibraryFolder.vue'
import PaperDetail from './paper/PaperDetail.vue'

interface LibraryFolder {
  id: string
  name: string
  paperIds: string[]
  children?: LibraryFolder[]
}

const searchQuery = ref('')
const selectedPaperId = ref('paper-4')
const folderPanelVisible = ref(true)
const selectedFolderId = ref<string>('all')
const editingFolderId = ref<string | null>(null)
const editingFolderName = ref('')
const expandedFolders = ref<Set<string>>(new Set())
const paperDetailVisible = ref(false)
const selectedPaper = ref<LibraryPaper | null>(null)
const router = useRouter()

const folders = ref<LibraryFolder[]>([
  {
    id: 'folder-1',
    name: '深度学习',
    paperIds: ['paper-1', 'paper-2'],
    children: [
      {
        id: 'folder-1-1',
        name: 'Transformer',
        paperIds: ['paper-1'],
        children: [
          {
            id: 'folder-1-1-1',
            name: 'Attention机制',
            paperIds: [],
            children: [
              {
                id: 'folder-1-1-1-1',
                name: 'Self-Attention',
                paperIds: [],
                children: [
                  {
                    id: 'folder-1-1-1-1-1',
                    name: 'Multi-Head Attention',
                    paperIds: [],
                  }
                ]
              }
            ]
          },
          {
            id: 'folder-1-1-2',
            name: 'Positional Encoding',
            paperIds: [],
          }
        ]
      },
      {
        id: 'folder-1-2',
        name: 'CNN',
        paperIds: ['paper-2'],
      },
    ],
  },
  {
    id: 'folder-2',
    name: '计算机视觉',
    paperIds: ['paper-1', 'paper-3', 'paper-5'],
    children: [
      {
        id: 'folder-2-1',
        name: '目标检测',
        paperIds: ['paper-3'],
      },
    ],
  },
  {
    id: 'folder-3',
    name: '自然语言处理',
    paperIds: ['paper-2', 'paper-4'],
  },
])

const papers = ref<LibraryPaper[]>([
  {
    id: 'paper-1',
    title: 'Transformers in Vision',
    authors: 'A. Calianham',
    year: 2022,
    status: 'Processing',
    source: 'CVPR',
    keyPoints: {
      background: '视觉任务中传统CNN的局限性，需要更好的长距离依赖建模',
      method: '将图像分割为visual tokens，使用Transformer编码器处理',
      innovation: '首次将纯Transformer架构应用于计算机视觉任务',
      conclusion: 'ViT在大规模数据集上可以达到甚至超越SOTA CNN的性能'
    },
  },
  {
    id: 'paper-2',
    title: 'Transformers in Poraios and Grapheni Methods',
    authors: 'R. K. Rainur',
    year: 2023,
    status: 'PendingConfirmation',
    source: 'arXiv',
    keyPoints: {
      background: '多模态数据对齐和检索存在语义鸿沟问题',
      method: '采用跨模态对齐技术和混合检索策略',
      innovation: '提出新颖的跨模态表示学习方法',
      conclusion: '显著提升了跨模态检索的准确性和效率'
    },
  },
  {
    id: 'paper-3',
    title: 'Transformers in Vision',
    authors: 'R. S. Soft',
    year: 2023,
    status: 'Confirmed',
    source: 'NeurIPS',
    keyPoints: {
      background: '域适应和零样本迁移在实际应用中面临挑战',
      method: '利用领域自适应技术和零样本学习框架',
      innovation: '设计了新的域不变特征提取器',
      conclusion: '在多个基准测试中实现了优异的零样本迁移性能'
    },
  },
  {
    id: 'paper-4',
    title: 'Transformers in Vision',
    authors: 'R. C. Bamer, R.A',
    year: 2022,
    status: 'PendingConfirmation',
    source: 'ICLR',
    keyPoints: {
      background: '传统序列模型的训练效率和并行化能力不足',
      method: '引入自注意力机制实现并行处理',
      innovation: 'Attention机制大幅减少训练时间并提升模型表现',
      conclusion: 'Transformer成为NLP和CV领域的基础架构'
    },
  },
  {
    id: 'paper-5',
    title: 'Transformens and Meal Designers in Vision',
    authors: 'A. Steruan R. Maris',
    year: 2023,
    status: 'Confirmed',
    source: 'ECCV',
    keyPoints: {
      background: '视觉模型训练需要大量数据和计算资源',
      method: '优化数据集效率和训练配方设计',
      innovation: '提出更高效的训练策略和数据增强方法',
      conclusion: '在减少资源消耗的同时保持了模型性能'
    },
  },
])

const filteredPapers = computed(() => {
  let result = papers.value
  
  // 根据文件夹筛选
  if (selectedFolderId.value !== 'all') {
    const folder = folders.value.find(f => f.id === selectedFolderId.value)
    if (folder) {
      result = result.filter(paper => folder.paperIds.includes(paper.id))
    }
  }
  
  // 根据搜索关键词筛选
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) {
    return result
  }

  return result.filter((paper) => paper.title.toLowerCase().includes(keyword))
})

const handleReview = (paper: LibraryPaper) => {
  selectedPaper.value = paper
  selectedPaperId.value = paper.id
  // 不再需要初始化draftKeyPoints，由PaperDetail组件内部管理
  paperDetailVisible.value = true
}

// 删除论文
const handleDeletePaper = async (paper: LibraryPaper) => {
  try {
    await ElMessageBox({
      title: '删除论文',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip dialog-warning' }, `确定要删除论文 "${paper.title}" 吗？`),
        h('p', { class: 'dialog-hint' }, '请选择删除范围：')
      ]),
      confirmButtonText: selectedFolderId.value !== 'all' ? '从所有位置彻底删除' : '从所有位置删除',
      cancelButtonText: selectedFolderId.value !== 'all' ? '仅从当前文件夹移除' : '取消',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      distinguishCancelAndClose: true,
      beforeClose: (action, instance, done) => {
        if (action === 'confirm') {
          // 用户选择了"从所有位置彻底删除"
          done()
        } else if (action === 'cancel' && selectedFolderId.value !== 'all') {
          // 用户在非全部视图下选择了"仅从当前文件夹移除"
          done()
        } else {
          // 用户关闭对话框或在全部视图下点击取消
          done()
        }
      }
    })
    
    // 执行全局删除(或全部视图下的直接删除)
    if (selectedFolderId.value === 'all') {
      // 在"全部论文"视图下,直接从全局删除
      await performGlobalDelete(paper)
    }
  } catch (action) {
    if (action === 'confirm') {
      // 用户点击了"从所有位置彻底删除"按钮
      try {
        await ElMessageBox.confirm(
          '此操作将从所有文件夹中彻底删除该论文,且不可恢复。确定要继续吗?',
          '警告',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        await performGlobalDelete(paper)
      } catch {
        // 用户取消了彻底删除
      }
    } else if (action === 'cancel' && selectedFolderId.value !== 'all') {
      // 用户点击了"仅从当前文件夹移除"按钮
      const folder = folders.value.find(f => f.id === selectedFolderId.value)
      if (folder) {
        const index = folder.paperIds.indexOf(paper.id)
        if (index > -1) {
          folder.paperIds.splice(index, 1)
          ElMessage.success('已从当前文件夹移除')
        }
      }
    }
    // 用户关闭对话框,不做任何操作
  }
}

// 执行全局删除
const performGlobalDelete = async (paper: LibraryPaper) => {
  // 从所有文件夹中移除
  folders.value.forEach(folder => {
    const removePaperFromFolder = (f: any) => {
      const index = f.paperIds.indexOf(paper.id)
      if (index > -1) {
        f.paperIds.splice(index, 1)
      }
      if (f.children) {
        f.children.forEach(removePaperFromFolder)
      }
    }
    removePaperFromFolder(folder)
  })
  
  // 从论文列表中删除
  const index = papers.value.findIndex(p => p.id === paper.id)
  if (index > -1) {
    papers.value.splice(index, 1)
  }
  
  ElMessage.success('论文已彻底删除')
}

// 保存关键点（从抽屉组件触发）
const handleSaveKeyPoints = async (paperId: string, keyPoints: PaperKeyPoints) => {
  try {
    await saveKeyPointsApi(paperId, keyPoints)
    
    // 更新本地数据
    const paper = papers.value.find((item) => item.id === paperId)
    if (paper) {
      paper.keyPoints = keyPoints
      paper.status = 'Confirmed'  // 确认后状态变为已确认
    }
    
    ElMessage.success('关键点已保存到服务器')
  } catch (error) {
    ElMessage.error('保存失败，请重试')
    console.error('保存关键点失败:', error)
  }
}

// 预览 PDF
const handlePreviewPdf = (paperId: string) => {
  // 跳转到PDF预览页面
  router.push({
    name: 'paper-pdf',
    params: { paperId }
  })
}

// 状态映射（中文显示）
const statusTextMap: Record<LibraryPaper['status'], string> = {
  Processing: '处理中',
  PendingConfirmation: '未确认',
  Confirmed: '已确认',
}

const statusClassMap: Record<LibraryPaper['status'], string> = {
  Processing: 'is-warning',
  PendingConfirmation: 'is-brand',
  Confirmed: 'is-success',
}
</script>

<template>
  <section class="library-page" :class="{ 'folder-panel-open': folderPanelVisible }">
    <!-- 文件夹抽屉组件 -->
    <LibraryFolder
      v-model:selected-folder-id="selectedFolderId"
      v-model:expanded-folders="expandedFolders"
      v-model:folder-panel-visible="folderPanelVisible"
      :folders="folders"
    />

    <!-- 论文详情抽屉 -->
    <PaperDetail
      v-model="paperDetailVisible"
      :paper="selectedPaper"
      @save="handleSaveKeyPoints"
      @preview-pdf="handlePreviewPdf"
    />

    <!-- 主内容区 -->
    <div class="library-main">
      <!-- 顶部工具栏 -->
      <header class="library-header">
        <div class="library-header__left">
          <span v-if="selectedFolderId !== 'all'" class="current-folder">
            当前文件夹：{{ folders.find(f => f.id === selectedFolderId)?.name || '全部' }}
          </span>
          <span v-else class="current-folder">全部论文</span>
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
              <span class="status-pill" :class="statusClassMap[row.status as LibraryPaper['status']]">
                {{ statusTextMap[row.status as LibraryPaper['status']] }}
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

      <!-- 移除旧的Key Points Review区域，因为现在使用PaperDetail抽屉 -->
    </div>
  </section>
</template>

<style scoped>
.library-page {
  display: flex;
  gap: 0;
  min-height: calc(100vh - 60px);
  position: relative;
}

/* 主内容区 */
.library-main {
  flex: 1;
  display: grid;
  gap: 0.9rem;
  padding: 1.2rem 1.5rem 1.5rem;
  min-width: 0;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 当文件夹面板打开时，主内容区右移 */
.library-page.folder-panel-open .library-main {
  margin-left: 280px;
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid var(--line-soft);
}

.library-header__left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.current-folder {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.library-search {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  min-width: min(340px, 100%);
  padding: 0.56rem 0.8rem;
  border-radius: 10px;
  border: 1px solid var(--line-soft);
  background: white;
  color: var(--text-secondary);
  font-size: 0.88rem;
}

.library-search input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
}

.library-table {
  padding: 0.8rem 0 1rem;
  border-bottom: 1px solid var(--line-soft);
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

@media (max-width: 820px) {
  .library-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .library-header__left {
    width: 100%;
    flex-wrap: wrap;
  }

  .library-search {
    width: 100%;
    min-width: 0;
  }
}
</style>

<style>
/* 文件夹操作弹窗全局样式 */
.folder-operation-message-box {
  border-radius: 12px;
  overflow: hidden;
}

.folder-operation-message-box .el-message-box__header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--line-soft);
}

.folder-operation-message-box .el-message-box__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.folder-operation-message-box .el-message-box__content {
  padding: 24px;
}

.folder-operation-message-box .el-message-box__btns {
  padding: 16px 24px 24px;
  display: flex;
  gap: 12px;
}

.folder-operation-message-box .el-button--primary {
  background-color: var(--brand);
  border-color: var(--brand);
}

.folder-operation-message-box .el-button--default {
  background-color: white;
  border-color: var(--line-soft);
}

.folder-operation-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-tip {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.dialog-warning {
  color: var(--danger);
  font-weight: 500;
}

.dialog-hint {
  margin: 8px 0 0 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
</style>
