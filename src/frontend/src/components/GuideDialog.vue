<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Collection,
  ChatDotRound,
  Search,
  Connection,
  Setting,
  Document,
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
      'Scider 帮助你高效管理论文、借助 AI 阅读文献、构建知识图谱，让科研工作更轻松。本指南将带你快速了解核心功能。',
    action: '点击「下一步」开始探索',
    color: '#4a9d9a',
  },
  {
    icon: Collection,
    title: '我的文库',
    subtitle: '论文收藏与管理',
    description:
      '上传 PDF 论文，系统自动解析元数据并提取关键内容。你可以创建文件夹按课题分类整理论文，点击任意论文查看其研究背景、方法、创新点和结论。',
    action: '进入「我的文库」，点击上传按钮试试',
    color: '#3b82f6',
  },
  {
    icon: ChatDotRound,
    title: 'AI 智能对话',
    subtitle: '与论文深度互动',
    description:
      '打开任意论文的 PDF 预览页面，右侧 AI 对话面板会加载该论文的四要素摘要。你可以直接向 AI 提问，获取论文内容的深入解析，所有回答均为流式生成。',
    action: '打开一篇论文，在右侧 AI 面板提问',
    color: '#8b5cf6',
  },
  {
    icon: Search,
    title: '发现论文',
    subtitle: '探索前沿研究',
    description:
      '在「发现论文」页面输入关键词，即可搜索相关领域的最新文献。你还可通过「上下游分析」功能，查看一篇论文引用了哪些前序研究，以及后续研究如何基于它展开。',
    action: '去「发现论文」页面搜索你感兴趣的关键词',
    color: '#f59e0b',
  },
  {
    icon: Connection,
    title: '知识图谱',
    subtitle: '可视化论文关系网络',
    description:
      '知识图谱以图形化方式展示你的论文之间的引用关系，帮助你直观理解研究脉络、发现关键节点论文，更高效地把控研究领域全貌。',
    action: '前往「知识图谱」页面查看可视化关系',
    color: '#ec4899',
  },
  {
    icon: Setting,
    title: '个性化设置',
    subtitle: '配置你的使用体验',
    description:
      '在设置页面你可以修改个人资料、配置 AI 模型提供商参数、以及修改登录密码。你可随时通过右上角头像菜单再次查看本指南。',
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
