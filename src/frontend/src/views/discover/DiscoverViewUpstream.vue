<script setup lang="ts">
import { onMounted } from 'vue'
import { Search, Document } from '@element-plus/icons-vue'
import { useCitationGraph } from '../../discover/composables/useCitationGraph'

const {
  selectedPaperId,
  selectedPaper,
  libraryPapers,
  upstreamLoading,
  downstreamLoading,
  upstreamError,
  downstreamError,
  upstreamKeyword,
  downstreamKeyword,
  filteredUpstreamPapers,
  filteredDownstreamPapers,
  selectPaper,
  clearSelection,
  ensureLibraryLoaded,
} = useCitationGraph()

onMounted(() => {
  ensureLibraryLoaded()
})
</script>

<template>
  <section class="discover-page">
    <!-- 论文选择器 -->
    <div class="discover-paper-selector">
      <label class="selector-label">
        <el-icon><Document /></el-icon>
        <span>从文库中选择论文：</span>
      </label>
      <el-select
        v-model="selectedPaperId"
        placeholder="请选择一篇已确认的论文"
        class="paper-select"
        filterable
        clearable
        @change="selectPaper"
        @clear="clearSelection"
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

    <!-- 未选择论文时的提示 -->
    <div v-if="!selectedPaperId" class="empty-state">
      <el-icon class="empty-icon"><Document /></el-icon>
      <p>请从上方下拉框选择一篇文库中的论文，查看其上下游关联研究</p>
    </div>

    <!-- 已选择论文 —— 上下游结果 -->
    <template v-if="selectedPaperId">
      <!-- 上游搜索 -->
      <div class="citation-search-bar">
        <label class="citation-search">
          <el-icon><Search /></el-icon>
          <input v-model="upstreamKeyword" type="text" placeholder="在上游论文中搜索..." />
        </label>
      </div>

      <!-- 上游论文 -->
      <section class="relation-section">
        <h2 class="section-title">
          <span class="title-badge upstream">↑</span>
          上游论文
          <span class="count-badge">{{ filteredUpstreamPapers.length }}</span>
          <span v-if="selectedPaper" class="selected-hint">
            基于 · {{ selectedPaper.title }}
          </span>
        </h2>

        <div v-if="upstreamLoading" class="state-message">加载上游论文中...</div>
        <div v-else-if="upstreamError" class="state-message state-error">{{ upstreamError }}</div>
        <div v-else-if="filteredUpstreamPapers.length === 0" class="paper-empty">
          <p>暂无上游论文</p>
        </div>

        <article v-for="item in filteredUpstreamPapers" :key="item.id" class="citation-item">
          <div class="citation-item__main">
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

      <!-- 下游搜索 -->
      <div class="citation-search-bar">
        <label class="citation-search">
          <el-icon><Search /></el-icon>
          <input v-model="downstreamKeyword" type="text" placeholder="在下游论文中搜索..." />
        </label>
      </div>

      <!-- 下游论文 -->
      <section class="relation-section">
        <h2 class="section-title">
          <span class="title-badge downstream">↓</span>
          下游论文
          <span class="count-badge">{{ filteredDownstreamPapers.length }}</span>
        </h2>

        <div v-if="downstreamLoading" class="state-message">加载下游论文中...</div>
        <div v-else-if="downstreamError" class="state-message state-error">{{ downstreamError }}</div>
        <div v-else-if="filteredDownstreamPapers.length === 0" class="paper-empty">
          <p>暂无下游论文</p>
        </div>

        <article v-for="item in filteredDownstreamPapers" :key="item.id" class="citation-item">
          <div class="citation-item__main">
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
  max-width: 960px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

/* 论文选择器 */
.discover-paper-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.2rem;
  background: var(--bg-secondary, #f8fafc);
  border-radius: 10px;
  border: 1px solid var(--line-soft, #e2e8f0);
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
  color: var(--text-tertiary, #94a3b8);
}

/* 搜索栏 */
.citation-search-bar {
  margin-top: 0.5rem;
}

.citation-search {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  max-width: 400px;
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--line-soft, #e2e8f0);
  background: white;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.citation-search input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
  color: var(--text-primary);
  font-size: 0.85rem;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--text-tertiary, #94a3b8);
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

.state-message {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: var(--text-tertiary, #94a3b8);
  font-size: 0.9rem;
}

.state-error {
  color: #ef4444;
}

/* 关系分区 */
.relation-section {
  margin-top: 0.5rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0 0 1rem;
  font-size: 1.1rem;
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
  flex-shrink: 0;
}

.title-badge.upstream {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.title-badge.downstream {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 11px;
  background: var(--bg-secondary, #f1f5f9);
  color: var(--text-tertiary, #94a3b8);
  font-size: 0.75rem;
  font-weight: 600;
}

.selected-hint {
  margin-left: 0.5rem;
  font-size: 0.8rem;
  font-weight: 400;
  color: var(--text-tertiary, #94a3b8);
}

/* 论文卡片 */
.citation-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem;
  margin-bottom: 0.8rem;
  border-radius: 8px;
  border: 1px solid var(--line-soft, #e2e8f0);
  background: white;
  transition: all 0.2s ease;
}

.citation-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-color: var(--brand, #4f46e5);
}

.citation-item:last-child {
  margin-bottom: 0;
}

.item-title {
  margin: 0 0 0.4rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.4rem;
  color: var(--text-secondary);
  font-size: 0.83rem;
  flex-wrap: wrap;
}

.meta-separator {
  opacity: 0.6;
}

.citation-count {
  color: var(--brand, #4f46e5);
  font-weight: 500;
}

.item-description {
  color: var(--text-tertiary);
  font-size: 0.88rem;
  margin: 0;
  line-height: 1.6;
}

.paper-empty {
  padding: 2rem;
  text-align: center;
  color: var(--text-tertiary);
  background: var(--bg-secondary, #f8fafc);
  border-radius: 8px;
  border: 1px dashed var(--line-soft, #e2e8f0);
}

.paper-empty p {
  margin: 0;
  font-size: 0.9rem;
}

/* Element Plus overrides */
:deep(.paper-select .el-select__wrapper) {
  background-color: white;
  border: 1px solid var(--line-soft, #e2e8f0);
}

:deep(.paper-select.is-focus .el-select__wrapper) {
  box-shadow: 0 0 0 1px var(--brand, #4f46e5) inset;
}

@media (max-width: 820px) {
  .discover-page {
    padding: 1rem;
  }

  .discover-paper-selector {
    flex-direction: column;
    align-items: stretch;
  }

  .paper-select {
    min-width: 0;
  }

  .citation-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .citation-search {
    max-width: 100%;
  }
}
</style>
