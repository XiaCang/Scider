<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Back, Edit, Delete } from '@element-plus/icons-vue'
import type { LibraryPaper } from '../../types/library'
import type { GraphNodeData, NodeType } from '../../types/graph'
import { updateGraphNode, deleteGraphNode } from '../../api/graph'

interface Props {
  modelValue: boolean
  nodeData: GraphNodeData | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'navigate-to-paper', paperId: string): void
  (e: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const drawerVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const showPaperDetail = ref(false)
const windowWidth = ref(window.innerWidth)
const isEditing = ref(false)
const editForm = ref({
  name: '',
  category: 0,
  node_type: '',
})

const handleResize = () => { windowWidth.value = window.innerWidth }
onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => window.removeEventListener('resize', handleResize))

const drawerSize = computed(() => {
  if (windowWidth.value < 768) return '100%'
  if (windowWidth.value < 1200) return '500px'
  return '600px'
})

const getTypeLabel = (type: NodeType) => {
  const labels: Record<NodeType, string> = {
    paper: '论文',
    background: '研究背景',
    method: '研究方法',
    innovation: '创新点',
    conclusion: '结论',
    custom: '自定义',
  }
  return labels[type] || '节点'
}

const getTypeClass = (type: NodeType) => `node-type--${type}`

const displayNodeData = computed(() => {
  if (!props.nodeData) return null
  if (showPaperDetail.value && props.nodeData.paperId) {
    const paperInfo = props.nodeData.paperInfo || {
      id: props.nodeData.paperId,
      title: `论文 ${props.nodeData.paperId}`,
      authors: '未知',
      year: 0,
      status: 'Unknown' as LibraryPaper['status'],
      source: '未知',
      keyPoints: { background: '', method: '', innovation: '', conclusion: '' },
    }
    return {
      id: props.nodeData.paperId,
      name: paperInfo.title || `论文 ${props.nodeData.paperId}`,
      type: 'paper' as NodeType,
      paperInfo,
      paperId: props.nodeData.paperId,
      content: props.nodeData.content,
    }
  }
  return props.nodeData
})

const handleViewPaperDetail = () => {
  if (props.nodeData?.paperId) {
    showPaperDetail.value = true
  } else {
    ElMessage.warning('该节点未关联论文信息')
  }
}

const handleBackToElement = () => { showPaperDetail.value = false }

const handleNavigateToPdf = () => {
  const targetPaperId = displayNodeData.value?.id
  if (targetPaperId) emit('navigate-to-paper', targetPaperId)
}

const startEdit = () => {
  if (!props.nodeData) return
  if (props.nodeData.type === 'paper') {
    ElMessage.warning('系统论文节点不可编辑')
    return
  }
  editForm.value = {
    name: props.nodeData.name,
    category: props.nodeData.category ?? 0,
    node_type: props.nodeData.node_type || props.nodeData.type,
  }
  isEditing.value = true
}

const cancelEdit = () => { isEditing.value = false }

const submitEdit = async () => {
  if (!props.nodeData || props.nodeData.type === 'paper') return
  try {
    await updateGraphNode(props.nodeData.id, {
      name: editForm.value.name,
      category: editForm.value.category,
      node_type: editForm.value.node_type,
    })
    ElMessage.success('节点更新成功')
    isEditing.value = false
    emit('refresh')
    drawerVisible.value = false
  } catch {
    ElMessage.error('更新失败')
  }
}

