<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowRight, Back } from '@element-plus/icons-vue'
import type { LibraryPaper } from '../../types/library'

import type { GraphNodeData, NodeType } from '../../types/graph'

interface Props {
  modelValue: boolean
  nodeData: GraphNodeData | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'navigate-to-paper', paperId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算属性：抽屉显示状态
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 内部状态：是否显示论文详情视图（用于四要素节点切换）
const showPaperDetail = ref(false)

// 获取节点类型标签
const getTypeLabel = (type: NodeType) => {
  const labels: Record<NodeType, string> = {
    paper: '论文',
    background: '研究背景',
    method: '研究方法',
    innovation: '创新点',
    conclusion: '结论'
  }
  return labels[type]
}

// 获取节点类型样式类
const getTypeClass = (type: NodeType) => {
  return `node-type--${type}`
}

// 获取当前显示的节点数据（可能是原始节点或其所属论文节点）
const displayNodeData = computed(() => {
  if (!props.nodeData) return null
  
  // 如果是四要素节点且已切换到论文详情视图
  if (showPaperDetail.value && props.nodeData.paperId) {
    // 优先使用 nodeData 中的 paperInfo，如果没有则构造基本对象
    const paperInfo = props.nodeData.paperInfo || {
      id: props.nodeData.paperId,
      title: `论文 ${props.nodeData.paperId}`,
      authors: '未知',
      year: 0,
      status: 'Unknown' as LibraryPaper['status'],
      source: '未知',
      keyPoints: {
        background: '',
        method: '',
        innovation: '',
        conclusion: ''
      }
    }
    
    return {
      id: props.nodeData.paperId,
      name: paperInfo.title || `论文 ${props.nodeData.paperId}`,
      type: 'paper' as NodeType,
      paperInfo: paperInfo,
      // 保留原始节点的 paperId 和 content（用于模板中的条件判断）
      paperId: props.nodeData.paperId,
      content: props.nodeData.content
    }
  }
  
  return props.nodeData
})

// 处理四要素节点的"查看论文详情"按钮点击
const handleViewPaperDetail = () => {
  if (props.nodeData?.paperId) {
    showPaperDetail.value = true
    ElMessage.info('已切换到论文详情视图')
  } else {
    ElMessage.warning('该节点未关联论文信息')
  }
}

// 返回到要素详情视图
const handleBackToElement = () => {
  showPaperDetail.value = false
}

// 从论文节点跳转到 PDF 预览页
const handleNavigateToPdf = () => {
  const targetPaperId = displayNodeData.value?.id
  if (targetPaperId) {
    emit('navigate-to-paper', targetPaperId)
  }
}

// 关闭抽屉时重置状态
const handleClose = () => {
  showPaperDetail.value = false
  drawerVisible.value = false
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    :title="displayNodeData ? `${getTypeLabel(displayNodeData.type)}详情` : '节点详情'"
    direction="rtl"
    size="650px"
    @close="handleClose"
  >
    <div v-if="displayNodeData" class="node-detail">
      <!-- 返回按钮（仅在四要素节点切换到论文详情时显示） -->
      <div v-if="showPaperDetail" class="back-button-container">
        <el-button text @click="handleBackToElement">
          <el-icon><Back /></el-icon>
          返回要素详情
        </el-button>
      </div>

      <!-- 节点类型标识 -->
      <div class="node-type-badge" :class="getTypeClass(displayNodeData.type)">
        {{ getTypeLabel(displayNodeData.type) }}
      </div>

      <!-- 节点名称 -->
      <h2 class="node-name">{{ displayNodeData.name }}</h2>

      <!-- 论文节点：展示完整论文信息 -->
      <div v-if="displayNodeData.type === 'paper' && displayNodeData.paperInfo" class="paper-info-section">
        <section class="info-group">
          <label class="info-label">作者</label>
          <p class="info-value">{{ displayNodeData.paperInfo.authors }}</p>
        </section>

        <section class="info-group">
          <label class="info-label">年份</label>
          <p class="info-value">{{ displayNodeData.paperInfo.year }}</p>
        </section>

        <section class="info-group">
          <label class="info-label">来源</label>
          <p class="info-value">{{ displayNodeData.paperInfo.source }}</p>
        </section>

        <section class="info-group">
          <label class="info-label">状态</label>
          <p class="info-value">{{ displayNodeData.paperInfo.status }}</p>
        </section>

        <!-- 关键点展示 -->
        <section v-if="displayNodeData.paperInfo.keyPoints" class="keypoints-section">
          <h3 class="section-title">关键点</h3>
          
          <div class="keypoint-item">
            <label class="keypoint-label">🎯 研究背景</label>
            <p class="keypoint-content">{{ displayNodeData.paperInfo.keyPoints.background || '暂无' }}</p>
          </div>

          <div class="keypoint-item">
            <label class="keypoint-label">🔬 研究方法</label>
            <p class="keypoint-content">{{ displayNodeData.paperInfo.keyPoints.method || '暂无' }}</p>
          </div>

          <div class="keypoint-item">
            <label class="keypoint-label">💡 创新点</label>
            <p class="keypoint-content">{{ displayNodeData.paperInfo.keyPoints.innovation || '暂无' }}</p>
          </div>

          <div class="keypoint-item">
            <label class="keypoint-label">✅ 结论</label>
            <p class="keypoint-content">{{ displayNodeData.paperInfo.keyPoints.conclusion || '暂无' }}</p>
          </div>
        </section>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="primary" @click="handleNavigateToPdf">
            <el-icon><ArrowRight /></el-icon>
            查看 PDF
          </el-button>
        </div>
      </div>

      <!-- 四要素节点：展示要素内容和跳转按钮 -->
      <div v-else-if="displayNodeData.type !== 'paper'" class="element-info-section">
        <section class="info-group">
          <label class="info-label">所属论文</label>
          <p class="info-value">{{ displayNodeData.paperTitle }}</p>
        </section>

        <section v-if="displayNodeData.content" class="content-section">
          <label class="info-label">详细内容</label>
          <div class="content-text">{{ displayNodeData.content }}</div>
        </section>

        <!-- 查看论文详情的按钮（切换抽屉内容） -->
        <div class="action-buttons">
          <el-button type="primary" @click="handleViewPaperDetail" :disabled="!displayNodeData.paperId">
            <el-icon><ArrowRight /></el-icon>
            查看论文详情
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-empty description="暂无详细信息" />
      </div>
    </div>

    <div v-else class="empty-state">
      <el-empty description="请选择一个节点查看详情" />
    </div>
  </el-drawer>
</template>

<style scoped>
.node-detail {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  padding: 0 0.5rem;
}

/* 返回按钮容器 */
.back-button-container {
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--line-soft);
}

/* 节点类型徽章 */
.node-type-badge {
  display: inline-block;
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
  width: fit-content;
}

.node-type--paper {
  background: #173668;
  color: white;
}

.node-type--background {
  background: #fef3c7;
  color: #f59e0b;
}

.node-type--method {
  background: #dbeafe;
  color: #3b82f6;
}

.node-type--innovation {
  background: #fef9c3;
  color: #eab308;
}

.node-type--conclusion {
  background: #dcfce7;
  color: #22c55e;
}

/* 节点名称 */
.node-name {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.4;
}

/* 信息组 */
.info-group {
  margin-bottom: 0.8rem;
}

.info-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 0.3rem;
}

.info-value {
  font-size: 0.95rem;
  color: var(--text-primary);
  margin: 0;
}

/* 关键点区域 */
.keypoints-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--line-soft);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
}

.keypoint-item {
  margin-bottom: 1rem;
}

.keypoint-label {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 0.4rem;
}

.keypoint-content {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  padding: 0.6rem;
  background: var(--bg-secondary);
  border-radius: 6px;
}

/* 内容区域 */
.content-section {
  margin-top: 1rem;
}

.content-text {
  font-size: 0.95rem;
  color: var(--text-primary);
  line-height: 1.8;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  white-space: pre-wrap;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--line-soft);
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}
</style>
