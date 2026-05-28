<script setup lang="ts">
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import ImageExt from '@tiptap/extension-image'
import LinkExt from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import Highlight from '@tiptap/extension-highlight'
import { marked } from 'marked'
import TurndownService from 'turndown'
import {
  List, Sort, Picture, Cpu, CollectionTag, Link,
} from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

type PreviewMode = 'live' | 'split'
const previewMode = ref<PreviewMode>('live')
let isExternalUpdate = false

// ---- Markdown ↔ HTML 转换 ----
marked.setOptions({ breaks: true })

const turndown = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced',
  emDelimiter: '*',
  bulletListMarker: '-',
})

function markdownToHtml(markdown: string): string {
  if (!markdown.trim()) return ''
  return marked.parse(markdown, { breaks: true }) as string
}

function htmlToMarkdown(html: string): string {
  if (!html.trim()) return ''
  return turndown.turndown(html)
}

// ---- 编辑器 ----
const editor = useEditor({
  content: markdownToHtml(props.modelValue || ''),
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3, 4] },
      codeBlock: { HTMLAttributes: { class: 'code-block' } },
    }),
    Placeholder.configure({
      placeholder: props.placeholder || '记录你对这篇论文的想法...',
    }),
    Underline,
    LinkExt.configure({
      openOnClick: true,
      HTMLAttributes: { rel: 'noopener noreferrer', target: '_blank' },
    }),
    ImageExt.configure({ inline: false }),
    TaskList,
    TaskItem.configure({ nested: true }),
    Highlight,
  ],
  onUpdate: ({ editor }) => {
    if (isExternalUpdate) return
    const html = editor.getHTML()
    const md = htmlToMarkdown(html)
    emit('update:modelValue', md)
  },
})

// 外部 modelValue 变化 → 同步到编辑器
watch(
  () => props.modelValue,
  (newVal) => {
    if (!editor.value) return
    const currentHtml = editor.value.getHTML()
    const currentMd = htmlToMarkdown(currentHtml)
    if (newVal !== currentMd) {
      isExternalUpdate = true
      const html = markdownToHtml(newVal || '')
      editor.value.commands.setContent(html || '<p></p>')
      nextTick(() => { isExternalUpdate = false })
    }
  }
)

onBeforeUnmount(() => {
  editor.value?.destroy()
})

// ---- 编辑器命令 ----
const isActive = (name: string, attrs?: Record<string, any>) =>
  editor.value?.isActive(name, attrs) ?? false

const toggleBold = () => editor.value?.chain().focus().toggleBold().run()
const toggleItalic = () => editor.value?.chain().focus().toggleItalic().run()
const toggleUnderline = () => editor.value?.chain().focus().toggleUnderline().run()
const toggleStrike = () => editor.value?.chain().focus().toggleStrike().run()
const toggleHeading = (level: 1 | 2 | 3 | 4) =>
  editor.value?.chain().focus().toggleHeading({ level }).run()
const toggleBulletList = () => editor.value?.chain().focus().toggleBulletList().run()
const toggleOrderedList = () => editor.value?.chain().focus().toggleOrderedList().run()
const toggleTaskList = () => editor.value?.chain().focus().toggleTaskList().run()
const toggleCode = () => editor.value?.chain().focus().toggleCode().run()
const toggleCodeBlock = () => editor.value?.chain().focus().toggleCodeBlock().run()
const toggleBlockquote = () => editor.value?.chain().focus().toggleBlockquote().run()
const toggleHighlight = () => editor.value?.chain().focus().toggleHighlight().run()

const insertImage = () => {
  const url = window.prompt('输入图片链接：')
  if (url) editor.value?.chain().focus().setImage({ src: url }).run()
}

const setLink = () => {
  const url = window.prompt('输入链接地址：')
  if (url) editor.value?.chain().focus().setLink({ href: url }).run()
}

const setMode = (mode: PreviewMode) => {
  previewMode.value = mode
}

// 撤销 / 重做
const undo = () => editor.value?.chain().focus().undo().run()
const redo = () => editor.value?.chain().focus().redo().run()

// 分栏模式：textarea 输入同步
const splitValue = ref(props.modelValue)
watch(() => props.modelValue, (v) => { splitValue.value = v })
const onSplitInput = (e: Event) => {
  const val = (e.target as HTMLTextAreaElement).value
  splitValue.value = val
  emit('update:modelValue', val)
}
</script>

