<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useSearch } from '../../discover/composables/useSearch'
import { yearOptions, venueOptions, sortOptions } from '../../discover/constants'

const {
  keyword,
  selectedYear,
  selectedVenue,
  sortBy,
  loading,
  error,
  filteredResults,
} = useSearch()

/* ── 自定义下拉面板 ── */
const yearOpen = ref(false)
const venueOpen = ref(false)
const sortOpen = ref(false)

function toggleYear() { yearOpen.value = !yearOpen.value; venueOpen.value = false; sortOpen.value = false }
function toggleVenue() { venueOpen.value = !venueOpen.value; yearOpen.value = false; sortOpen.value = false }
function toggleSort() { sortOpen.value = !sortOpen.value; yearOpen.value = false; venueOpen.value = false }

function closeAll() { yearOpen.value = false; venueOpen.value = false; sortOpen.value = false }

function onYearPick(val: string) { selectedYear.value = val; yearOpen.value = false }
function onVenuePick(val: string) { selectedVenue.value = val; venueOpen.value = false }
function onSortPick(val: string) { sortBy.value = val; sortOpen.value = false }

function viewDetails(itemId: string) {
  console.log('view details:', itemId)
}

const currentYearLabel = computed(() =>
  yearOptions.find(o => o.value === selectedYear.value)?.label ?? '全部年份'
)
const currentVenueLabel = computed(() =>
  venueOptions.find(o => o.value === selectedVenue.value)?.label ?? '全部来源'
)
const currentSortLabel = computed(() =>
  sortOptions.find(o => o.value === sortBy.value)?.label ?? '相关性'
)

/* ── 推荐模型 ── */
</script>

<template>
  <section class="discover-page" @click="closeAll">

    <!-- 搜索区：紧凑一行 -->
    <div class="hero-search">
      <div class="search-bar">
        <el-icon class="bar-icon"><Search /></el-icon>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索论文、作者、关键词..."
          class="bar-input"
        />
        <div class="bar-divider" />
        <div class="bar-filters">
          <!-- 年份 -->
          <div class="pill-wrap">
            <button class="pill" :class="{ active: selectedYear }" @click.stop="toggleYear">
              {{ currentYearLabel }}
              <svg class="pill-cv" :class="{ up: yearOpen }" width="8" height="5" viewBox="0 0 8 5"><path d="M1 1l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
            <Transition name="fade-drop">
              <div v-if="yearOpen" class="pill-dropdown">
                <button v-for="opt in yearOptions" :key="opt.value" class="pill-opt" :class="{ sel: selectedYear === opt.value }" @click="onYearPick(opt.value)">{{ opt.label }}</button>
              </div>
            </Transition>
          </div>
          <!-- 来源 -->
          <div class="pill-wrap">
            <button class="pill" :class="{ active: selectedVenue }" @click.stop="toggleVenue">
              {{ currentVenueLabel }}
              <svg class="pill-cv" :class="{ up: venueOpen }" width="8" height="5" viewBox="0 0 8 5"><path d="M1 1l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
            <Transition name="fade-drop">
              <div v-if="venueOpen" class="pill-dropdown">
                <button v-for="opt in venueOptions" :key="opt.value" class="pill-opt" :class="{ sel: selectedVenue === opt.value }" @click="onVenuePick(opt.value)">{{ opt.label }}</button>
              </div>
            </Transition>
          </div>
          <!-- 排序 -->
          <div class="pill-wrap">
            <button class="pill" :class="{ active: sortBy !== 'relevance' }" @click.stop="toggleSort">
              {{ currentSortLabel }}
              <svg class="pill-cv" :class="{ up: sortOpen }" width="8" height="5" viewBox="0 0 8 5"><path d="M1 1l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
            <Transition name="fade-drop">
              <div v-if="sortOpen" class="pill-dropdown pill-dropdown--right">
                <button v-for="opt in sortOptions" :key="opt.value" class="pill-opt" :class="{ sel: sortBy === opt.value }" @click="onSortPick(opt.value)">{{ opt.label }}</button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>

    <!-- 推荐提示 -->
    <p v-if="!keyword && !loading && filteredResults.length > 0" class="discover-hint">
      基于你的文库和阅读记录为你推荐以下论文
    </p>

    <!-- 加载态 -->
    <div v-if="loading" class="state-message">
      <div class="loading-dots"><span /><span /><span /></div>
      <p>正在加载推荐...</p>
    </div>

    <!-- 错误态 -->
    <div v-if="error" class="state-message state-error">
      <p>{{ error }}</p>
    </div>

    <!-- 结果列表 -->
    <div v-if="!loading" class="discover-list">
      <div v-if="filteredResults.length === 0 && !error" class="empty-list">
        <div class="empty-icon-wrap">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none"><rect x="10" y="6" width="28" height="36" rx="4" stroke="#cbd5e1" stroke-width="2" fill="none"/><path d="M18 18h12M18 25h12M18 32h8" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round"/></svg>
        </div>
        <p>{{ keyword ? '未找到匹配的论文' : '暂无推荐内容' }}</p>
      </div>

      <TransitionGroup name="card-enter" tag="div" class="card-list">
        <article v-for="item in filteredResults" :key="item.id" class="paper-card">
          <div class="card-body">
            <div class="card-header">
              <h3 class="card-title">{{ item.title }}</h3>
            </div>
            <div class="card-meta">
              <span class="meta-year">{{ item.year }}</span>
              <span class="meta-dot">·</span>
              <span class="meta-authors">{{ item.authors }}</span>
              <span v-if="item.venue" class="meta-venue">{{ item.venue }}</span>
            </div>
            <p v-if="item.reason" class="card-reason">{{ item.reason }}</p>
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
    </div>
  </section>
