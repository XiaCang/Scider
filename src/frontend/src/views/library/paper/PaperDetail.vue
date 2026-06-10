<script setup lang="ts">
import { Check, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref, watch } from 'vue'

import type { LibraryPaper, PaperKeyPoints } from '../../../types/library'

interface Props {
  modelValue: boolean
  paper: LibraryPaper | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', paperId: string, keyPoints: PaperKeyPoints): void
  (e: 'previewPdf', paperId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 本地编辑的关键点(四维度结构化数据)
const draftKeyPoints = ref<PaperKeyPoints>({
  background: '',
  method: '',
  innovation: '',
  conclusion: ''
})

// 计算属性：抽屉显示状态
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 监听论文变化，初始化关键点数据
watch(() => props.paper, (newPaper) => {
  if (newPaper) {
    // 如果 keyPoints 是对象格式，直接使用；如果是数组格式，进行转换(兼容旧数据)
    if (typeof newPaper.keyPoints === 'object' && !Array.isArray(newPaper.keyPoints)) {
      draftKeyPoints.value = { ...newPaper.keyPoints }
    } else {
      // 兼容旧数据：将数组转换为四维度结构
      const oldKeyPoints = Array.isArray(newPaper.keyPoints) ? newPaper.keyPoints : []
      draftKeyPoints.value = {
        background: oldKeyPoints[0] || '',
        method: oldKeyPoints[1] || '',
        innovation: oldKeyPoints[2] || '',
        conclusion: oldKeyPoints[3] || ''
      }
    }
  }
}, { immediate: true })

// 当抽屉打开时初始化
const handleDrawerOpen = () => {
  if (props.paper) {
    // 已在 watch 中处理
  }
}

// 关闭抽屉前的确认（可选）
const handleBeforeClose = (done: () => void) => {
  // 直接关闭，不做拦截
  done()
}

// 保存关键点
const handleSaveKeyPoints = () => {
  if (!props.paper) return

  // 验证四个维度是否都有内容
  if (!draftKeyPoints.value.background.trim() ||
      !draftKeyPoints.value.method.trim() ||
      !draftKeyPoints.value.innovation.trim() ||
      !draftKeyPoints.value.conclusion.trim()) {
    ElMessage.warning('请填写所有四个维度的关键信息')
    return
  }

  emit('save', props.paper.id, { ...draftKeyPoints.value })
  drawerVisible.value = false
}

// 预览 PDF
const handlePreviewPdf = () => {
  if (!props.paper) return
  emit('previewPdf', props.paper.id)
}

// 状态映射（中文显示）
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
  PENDING_PARSING: 'is-warning',
  PARSING: 'is-warning',
  PENDING_EXTRACTION: 'is-brand',
  EXTRACTING: 'is-brand',
  PENDING_CONFIRMATION: 'is-success',
  CONFIRMED: 'is-success',
  FAILED: 'is-danger',
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="论文详情"
    direction="rtl"
    size="680px"
    :before-close="handleBeforeClose"
    @open="handleDrawerOpen"
  >
    <div v-if="paper" class="paper-detail">
      <!-- 论文基本信息 -->
      <section class="paper-info">
        <h2 class="paper-title">{{ paper.title }}</h2>

        <div class="paper-meta">
          <div class="meta-item meta-item--full">
            <span class="meta-label">作者：</span>
            <span class="meta-value meta-value--ellipsis" :title="paper.authors">{{ paper.authors }}</span>
          </div>

          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">年份：</span>
              <span class="meta-value">{{ paper.year }}</span>
            </div>

            <div class="meta-item">
              <span class="meta-label">来源：</span>
              <span class="meta-value meta-value--ellipsis" :title="paper.source">{{ paper.source }}</span>
            </div>

            <div class="meta-item">
              <span class="meta-label">状态：</span>
              <span class="status-pill" :class="statusClassMap[paper.status]">
                {{ statusTextMap[paper.status] }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- 关键点编辑区(四维度结构化) -->
      <section class="keypoints-section">
        <h3 class="section-title">
          关键点
        </h3>
        <p class="section-description">
          通过大语言模型从论文全文中提取的四个维度核心要素
        </p>

        <div class="keypoints-list">
          <!-- 研究背景 -->
          <div class="keypoint-card card-bg">
            <label class="keypoint-label">
              研究背景
            </label>
            <p class="keypoint-hint">该研究试图解决什么问题？</p>
            <el-input
              v-model="draftKeyPoints.background"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 10 }"
              placeholder="请输入研究背景..."
              class="keypoint-textarea"
            />
          </div>

          <!-- 研究方法 -->
          <div class="keypoint-card card-method">
            <label class="keypoint-label">
              研究方法
            </label>
            <p class="keypoint-hint">采用了何种技术路径或实验设计？</p>
            <el-input
              v-model="draftKeyPoints.method"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 10 }"
              placeholder="请输入研究方法..."
              class="keypoint-textarea"
            />
          </div>

