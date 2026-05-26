<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import {
  List,
  Sort,
  Tickets,
  Picture,
  Cpu,
  CollectionTag,
} from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

type PreviewMode = 'split' | 'live'

const previewMode = ref<PreviewMode>('live')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const hasContent = computed(() => Boolean(props.modelValue?.trim()))
const markdownHtml = computed(() => {
  if (!props.modelValue?.trim()) return ''
  return marked.parse(props.modelValue, { breaks: true }) as string
})

const setMode = (mode: PreviewMode) => {
  previewMode.value = mode
}

const handleInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}

// ── Toolbar helpers ──

const insertMarkdown = (before: string, after: string, defaultText = 'text') => {
  const ta = textareaRef.value
  if (!ta) return

  const start = ta.selectionStart
  const end = ta.selectionEnd
  const text = props.modelValue
  const selected = text.slice(start, end) || defaultText

  const newText = text.slice(0, start) + before + selected + after + text.slice(end)
  emit('update:modelValue', newText)

  requestAnimationFrame(() => {
    ta.focus()
    const pos = start + before.length
    ta.setSelectionRange(pos, pos + selected.length)
  })
}

const toggleBold = () => insertMarkdown('**', '**', '粗体文字')
const toggleItalic = () => insertMarkdown('*', '*', '斜体文字')
const toggleHeading = () => {
  const ta = textareaRef.value
  if (!ta) return
  const start = ta.selectionStart
  const text = props.modelValue
  const lineStart = text.lastIndexOf('\n', start - 1) + 1
  const lineEnd = text.indexOf('\n', start)
  const line = text.slice(lineStart, lineEnd === -1 ? text.length : lineEnd)

  if (/^#{1,6}\s/.test(line)) {
    const headingEnd = line.indexOf(' ')
    const newText = text.slice(0, lineStart) + line.slice(headingEnd + 1) + text.slice(lineStart + line.length)
    emit('update:modelValue', newText)
  } else {
    insertMarkdown('### ', '', '标题')
  }
}

const toggleBulletList = () => insertMarkdown('- ', '', '列表项')
const toggleOrderedList = () => insertMarkdown('1. ', '', '列表项')
const toggleCode = () => insertMarkdown('`', '`', 'code')
const toggleCodeBlock = () => insertMarkdown('```\n', '\n```', '代码块')

/** 图片上传（stub — 仅插入 markdown 图片语法） */
const insertImage = () => {
  const ta = textareaRef.value
  if (!ta) return

  const start = ta.selectionStart
  const end = ta.selectionEnd
  const text = props.modelValue
  const selected = text.slice(start, end)

  const alt = selected || '图片描述'
  const stubUrl = 'https://via.placeholder.com/400x200?text=Paste+image+URL+here'
  const markdown = `![${alt}](${stubUrl})`

  const newText = text.slice(0, start) + markdown + text.slice(end)
  emit('update:modelValue', newText)
}
</script>

