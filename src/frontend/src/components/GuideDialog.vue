<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Collection,
  ChatDotRound,
  Search,
  Connection,
  Setting,
  Document,
  Reading,
  EditPen,
} from '@element-plus/icons-vue'

interface OnboardStep {
  icon: any
  title: string
  subtitle: string
  description: string
  action: string
  color: string
}

const steps: OnboardStep[] = [
  {
    icon: Document,
    title: '欢迎使用 Scider',
    subtitle: '智能学术论文管理平台',
    description:
      'Scider 帮助你高效管理论文、借助 AI 阅读文献、构建知识图谱、沉淀研究笔记，让科研工作更轻松。本指南将带你快速了解核心功能。',
    action: '点击「下一步」开始探索',
    color: '#4a9d9a',
  },
  {
    icon: Collection,
    title: '我的文库',
    subtitle: '论文收藏、分类与确认',
    description:
      '上传 PDF 论文，系统通过异步任务自动解析元数据并提取四维度关键点（研究背景、方法、创新点、结论）。创建文件夹分类管理，确认后的论文可纳入知识图谱构建。',
    action: '进入「我的文库」，点击上传按钮导入你的第一篇论文',
    color: '#3b82f6',
  },
  {
    icon: ChatDotRound,
    title: 'AI 问答助手',
    subtitle: '基于论文内容的智能问答',
    description:
      '在 PDF 阅读界面打开 AI 对话侧栏，基于当前论文内容提问；在知识图谱界面可基于图谱内容分析。支持流式回答与多轮对话，采用 RAG 技术确保回答贴合论文原文。',
    action: '打开一篇论文的 PDF，在右侧 AI 面板提问',
    color: '#8b5cf6',
  },
  {
    icon: Search,
    title: '发现论文',
    subtitle: '关键词检索、上下游分析、方向推荐',
    description:
      '输入关键词搜索学术 API 发现相关论文；选择已入库论文查看其引用脉络（上游参考文献与下游引用文献）；系统根据文库论文向量智能推荐相似研究。',
    action: '去「发现论文」页面搜索你感兴趣的关键词',
    color: '#f59e0b',
  },
  {
    icon: Connection,
    title: '知识图谱',
    subtitle: 'LLM 自动生成学术知识网络',
    description:
      '选择文件夹后，LLM 自动分析论文并生成力导向图，节点按研究主题自动聚类着色。支持拖拽缩放、手动编辑图谱、点击节点查看详情，以及导出 PNG/SVG。',
    action: '前往「知识图谱」页面，选择一个文件夹生成图谱',
    color: '#ec4899',
  },
  {
    icon: Reading,
    title: 'PDF 阅读与标注',
    subtitle: '增强型论文阅读体验',
    description:
      '支持连续滚动浏览、页码快速定位、文档内文字搜索高亮。可在 PDF 中做文本高亮标注并持久化保存，右侧对照四要素要点辅助深度研读。',
    action: '打开一篇论文的 PDF 预览页面体验阅读功能',
    color: '#10b981',
  },
  {
    icon: EditPen,
    title: '笔记与知识管理',
    subtitle: '富文本笔记，联动 PDF 批注',
    description:
      '支持 Markdown 语法与 LaTeX 数学公式的富文本编辑器，按论文分组管理笔记。笔记批注可与 PDF 位置联动，点击即跳转，支持导出 Markdown/TXT/PDF 文件。',
    action: '在一篇论文的详情页创建你的第一条研究笔记',
    color: '#f97316',
  },
  {
    icon: Setting,
    title: '个性化设置',
    subtitle: '配置你的使用体验',
    description:
      '在设置页面你可以修改个人资料、配置多模型提供商 API 密钥、管理密码与账户安全。深色模式一键切换。你可随时通过右上角头像菜单再次查看本指南。',
    action: '点击「开始使用」进入 Scider',
    color: '#6b7280',
  },
]

const visible = ref(false)
const currentStep = ref(0)
const hasShownThisSession = ref(false)

const GUIDE_STORAGE_KEY = 'scider_guide_viewed'

const isFirstStep = computed(() => currentStep.value === 0)
const isLastStep = computed(() => currentStep.value === steps.length - 1)
const current = computed(() => steps[currentStep.value])

function shouldShow(): boolean {
  if (hasShownThisSession.value) return false
  const viewed = localStorage.getItem(GUIDE_STORAGE_KEY)
  return viewed !== '1'
}

function markAsViewed(): void {
  localStorage.setItem(GUIDE_STORAGE_KEY, '1')
  hasShownThisSession.value = true
}

