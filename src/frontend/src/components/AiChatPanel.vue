<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Promotion, Delete, ChatDotSquare, InfoFilled, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import { createChatConnection } from '../api/chat'
import type { ChatMessage, PaperKeyPoints } from '../types/library'
import { fetchPaperByIdApi } from '../api/library'

const props = defineProps<{
  paperId: string
}>()

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

// 四要素相关
const keyPointsPanelVisible = ref(false)
const keyPoints = ref<PaperKeyPoints>({
  background: '',
  method: '',
  innovation: '',
  conclusion: '',
})
const loadingKeyPoints = ref(false)
let keyPointsLoaded = false  // 标记是否已加载过数据

// 流式构建中的消息 ID
let streamingMsgId = ''

let chatConnection: ReturnType<typeof createChatConnection> | null = null

// 静默预加载四要素（避免展开时请求导致高度突变）
const preloadKeyPoints = async () => {
  if (keyPointsLoaded) return
  try {
    const res = await fetchPaperByIdApi(props.paperId)
    const paperData = (res as any).data?.data || (res as any).data
    const fetchedKeyPoints = paperData?.keyPoints || {}
    keyPoints.value = {
      background: fetchedKeyPoints.background || '',
      method: fetchedKeyPoints.method || '',
      innovation: fetchedKeyPoints.innovation || '',
      conclusion: fetchedKeyPoints.conclusion || '',
    }
    keyPointsLoaded = true
  } catch (error) {
    console.error('预加载四要素失败:', error)
  }
}

// 切换面板（不再在切换时请求数据，因为已预加载）
const toggleKeyPointsPanel = () => {
  keyPointsPanelVisible.value = !keyPointsPanelVisible.value
}

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

  // 预加载四要素数据
  preloadKeyPoints()
})

onUnmounted(() => {
  chatConnection?.close()
  chatConnection = null
})

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value || !chatConnection) return

  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: text,
    createdAt: new Date().toISOString(),
  })
  inputText.value = ''
  sending.value = true
  streamingMsgId = (Date.now() + 1).toString()

  chatConnection.send(text)
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

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

defineExpose({ askWithContext })
</script>

<template>
  <div class="ai-chat-panel">
    <div class="ai-header">
      <el-icon :size="16"><ChatDotSquare /></el-icon>
      <span>AI 对话</span>
      <div class="ai-header-actions">
        <el-button
          size="small"
          text
          class="ai-header-btn"
          @click="toggleKeyPointsPanel"
        >
          <el-icon :size="14"><InfoFilled /></el-icon>
          论文四要素
          <el-icon :size="12" style="margin-left: 4px">
            <ArrowDown v-if="!keyPointsPanelVisible" />
            <ArrowUp v-else />
          </el-icon>
        </el-button>
        <el-button
          v-if="messages.length > 0"
          size="small"
          text
          class="ai-header-btn"
          @click="clearMessages"
        >
          <el-icon :size="14"><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 四要素面板（带简约过渡） -->
    <transition name="slide-fade">
      <div v-if="keyPointsPanelVisible" class="keypoints-panel">
        <div v-loading="loadingKeyPoints" class="keypoints-container">
          <div v-if="!loadingKeyPoints" class="keypoints-list">
            <div class="keypoint-card">
              <div class="keypoint-label">研究背景</div>
              <div class="keypoint-content">{{ keyPoints.background || '暂无内容' }}</div>
            </div>
            <div class="keypoint-card">
              <div class="keypoint-label">研究方法</div>
              <div class="keypoint-content">{{ keyPoints.method || '暂无内容' }}</div>
            </div>
            <div class="keypoint-card">
              <div class="keypoint-label">创新点</div>
              <div class="keypoint-content">{{ keyPoints.innovation || '暂无内容' }}</div>
            </div>
            <div class="keypoint-card">
              <div class="keypoint-label">结论</div>
              <div class="keypoint-content">{{ keyPoints.conclusion || '暂无内容' }}</div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <div class="ai-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="ai-empty">
        <p>对论文内容有疑问？</p>
        <p>选中 PDF 文字后右键→"向 AI 提问"</p>
        <p>或在下方输入问题</p>
      </div>
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="ai-msg"
        :class="msg.role"
      >
        <div class="ai-msg-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
        <div class="ai-msg-content">{{ msg.content }}</div>
      </div>
      <div v-if="sending && !streamingMsgId" class="ai-msg assistant">
        <div class="ai-msg-label">AI</div>
        <div class="ai-msg-content ai-thinking">思考中...</div>
      </div>
    </div>

    <div class="ai-input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        placeholder="输入问题，Enter 发送..."
        :disabled="sending"
        @keydown="handleKeydown"
      />
      <el-button
        type="primary"
        :icon="Promotion"
        :loading="sending"
        @click="sendMessage"
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

.ai-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--line-soft);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  flex-shrink: 0;
  z-index: 10;
  background: white;
}

.ai-header-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
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
  margin-bottom: 12px;
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
  background: #ecf5ff;
}

.ai-thinking {
  color: #999;
  font-style: italic;
}

.ai-input-area {
  display: flex;
  gap: 6px;
  padding: 8px 10px;
  border-top: 1px solid var(--line-soft);
  flex-shrink: 0;
  align-items: flex-end;
}

.ai-input-area :deep(.el-textarea__inner) {
  font-size: 0.82rem;
  line-height: 1.5;
  resize: none;
}

/* 四要素面板样式 */
.keypoints-panel {
  border-bottom: 1px solid var(--line-soft);
  background: #fafbfc;
  max-height: 52vh;
  overflow-y: auto;
}

.keypoints-container {
  padding: 12px 16px;
}

.keypoints-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.keypoint-card {
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.keypoint-card:not(:last-child) {
  border-bottom: 1px solid #eee;
}

.keypoint-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #888;
  margin-bottom: 4px;
  letter-spacing: 0.3px;
}

.keypoint-content {
  font-size: 0.78rem;
  line-height: 1.5;
  color: #3a3a3a;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.2s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-8px);
  opacity: 0;
}
.slide-fade-enter-to,
.slide-fade-leave-from {
  transform: translateY(0);
  opacity: 1;
}
</style>