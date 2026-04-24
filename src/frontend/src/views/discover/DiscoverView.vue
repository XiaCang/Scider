<script setup lang="ts">
import { ArrowDown, Search } from '@element-plus/icons-vue'
import { ref } from 'vue'

const quickSearch = ref('')
const selectedYear = ref<string>('')
const selectedVenue = ref<string>('')
const sortBy = ref<string>('relevance')

const yearOptions = [
  { label: '全部年份', value: '' },
  { label: '2025', value: '2025' },
  { label: '2024', value: '2024' },
  { label: '2023', value: '2023' },
  { label: '2022', value: '2022' },
  { label: '2021及更早', value: '2021' },
]

const venueOptions = [
  { label: '全部类型', value: '' },
  { label: 'arXiv', value: 'arXiv' },
  { label: 'SIGIR', value: 'SIGIR' },
  { label: 'CHI', value: 'CHI' },
  { label: 'ACL', value: 'ACL' },
  { label: 'NeurIPS', value: 'NeurIPS' },
]

const sortOptions = [
  { label: '相关性', value: 'relevance' },
  { label: '最新发表', value: 'year-desc' },
  { label: '最早发表', value: 'year-asc' },
  { label: '标题 A-Z', value: 'title-asc' },
]

const recommendations = [
  {
    id: 'rec-1',
    title: 'Scientific Document VLMs for Reading Assistance',
    authors: 'Smith, J. et al.',
    venue: 'arXiv',
    year: 2025,
    relation: 'Trending',
    reason: '和你当前的"多模态论文理解"方向高度接近，可作为入门综述入口。',
    description: '该研究探讨了视觉语言模型在科学文档阅读辅助中的应用，提供了系统性的分析和评估。',
  },
  {
    id: 'rec-2',
    title: 'Citation-aware Retrieval for Research Exploration',
    authors: 'Johnson, M. et al.',
    venue: 'SIGIR',
    year: 2024,
    relation: 'Upstream',
    reason: '适合作为文献追踪与上下游检索能力的技术参考。',
    description: '提出了一种基于引用感知的检索方法，能够有效追踪学术文献的上下游关系。',
  },
  {
    id: 'rec-3',
    title: 'Interactive Knowledge Graphs for Scholarly Search',
    authors: 'Williams, K. et al.',
    venue: 'CHI',
    year: 2024,
    relation: 'Downstream',
    reason: '和知识图谱可视化及科研探索交互关系较强。',
    description: '研究了交互式知识图谱在学术搜索中的应用，提升了用户探索和理解复杂研究领域的能力。',
  },
]
</script>

<template>
  <section class="discover-page">
    <div class="discover-search-bar">
      <label class="discover-search">
        <el-icon><Search /></el-icon>
        <input v-model="quickSearch" type="text" placeholder="Search papers, authors, topics..." />
      </label>
      
      <div class="discover-filters">
        <el-dropdown trigger="click">
          <el-button plain>
            {{ selectedYear ? yearOptions.find(opt => opt.value === selectedYear)?.label : '年份' }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="option in yearOptions"
                :key="option.value"
                @click="selectedYear = option.value"
              >
                {{ option.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown trigger="click">
          <el-button plain>
            {{ selectedVenue ? venueOptions.find(opt => opt.value === selectedVenue)?.label : '类型' }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="option in venueOptions"
                :key="option.value"
                @click="selectedVenue = option.value"
              >
                {{ option.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown trigger="click">
          <el-button plain>
            {{ sortOptions.find(opt => opt.value === sortBy)?.label || '排序' }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="option in sortOptions"
                :key="option.value"
                @click="sortBy = option.value"
              >
                {{ option.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <section class="discover-list">
      <article v-for="item in recommendations" :key="item.id" class="discover-item">
        <div class="discover-item__main">
          <h2 class="item-title">{{ item.title }}</h2>
          <div class="item-meta">
            <span>{{ item.year }}</span>
            <span class="meta-separator">·</span>
            <span>{{ item.authors }}</span>
            <span class="meta-separator">·</span>
            <span>{{ item.venue }}</span>
          </div>
          <p class="item-description">{{ item.description }}</p>
        </div>
        <el-button plain>View Details</el-button>
      </article>
    </section>
  </section>
</template>

<style scoped>
.discover-page {
  display: grid;
  gap: 0.9rem;
}

.discover-search-bar {
  margin-bottom: 0.9rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid var(--line-soft);
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  align-items: center;
}

.discover-search {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  min-width: min(500px, 48vw);
  padding: 0.56rem 0.8rem;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: white;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.discover-search input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
  color: var(--text-primary);
}

.discover-filters {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.discover-list {
  display: grid;
  gap: 1rem;
  padding-top: 1rem;
}

.discover-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 0.8rem;
  border-top: 1px solid var(--line-soft);
}

.discover-item:first-child {
  padding-top: 0;
  border-top: 0;
}

.item-title {
  margin: 0 0 0.5rem;
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-primary);
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.88rem;
}

.meta-separator {
  opacity: 0.6;
}

.item-description {
  color: var(--text-tertiary);
  font-size: 0.88rem;
  margin: 0;
  line-height: 1.6;
}

@media (max-width: 820px) {
  .discover-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .discover-search {
    width: 100%;
    min-width: 0;
  }

  .discover-filters {
    width: 100%;
  }

  .discover-filters :deep(.el-select) {
    flex: 1;
    min-width: 120px;
  }
}
</style>
