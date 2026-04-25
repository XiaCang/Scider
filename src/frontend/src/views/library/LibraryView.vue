<script setup lang="ts">
import { EditPen, FolderOpened, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, ref } from 'vue'

import type { LibraryPaper } from '../../api/library'
import LibraryFolder from './LibraryFolder.vue'

interface LibraryFolder {
  id: string
  name: string
  paperIds: string[]
  children?: LibraryFolder[]
}

const searchQuery = ref('')
const selectedPaperId = ref('paper-4')
const draftKeyPoints = ref('1. Attention mechanism\n2. Parallel processing\n3. Reduced training time')
const folderPanelVisible = ref(true)
const selectedFolderId = ref<string>('all')
const editingFolderId = ref<string | null>(null)
const editingFolderName = ref('')
const expandedFolders = ref<Set<string>>(new Set())

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
    keyPoints: ['Visual tokenization', 'Scalable encoder blocks'],
  },
  {
    id: 'paper-2',
    title: 'Transformers in Poraios and Grapheni Methods',
    authors: 'R. K. Rainur',
    year: 2023,
    status: 'Completed',
    source: 'arXiv',
    keyPoints: ['Cross-modal alignment', 'Hybrid retrieval'],
  },
  {
    id: 'paper-3',
    title: 'Transformers in Vision',
    authors: 'R. S. Soft',
    year: 2023,
    status: 'Completed',
    source: 'NeurIPS',
    keyPoints: ['Domain adaptation', 'Zero-shot transfer'],
  },
  {
    id: 'paper-4',
    title: 'Transformers in Vision',
    authors: 'R. C. Bamer, R.A',
    year: 2022,
    status: 'Awaiting Review',
    source: 'ICLR',
    keyPoints: ['Attention mechanism', 'Parallel processing', 'Reduced training time'],
  },
  {
    id: 'paper-5',
    title: 'Transformens and Meal Designers in Vision',
    authors: 'A. Steruan R. Maris',
    year: 2023,
    status: 'Completed',
    source: 'ECCV',
    keyPoints: ['Dataset efficiency', 'Training recipe'],
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
  selectedPaperId.value = paper.id
  draftKeyPoints.value = paper.keyPoints.map((item, index) => `${index + 1}. ${item}`).join('\n')
}

const handleSave = () => {
  const paper = papers.value.find((item) => item.id === selectedPaperId.value)
  if (!paper) {
    return
  }

  paper.keyPoints = draftKeyPoints.value
    .split('\n')
    .map((item) => item.trim().replace(/^\d+\.\s*/, ''))
    .filter(Boolean)
  paper.status = 'Completed'
  ElMessage.success('Key Points saved locally. Replace with saveKeyPointsApi later.')
}

// 处理文件夹相关事件
const handleCreateFolderEvent = async () => {
  try {
    const { value: folderName } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '文件夹名称不能为空',
    })
    
    const newFolder: LibraryFolder = {
      id: `folder-${Date.now()}`,
      name: folderName,
      paperIds: [],
    }
    
    folders.value.push(newFolder)
    ElMessage.success('文件夹创建成功')
  } catch {
    // 用户取消操作
  }
}

const handleCreateRootFolderEvent = (folder: LibraryFolder) => {
  folders.value.push(folder)
  ElMessage.success('文件夹创建成功')
}

const handleEditFolderEvent = (folder: LibraryFolder) => {
  editingFolderId.value = folder.id
  editingFolderName.value = folder.name
}

const statusClassMap: Record<LibraryPaper['status'], string> = {
  Processing: 'is-warning',
  Completed: 'is-success',
  'Awaiting Review': 'is-brand',
}
</script>

<template>
  <section class="library-page">
    <!-- 文件夹抽屉组件 -->
    <LibraryFolder
      v-model:selected-folder-id="selectedFolderId"
      v-model:expanded-folders="expandedFolders"
      v-model:folder-panel-visible="folderPanelVisible"
      :folders="folders"
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
                {{ row.status }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="Action" width="200">
            <template #default="{ row }">
              <el-button text @click="handleReview(row)">
                <el-icon><EditPen /></el-icon>
                Review Key Points 
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="library-review">
        <div class="library-review__header">
          <div>
            <h2 class="section-title">Key Points Review</h2>
            <p class="section-description">这里是后续对接异步提炼结果和人工校对的入口区域。</p>
          </div>
          <span class="status-pill is-brand">
            <el-icon><FolderOpened /></el-icon>
            {{ selectedPaperId }}
          </span>
        </div>

        <el-input
          v-model="draftKeyPoints"
          type="textarea"
          :rows="8"
          placeholder="Review and edit extracted key points..."
        />

        <div class="library-review__actions">
          <el-button type="primary" @click="handleSave">Save</el-button>
        </div>
      </section>
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

.library-review__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.8rem;
}

.library-review {
  padding-top: 1rem;
}

.library-review__actions {
  display: flex;
  justify-content: flex-start;
  margin-top: 0.8rem;
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
