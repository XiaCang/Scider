<script setup lang="ts">
import { Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref, watch } from 'vue'

import type { LibraryPaper } from '../../../types/library'

interface Props {
  modelValue: boolean
  paper: LibraryPaper | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'importToLibrary', paper: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算属性：抽屉显示状态
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 添加到文库
const handleImportToLibrary = () => {
  if (!props.paper) return
  emit('importToLibrary', props.paper)
}

// 状态映射（中文显示）
const statusTextMap: Record<string, string> = {
  PENDING_PARSING: '解析中',
  PARSING: '解析中',
  PENDING_EXTRACTION: '提取中',
  EXTRACTING: '提取中',
  PENDING_CONFIRMATION: '待确认',
  CONFIRMED: '已确认',
  FAILED: '失败',
}

const statusClassMap: Record<string, string> = {
  PENDING_PARSING: 'is-warning',
  PARSING: 'is-warning',
  PENDING_EXTRACTION: 'is-brand',
  EXTRACTING: 'is-brand',
  PENDING_CONFIRMATION: 'is-success',
  CONFIRMED: 'is-success',
  FAILED: 'is-danger',
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="论文详情"
    direction="rtl"
    size="680px"
  >
    <div v-if="paper" class="paper-detail">
      <!-- 论文基本信息 -->
      <section class="paper-info">
        <h2 class="paper-title">{{ paper.title }}</h2>

        <div class="paper-meta">
          <div class="meta-item meta-item--full">
            <span class="meta-label">作者：</span>
            <span class="meta-value meta-value--ellipsis" :title="paper.authors">{{ paper.authors }}</span>
          </div>

          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">年份：</span>
              <span class="meta-value">{{ paper.year }}</span>
            </div>

            <div class="meta-item">
              <span class="meta-label">来源：</span>
              <span class="meta-value meta-value--ellipsis" :title="paper.source">{{ paper.source }}</span>
            </div>

            <div class="meta-item">
              <span class="meta-label">状态：</span>
              <span class="status-pill" :class="statusClassMap[paper.status]">
                {{ statusTextMap[paper.status] }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- 摘要信息 -->
      <section v-if="paper.abstract" class="abstract-section">
        <h3 class="section-title">摘要</h3>
        <p class="abstract-text">{{ paper.abstract }}</p>
      </section>

      <!-- 操作按钮区 -->
      <section class="action-section">
        <el-button
          type="success"
          size="large"
          @click="handleImportToLibrary"
        >
          <el-icon><Check /></el-icon>
          添加到文库
        </el-button>
      </section>
    </div>

    <div v-else class="empty-state">
      <el-empty description="请选择一篇论文查看详情" />
    </div>
  </el-drawer>
</template>

<style scoped>
.paper-detail {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 0 0.25rem;
}

/* 论文基本信息 */
.paper-info {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--line-soft);
}

.paper-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.7rem 0;
  line-height: 1.45;
}

.paper-meta {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.8rem;
}

/* 作者行独占一行 */
.meta-item--full {
  max-width: 100%;
}

/* 年份 / 来源 / 状态 一行排列 */
.meta-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
}

.meta-label {
  color: var(--text-secondary);
  font-weight: 500;
  flex-shrink: 0;
}

.meta-value {
  color: var(--text-primary);
}

.meta-value--ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* 摘要区域 */
.abstract-section {
  flex: 1;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.abstract-text {
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0;
  white-space: pre-wrap;
}

/* 操作按钮区 */
.action-section {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line-soft);
}

.action-section .el-button {
  flex: 1;
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .meta-row {
    flex-direction: column;
    gap: 0.3rem;
  }

  .action-section {
    flex-direction: column;
  }
}
</style>
