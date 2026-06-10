<script setup lang="ts">
import { EditPen, FolderOpened, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'

import type { LibraryPaper } from '../../api/library'

const searchQuery = ref('')
const selectedPaperId = ref('paper-4')
const draftKeyPoints = ref('1. Attention mechanism\n2. Parallel processing\n3. Reduced training time')

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
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) {
    return papers.value
  }

  return papers.value.filter((paper) => paper.title.toLowerCase().includes(keyword))
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

const statusClassMap: Record<LibraryPaper['status'], string> = {
  Processing: 'is-warning',
  Completed: 'is-success',
  'Awaiting Review': 'is-brand',
}
</script>

<template>
  <section class="library-page">
    <header class="library-header">
      <div>
        <h1 class="section-title">My Library</h1>
        <p class="section-description">上传后的论文会在这里形成基础文库，可用于搜索、审核 Key Points 和后续图谱关联。</p>
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
  </section>
</template>

<style scoped>
.library-page {
  display: grid;
  gap: 0.9rem;
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid var(--line-soft);
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
  .library-header,
  .library-review__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .library-search {
    width: 100%;
    min-width: 0;
  }
}
</style>
