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
  ElMessage.success('关键点已保存')
  drawerVisible.value = false
}

// 预览 PDF
const handlePreviewPdf = () => {
  if (!props.paper) return
  emit('previewPdf', props.paper.id)
}

// 状态映射（中文显示）
const statusTextMap: Record<LibraryPaper['status'], string> = {
  Processing: '处理中',
  PendingConfirmation: '未确认',
  Confirmed: '已确认',
}

const statusClassMap: Record<LibraryPaper['status'], string> = {
  Processing: 'is-warning',
  PendingConfirmation: 'is-brand',
  Confirmed: 'is-success',
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="论文详情"
    direction="rtl"
    size="750px"
    :before-close="handleBeforeClose"
    @open="handleDrawerOpen"
  >
    <div v-if="paper" class="paper-detail">
      <!-- 论文基本信息 -->
      <section class="paper-info">
        <h2 class="paper-title">{{ paper.title }}</h2>
        
        <div class="paper-meta">
          <div class="meta-item">
            <span class="meta-label">作者：</span>
            <span class="meta-value">{{ paper.authors }}</span>
          </div>
          
          <div class="meta-item">
            <span class="meta-label">年份：</span>
            <span class="meta-value">{{ paper.year }}</span>
          </div>
          
          <div class="meta-item">
            <span class="meta-label">来源：</span>
            <span class="meta-value">{{ paper.source }}</span>
          </div>
          
          <div class="meta-item">
            <span class="meta-label">状态：</span>
            <span class="status-pill" :class="statusClassMap[paper.status]">
              {{ statusTextMap[paper.status] }}
            </span>
          </div>
        </div>
      </section>

      <!-- 关键点编辑区(四维度结构化) -->
      <section class="keypoints-section">
        <h3 class="section-title">
          关键点（Key Points）
        </h3>
        <p class="section-description">
          通过大语言模型从论文全文中提取的四个维度核心要素
        </p>
        
        <div class="keypoints-grid">
          <!-- 研究背景 -->
          <div class="keypoint-item">
            <label class="keypoint-label">
              <span class="label-icon">📋</span>
              研究背景
            </label>
            <p class="keypoint-hint">该研究试图解决什么问题？</p>
            <el-input
              v-model="draftKeyPoints.background"
              type="textarea"
              :rows="4"
              placeholder="请输入研究背景..."
              class="keypoint-textarea"
            />
          </div>

          <!-- 研究方法 -->
          <div class="keypoint-item">
            <label class="keypoint-label">
              <span class="label-icon">🔬</span>
              研究方法
            </label>
            <p class="keypoint-hint">采用了何种技术路径或实验设计？</p>
            <el-input
              v-model="draftKeyPoints.method"
              type="textarea"
              :rows="4"
              placeholder="请输入研究方法..."
              class="keypoint-textarea"
            />
          </div>

          <!-- 创新点 -->
          <div class="keypoint-item">
            <label class="keypoint-label">
              <span class="label-icon">💡</span>
              创新点
            </label>
            <p class="keypoint-hint">与现有工作相比，独特贡献是什么？</p>
            <el-input
              v-model="draftKeyPoints.innovation"
              type="textarea"
              :rows="4"
              placeholder="请输入创新点..."
              class="keypoint-textarea"
            />
          </div>

          <!-- 结论 -->
          <div class="keypoint-item">
            <label class="keypoint-label">
              <span class="label-icon">✅</span>
              结论
            </label>
            <p class="keypoint-hint">研究得出了何种关键发现？</p>
            <el-input
              v-model="draftKeyPoints.conclusion"
              type="textarea"
              :rows="4"
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
  gap: 1.5rem;
  padding: 0 0.5rem;
}

/* 论文基本信息 */
.paper-info {
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--line-soft);
}

.paper-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  line-height: 1.4;
}

.paper-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.8rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.meta-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.meta-value {
  color: var(--text-primary);
}

/* 关键点编辑区 */
.keypoints-section {
  flex: 1;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.section-description {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0 0 1.2rem 0;
}

/* 四维度网格布局 */
.keypoints-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.2rem;
}

.keypoint-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.keypoint-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

.label-icon {
  font-size: 1.1rem;
}

.keypoint-hint {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0;
  font-style: italic;
}

.keypoint-textarea {
  :deep(.el-textarea__inner) {
    font-family: inherit;
    font-size: 0.9rem;
    line-height: 1.6;
    resize: vertical;
  }
}

/* 操作按钮区 */
.action-section {
  display: flex;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line-soft);
}

.action-section .el-button {
  flex: 1;
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
  .paper-meta {
    grid-template-columns: 1fr;
  }
  
  .keypoints-grid {
    grid-template-columns: 1fr;
  }
  
  .action-section {
    flex-direction: column;
  }
}
</style>
