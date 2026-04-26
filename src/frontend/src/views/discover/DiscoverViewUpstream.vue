<script setup lang="ts">
import { Search, Document } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import type { LibraryPaper } from '../../api/library'

const quickSearch = ref('')
const selectedPaperId = ref<string>('')

// 模拟文库中的论文数据（实际应从API获取）
const libraryPapers = ref<LibraryPaper[]>([
  {
    id: 'paper-1',
    title: 'Transformers in Vision',
    authors: 'A. Calianham',
    year: 2022,
    status: 'Confirmed',
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
    status: 'Confirmed',
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
    status: 'Confirmed',
    source: 'ICLR',
    keyPoints: {
      background: '传统序列模型的训练效率和并行化能力不足',
      method: '引入自注意力机制实现并行处理',
      innovation: 'Attention机制大幅减少训练时间并提升模型表现',
      conclusion: 'Transformer成为NLP和CV领域的基础架构'
    },
  },
])

// 根据选择的论文生成上下游论文数据
const upstreamPapers = computed(() => {
  if (!selectedPaperId.value) return []
  
  const selectedPaper = libraryPapers.value.find(p => p.id === selectedPaperId.value)
  if (!selectedPaper) return []

  // 这里应该调用API获取真实的上下游论文
  // 目前使用模拟数据
  return [
    {
      id: 'up-1',
      title: 'Transformer Architecture Analysis',
      authors: 'Vaswani, A. et al.',
      venue: 'NeurIPS',
      year: 2017,
      relation: 'Upstream',
      citationCount: 15240,
      description: `基于 "${selectedPaper.title}" 的原始Transformer论文，奠定了注意力机制的基础。`,
    },
    {
      id: 'up-2',
      title: 'BERT: Pre-training of Deep Bidirectional Transformers',
      authors: 'Devlin, J. et al.',
      venue: 'NAACL',
      year: 2019,
      relation: 'Upstream',
      citationCount: 24320,
      description: 'BERT模型开创了双向预训练的新时代。',
    },
    {
      id: 'up-3',
      title: 'RoBERTa: A Robustly Optimized BERT Pretraining Approach',
      authors: 'Liu, Y. et al.',
      venue: 'arXiv',
      year: 2019,
      relation: 'Upstream',
      citationCount: 8760,
      description: '对BERT的训练方式进行了优化，提升了性能。',
    },
  ]
})

const downstreamPapers = computed(() => {
  if (!selectedPaperId.value) return []
  
  const selectedPaper = libraryPapers.value.find(p => p.id === selectedPaperId.value)
  if (!selectedPaper) return []

  // 这里应该调用API获取真实的上下游论文
  // 目前使用模拟数据
  return [
    {
      id: 'down-1',
      title: 'GPT-3: Language Models are Few-Shot Learners',
      authors: 'Brown, T. et al.',
      venue: 'NeurIPS',
      year: 2020,
      relation: 'Downstream',
      citationCount: 12540,
      description: 'GPT-3展示了大规模语言模型的强大能力。',
    },
    {
      id: 'down-2',
      title: 'T5: Exploring the Limits of Transfer Learning',
      authors: 'Raffel, C. et al.',
      venue: 'JMLR',
      year: 2020,
      relation: 'Downstream',
      citationCount: 7890,
      description: 'Text-to-Text Transfer Transformer统一了NLP任务框架。',
    },
  ]
})

// 过滤后的论文列表
const filteredUpstreamPapers = computed(() => {
  const keyword = quickSearch.value.trim().toLowerCase()
  if (!keyword) return upstreamPapers.value
  
  return upstreamPapers.value.filter(
    paper => 
      paper.title.toLowerCase().includes(keyword) ||
      paper.authors.toLowerCase().includes(keyword) ||
      paper.description.toLowerCase().includes(keyword)
  )
})

const filteredDownstreamPapers = computed(() => {
  const keyword = quickSearch.value.trim().toLowerCase()
  if (!keyword) return downstreamPapers.value
  
  return downstreamPapers.value.filter(
    paper => 
      paper.title.toLowerCase().includes(keyword) ||
      paper.authors.toLowerCase().includes(keyword) ||
      paper.description.toLowerCase().includes(keyword)
  )
})

// 处理论文选择
const handlePaperSelect = (paperId: string) => {
  selectedPaperId.value = paperId
  quickSearch.value = '' // 清空搜索框
}
</script>