function show(): void {
  if (!shouldShow()) return
  visible.value = true
  currentStep.value = 0
}

function handleNext(): void {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function handlePrev(): void {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function handleClose(): void {
  visible.value = false
  markAsViewed()
}

function handleSkip(): void {
  handleClose()
}

defineExpose({ show })
</script>

<template>
  <el-dialog
    v-model="visible"
    title=""
    width="560px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="true"
    top="8vh"
    class="onboard-dialog"
    @close="handleClose"
  >
    <div class="onboard">
      <!-- 插图区 -->
      <div class="onboard-illustration" :style="{ '--step-color': current.color }">
        <div class="onboard-icon-ring">
          <el-icon :size="36">
            <component :is="current.icon" />
          </el-icon>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="onboard-body">
        <h2 class="onboard-title">{{ current.title }}</h2>
        <p class="onboard-subtitle">{{ current.subtitle }}</p>
        <p class="onboard-desc">{{ current.description }}</p>
      </div>

      <!-- 步骤指示器 -->
      <div class="onboard-dots">
        <span
          v-for="(_, idx) in steps"
          :key="idx"
          class="onboard-dot"
          :class="{
            'is-active': idx === currentStep,
            'is-done': idx < currentStep,
          }"
        ></span>
      </div>

      <!-- 底部操作 -->
      <div class="onboard-footer">
        <div class="onboard-footer__left">
          <button
            v-if="!isLastStep"
            class="onboard-skip"
            type="button"
            @click="handleSkip"
          >
            跳过引导
          </button>
        </div>
        <div class="onboard-footer__right">
          <el-button
            v-if="!isFirstStep"
            size="default"
            @click="handlePrev"
          >
            上一步
          </el-button>
          <el-button
            v-if="!isLastStep"
            type="primary"
            size="default"
            @click="handleNext"
          >
            下一步
          </el-button>
          <el-button
            v-else
            type="primary"
            size="default"
            @click="handleClose"
          >
            开始使用
          </el-button>
        </div>
      </div>

      <!-- 操作提示 -->
      <p class="onboard-action-hint">{{ current.action }}</p>
    </div>
  </el-dialog>
</template>

<style scoped>
.onboard {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 16px 0;
}

/* ── 插图区 ── */
.onboard-illustration {
  width: 112px;
  height: 112px;
  border-radius: 50%;
  background: rgba(74, 157, 154, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  position: relative;
}

.onboard-illustration::after {
  content: '';
  position: absolute;
  inset: -12px;
  border-radius: 50%;
  border: 2px dashed rgba(74, 157, 154, 0.15);
  animation: spin-slow 20s linear infinite;
}

.onboard-icon-ring {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--step-color, #4a9d9a);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

@keyframes spin-slow {
  to {
    transform: rotate(360deg);
  }
}

/* ── 内容区 ── */
.onboard-body {
  text-align: center;
  max-width: 440px;
}

.onboard-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  line-height: 1.3;
}

.onboard-subtitle {
  margin: 6px 0 0;
  font-size: 0.88rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.onboard-desc {
  margin: 14px 0 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.65;
}

/* ── 步骤指示器 ── */
.onboard-dots {
  display: flex;
  gap: 8px;
  margin-top: 20px;
}

.onboard-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e5e7eb;
  transition: all 0.3s ease;
}

.onboard-dot.is-active {
  background: var(--brand, #4a9d9a);
  box-shadow: 0 0 0 4px rgba(74, 157, 154, 0.15);
  width: 24px;
  border-radius: 4px;
}

.onboard-dot.is-done {
  background: #a7d1d0;
}

/* ── 底部操作 ── */
.onboard-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--line-soft, rgba(0, 0, 0, 0.06));
}

.onboard-footer__right {
  display: flex;
  gap: 8px;
}

.onboard-skip {
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.15s;
}

.onboard-skip:hover {
  color: var(--text-secondary);
}

/* ── 操作提示 ── */
.onboard-action-hint {
  margin: 10px 0 4px;
  font-size: 0.78rem;
  color: var(--brand, #4a9d9a);
  font-weight: 500;
  text-align: center;
}
</style>

<style>
.onboard-dialog {
  border-radius: 20px;
}

.onboard-dialog .el-dialog__header {
  display: none;
}

.onboard-dialog .el-dialog__body {
  padding: 0;
}

.onboard-dialog .el-dialog__headerbtn {
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
}

.onboard-dialog .el-dialog__headerbtn:hover {
  background: rgba(0, 0, 0, 0.04);
}
</style>
