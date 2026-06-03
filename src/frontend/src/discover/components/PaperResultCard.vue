<template>
  <article class="paper-card" @contextmenu.prevent="showContextMenu($event)">
    <h3 class="card-title">{{ paper.title }}</h3>

    <div class="card-meta">
      <span>{{ paper.year }}</span>
      <span class="meta-dot">·</span>
      <span v-if="paper.venue" class="meta-venue">{{ paper.venue }}</span>
      <span v-if="paper.venue" class="meta-dot">·</span>
      <span class="meta-citation">被引 {{ paper.citation_count ?? 0 }}</span>
      <span v-if="paper.in_library" class="meta-library">已在文库</span>
    </div>

    <div class="card-authors" :title="paper.authors">{{ paper.authors || '未知作者' }}</div>

    <div class="card-divider" />

    <p v-if="abstract" class="card-abstract">{{ abstract }}</p>
    <p v-else class="card-abstract card-abstract-empty">暂无摘要</p>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
      >
        <div class="context-menu-header">复制</div>
        <button class="context-menu-item" @click="copyField('title', paper.title)" title="复制标题">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
          标题
        </button>
        <button class="context-menu-item" @click="copyField('authors', paper.authors)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          作者
        </button>
        <button class="context-menu-item" @click="copyField('doi', doiStr)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
          DOI
        </button>
        <button class="context-menu-item" @click="copyField('arxiv', arxivStr)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M16 8l-8 8"/><path d="M8 8h8v8"/></svg>
          arXiv ID
        </button>
        <button class="context-menu-item" @click="copyField('abstract', abstract)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          摘要
        </button>
        <div class="context-menu-divider" />
        <button class="context-menu-item" @click="copyAll">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
          全部信息
        </button>
      </div>
    </Teleport>
  </article>
</template>

<script setup lang="ts">
import { computed, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { SearchResult, CitationPaper } from '../../discover/types'

type PaperItem = (SearchResult | CitationPaper) & { in_library?: boolean }

const props = defineProps<{
  paper: PaperItem
}>()

const abstract = computed(() => {
  const p = props.paper as any
  return p.abstract || p.description || ''
})

const doiStr = computed(() => (props.paper as any).doi || '')
const arxivStr = computed(() => (props.paper as any).arxiv_id || '')

/* ── 右键菜单 ── */
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
})

function showContextMenu(e: MouseEvent) {
  // 确保菜单不超出视口
  const menuWidth = 200
  const menuHeight = 300
  let x = e.clientX
  let y = e.clientY
  if (x + menuWidth > window.innerWidth) x = window.innerWidth - menuWidth - 8
  if (y + menuHeight > window.innerHeight) y = window.innerHeight - menuHeight - 8
  contextMenu.x = x
  contextMenu.y = y
  contextMenu.visible = true
}

function hideContextMenu() {
  contextMenu.visible = false
}

function onGlobalClick() {
  if (contextMenu.visible) hideContextMenu()
}

onMounted(() => document.addEventListener('click', onGlobalClick))
onUnmounted(() => document.removeEventListener('click', onGlobalClick))

/* ── 复制功能 ── */
function copyToClipboard(text: string, label: string) {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success(`已复制${label}`)
    hideContextMenu()
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

function copyField(field: string, value: string | undefined) {
  if (value) copyToClipboard(value, field === 'title' ? '标题' : field === 'authors' ? '作者' : field === 'doi' ? 'DOI' : field === 'arxiv' ? 'arXiv ID' : '摘要')
}

function copyAll() {
  const p = props.paper as any
  const parts: string[] = []
  if (p.title) parts.push(`标题: ${p.title}`)
  if (p.authors) parts.push(`作者: ${p.authors}`)
  if (p.year) parts.push(`年份: ${p.year}`)
  if (p.venue) parts.push(`来源: ${p.venue}`)
  if (doiStr.value) parts.push(`DOI: ${doiStr.value}`)
  if (arxivStr.value) parts.push(`arXiv: ${arxivStr.value}`)
  if (abstract.value) parts.push(`摘要: ${abstract.value}`)
  copyToClipboard(parts.join('\n'), '全部信息')
}
</script>

<style scoped>
.paper-card {
  position: relative;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
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

.card-title {
  margin: 0 0 0.35rem;
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
  flex-wrap: wrap;
  overflow: hidden;
}

.meta-venue {
  color: var(--brand-accent);
  opacity: 0.75;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-citation {
  color: var(--brand-accent);
  font-weight: 500;
  opacity: 0.85;
}

.meta-library {
  color: #10b981;
  font-weight: 500;
  font-size: 0.72rem;
  background: rgba(16, 185, 129, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
}

.card-authors {
  margin-top: 0.2rem;
  font-size: 0.78rem;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-divider {
  margin: 0.55rem 0;
  height: 1px;
  background: rgba(148, 163, 184, 0.12);
}

.card-abstract {
  margin: 0;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-abstract-empty {
  font-style: italic;
  opacity: 0.5;
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

.context-menu-item:hover:not(:disabled) {
  background: #f1f5f9;
  color: #1e293b;
}

.context-menu-item:active:not(:disabled) {
  background: #e2e8f0;
}

.context-menu-item:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.context-menu-divider {
  margin: 0.2rem 0.5rem;
  height: 1px;
  background: #e2e8f0;
}
</style>