<template>
  <div class="md-editor" :class="`mode-${previewMode}`">
    <!-- 工具栏 -->
    <div class="md-toolbar">
      <div class="md-toolbar-group">
        <el-tooltip content="撤销" placement="top" :show-after="400">
          <button class="md-btn" @click="undo" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
          </button>
        </el-tooltip>
        <el-tooltip content="重做" placement="top" :show-after="400">
          <button class="md-btn" @click="redo" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
          </button>
        </el-tooltip>
      </div>

      <div class="md-separator" />

      <div class="md-toolbar-group">
        <el-tooltip content="粗体" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('bold') }" @click="toggleBold" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" /><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" />
            </svg>
          </button>
        </el-tooltip>
        <el-tooltip content="斜体" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('italic') }" @click="toggleItalic" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="19" y1="4" x2="10" y2="4" /><line x1="14" y1="20" x2="5" y2="20" /><line x1="15" y1="4" x2="9" y2="20" />
            </svg>
          </button>
        </el-tooltip>
        <el-tooltip content="下划线" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('underline') }" @click="toggleUnderline" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3" /><line x1="4" y1="21" x2="20" y2="21" />
            </svg>
          </button>
        </el-tooltip>
        <el-tooltip content="删除线" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('strike') }" @click="toggleStrike" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="3" y1="12" x2="21" y2="12" /><path d="M16 6H9a3 3 0 0 0 0 6" /><path d="M8 18h7a3 3 0 0 0 3-3" />
            </svg>
          </button>
        </el-tooltip>
      </div>

      <div class="md-separator" />

      <div class="md-toolbar-group">
        <el-tooltip content="标题 1" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('heading', { level: 1 }) }" @click="toggleHeading(1)" tabindex="-1">H1</button>
        </el-tooltip>
        <el-tooltip content="标题 2" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('heading', { level: 2 }) }" @click="toggleHeading(2)" tabindex="-1">H2</button>
        </el-tooltip>
        <el-tooltip content="标题 3" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('heading', { level: 3 }) }" @click="toggleHeading(3)" tabindex="-1">H3</button>
        </el-tooltip>
      </div>

      <div class="md-separator" />

      <div class="md-toolbar-group">
        <el-tooltip content="无序列表" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('bulletList') }" @click="toggleBulletList" tabindex="-1">
            <el-icon :size="15"><List /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="有序列表" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('orderedList') }" @click="toggleOrderedList" tabindex="-1">
            <el-icon :size="15"><Sort /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="任务列表" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('taskList') }" @click="toggleTaskList" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" /><path d="m9 12 2 2 4-4" />
            </svg>
          </button>
        </el-tooltip>
      </div>

      <div class="md-separator" />

      <div class="md-toolbar-group">
        <el-tooltip content="行内代码" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('code') }" @click="toggleCode" tabindex="-1">
            <el-icon :size="15"><Cpu /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="代码块" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('codeBlock') }" @click="toggleCodeBlock" tabindex="-1">
            <el-icon :size="15"><CollectionTag /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="引用" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('blockquote') }" @click="toggleBlockquote" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z" /><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z" />
            </svg>
          </button>
        </el-tooltip>
        <el-tooltip content="高亮" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('highlight') }" @click="toggleHighlight" tabindex="-1">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 2 2.5 5.5L20 9l-4 4 1 5.5L12 16l-5 2.5L8 13l-4-4 5.5-1.5Z" />
            </svg>
          </button>
        </el-tooltip>
      </div>

      <div class="md-separator" />

      <div class="md-toolbar-group">
        <el-tooltip content="插入图片" placement="top" :show-after="400">
          <button class="md-btn" @click="insertImage" tabindex="-1">
            <el-icon :size="15"><Picture /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="插入链接" placement="top" :show-after="400">
          <button class="md-btn" :class="{ 'is-active': isActive('link') }" @click="setLink" tabindex="-1">
            <el-icon :size="15"><Link /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <div class="md-toolbar-spacer" />

      <div class="md-toolbar-group mode-switch">
        <button
          class="md-btn mode-btn"
          :class="{ 'is-active': previewMode === 'live' }"
          @click="setMode('live')"
        >
          所见即所得
        </button>
        <button
          class="md-btn mode-btn"
          :class="{ 'is-active': previewMode === 'split' }"
          @click="setMode('split')"
        >
          源码
        </button>
      </div>
    </div>

    <!-- 所见即所得模式 -->
    <div v-if="previewMode === 'live'" class="md-live">
      <EditorContent :editor="editor" class="tiptap-editor" />
    </div>

    <!-- 分栏模式 -->
    <div v-else class="md-split">
      <textarea
        class="md-textarea"
        :value="splitValue"
        :placeholder="props.placeholder || '支持 Markdown 语法...'"
        @input="onSplitInput"
      />
      <div class="md-preview markdown-body" v-html="markdownToHtml(splitValue)" />
    </div>
  </div>
</template>

<style scoped>
.md-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: white;
  overflow: hidden;
}

/* 工具栏 */
.md-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 6px;
  border-bottom: 1px solid var(--line-soft);
  background: #fafafa;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.md-toolbar-group {
  display: flex;
  align-items: center;
  gap: 1px;
}

.md-separator {
  width: 1px;
  height: 20px;
  background: #e0e0e0;
  margin: 0 3px;
  flex-shrink: 0;
}

.md-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #555;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  transition: background 0.12s, color 0.12s;
  flex-shrink: 0;
}

.md-btn:hover {
  background: #e8e8e8;
  color: #333;
}

.md-btn:active {
  background: #ddd;
}

.md-btn.is-active {
  background: #d4e6ff;
  color: #1a73e8;
}

