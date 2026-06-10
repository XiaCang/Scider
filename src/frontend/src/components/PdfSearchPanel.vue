<template>
  <div class="pdf-search-overlay" @keydown.escape="$emit('close')">
    <div class="search-input-row">
      <el-input
        ref="inputRef"
        v-model="searchKeyword"
        placeholder="搜索论文内容..."
        size="small"
        clearable
        @input="handleSearchInput"
        @keydown.enter="jumpToMatch"
        @keydown.up.prevent="prevMatch"
        @keydown.down.prevent="nextMatch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <span class="match-count" v-if="hasSearched">
        {{ totalResults > 0 ? `${currentMatchIndex + 1}/${totalResults}` : '0' }}
      </span>
      <el-button size="small" text @click="$emit('close')">
        关闭
      </el-button>
    </div>

    <div v-if="searchResults.length > 0" class="search-results-list">
      <div
        v-for="(result, index) in searchResults"
        :key="index"
        class="search-result-item"
        :class="{ highlighted: index === currentMatchIndex }"
        @click="goToResult(index)"
      >
        <span class="result-page-tag">P{{ result.page_number }}</span>
        <span class="result-text" v-html="result.highlights[0]"></span>
      </div>
      <div v-if="totalResults > 50" class="results-truncated">
        仅显示前 50 条结果
      </div>
    </div>

    <div v-else-if="hasSearched && totalResults === 0" class="search-no-result">
      未找到匹配结果
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { searchInPaperApi } from '../api/library'
import type { SearchResultItem } from '../api/library'

const props = defineProps<{
  paperId: string
}>()

const emit = defineEmits<{
  (e: 'jump-to-page', page: number): void
  (e: 'close'): void
}>()

const inputRef = ref<any>(null)
const searchKeyword = ref('')
const searchResults = ref<SearchResultItem[]>([])
const totalResults = ref(0)
const hasSearched = ref(false)
const currentMatchIndex = ref(0)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const handleSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  currentMatchIndex.value = 0

  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    totalResults.value = 0
    hasSearched.value = false
    return
  }

  searchTimer = setTimeout(() => executeSearch(), 300)
}

const executeSearch = async () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) return

  try {
    const response = await searchInPaperApi(props.paperId, { keyword, limit: 50 })
    const data = ('data' in response) ? (response as any).data : response
    searchResults.value = data.results || []
    totalResults.value = data.total_results || 0
    hasSearched.value = true
  } catch (error) {
    console.error('搜索失败:', error)
    searchResults.value = []
    totalResults.value = 0
    hasSearched.value = true
  }
}

const jumpToMatch = () => {
  if (searchResults.value.length > 0) {
    const r = searchResults.value[currentMatchIndex.value]
    emit('jump-to-page', r.page_number)
  }
}

const goToResult = (index: number) => {
  currentMatchIndex.value = index
  const r = searchResults.value[index]
  if (r) emit('jump-to-page', r.page_number)
}

const prevMatch = () => {
  if (searchResults.value.length > 0) {
    currentMatchIndex.value = (currentMatchIndex.value - 1 + searchResults.value.length) % searchResults.value.length
    const r = searchResults.value[currentMatchIndex.value]
    emit('jump-to-page', r.page_number)
  }
}

const nextMatch = () => {
  if (searchResults.value.length > 0) {
    currentMatchIndex.value = (currentMatchIndex.value + 1) % searchResults.value.length
    const r = searchResults.value[currentMatchIndex.value]
    emit('jump-to-page', r.page_number)
  }
}

const focus = () => {
  nextTick(() => inputRef.value?.focus())
}

watch(() => props.paperId, () => {
  searchKeyword.value = ''
  searchResults.value = []
  totalResults.value = 0
  hasSearched.value = false
})

defineExpose({ focus })
</script>

<style scoped>
.pdf-search-overlay {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 380px;
  max-height: 60vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-input-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--line-soft);
}

.search-input-row :deep(.el-input) {
  flex: 1;
}

.match-count {
  font-size: 0.75rem;
  color: #999;
  white-space: nowrap;
  min-width: 36px;
  text-align: center;
}

.search-results-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
  max-height: 40vh;
}

.search-result-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 10px;
  cursor: pointer;
  transition: background 0.1s;
}

.search-result-item:hover {
  background: #f5f7fa;
}

.search-result-item.highlighted {
  background: #ecf5ff;
}

.result-page-tag {
  flex-shrink: 0;
  font-size: 0.7rem;
  font-weight: 600;
  color: #409eff;
  background: #ecf5ff;
  padding: 1px 6px;
  border-radius: 3px;
  margin-top: 2px;
}

.result-text {
  font-size: 0.8rem;
  line-height: 1.5;
  color: #555;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.result-text :deep(.search-highlight) {
  background-color: #ffeb3b;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 500;
}

.results-truncated {
  padding: 6px 10px;
  font-size: 0.72rem;
  color: #bbb;
  text-align: center;
}

.search-no-result {
  padding: 16px;
  text-align: center;
  font-size: 0.8rem;
  color: #999;
}
</style>