const handleDeleteNode = async () => {
  if (!props.nodeData || props.nodeData.type === 'paper') return
  try {
    await ElMessageBox.confirm(`确定要删除节点"${props.nodeData.name}"吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteGraphNode(props.nodeData.id)
    ElMessage.success('节点已删除')
    emit('refresh')
    drawerVisible.value = false
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleClose = () => {
  showPaperDetail.value = false
  isEditing.value = false
  drawerVisible.value = false
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    :title="displayNodeData ? `${getTypeLabel(displayNodeData.type)}详情` : '节点详情'"
    direction="rtl"
    :size="drawerSize"
    @close="handleClose"
  >
    <div v-if="displayNodeData" class="node-detail">
      <!-- 返回按钮 -->
      <div v-if="showPaperDetail" class="node-back">
        <el-button text @click="handleBackToElement">
          <el-icon><Back /></el-icon> 返回
        </el-button>
      </div>

      <!-- 类型标签 + 标题 -->
      <div class="node-head">
        <span class="node-badge" :class="getTypeClass(displayNodeData.type)">
          {{ getTypeLabel(displayNodeData.type) }}
        </span>
        <h2 class="node-title">{{ displayNodeData.name }}</h2>
      </div>

      <!-- 编辑模式 -->
      <div v-if="isEditing" class="edit-block">
        <div class="edit-field">
          <label class="edit-label">节点名称</label>
          <el-input v-model="editForm.name" size="large" />
        </div>
        <div class="edit-field">
          <label class="edit-label">分类索引</label>
          <el-input-number v-model="editForm.category" :min="0" :max="10" />
        </div>
        <div class="edit-field">
          <label class="edit-label">节点类型</label>
          <el-input v-model="editForm.node_type" placeholder="custom" />
        </div>
        <div class="edit-actions">
          <el-button @click="cancelEdit">取消</el-button>
          <el-button type="primary" @click="submitEdit">保存</el-button>
        </div>
      </div>

      <!-- 论文节点 -->
      <template v-else-if="displayNodeData.type === 'paper' && displayNodeData.paperInfo">
        <div class="info-grid">
          <div class="info-row">
            <span class="info-key">作者</span>
            <span class="info-val">{{ displayNodeData.paperInfo.authors }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">年份</span>
            <span class="info-val">{{ displayNodeData.paperInfo.year }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">来源</span>
            <span class="info-val">{{ displayNodeData.paperInfo.source }}</span>
          </div>
        </div>

        <div v-if="displayNodeData.paperInfo.keyPoints" class="kp-section">
          <h3 class="kp-heading">关键点</h3>
          <div class="kp-list">
            <div class="kp-item">
              <span class="kp-tag kp-bg">研究背景</span>
              <p class="kp-text">{{ displayNodeData.paperInfo.keyPoints.background || '暂无' }}</p>
            </div>
            <div class="kp-item">
              <span class="kp-tag kp-method">研究方法</span>
              <p class="kp-text">{{ displayNodeData.paperInfo.keyPoints.method || '暂无' }}</p>
            </div>
            <div class="kp-item">
              <span class="kp-tag kp-innov">创新点</span>
              <p class="kp-text">{{ displayNodeData.paperInfo.keyPoints.innovation || '暂无' }}</p>
            </div>
            <div class="kp-item">
              <span class="kp-tag kp-conc">结论</span>
              <p class="kp-text">{{ displayNodeData.paperInfo.keyPoints.conclusion || '暂无' }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- 非论文节点 -->
      <template v-else>
        <div class="info-grid">
          <div class="info-row">
            <span class="info-key">所属论文</span>
            <span class="info-val">{{ displayNodeData.paperTitle || '未知' }}</span>
          </div>
        </div>
        <div v-if="displayNodeData.content" class="content-block">
          <span class="info-key">详细内容</span>
          <div class="content-body">{{ displayNodeData.content }}</div>
        </div>
      </template>

      <!-- 操作按钮 -->
      <div class="actions">
        <template v-if="displayNodeData.type === 'paper'">
          <el-button type="primary" @click="handleNavigateToPdf">查看 PDF</el-button>
          <el-button v-if="displayNodeData.paperId" @click="handleViewPaperDetail">论文详情</el-button>
        </template>
        <template v-else-if="!isEditing">
          <el-button type="primary" plain @click="startEdit">
            <el-icon><Edit /></el-icon> 编辑
          </el-button>
          <el-button v-if="displayNodeData.paperId" @click="handleViewPaperDetail">查看论文</el-button>
          <el-button type="danger" plain @click="handleDeleteNode">
            <el-icon><Delete /></el-icon> 删除
          </el-button>
        </template>
      </div>
    </div>
    <div v-else class="empty-state">
      <el-empty description="请选择一个节点" />
    </div>
  </el-drawer>
</template>

<style scoped>
.node-detail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.node-back {
  margin-bottom: 0.25rem;
}

.node-head {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--line-soft);
}

.node-badge {
  display: inline-block;
  width: fit-content;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.node-type--paper     { background: rgba(74, 157, 154, 0.12); color: #4a9d9a; }
.node-type--background { background: rgba(107, 142, 142, 0.12); color: #5a7a7a; }
.node-type--method    { background: rgba(232, 184, 109, 0.12); color: #b88a3e; }
.node-type--innovation { background: rgba(193, 119, 103, 0.12); color: #c17767; }
.node-type--conclusion { background: rgba(74, 157, 154, 0.12); color: #3d8b88; }
.node-type--custom    { background: rgba(139, 124, 179, 0.12); color: #7b6da8; }

.node-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;
}

/* ── 信息行 ── */
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-bottom: 0.25rem;
}

.info-row {
  display: flex;
  gap: 0.75rem;
  font-size: 0.85rem;
  line-height: 1.5;
}

.info-key {
  flex-shrink: 0;
  min-width: 5em;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-val {
  color: var(--text-primary);
  word-break: break-word;
}

/* ── 关键点 ── */
.kp-section {
  padding-top: 1rem;
  border-top: 1px solid var(--line-soft);
}

.kp-heading {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.kp-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.kp-item {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.kp-tag {
  display: inline-block;
  width: fit-content;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 600;
}

.kp-bg     { background: rgba(107, 142, 142, 0.1); color: #5a7a7a; }
.kp-method { background: rgba(232, 184, 109, 0.1); color: #b88a3e; }
.kp-innov  { background: rgba(193, 119, 103, 0.1); color: #c17767; }
.kp-conc   { background: rgba(74, 157, 154, 0.1);  color: #3d8b88; }

.kp-text {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.65;
  color: var(--text-secondary);
}

/* ── 内容区块 ── */
.content-block {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.content-body {
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--text-primary);
  padding: 0.75rem 0.85rem;
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
}

/* ── 编辑表单 ── */
.edit-block {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
}

.edit-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.edit-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.edit-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.25rem;
}

/* ── 操作按钮 ── */
.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding-top: 1rem;
  margin-top: auto;
  border-top: 1px solid var(--line-soft);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

@media (max-width: 768px) {
  .node-title { font-size: 1rem; }
  .actions { flex-direction: column; }
}
</style>
