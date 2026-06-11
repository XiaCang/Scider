<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Promotion, CopyDocument, Refresh, Edit, Check, Close } from '@element-plus/icons-vue'
import { createChatConnection } from '../api/chat'
import type { ChatMessage } from '../types/library'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { ElMessage } from 'element-plus'

// 配置 marked
marked.setOptions({
  gfm: true,
  breaks: true,
})

// 渲染 Markdown 并净化 HTML
const renderMarkdown = (content: string) => {
  if (!content) return ''
  const rawHtml = marked.parse(content, { async: false }) as string
  return DOMPurify.sanitize(rawHtml)
}

const props = defineProps<{
  paperId: string
}>()

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const editInput = ref('')
const editingId = ref<string | null>(null)

// 流式构建中的消息 ID
let streamingMsgId = ''

let chatConnection: ReturnType<typeof createChatConnection> | null = null

onMounted(() => {
  chatConnection = createChatConnection(props.paperId, {
    onToken: (token) => {
      const last = messages.value[messages.value.length - 1]
      if (last && last.id === streamingMsgId) {
        last.content += token
      } else {
        messages.value.push({
          id: streamingMsgId,
          role: 'assistant',
          content: token,
          createdAt: new Date().toISOString(),
        })
      }
      scrollToBottom()
    },
    onDone: (fullContent, _sources) => {
      if (fullContent) {
        const last = messages.value[messages.value.length - 1]
        if (last && last.id === streamingMsgId) {
          last.content = fullContent
        }
      }
      sending.value = false
      streamingMsgId = ''
      scrollToBottom()
    },
    onError: (error) => {
      if (streamingMsgId) {
        const last = messages.value[messages.value.length - 1]
        if (last && last.id === streamingMsgId) {
          last.content += `\n\n**${error}**`
        }
        streamingMsgId = ''
      } else {
        messages.value.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: `⚠️ ${error}`,
          createdAt: new Date().toISOString(),
        })
      }
      sending.value = false
      scrollToBottom()
    },
  })
})

onUnmounted(() => {
  chatConnection?.close()
  chatConnection = null
})

const sendMessage = async (text?: string) => {
  const content = text ?? inputText.value.trim()
  if (!content || sending.value || !chatConnection) return

  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content,
    createdAt: new Date().toISOString(),
  })
  if (!text) inputText.value = ''
  sending.value = true
  streamingMsgId = (Date.now() + 1).toString()

  chatConnection.send(content)
  await nextTick()
  scrollToBottom()
}

const askWithContext = async (selectedText: string) => {
  if (!chatConnection) return
  const question = `关于这段文字：「${selectedText.slice(0, 200)}」，请解释一下。`
  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: question,
    createdAt: new Date().toISOString(),
  })
  sending.value = true
  streamingMsgId = (Date.now() + 1).toString()

  chatConnection.send(question)
  await nextTick()
  scrollToBottom()
}

const clearMessages = () => {
  messages.value = []
  chatConnection?.clear()
}

const scrollToBottom = () => {
  void nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// ── 键盘：Enter = 换行，Shift+Enter = 发送 ──
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// ── 自动调整输入框高度 ──
const autoResize = (e: Event) => {
  const ta = e.target as HTMLTextAreaElement
  ta.style.height = 'auto'
  const maxH = 160
  ta.style.height = `${Math.min(ta.scrollHeight, maxH)}px`
}

// ── 消息操作：复制 ──
const copyMessage = (content: string) => {
  navigator.clipboard.writeText(content).then(() => {
    ElMessage.success('已复制')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// ── 消息操作：重发 ──
const retryMessage = (msg: ChatMessage) => {
  if (msg.role !== 'user') return
  const idx = messages.value.findIndex(m => m.id === msg.id)
  if (idx !== -1) messages.value.splice(idx, 1)
  sendMessage(msg.content)
}

// ── 消息操作：编辑 ──
const startEdit = (msg: ChatMessage) => {
  editingId.value = msg.id
  editInput.value = msg.content
  nextTick(() => {
    const ta = document.querySelector('.chat-edit-textarea') as HTMLTextAreaElement
    ta?.focus()
  })
}

const cancelEdit = () => {
  editingId.value = null
  editInput.value = ''
}

const saveEdit = (msg: ChatMessage) => {
  const text = editInput.value.trim()
  if (!text) return
  const idx = messages.value.findIndex(m => m.id === msg.id)
  if (idx !== -1) messages.value.splice(idx, 1)
  editingId.value = null
  editInput.value = ''
  sendMessage(text)
}

defineExpose({ askWithContext, clearMessages })
</script>

<template>
  <div class="ai-chat-panel">
    <div class="ai-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="ai-empty">
        <p>对论文内容有疑问？</p>
        <p>选中 PDF 文字后右键→"向 AI 提问"</p>
        <p>或在下方输入问题</p>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="ai-msg"
        :class="msg.role"
      >
        <div class="ai-msg-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>

        <!-- 编辑模式 -->
        <div v-if="editingId === msg.id" class="chat-edit-wrap">
          <textarea
            v-model="editInput"
            class="chat-edit-textarea"
            @input="autoResize"
            @keydown="handleKeydown"
          />
          <div class="chat-edit-actions">
            <el-button size="small" type="primary" :icon="Check" @click="saveEdit(msg)">保存</el-button>
            <el-button size="small" :icon="Close" @click="cancelEdit">取消</el-button>
          </div>
        </div>

        <!-- 显示模式 -->
        <template v-else>
          <div v-if="msg.role === 'assistant'" class="ai-msg-content markdown-body" v-html="renderMarkdown(msg.content)" />
          <div v-else class="ai-msg-content">{{ msg.content }}</div>
          <!-- 消息操作按钮 -->
          <div class="ai-msg-actions">
            <button class="ai-action-btn" title="复制" @click="copyMessage(msg.content)">
              <el-icon :size="13"><CopyDocument /></el-icon>
            </button>
            <button v-if="msg.role === 'user'" class="ai-action-btn" title="重发" @click="retryMessage(msg)">
              <el-icon :size="13"><Refresh /></el-icon>
            </button>
            <button v-if="msg.role === 'user'" class="ai-action-btn" title="修改" @click="startEdit(msg)">
              <el-icon :size="13"><Edit /></el-icon>
            </button>
          </div>
        </template>
      </div>

      <div v-if="sending && !streamingMsgId" class="ai-msg assistant">
        <div class="ai-msg-label">AI</div>
        <div class="ai-msg-content ai-thinking">思考中...</div>
      </div>
    </div>

    <div class="ai-input-area">
      <textarea
        ref="textareaRef"
        v-model="inputText"
        class="ai-textarea"
        placeholder="输入问题，Shift+Enter 发送..."
        :disabled="sending"
        @input="autoResize"
        @keydown="handleKeydown"
      />
      <el-button
        type="primary"
        :icon="Promotion"
        :loading="sending"
        @click="sendMessage()"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.ai-chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  /* 关键：强制滚动条占位，避免展开面板时滚动条出现/消失导致宽度抖动 */
  overflow-y: auto;
  scrollbar-gutter: stable; /* 现代浏览器预留滚动条空间，更平滑 */
}

.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px 12px;
  min-height: 0;
}

.ai-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #bbb;
  font-size: 0.8rem;
  text-align: center;
  gap: 4px;
}

.ai-empty p {
  margin: 0;
}

.ai-msg {
  margin-bottom: 14px;
}

.ai-msg-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: #999;
  margin-bottom: 3px;
}