          <!-- 创新点 -->
          <div class="keypoint-card card-innovation">
            <label class="keypoint-label">
              创新点
            </label>
            <p class="keypoint-hint">与现有工作相比，独特贡献是什么？</p>
            <el-input
              v-model="draftKeyPoints.innovation"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 10 }"
              placeholder="请输入创新点..."
              class="keypoint-textarea"
            />
          </div>

          <!-- 结论 -->
          <div class="keypoint-card card-conclusion">
            <label class="keypoint-label">
              结论
            </label>
            <p class="keypoint-hint">研究得出了何种关键发现？</p>
            <el-input
              v-model="draftKeyPoints.conclusion"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 10 }"
              placeholder="请输入结论..."
              class="keypoint-textarea"
            />
          </div>
        </div>
      </section>

      <!-- 操作按钮区 -->
      <section class="action-section">
        <el-button
          type="primary"
          size="large"
          @click="handleSaveKeyPoints"
        >
          <el-icon><Check /></el-icon>
          确认关键点
        </el-button>

        <el-button
          size="large"
          @click="handlePreviewPdf"
        >
          <el-icon><Document /></el-icon>
          预览 PDF
        </el-button>
      </section>
    </div>

    <div v-else class="empty-state">
      <el-empty description="请选择一篇论文查看详情" />
    </div>
  </el-drawer>
</template>

<style scoped>
.paper-detail {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 0 0.25rem;
}

/* 论文基本信息 */
.paper-info {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--line-soft);
}

.paper-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.7rem 0;
  line-height: 1.45;
}

.paper-meta {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.8rem;
}

/* 作者行独占一行 */
.meta-item--full {
  max-width: 100%;
}

/* 年份 / 来源 / 状态 一行排列 */
.meta-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
}

.meta-label {
  color: var(--text-secondary);
  font-weight: 500;
  flex-shrink: 0;
}

.meta-value {
  color: var(--text-primary);
}

.meta-value--ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* 关键点编辑区 */
.keypoints-section {
  flex: 1;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.3rem 0;
}

.section-description {
  font-size: 0.76rem;
  color: var(--text-secondary);
  margin: 0 0 1rem 0;
}

/* 纵向卡片列表 */
.keypoints-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.keypoint-card {
  border-radius: 10px;
  padding: 1rem 1.1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

/* 四色左边框 */
.card-bg {
  background: #f0f7ff;
  border-left: 4px solid #409eff;
}
.card-method {
  background: #f0faf0;
  border-left: 4px solid #67c23a;
}
.card-innovation {
  background: #fff7e6;
  border-left: 4px solid #e6a23c;
}
.card-conclusion {
  background: #f5f0ff;
  border-left: 4px solid #9b59b6;
}

.keypoint-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.keypoint-hint {
  font-size: 0.73rem;
  color: var(--text-secondary);
  margin: 0 0 0.25rem 0;
}

.keypoint-textarea {
  :deep(.el-textarea__inner) {
    font-family: inherit;
    font-size: 0.85rem;
    line-height: 1.65;
    resize: none;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid var(--el-border-color);
    transition: border-color 0.2s, box-shadow 0.2s;
    background: var(--bg-solid);
  }

  :deep(.el-textarea__inner:focus) {
    border-color: var(--el-color-primary);
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.15);
  }
}

/* 操作按钮区 */
.action-section {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line-soft);
}

.action-section :deep(.el-button) {
  flex: 1;
}

.action-section :deep(.el-button):not(.el-button--primary):not(:disabled):hover {
  color: var(--brand);
  background-color: var(--brand-soft);
  border-color: transparent;
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .meta-row {
    flex-direction: column;
    gap: 0.3rem;
  }

  .action-section {
    flex-direction: column;
  }
}
</style>
