<!-- PaperListItem.vue（原 PaperCardList.vue，移除全选栏，复选框圆形移至右上角） -->
<script setup lang="ts">
import type { LibraryPaper } from '../../../types/library'

interface Props {
  papers: LibraryPaper[]
  selectedIds: Set<string>   // 已选中的论文 ID 集合
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:selectedIds': [ids: Set<string>]
  'select-paper': [paper: LibraryPaper]   // 点击卡片主体时打开详情
}>()

// 状态映射（用于展示标签样式）
const statusTextMap: Record<string, string> = {
  pending_parsing: '解析中',
  PARSING: '解析中',
  pending_extraction: '提取中',
  EXTRACTING: '提取中',
  pending_confirmation: '待确认',
}
const statusClassMap: Record<string, string> = {
  pending_parsing: 'status-processing',
  PARSING: 'status-processing',
  pending_extraction: 'status-pending',
  EXTRACTING: 'status-pending',
  pending_confirmation: 'status-confirmed',
}

// 处理复选框变化
const toggleSelect = (paperId: string, event: Event) => {
  event.stopPropagation() // 防止冒泡到卡片其他区域
  const checked = (event.target as HTMLInputElement).checked
  const newSet = new Set(props.selectedIds)
  if (checked) {
    newSet.add(paperId)
  } else {
    newSet.delete(paperId)
  }
  emit('update:selectedIds', newSet)
}
</script>

<template>
  <div class="paper-list">
    <div v-if="papers.length === 0" class="empty-state">
      <el-empty description="暂无论文" :image-size="100" />
    </div>

    <div v-for="paper in papers" :key="paper.id" class="paper-card">
      <!-- 圆形复选框（右上角） -->
      <div class="card-checkbox">
        <input
          type="checkbox"
          :checked="selectedIds.has(paper.id)"
          @change="(e) => toggleSelect(paper.id, e)"
        />
      </div>
      <!-- 卡片主体内容（点击预览详情） -->
      <div class="card-content" @click="emit('select-paper', paper)">
        <div class="paper-title">{{ paper.title }}</div>
        <div class="paper-authors">{{ paper.authors || '未知作者' }}</div>
        <div class="paper-venue">{{ '未知出处' }}</div>
        <div class="paper-meta">
          <span class="year">{{ paper.year || '未知年份' }}</span>
          <span class="tag status-tag" :class="statusClassMap[paper.status]">
            {{ statusTextMap[paper.status] || paper.status }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.paper-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.empty-state {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.paper-card {
  position: relative;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
  transition: background 0.15s, border-color 0.15s;
}

.paper-card:hover {
  background: #fafcff;
  border-color: #cbd5e1;
}

/* 圆形复选框 - 右上角 */
.card-checkbox {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 1;
}

.card-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin: 0;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background: white;
  border: 1.5px solid #cbd5e1;
  border-radius: 50%;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-checkbox input[type="checkbox"]:checked {
  background-color: #3b82f6;
  border-color: #3b82f6;
  box-shadow: inset 0 0 0 3px white;
}

.card-checkbox input[type="checkbox"]:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.card-checkbox input[type="checkbox"]:hover {
  border-color: #94a3b8;
}

/* 卡片内容区域（点击打开详情） */
.card-content {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 28px; /* 为右上角复选框预留空间 */
}

.paper-title {
  font-weight: 500;
  font-size: 0.95rem;
  color: #1e293b;
  line-height: 1.4;
}

.paper-authors,
.paper-venue {
  font-size: 0.8rem;
  color: #5b6e8c;
}

.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-top: 2px;
}

.year {
  font-size: 0.75rem;
  color: #6c7a91;
}

.tag {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 20px;
  background-color: #f0f2f5;
  color: #4b5563;
}

.status-processing {
  background: #fff7e5;
  color: #d97706;
}
.status-pending {
  background: #e6f7ff;
  color: #0891b2;
}
.status-confirmed {
  background: #e6f9ed;
  color: #059669;
}
</style>