</template>

<style scoped>
/* ════════ 页面布局 ════════ */
.discover-page {
  max-width: 880px;
  margin: 0 auto;
  padding: 2rem 2rem 3rem;
}

/* ════════ 紧凑搜索区 ════════ */
.hero-search {
  margin-bottom: 1.25rem;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  padding: 0.4rem 0.6rem 0.4rem 0.85rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
  transition: all 0.25s ease;
}

.search-bar:focus-within {
  border-color: rgba(47, 107, 255, 0.25);
  box-shadow: 0 4px 20px rgba(47, 107, 255, 0.08);
  background: rgba(255, 255, 255, 0.92);
}

.bar-icon {
  font-size: 0.95rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.bar-input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.bar-input::placeholder {
  color: var(--text-tertiary);
}

.bar-divider {
  width: 1px;
  height: 18px;
  background: rgba(148, 163, 184, 0.2);
  flex-shrink: 0;
  margin: 0 0.15rem;
}

.bar-filters {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-shrink: 0;
}

.pill-wrap {
  position: relative;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.55rem;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  white-space: nowrap;
}

.pill:hover {
  background: rgba(148, 163, 184, 0.08);
  color: var(--text-secondary);
}

.pill.active {
  background: rgba(47, 107, 255, 0.07);
  color: var(--brand-accent);
}

.pill-cv {
  transition: transform 0.2s ease;
}
.pill-cv.up {
  transform: rotate(180deg);
}

/* ── dropdown 浮层 ── */
.pill-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 50;
  min-width: 120px;
  padding: 0.25rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(148, 163, 184, 0.1);
  box-shadow: 0 10px 32px rgba(15, 23, 42, 0.08);
}

.pill-dropdown--right {
  left: auto;
  right: 0;
}

.pill-opt {
  display: block;
  width: 100%;
  padding: 0.35rem 0.65rem;
  border: 0;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.78rem;
  text-align: left;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.pill-opt:hover {
  background: rgba(47, 107, 255, 0.06);
}

.pill-opt.sel {
  color: var(--brand-accent);
  font-weight: 600;
  background: rgba(47, 107, 255, 0.06);
}

/* ════════ 推荐提示 ════════ */
.discover-hint {
  margin: 0 0 1rem;
  font-size: 0.82rem;
  color: var(--text-tertiary);
}

/* ════════ 状态 ════════ */
.state-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 4rem 1rem;
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
  width: 8px;
  height: 8px;
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

/* ════════ 空状态 ════════ */
.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.empty-icon-wrap {
  opacity: 0.5;
}

/* ════════ 论文卡片列表 ════════ */
.card-list {
  display: grid;
  gap: 1rem;
}

.paper-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.35rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(148, 163, 184, 0.08);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
  transition: all 0.2s ease;
}

.paper-card:hover {
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.06);
  border-color: rgba(148, 163, 184, 0.15);
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-title {
  margin: 0 0 0.35rem;
  font-size: 1.02rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.45;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.meta-dot {
  opacity: 0.4;
}

.meta-venue {
  color: var(--brand-accent);
  opacity: 0.75;
}

.card-reason {
  margin: 0 0 0.35rem;
  font-size: 0.82rem;
  color: var(--brand-accent);
  line-height: 1.5;
  opacity: 0.85;
}

.card-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-tertiary);
  line-height: 1.6;
}

.card-actions {
  flex-shrink: 0;
  padding-top: 0.2rem;
}

.view-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: color 0.2s ease;
  white-space: nowrap;
}

.view-link:hover {
  color: var(--brand-accent);
}

/* ════════ 过渡动画 ════════ */
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
  .discover-page {
    padding: 1rem;
  }

  .paper-card {
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
  }

  .card-actions {
    align-self: flex-end;
  }
}
</style>
