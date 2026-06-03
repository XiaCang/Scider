<!-- PaperListItem.vue — 文库论文卡片列表，含右键复制菜单 -->
<script setup lang="ts">
import { reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
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

/* ── 右键菜单 ── */
const contextPaper = reactive<{ paper: LibraryPaper | null }>({ paper: null })
const contextMenu = reactive({ visible: false, x: 0, y: 0 })

function showContextMenu(e: MouseEvent, paper: LibraryPaper) {
  const menuWidth = 200
  const menuHeight = 300
  let x = e.clientX
  let y = e.clientY
  if (x + menuWidth > window.innerWidth) x = window.innerWidth - menuWidth - 8
  if (y + menuHeight > window.innerHeight) y = window.innerHeight - menuHeight - 8
  contextPaper.paper = paper
  contextMenu.x = x
  contextMenu.y = y
  contextMenu.visible = true
}

function hideContextMenu() {
  contextMenu.visible = false
  contextPaper.paper = null
}

function onGlobalClick() {
  if (contextMenu.visible) hideContextMenu()
}

onMounted(() => document.addEventListener('click', onGlobalClick))
onUnmounted(() => document.removeEventListener('click', onGlobalClick))

/* ── 复制功能 ── */
function copyToClipboard(text: string, label: string) {
  if (!text) {
    ElMessage.info(`暂无${label}`)
    return
  }
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success(`已复制${label}`)
    hideContextMenu()
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

function copyField(_field: string, value: string | undefined, label: string) {
  copyToClipboard(value || '', label)
}

function copyAll(paper: LibraryPaper) {
  const parts: string[] = []
  if (paper.title) parts.push(`标题: ${paper.title}`)
  if (paper.authors) parts.push(`作者: ${paper.authors}`)
  if (paper.year) parts.push(`年份: ${paper.year}`)
  if (paper.source) parts.push(`来源: ${paper.source}`)
  if (paper.doi) parts.push(`DOI: ${paper.doi}`)
  if (paper.arxiv_id) parts.push(`arXiv: ${paper.arxiv_id}`)
  if (paper.abstract) parts.push(`摘要: ${paper.abstract}`)
  copyToClipboard(parts.join('\n'), '全部信息')
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
      @contextmenu.prevent="showContextMenu($event, paper)"
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

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="contextMenu.visible && contextPaper.paper"
        class="context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
      >
        <div class="context-menu-header">复制</div>
        <button class="context-menu-item" @click="copyField('title', contextPaper.paper!.title, '标题')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
          标题
        </button>
        <button class="context-menu-item" @click="copyField('authors', contextPaper.paper!.authors, '作者')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          作者
        </button>
        <button class="context-menu-item" @click="copyField('doi', contextPaper.paper!.doi, 'DOI')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
          DOI
        </button>
        <button class="context-menu-item" @click="copyField('arxiv', contextPaper.paper!.arxiv_id, 'arXiv ID')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M16 8l-8 8"/><path d="M8 8h8v8"/></svg>
          arXiv ID
        </button>
        <button class="context-menu-item" @click="copyField('abstract', contextPaper.paper!.abstract, '摘要')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          摘要
        </button>
        <div class="context-menu-divider" />
        <button class="context-menu-item" @click="contextPaper.paper && copyAll(contextPaper.paper)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
          全部信息
        </button>
      </div>
    </Teleport>
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

<!-- 右键菜单样式（非 scoped，因为 Teleport 到 body） -->
<style>
.context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 180px;
  padding: 0.35rem 0;
  background: #ffffff;
  border-radius: 10px;
  box-shadow:
    0 10px 30px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(0, 0, 0, 0.04);
  animation: context-menu-enter 0.12s ease-out;
}

@keyframes context-menu-enter {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-4px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.context-menu-header {
  padding: 0.3rem 0.85rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.45rem 0.85rem;
  border: none;
  background: transparent;
  color: #334155;
  font-size: 0.82rem;
  text-align: left;
  cursor: pointer;
  transition: background 0.1s ease;
  white-space: nowrap;
}

.context-menu-item:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.context-menu-item:active {
  background: #e2e8f0;
}

.context-menu-divider {
  margin: 0.2rem 0.5rem;
  height: 1px;
  background: #e2e8f0;
}
</style>
