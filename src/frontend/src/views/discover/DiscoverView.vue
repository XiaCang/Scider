<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useSearch } from '../../discover/composables/useSearch'
import PaperResultCard from '../../discover/components/PaperResultCard.vue'
import PaperDetailSimple from '../library/paper/PaperDetailSimple.vue'
import { yearOptions, venueOptions, sortOptions } from '../../discover/constants'
import type { LibraryPaper } from '../../types/library'
import { fetchPaperByIdApi } from '../../api/library'
import { importPaperApi } from '../../api/discover'
import { ElMessage } from 'element-plus'

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

const currentYearLabel = computed(() =>
  yearOptions.find(o => o.value === selectedYear.value)?.label ?? '全部年份'
)
const currentVenueLabel = computed(() =>
  venueOptions.find(o => o.value === selectedVenue.value)?.label ?? '全部来源'
)
const currentSortLabel = computed(() =>
  sortOptions.find(o => o.value === sortBy.value)?.label ?? '相关性'
)

/* ── 论文详情抽屉 ── */
const detailVisible = ref(false)
const selectedPaper = ref<LibraryPaper | null>(null)

// 处理点击论文卡片
const handlePaperClick = async (paper: any) => {
  // 如果论文已在文库中，获取完整详情
  if ((paper as any).in_library && paper.id) {
    try {
      const { data } = await fetchPaperByIdApi(paper.id)
      selectedPaper.value = data
    } catch (err) {
      ElMessage.error('加载论文详情失败')
      console.error(err)
      return
    }
  } else {
    // 对于未入库的论文，使用搜索结果的简化信息
    selectedPaper.value = {
      id: paper.semantic_id || paper.id || '',
      title: paper.title || '',
      authors: paper.authors || '',
      year: paper.year || 0,
      venue: paper.venue || '',
      citation_count: paper.citation_count || 0,
      abstract: paper.abstract || paper.description || '',
      pdf_url: paper.pdf_url || '',
      doi: paper.doi || '',
      status: 'PENDING',
      source: paper.source_type || 'external',
      keyPoints: null,
      in_library: false,
    } as any
  }
  
  detailVisible.value = true
}

// 保存关键点
const handleSaveKeyPoints = async (paperId: string, keyPoints: any) => {
  // TODO: 调用API保存关键点
  ElMessage.success('关键点已保存')
  detailVisible.value = false
}

// 预览PDF
const handlePreviewPdf = (paperId: string) => {
  detailVisible.value = false
  // TODO: 跳转到PDF预览页
  // router.push({ name: 'paper-pdf', params: { paperId } })
}

// 添加到文库
const handleImportToLibrary = async (paper: any) => {
  try {
    // 构造导入请求数据
    const importData = {
      title: paper.title,
      authors: paper.authors || null,
      abstract: paper.abstract || null,
      doi: paper.doi || null,
      year: paper.year || null,
      venue: paper.venue || null,
      pdf_url: paper.pdf_url || null,
    }
    
    // 调用导入API
    await importPaperApi(importData)
    
    ElMessage.success('论文已成功添加到文库')
    detailVisible.value = false
    
    // 刷新推荐列表或搜索结果
    // TODO: 根据需要刷新数据
  } catch (err) {
    ElMessage.error('添加论文到文库失败')
    console.error(err)
  }
}

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
        <div
          v-for="item in filteredResults"
          :key="item.id"
          @click="handlePaperClick(item)"
          class="paper-card-wrapper"
        >
          <PaperResultCard
            :paper="item"
          />
        </div>
      </TransitionGroup>
    </div>

    <!-- 论文详情抽屉 -->
    <PaperDetailSimple
      v-model="detailVisible"
      :paper="selectedPaper"
      @import-to-library="handleImportToLibrary"
    />

  </section>
</template>

<style scoped>
/* ════════ 页面布局 ════════ */
.discover-page {
  max-width: 880px;
  margin: 0 auto;
  padding: 2rem 2rem 3rem;
}

/* ── 搜索区 ── */
.hero-search {
  margin-bottom: 1rem;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #f9fafb;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.bar-icon {
  margin-left: 1rem;
  color: #94a3b8;
}

.bar-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  background-color: transparent;
  font-size: 1rem;
  color: #1e293b;

  &:focus {
    outline: none;
  }
}

.bar-divider {
  width: 1px;
  height: 2rem;
  background-color: #e2e8f0;
}

.bar-filters {
  display: flex;
  align-items: center;
}

/* ── 下拉面板 ── */
.pill-wrap {
  position: relative;
  margin-left: 0.5rem;
}

.pill {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  background-color: #fff;
  font-size: 0.875rem;
  color: #1e293b;
  cursor: pointer;

  &.active {
    border-color: #4f46e5;
    color: #4f46e5;
  }
}

.pill-cv {
  margin-left: 0.5rem;
  width: 8px;
  height: 5px;
  transition: transform 0.2s ease-in-out;

  &.up {
    transform: rotate(180deg);
  }
}

.pill-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;

  &--right {
    right: 0;
    left: auto;
  }
}

.pill-opt {
  display: block;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  color: #1e293b;
  cursor: pointer;

  &:hover {
    background-color: #f3f4f6;
  }

  &.sel {
    background-color: #e0e7ff;
    color: #4f46e5;
  }
}

/* ── 推荐提示 ── */
.discover-hint {
  margin-bottom: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

/* ── 加载态 ── */
.state-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 20rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.loading-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.loading-dots span {
  display: inline-block;
  width: 0.5rem;
  height: 0.5rem;
  margin: 0 0.25rem;
  background-color: #94a3b8;
  border-radius: 50%;
  animation: loading-bounce 0.6s infinite alternate;

  &:nth-child(2) {
    animation-delay: 0.2s;
  }

  &:nth-child(3) {
    animation-delay: 0.4s;
  }
}

@keyframes loading-bounce {
  0% {
    transform: translateY(0);
  }

  100% {
    transform: translateY(-0.5rem);
  }
}

/* ── 错误态 ── */
.state-error {
  color: #ef4444;
}

/* ── 结果列表 ── */
.discover-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 20rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.empty-icon-wrap {
  margin-bottom: 1rem;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.paper-card-wrapper {
  cursor: pointer;

  &:hover {
    background-color: #f3f4f6;
  }
}

/* ── 过渡效果 ── */
.fade-drop-enter-active,
.fade-drop-leave-active {
  transition: opacity 0.2s ease-in-out;
}

.fade-drop-enter-from,
.fade-drop-leave-to {
  opacity: 0;
}

.card-enter-enter-active,
.card-enter-leave-active {
  transition: opacity 0.2s ease-in-out;
}

.card-enter-enter-from,
.card-enter-leave-to {
  opacity: 0;
}

</style>