<template>
  <div class="md-editor" :class="`mode-${previewMode}`">
    <!-- 工具栏 -->
    <div class="md-toolbar">
      <div class="md-toolbar-group">
        <el-tooltip content="粗体" placement="top" :show-after="400">
          <button class="md-btn" @click="toggleBold" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" />
              <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" />
            </svg>
          </button>
        </el-tooltip>
        <el-tooltip content="斜体" placement="top" :show-after="400">
          <button class="md-btn" @click="toggleItalic" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="19" y1="4" x2="10" y2="4" />
              <line x1="14" y1="20" x2="5" y2="20" />
              <line x1="15" y1="4" x2="9" y2="20" />
            </svg>
          </button>
        </el-tooltip>
        <el-tooltip content="标题" placement="top" :show-after="400">
          <button class="md-btn" @click="toggleHeading" tabindex="-1">
            <el-icon :size="15"><Tickets /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <div class="md-toolbar-group">
        <el-tooltip content="无序列表" placement="top" :show-after="400">
          <button class="md-btn" @click="toggleBulletList" tabindex="-1">
            <el-icon :size="15"><List /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="有序列表" placement="top" :show-after="400">
          <button class="md-btn" @click="toggleOrderedList" tabindex="-1">
            <el-icon :size="15"><Sort /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <div class="md-toolbar-group">
        <el-tooltip content="行内代码" placement="top" :show-after="400">
          <button class="md-btn" @click="toggleCode" tabindex="-1">
            <el-icon :size="15"><Cpu /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="代码块" placement="top" :show-after="400">
          <button class="md-btn" @click="toggleCodeBlock" tabindex="-1">
            <el-icon :size="15"><CollectionTag /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="插入图片" placement="top" :show-after="400">
          <button class="md-btn" @click="insertImage" tabindex="-1">
            <el-icon :size="15"><Picture /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <div class="md-toolbar-spacer" />

      <!-- 预览模式切换 -->
      <div class="md-toolbar-group mode-switch">
        <button
          class="md-btn mode-btn"
          :class="{ 'is-active': previewMode === 'live' }"
          @click="setMode('live')"
          tabindex="-1"
        >
          实时预览
        </button>
        <button
          class="md-btn mode-btn"
          :class="{ 'is-active': previewMode === 'split' }"
          @click="setMode('split')"
          tabindex="-1"
        >
          分栏预览
        </button>
      </div>
    </div>

    <!-- 分栏模式：编辑区 + 预览区 -->
    <template v-if="previewMode === 'split'">
      <div class="md-body">
        <textarea
          ref="textareaRef"
          class="md-textarea"
          :value="modelValue"
          :placeholder="placeholder || '支持 Markdown 语法...'"
          @input="handleInput"
        />
      </div>
      <div class="md-preview-section" :class="{ 'is-empty': !hasContent }">
        <div class="md-preview-label">预览</div>
        <div class="md-preview markdown-body">
          <div v-if="!hasContent" class="md-preview-empty">
            <span>输入内容后可预览渲染效果</span>
          </div>
          <div v-else v-html="markdownHtml" />
        </div>
      </div>
    </template>

    <!-- 实时预览模式：只显示渲染结果 -->
    <div v-else class="md-live markdown-body">
      <div v-if="!hasContent" class="md-live-empty">
        <textarea
          ref="textareaRef"
          class="md-live-textarea"
          :value="modelValue"
          :placeholder="placeholder || '开始写作...（支持 Markdown 语法）'"
          @input="handleInput"
        />
      </div>
      <div v-else v-html="markdownHtml" />
      <!-- 点击预览区域重新唤起编辑 -->
      <div
        v-if="hasContent"
        class="md-live-edit-trigger"
        @click="setMode('split')"
      >
        点击编辑
      </div>
    </div>
  </div>
</template>

<style scoped>
.md-editor {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-page);
  transition: border-color 0.2s ease;
}

.md-editor:focus-within {
  border-color: var(--brand);
}

/* ── 工具栏 ── */
.md-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 8px;
  border-bottom: 1px solid var(--line-soft);
  background: var(--bg-secondary);
  user-select: none;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.md-toolbar-group {
  display: flex;
  align-items: center;
  gap: 1px;
}

.md-toolbar-group + .md-toolbar-group {
  margin-left: 2px;
  padding-left: 2px;
  border-left: 1px solid var(--line-soft);
}

.md-toolbar-spacer {
  flex: 1;
}

.md-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.12s ease;
}

.md-btn:hover {
  background: rgba(74, 157, 154, 0.08);
  color: var(--brand);
}

.md-btn:active {
  background: rgba(74, 157, 154, 0.15);
  transform: scale(0.95);
}

/* ── 模式切换按钮 ── */
.mode-switch {
  gap: 2px !important;
  border-left: 1px solid var(--line-soft);
  padding-left: 4px;
}

.mode-btn {
  width: auto;
  padding: 0 8px;
  font-size: 0.72rem;
  font-weight: 500;
  border-radius: 6px;
  letter-spacing: 0.02em;
}

.mode-btn.is-active {
  background: rgba(74, 157, 154, 0.12);
  color: var(--brand);
  font-weight: 600;
}

/* ── 分栏模式：编辑区 ── */
.md-body {
  flex-shrink: 0;
}

