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
  PENDING_PARSING: '解析中',
  PARSING: '解析中',
  PENDING_EXTRACTION: '提取中',
  EXTRACTING: '提取中',
  PENDING_CONFIRMATION: '待确认',
  CONFIRMED: '已确认',
  FAILED: '失败',
}
const statusClassMap: Record<string, string> = {
  PENDING_PARSING: 'status-processing',
  PARSING: 'status-processing',
  PENDING_EXTRACTION: 'status-pending',
  EXTRACTING: 'status-pending',
  PENDING_CONFIRMATION: 'status-confirmed',
  CONFIRMED: 'status-success',
  FAILED: 'status-failed',
}

// 处理复选框变化
const toggleSelect = (paperId: string, event: Event) => {
  event.stopPropagation()
  const checked = (event.target as HTMLInputElement).checked
  const newSet = new Set(props.selectedIds)
  if (checked) {
    newSet.add(paperId)
  } else {
    newSet.delete(paperId)
  }
  emit('update:selectedIds', newSet)
}

// 拖拽开始
const onDragStart = (paperId: string, event: DragEvent) => {
  event.dataTransfer!.setData('text/plain', `paper:${paperId}`)
  event.dataTransfer!.effectAllowed = 'move'
}
</script>

<template>
  <div class="paper-list">
    <div v-if="papers.length === 0" class="empty-state">
      <el-empty description="暂无论文" :image-size="100" />
    </div>

    <div
      v-for="paper in papers"
      :key="paper.id"
      class="paper-card"
      draggable="true"
      @dragstart="onDragStart(paper.id, $event)"
    >
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
        <!-- 左侧信息区 -->
        <div class="paper-info-left">
          <div class="paper-title">{{ paper.title }}</div>
          <div class="paper-authors">{{ paper.authors || '未知作者' }}</div>
          <div class="paper-venue">{{ paper.source || '未知出处' }}</div>
          <div class="paper-year">{{ paper.year || '未知年份' }}</div>
        </div>
        <!-- 右侧状态区 -->
        <div class="paper-status-right">
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
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 16px;
  transition: background 0.15s, border-color 0.15s;
}

.paper-card:hover {
  background: #faf8f5;
  border-color: #d1d5db;
}

.paper-card[draggable="true"] {
  cursor: grab;
}

.paper-card[draggable="true"]:active {
  opacity: 0.6;
  cursor: grabbing;
}

/* 圆形复选框 - 右上角 */
.card-checkbox {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
}

.card-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin: 0;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background: white;
  border: 1.5px solid #d1d5db;
  border-radius: 50%;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-checkbox input[type="checkbox"]:checked {
  background-color: #4a9d9a;
  border-color: #4a9d9a;
  box-shadow: inset 0 0 0 3px white;
}

.card-checkbox input[type="checkbox"]:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(74, 157, 154, 0.2);
}

.card-checkbox input[type="checkbox"]:hover {
  border-color: #9ca3af;
}

/* 卡片内容区域（点击打开详情） */
.card-content {
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-right: 28px; /* 为右上角复选框预留空间 */
}

/* 左侧信息区 */
.paper-info-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0; /* 允许文本截断 */
}

.paper-title {
  font-weight: 500;
  font-size: 0.95rem;
  color: #1f2937;
  line-height: 1.4;
}

.paper-authors,
.paper-venue,
.paper-year{
  font-size: 0.8rem;
  color: #6b7280;
}

/* 右侧状态区 */
.paper-status-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.tag {
  font-size: 0.75rem;
  padding: 4px 12px;
  border-radius: 20px;
  background-color: #f5f0ea;
  color: #6b7280;
  white-space: nowrap;
}

.status-processing {
  background: rgba(232, 184, 109, 0.12);
  color: #b88a3e;
}
.status-pending {
  background: rgba(74, 157, 154, 0.1);
  color: #4a9d9a;
}
.status-confirmed {
  background: rgba(74, 157, 154, 0.1);
  color: #4a9d9a;
}
.status-success {
  background: rgba(74, 157, 154, 0.1);
  color: #4a9d9a;
}
.status-failed {
  background: rgba(193, 119, 103, 0.12);
  color: #c17767;
}
</style>