.ai-msg.user .ai-msg-label {
  color: var(--brand);
}

.ai-msg-content {
  font-size: 0.84rem;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 8px 10px;
  border-radius: 6px;
  background: #f5f7fa;
}

.ai-msg.user .ai-msg-content {
  background: rgba(74, 157, 154, 0.08);
}

.ai-thinking {
  color: #999;
  font-style: italic;
}

/* ── 消息操作按钮 ── */
.ai-msg-actions {
  display: flex;
  gap: 2px;
  margin-top: 3px;
  padding-left: 2px;
  opacity: 0;
  transition: opacity 0.15s;
}

.ai-msg:hover .ai-msg-actions {
  opacity: 1;
}

.ai-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #999;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.ai-action-btn:hover {
  background: #f0f0f0;
  color: #555;
}

.ai-action-btn:active {
  background: #e5e5e5;
}

/* ── 编辑模式 ── */
.chat-edit-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chat-edit-textarea {
  width: 100%;
  min-height: 60px;
  max-height: 200px;
  padding: 8px 10px;
  border: 1px solid var(--line-soft);
  border-radius: 6px;
  font-size: 0.84rem;
  line-height: 1.6;
  font-family: inherit;
  resize: none;
  outline: none;
  background: #fafafa;
  color: #333;
  transition: border-color 0.15s;
  box-sizing: border-box;
  scrollbar-width: none;
}
.chat-edit-textarea::-webkit-scrollbar {
  display: none;
}

.chat-edit-textarea:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 2px rgba(74, 157, 154, 0.12);
}

.chat-edit-actions {
  display: flex;
  gap: 6px;
}

/* ── 输入区 ── */
.ai-input-area {
  display: flex;
  gap: 6px;
  padding: 8px 10px;
  border-top: 1px solid var(--line-soft);
  flex-shrink: 0;
  align-items: flex-end;
}

.ai-textarea {
  flex: 1;
  height: 34px;
  max-height: 160px;
  padding: 7px 10px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  font-size: 0.82rem;
  line-height: 1.5;
  font-family: inherit;
  resize: none;
  outline: none;
  background: #fafafa;
  color: #333;
  transition: border-color 0.15s;
  box-sizing: border-box;
  scrollbar-width: none;
}
.ai-textarea::-webkit-scrollbar {
  display: none;
}

.ai-textarea:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 2px rgba(74, 157, 154, 0.1);
}

.ai-textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Markdown 渲染样式 */
.ai-msg-content.markdown-body {
  background: #f5f7fa;
  padding: 8px 10px;
  border-radius: 6px;
  overflow-x: auto;
}

.ai-msg.user .ai-msg-content.markdown-body {
  background: rgba(74, 157, 154, 0.08);
}

.markdown-body p,
.markdown-body pre,
.markdown-body ul,
.markdown-body ol,
.markdown-body blockquote {
  margin: 0 0 8px 0;
}
.markdown-body p:last-child,
.markdown-body pre:last-child,
.markdown-body ul:last-child,
.markdown-body ol:last-child {
  margin-bottom: 0;
}
.markdown-body pre {
  background: #f0f0f0;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
}
.markdown-body code {
  font-family: monospace;
  font-size: 0.85em;
  background: #e9ecef;
  padding: 2px 4px;
  border-radius: 4px;
}
.markdown-body pre code {
  background: transparent;
  padding: 0;
}
.markdown-body h1, .markdown-body h2, .markdown-body h3,
.markdown-body h4, .markdown-body h5, .markdown-body h6 {
  margin: 12px 0 8px;
  font-weight: 600;
}
.markdown-body a {
  color: var(--brand, #409eff);
  text-decoration: none;
}
.markdown-body a:hover {
  text-decoration: underline;
}
.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 8px;
}
.markdown-body th, .markdown-body td {
  border: 1px solid #ddd;
  padding: 6px;
}
</style>
