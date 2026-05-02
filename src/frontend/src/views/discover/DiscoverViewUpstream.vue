<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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

/* ── 自定义下拉选择 ── */
const selectorOpen = ref(false)
const searchQuery = ref('')

const filteredLibraryPapers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return libraryPapers.value
  return libraryPapers.value.filter(
    p => p.title.toLowerCase().includes(q) || p.authors?.toLowerCase().includes(q)
  )
})

function toggleSelector() {
  selectorOpen.value = !selectorOpen.value
  if (selectorOpen.value) searchQuery.value = ''
}

function onSelectPaper(id: string) {
  selectPaper(id)
  selectorOpen.value = false
}

function onClear() {
  clearSelection()
  selectorOpen.value = false
}

function closeSelector() {
  selectorOpen.value = false
}

function viewDetails(itemId: string) {
  console.log('view details:', itemId)
}
</script>

<template>
  <section class="upstream-page" @click="closeSelector">

    <!-- ── 论文选择器 ── -->
    <div class="paper-selector">
      <div class="selector-label">
        <el-icon><Document /></el-icon>
        <span>选择论文</span>
      </div>

      <div class="selector-control">
        <button class="selector-trigger" @click.stop="toggleSelector">
          <span v-if="selectedPaper" class="trigger-text">{{ selectedPaper.title }}</span>
          <span v-else class="trigger-placeholder">从文库中选择一篇论文查看上下游...</span>
          <svg class="trigger-chevron" :class="{ up: selectorOpen }" width="12" height="8" viewBox="0 0 12 8"><path d="M2 2l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>

        <Transition name="fade-drop">
          <div v-if="selectorOpen" class="selector-dropdown" @click.stop>
            <div class="selector-search-wrap">
              <el-icon class="selector-search-icon"><Search /></el-icon>
              <input
                v-model="searchQuery"
                class="selector-search"
                placeholder="搜索论文标题..."
              />
            </div>
            <div class="selector-list">
              <button
                v-for="paper in filteredLibraryPapers"
                :key="paper.id"
                class="selector-item"
                :class="{ active: paper.id === selectedPaperId }"
                @click="onSelectPaper(paper.id)"
              >
                <span class="si-title">{{ paper.title }}</span>
                <span class="si-meta">{{ paper.year }} · {{ paper.source || '文库' }}</span>
              </button>
              <div v-if="filteredLibraryPapers.length === 0" class="selector-empty">
                无匹配结果
              </div>
            </div>
            <div v-if="selectedPaper" class="selector-footer">
              <button class="selector-clear" @click="onClear">清除选择</button>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- ── 未选择 ── -->
    <div v-if="!selectedPaperId" class="empty-state">
      <div class="empty-graphic">
        <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
          <circle cx="28" cy="28" r="26" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="4 4" fill="none"/>
          <path d="M28 16v16M20 24h16" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
      <p class="empty-text">从上方选择一篇文库中的论文</p>
      <p class="empty-hint">查看其参考文献（上游）与引证文献（下游）</p>
    </div>

    <!-- ── 已选择论文 —— 上下游结果 ── -->
    <template v-if="selectedPaperId">
      <!-- 上游 -->
      <section class="relation-section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="title-badge upstream">↑</span>
            <h2 class="section-title">上游论文</h2>
            <span class="count-pill">{{ filteredUpstreamPapers.length }}</span>
          </div>
          <div v-if="selectedPaper" class="section-context">
            基于 <strong>{{ selectedPaper.title }}</strong>
          </div>
        </div>

        <div v-if="upstreamLoading" class="state-message">
          <div class="loading-dots"><span /><span /><span /></div>
          <p>加载上游论文中...</p>
        </div>
        <div v-else-if="upstreamError" class="state-message state-error">
          <p>{{ upstreamError }}</p>
        </div>

        <template v-else>
          <!-- 搜索 -->
          <div class="inline-search">
            <el-icon class="is-icon"><Search /></el-icon>
            <input v-model="upstreamKeyword" placeholder="在上游论文中搜索..." />
          </div>

          <div v-if="filteredUpstreamPapers.length === 0" class="empty-list">
            <p>{{ upstreamKeyword ? '未找到匹配的论文' : '暂无上游论文' }}</p>
          </div>

          <TransitionGroup name="card-enter" tag="div" class="card-list">
            <article v-for="item in filteredUpstreamPapers" :key="item.id" class="paper-card">
              <div class="card-body">
                <h3 class="card-title">{{ item.title }}</h3>
                <div class="card-meta">
                  <span>{{ item.year }}</span>
                  <span class="meta-dot">·</span>
                  <span>{{ item.authors }}</span>
                  <span v-if="item.venue" class="meta-dot">·</span>
                  <span v-if="item.venue">{{ item.venue }}</span>
                  <span class="meta-dot">·</span>
                  <span class="meta-citation">被引 {{ item.citationCount }}</span>
                </div>
                <p class="card-desc">{{ item.description }}</p>
              </div>
              <div class="card-actions">
                <button class="view-link" @click="viewDetails(item.id)">
                  查看详情
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M5 3l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
              </div>
            </article>
          </TransitionGroup>
        </template>
      </section>

      <!-- 下游 -->
      <section class="relation-section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="title-badge downstream">↓</span>
            <h2 class="section-title">下游论文</h2>
            <span class="count-pill">{{ filteredDownstreamPapers.length }}</span>
          </div>
        </div>

        <div v-if="downstreamLoading" class="state-message">
          <div class="loading-dots"><span /><span /><span /></div>
          <p>加载下游论文中...</p>
        </div>
        <div v-else-if="downstreamError" class="state-message state-error">
          <p>{{ downstreamError }}</p>
        </div>

        <template v-else>
          <div class="inline-search">
            <el-icon class="is-icon"><Search /></el-icon>
            <input v-model="downstreamKeyword" placeholder="在下游论文中搜索..." />
          </div>

          <div v-if="filteredDownstreamPapers.length === 0" class="empty-list">
            <p>{{ downstreamKeyword ? '未找到匹配的论文' : '暂无下游论文' }}</p>
          </div>

          <TransitionGroup name="card-enter" tag="div" class="card-list">
            <article v-for="item in filteredDownstreamPapers" :key="item.id" class="paper-card">
              <div class="card-body">
                <h3 class="card-title">{{ item.title }}</h3>
                <div class="card-meta">
                  <span>{{ item.year }}</span>
                  <span class="meta-dot">·</span>
                  <span>{{ item.authors }}</span>
                  <span v-if="item.venue" class="meta-dot">·</span>
                  <span v-if="item.venue">{{ item.venue }}</span>
                  <span class="meta-dot">·</span>
                  <span class="meta-citation">被引 {{ item.citationCount }}</span>
                </div>
                <p class="card-desc">{{ item.description }}</p>
              </div>
              <div class="card-actions">
                <button class="view-link" @click="viewDetails(item.id)">
                  查看详情
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M5 3l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
              </div>
            </article>
          </TransitionGroup>
        </template>
      </section>
    </template>
  </section>