.mode-btn {
  width: auto;
  padding: 0 8px;
  font-size: 0.75rem;
  font-weight: 500;
}

.md-toolbar-spacer {
  flex: 1;
}

/* 所见即所得编辑区 */
.md-live {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.tiptap-editor {
  padding: 14px 16px;
  outline: none;
  font-size: 0.88rem;
  line-height: 1.75;
  color: #333;
}

.tiptap-editor :deep(p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  color: #bbb;
  pointer-events: none;
  float: left;
  height: 0;
}

/* 分栏模式 */
.md-split {
  flex: 1;
  display: flex;
  min-height: 0;
}

.md-textarea {
  flex: 1;
  width: 50%;
  min-height: 100px;
  padding: 12px 14px;
  border: none;
  outline: none;
  resize: none;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.82rem;
  line-height: 1.7;
  background: #f8f9fa;
  color: #333;
}

.md-preview {
  flex: 1;
  width: 50%;
  padding: 12px 14px;
  overflow-y: auto;
  background: white;
  border-left: 1px solid var(--line-soft);
  font-size: 0.85rem;
  line-height: 1.7;
  color: #333;
}
</style>

<style>
/* Tiptap 编辑器内容样式 */
.tiptap-editor .ProseMirror {
  outline: none;
  min-height: 120px;
}

.tiptap-editor h1 { font-size: 1.5rem; font-weight: 700; margin: 0.6em 0 0.3em; }
.tiptap-editor h2 { font-size: 1.25rem; font-weight: 700; margin: 0.5em 0 0.25em; }
.tiptap-editor h3 { font-size: 1.1rem; font-weight: 600; margin: 0.4em 0 0.2em; }
.tiptap-editor h4 { font-size: 1rem; font-weight: 600; margin: 0.3em 0 0.15em; }

.tiptap-editor strong { font-weight: 700; }
.tiptap-editor em { font-style: italic; }
.tiptap-editor u { text-decoration: underline; }
.tiptap-editor s { text-decoration: line-through; }

.tiptap-editor p { margin: 0.3em 0; }

.tiptap-editor code {
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.82em;
  background: #f0f0f0;
  color: #d63384;
}

.tiptap-editor pre {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 14px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.6em 0;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8rem;
  line-height: 1.6;
}

.tiptap-editor pre code {
  background: none;
  color: inherit;
  padding: 0;
  font-size: inherit;
}

.tiptap-editor blockquote {
  border-left: 3px solid #4a9d9a;
  padding: 0.3em 1em;
  margin: 0.6em 0;
  background: rgba(74, 157, 154, 0.05);
  color: #555;
}

.tiptap-editor ul,
.tiptap-editor ol {
  padding-left: 1.5em;
  margin: 0.3em 0;
}

.tiptap-editor li {
  margin: 0.15em 0;
}

.tiptap-editor ul[data-type="taskList"] {
  list-style: none;
  padding-left: 0;
}

.tiptap-editor ul[data-type="taskList"] li {
  display: flex;
  align-items: flex-start;
  gap: 0.4em;
}

.tiptap-editor ul[data-type="taskList"] li > label {
  flex-shrink: 0;
  margin-top: 0.25em;
}

.tiptap-editor ul[data-type="taskList"] li > label input[type="checkbox"] {
  accent-color: #4a9d9a;
  cursor: pointer;
}

.tiptap-editor img {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 0.5em 0;
  display: block;
}

.tiptap-editor a {
  color: #1a73e8;
  text-decoration: underline;
  cursor: pointer;
}

.tiptap-editor mark {
  background: #fff3cd;
  padding: 0 3px;
  border-radius: 2px;
}

.tiptap-editor hr {
  border: none;
  border-top: 2px solid #e0e0e0;
  margin: 1em 0;
}

/* 分栏模式预览区样式 */
.md-preview h1 { font-size: 1.5rem; font-weight: 700; margin: 0.6em 0 0.3em; }
.md-preview h2 { font-size: 1.25rem; font-weight: 700; margin: 0.5em 0 0.25em; }
.md-preview h3 { font-size: 1.1rem; font-weight: 600; margin: 0.4em 0 0.2em; }
.md-preview p { margin: 0.3em 0; line-height: 1.7; }
.md-preview code {
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 0.82em;
  background: #f0f0f0;
  color: #d63384;
}
.md-preview pre {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 14px 16px;
  border-radius: 8px;
  overflow-x: auto;
}
.md-preview pre code { background: none; color: inherit; padding: 0; }
.md-preview blockquote {
  border-left: 3px solid #4a9d9a;
  padding: 0.3em 1em;
  margin: 0.6em 0;
  background: rgba(74, 157, 154, 0.05);
  color: #555;
}
.md-preview ul, .md-preview ol { padding-left: 1.5em; }
.md-preview img { max-width: 100%; border-radius: 6px; }
.md-preview a { color: #1a73e8; }
.md-preview table { border-collapse: collapse; width: 100%; margin: 0.5em 0; }
.md-preview th, .md-preview td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
.md-preview th { background: #f5f5f5; font-weight: 600; }
</style>
