<script setup lang="ts">
import { ArrowDown, Search } from '@element-plus/icons-vue'
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
  // search,
} = useSearch()

function viewDetails(itemId: string) {
  // TODO: 导航到论文详情页面
  console.log('view details:', itemId)
}

function handleSearchInput() {
  // 用户输入时实时过滤（已通过 computed filteredResults 实现）
}
</script>

<template>
  <section class="discover-page">
    <!-- 搜索栏 -->
    <div class="discover-search-bar">
      <label class="discover-search">
        <el-icon><Search /></el-icon>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索论文、作者、主题..."
          @input="handleSearchInput"
        />
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
            {{ selectedVenue ? venueOptions.find(opt => opt.value === selectedVenue)?.label : '来源' }}
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

    <!-- 推荐理由 -->
    <p v-if="!keyword" class="discover-hint">
      基于你的文库和阅读记录为你推荐以下论文
    </p>

    <!-- 加载状态 -->
    <div v-if="loading" class="state-message">
      <p>正在加载推荐...</p>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="state-message state-error">
      <p>{{ error }}</p>
    </div>

    <!-- 搜索结果 -->
    <section v-if="!loading" class="discover-list">
      <div v-if="filteredResults.length === 0" class="empty-list">
        <p>{{ keyword ? '未找到匹配的论文' : '暂无推荐内容' }}</p>
      </div>

      <article v-for="item in filteredResults" :key="item.id" class="discover-item">
        <div class="discover-item__main">
          <h2 class="item-title">{{ item.title }}</h2>
          <div class="item-meta">
            <span>{{ item.year }}</span>
            <span class="meta-separator">·</span>
            <span>{{ item.authors }}</span>
            <span class="meta-separator">·</span>
            <span>{{ item.venue }}</span>
          </div>
          <p v-if="item.reason" class="item-reason">
            {{ item.reason }}
          </p>
          <p class="item-description">{{ item.description }}</p>
        </div>
        <el-button plain @click="viewDetails(item.id)">View Details</el-button>
      </article>
    </section>
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

/* 搜索栏 */
.discover-search-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  align-items: center;
}

.discover-search {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
  min-width: min(400px, 48vw);
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
  font-size: 0.9rem;
}

.discover-filters {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

/* 推荐提示 */
.discover-hint {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-tertiary, #94a3b8);
}

/* 状态提示 */
.state-message {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: var(--text-tertiary, #94a3b8);
  font-size: 0.95rem;
}

.state-error {
  color: #ef4444;
}

/* 列表 */
.discover-list {
  display: grid;
  gap: 1rem;
}

.discover-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 0;
  border-top: 1px solid var(--line-soft, #e2e8f0);
}

.discover-item:first-child {
  border-top: 0;
  padding-top: 0;
}

.item-title {
  margin: 0 0 0.4rem;
  font-size: 1.15rem;
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
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.meta-separator {
  opacity: 0.6;
}

.item-reason {
  margin: 0 0 0.3rem;
  font-size: 0.85rem;
  color: var(--brand, #4f46e5);
  line-height: 1.5;
}

.item-description {
  color: var(--text-tertiary);
  font-size: 0.88rem;
  margin: 0;
  line-height: 1.6;
}

.empty-list {
  padding: 2rem;
  text-align: center;
  color: var(--text-tertiary);
  background: var(--bg-secondary, #f8fafc);
  border-radius: 8px;
  border: 1px dashed var(--line-soft, #e2e8f0);
}

.empty-list p {
  margin: 0;
  font-size: 0.9rem;
}

@media (max-width: 820px) {
  .discover-page {
    padding: 1rem;
  }

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
}
</style>