.md-textarea {
  width: 100%;
  min-height: 100px;
  max-height: 300px;
  padding: 10px 12px;
  border: none;
  outline: none;
  resize: vertical;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.82rem;
  line-height: 1.7;
  color: var(--text-primary);
  background: var(--bg-page);
}

.md-textarea::placeholder {
  color: var(--text-tertiary);
}

/* ── 分栏模式：预览区 ── */
.md-preview-section {
  border-top: 1px solid var(--line-soft);
  background: var(--bg-secondary);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.md-preview-section.is-empty {
  background: var(--bg-page);
}

.md-preview-label {
  padding: 5px 12px 3px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.md-preview {
  padding: 0 12px 12px;
  overflow-y: auto;
  flex: 1;
}

.md-preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60px;
  color: var(--text-tertiary);
  font-size: 0.78rem;
}

/* ── 实时预览模式 ── */
.mode-live .md-toolbar {
  border-bottom-color: var(--line-soft);
}

.md-live {
  flex: 1;
  padding: 16px 14px;
  overflow-y: auto;
  min-height: 120px;
  cursor: default;
}

.md-live-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

.md-live-textarea {
  width: 100%;
  min-height: 120px;
  padding: 0;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 0.88rem;
  line-height: 1.75;
  color: var(--text-tertiary);
  background: transparent;
}

.md-live-textarea::placeholder {
  color: var(--text-tertiary);
}

.md-live-edit-trigger {
  position: sticky;
  bottom: 0;
  text-align: center;
  padding: 6px 0 2px;
  font-size: 0.72rem;
  color: var(--text-tertiary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease;
  background: linear-gradient(transparent, var(--bg-page) 40%);
}

.md-live:hover .md-live-edit-trigger {
  opacity: 1;
}
</style>

<style>
/* ── Markdown 渲染样式（全局，因为 v-html 内容在 scoped 外） ── */
.markdown-body {
  font-size: 0.85rem;
  line-height: 1.75;
  color: var(--text-primary);
  word-wrap: break-word;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin: 1em 0 0.5em;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text-primary);
}

.markdown-body h1 { font-size: 1.3rem; }
.markdown-body h2 { font-size: 1.15rem; }
.markdown-body h3 { font-size: 1.05rem; }
.markdown-body h4 { font-size: 0.95rem; }

.markdown-body p {
  margin: 0 0 0.75em;
}

.markdown-body strong {
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-body em {
  font-style: italic;
}

.markdown-body ul,
.markdown-body ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.markdown-body li {
  margin: 0.25em 0;
}

.markdown-body li > ul,
.markdown-body li > ol {
  margin: 0.25em 0;
}

.markdown-body code {
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8em;
  background: rgba(74, 157, 154, 0.08);
  color: var(--brand);
}

.markdown-body pre {
  margin: 0.75em 0;
  padding: 12px 14px;
  border-radius: 8px;
  background: #f0f4f4;
  overflow-x: auto;
}

.markdown-body pre code {
  padding: 0;
  border-radius: 0;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.8rem;
  line-height: 1.6;
}

.markdown-body blockquote {
  margin: 0.75em 0;
  padding: 0.5em 1em;
  border-left: 3px solid var(--brand);
  background: rgba(74, 157, 154, 0.04);
  border-radius: 0 6px 6px 0;
  color: var(--text-secondary);
}

.markdown-body blockquote p {
  margin: 0.25em 0;
}

.markdown-body a {
  color: var(--brand);
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body img {
  max-width: 100%;
  border-radius: 8px;
  margin: 0.75em 0;
}

.markdown-body hr {
  margin: 1.5em 0;
  border: none;
  border-top: 1px solid var(--line-soft);
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75em 0;
  font-size: 0.82rem;
}

.markdown-body th,
.markdown-body td {
  padding: 8px 12px;
  border: 1px solid var(--line-soft);
  text-align: left;
}

.markdown-body th {
  background: var(--bg-secondary);
  font-weight: 600;
}

.markdown-body tr:nth-child(even) {
  background: var(--bg-secondary);
}

.markdown-body input[type="checkbox"] {
  margin-right: 4px;
}

.markdown-body del {
  color: var(--text-tertiary);
}
</style>
