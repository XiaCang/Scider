<template>
  <div class="pdf-search-panel">
    <!-- 搜索输入框 -->
    <div class="search-input-wrapper">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索论文内容..."
        clearable
        @input="handleSearchInput"
        @keyup.enter="executeSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 搜索结果列表 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <span>找到 {{ totalResults }} 个结果</span>
      </div>
      
      <el-scrollbar max-height="calc(100vh - 200px)">
        <div
          v-for="(result, index) in searchResults"
          :key="index"
          class="result-item"
          @click="jumpToPage(result.page_number)"
        >
          <div class="result-page-badge">
            P{{ result.page_number }}
          </div>
          <div 
            class="result-content"
            v-html="result.highlights[0]"
          ></div>
        </div>
      </el-scrollbar>
    </div>

    <!-- 无结果提示 -->
    <div v-else-if="hasSearched && totalResults === 0" class="no-results">
      <el-empty description="未找到匹配结果" :image-size="80" />
    </div>

    <!-- 初始状态提示 -->
    <div v-else class="search-hint">
      <el-icon :size="40" color="#dcdfe6"><Search /></el-icon>
      <p>输入关键词开始搜索</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { searchInPaperApi } from '../api/library'
import type { SearchResultItem } from '../api/library'

const props = defineProps<{
  paperId: string
}>()

const emit = defineEmits<{
  (e: 'jump-to-page', page: number): void
}>()

const searchKeyword = ref('')
const searchResults = ref<SearchResultItem[]>([])
const totalResults = ref(0)
const hasSearched = ref(false)

// 防抖定时器
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 处理输入（带防抖）
const handleSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    totalResults.value = 0
    hasSearched.value = false
    return
  }

  searchTimer = setTimeout(() => {
    executeSearch()
  }, 500)
}

// 执行搜索
const executeSearch = async () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) return

  try {
    const response = await searchInPaperApi(props.paperId, {
      keyword,
      limit: 50
    })
    
    // 响应拦截器已解包
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

// 跳转到指定页
const jumpToPage = (pageNumber: number) => {
  emit('jump-to-page', pageNumber)
}

// 监听 paperId 变化，清空搜索结果
watch(() => props.paperId, () => {
  searchKeyword.value = ''
  searchResults.value = []
  totalResults.value = 0
  hasSearched.value = false
})
</script>

<style scoped>
.pdf-search-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

.search-input-wrapper {
  padding: 16px;
  border-bottom: 1px solid var(--line-soft);
}

.search-results {
  flex: 1;
  overflow: hidden;
}

.results-header {
  padding: 12px 16px;
  font-size: 13px;
  color: #606266;
  border-bottom: 1px solid var(--line-soft);
  background: #f5f7fa;
}

.result-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line-soft);
  cursor: pointer;
  transition: background-color 0.2s;
}

.result-item:hover {
  background-color: #f5f7fa;
}

.result-page-badge {
  display: inline-block;
  padding: 2px 8px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  background: #ecf5ff;
  border-radius: 4px;
}

.result-content {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  word-break: break-word;
}

/* 高亮样式 */
:deep(.search-highlight) {
  background-color: #ffeb3b;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 500;
}

.no-results {
  padding: 40px 20px;
  text-align: center;
}

.search-hint {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  gap: 12px;
}

.search-hint p {
  margin: 0;
  font-size: 14px;
}
</style>