</template>

<style scoped>
/* ════════ 页面布局 ════════ */
.upstream-page {
  max-width: 880px;
  margin: 0 auto;
  padding: 2rem 2rem 3rem;
}

/* ════════ 论文选择器 ════════ */
.paper-selector {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1.25rem;
}

.selector-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
}

.selector-control {
  position: relative;
}

.selector-trigger {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  padding: 0.4rem 0.7rem;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.15);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.selector-trigger:hover {
  background: rgba(255, 255, 255, 0.85);
  border-color: rgba(148, 163, 184, 0.25);
}

.selector-trigger:focus-within {
  border-color: rgba(47, 107, 255, 0.25);
  box-shadow: 0 4px 20px rgba(47, 107, 255, 0.06);
}

.trigger-text {
  flex: 1;
  font-size: 0.82rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trigger-placeholder {
  flex: 1;
  font-size: 0.82rem;
  color: var(--text-tertiary);
}

.trigger-chevron {
  flex-shrink: 0;
  color: var(--text-tertiary);
  transition: transform 0.2s ease;
}

.trigger-chevron.up {
  transform: rotate(180deg);
}

/* ── 下拉浮层 ── */
.selector-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 50;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(148, 163, 184, 0.1);
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.selector-search-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}

.selector-search-icon {
  font-size: 1rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.selector-search {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.selector-search::placeholder {
  color: var(--text-tertiary);
}

.selector-list {
  max-height: 280px;
  overflow-y: auto;
  padding: 0.3rem;
}

.selector-item {
  display: block;
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 0;
  background: transparent;
  text-align: left;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.selector-item:hover {
  background: rgba(47, 107, 255, 0.05);
}

.selector-item.active {
  background: rgba(47, 107, 255, 0.06);
}

.si-title {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 0.15rem;
}

.si-meta {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.selector-empty {
  padding: 1.5rem 0.75rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.82rem;
}

.selector-footer {
  padding: 0.4rem 0.75rem;
  border-top: 1px solid rgba(148, 163, 184, 0.08);
}

.selector-clear {
  width: 100%;
  padding: 0.4rem;
  border: 0;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  cursor: pointer;
  border-radius: 8px;
  transition: color 0.2s ease;
}

.selector-clear:hover {
  color: #ef4444;
}

/* ════════ 空状态 ════════ */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 1rem;
  text-align: center;
}

.empty-graphic {
  margin-bottom: 1rem;
  opacity: 0.4;
}

.empty-text {
  margin: 0 0 0.3rem;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.empty-hint {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 0.82rem;
}

/* ════════ 分区 ════════ */
.relation-section {
  margin-bottom: 2.5rem;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.title-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 0.9rem;
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

.section-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
}

.count-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: rgba(148, 163, 184, 0.1);
  color: var(--text-tertiary);
  font-size: 0.72rem;
  font-weight: 600;
}

.section-context {
  font-size: 0.78rem;
  color: var(--text-tertiary);
  max-width: 50%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-context strong {
  color: var(--text-secondary);
  font-weight: 500;
}

/* ════════ 行内搜索 ════════ */
.inline-search {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.65rem;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.1);
  background: rgba(255, 255, 255, 0.45);
  margin-bottom: 0.85rem;
  transition: all 0.2s ease;
}

.inline-search:focus-within {
  border-color: rgba(47, 107, 255, 0.18);
  background: rgba(255, 255, 255, 0.7);
}

.inline-search .is-icon {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.inline-search input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 0.78rem;
  color: var(--text-primary);
}

.inline-search input::placeholder {
  color: var(--text-tertiary);
}

/* ════════ 状态 ════════ */
.state-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.state-error {
  color: #ef4444;
}

.loading-dots {
  display: flex;
  gap: 6px;
}
.loading-dots span {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--brand-accent);
  opacity: 0.3;
  animation: dot-bounce 1.2s ease-in-out infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-bounce {
  0%, 80%, 100% { opacity: 0.3; transform: scale(1); }
  40% { opacity: 1; transform: scale(1.3); }
}

.empty-list {
  padding: 2rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

/* ════════ 论文卡片 ════════ */
.card-list {
  display: grid;
  gap: 0.85rem;
}

.paper-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(148, 163, 184, 0.08);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
  transition: all 0.2s ease;
}

.paper-card:hover {
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.06);
  border-color: rgba(148, 163, 184, 0.15);
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-title {
  margin: 0 0 0.35rem;
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.45;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.5rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.meta-dot {
  opacity: 0.4;
}

.meta-citation {
  color: var(--brand-accent);
  font-weight: 500;
  opacity: 0.85;
}

.card-desc {
  margin: 0;
  font-size: 0.83rem;
  color: var(--text-tertiary);
  line-height: 1.6;
}

.card-actions {
  flex-shrink: 0;
  padding-top: 0.15rem;
}

.view-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 0.78rem;
  cursor: pointer;
  transition: color 0.2s ease;
  white-space: nowrap;
}

.view-link:hover {
  color: var(--brand-accent);
}

/* ════════ 过渡 ════════ */
.fade-drop-enter-active,
.fade-drop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-drop-enter-from,
.fade-drop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.card-enter-enter-active {
  transition: all 0.3s ease;
}
.card-enter-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

/* ════════ 响应式 ════════ */
@media (max-width: 820px) {
  .upstream-page {
    padding: 1rem;
  }

  .paper-card {
    flex-direction: column;
    gap: 0.6rem;
    padding: 1rem;
  }

  .card-actions {
    align-self: flex-end;
  }

  .section-context {
    max-width: 100%;
  }

  .selector-trigger {
    padding: 0.65rem 0.85rem;
  }
}
</style>