<template>
  <section class="discover-page">
    <!-- 论文选择区域 -->
    <div class="discover-paper-selector">
      <label class="selector-label">
        <el-icon><Document /></el-icon>
        <span>从我的文库中选择论文：</span>
      </label>
      <el-select
        v-model="selectedPaperId"
        placeholder="请选择一篇已确认的论文"
        class="paper-select"
        @change="handlePaperSelect"
      >
        <el-option
          v-for="paper in libraryPapers"
          :key="paper.id"
          :label="`${paper.title} (${paper.year})`"
          :value="paper.id"
        >
          <div class="select-option">
            <span class="option-title">{{ paper.title }}</span>
            <span class="option-meta">{{ paper.year }} · {{ paper.source }}</span>
          </div>
        </el-option>
      </el-select>
    </div>

    <!-- 搜索栏 -->
    <div v-if="selectedPaperId" class="discover-search-bar">
      <label class="discover-search">
        <el-icon><Search /></el-icon>
        <input v-model="quickSearch" type="text" placeholder="在结果中搜索..." />
      </label>
    </div>

    <!-- 未选择论文时的提示 -->
    <div v-if="!selectedPaperId" class="empty-state">
      <el-icon class="empty-icon"><Document /></el-icon>
      <p>请从上方下拉框选择一篇文库中的论文，查看其上下游关联研究</p>
    </div>

    <!-- 上下游论文列表 -->
    <template v-if="selectedPaperId">
      <!-- 上游论文 -->
      <section class="relation-section">
        <h2 class="section-title">
          <span class="title-badge upstream">↑</span>
          上游论文 ({{ filteredUpstreamPapers.length }})
        </h2>
        <div v-if="filteredUpstreamPapers.length === 0" class="empty-list">
          <p>暂无上游论文</p>
        </div>
        <article v-for="item in filteredUpstreamPapers" :key="item.id" class="discover-item">
          <div class="discover-item__main">
            <h3 class="item-title">{{ item.title }}</h3>
            <div class="item-meta">
              <span>{{ item.year }}</span>
              <span class="meta-separator">·</span>
              <span>{{ item.authors }}</span>
              <span class="meta-separator">·</span>
              <span>{{ item.venue }}</span>
              <span class="meta-separator">·</span>
              <span class="citation-count">被引 {{ item.citationCount }}</span>
            </div>
            <p class="item-description">{{ item.description }}</p>
          </div>
          <el-button plain size="small">查看详情</el-button>
        </article>
      </section>

      <!-- 下游论文 -->
      <section class="relation-section">
        <h2 class="section-title">
          <span class="title-badge downstream">↓</span>
          下游论文 ({{ filteredDownstreamPapers.length }})
        </h2>
        <div v-if="filteredDownstreamPapers.length === 0" class="empty-list">
          <p>暂无下游论文</p>
        </div>
        <article v-for="item in filteredDownstreamPapers" :key="item.id" class="discover-item">
          <div class="discover-item__main">
            <h3 class="item-title">{{ item.title }}</h3>
            <div class="item-meta">
              <span>{{ item.year }}</span>
              <span class="meta-separator">·</span>
              <span>{{ item.authors }}</span>
              <span class="meta-separator">·</span>
              <span>{{ item.venue }}</span>
              <span class="meta-separator">·</span>
              <span class="citation-count">被引 {{ item.citationCount }}</span>
            </div>
            <p class="item-description">{{ item.description }}</p>
          </div>
          <el-button plain size="small">查看详情</el-button>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.discover-page {
  display: grid;
  gap: 0.9rem;
}

/* 论文选择器样式 */
.discover-paper-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 10px;
  border: 1px solid var(--line-soft);
}

.selector-label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
  font-size: 0.95rem;
  font-weight: 500;
  white-space: nowrap;
}

.paper-select {
  flex: 1;
  min-width: 300px;
}

.select-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.option-title {
  font-weight: 500;
  color: var(--text-primary);
}

.option-meta {
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

/* 搜索栏样式 */
.discover-search-bar {
  margin-bottom: 0.9rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid var(--line-soft);
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

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--text-tertiary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state p {
  font-size: 0.95rem;
  margin: 0;
}

/* 关系分区样式 */
.relation-section {
  margin-top: 1.5rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0 0 1rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
}

.title-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 700;
}

.title-badge.upstream {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.title-badge.downstream {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.empty-list {
  padding: 2rem;
  text-align: center;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px dashed var(--line-soft);
}

.empty-list p {
  margin: 0;
  font-size: 0.9rem;
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
  padding: 1rem;
  margin-bottom: 0.8rem;
  border-radius: 8px;
  border: 1px solid var(--line-soft);
  background: white;
  transition: all 0.2s ease;
}

.discover-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-color: var(--brand-color);
}

.item-title {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.meta-separator {
  opacity: 0.6;
}

.citation-count {
  color: var(--brand-color);
  font-weight: 500;
}

.item-description {
  color: var(--text-tertiary);
  font-size: 0.88rem;
  margin: 0;
  line-height: 1.6;
}

/* 自定义 el-select 白色样式 */
:deep(.paper-select .el-input__wrapper),
:deep(.paper-select .el-select__wrapper) {
  background-color: white !important;
  border: 1px solid var(--line-soft) !important;
}

:deep(.paper-select .el-input__inner) {
  background-color: white;
  color: var(--text-primary);
}

:deep(.paper-select .el-input__suffix) {
  color: var(--text-secondary);
}

/* 选项高亮样式 */
:deep(.el-select .el-select-dropdown__item.hover),
:deep(.el-select .el-select-dropdown__item:hover) {
  background-color: var(--bg-secondary);
}

/* 选择器聚焦样式 */
:deep(.paper-select.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--brand-color) inset !important;
}

@media (max-width: 820px) {
  .discover-paper-selector {
    flex-direction: column;
    align-items: stretch;
  }

  .paper-select {
    min-width: 0;
  }

  .discover-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .discover-search {
    width: 100%;
    min-width: 0;
  }
}
</style>