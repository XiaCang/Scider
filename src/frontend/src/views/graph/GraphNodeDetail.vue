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
  return '650px'
})

const getTypeLabel = (type: NodeType) => {
  const labels: Record<NodeType, string> = {
    paper: '论文',
    background: '研究背景',
    method: '研究方法',
    innovation: '创新点',
    conclusion: '结论',
    custom: '自定义节点'
  }
  return labels[type] || '节点'
}

const getTypeClass = (type: NodeType) => {
  if (type === 'custom') return 'node-type--custom'
  return `node-type--${type}`
}

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
      keyPoints: { background: '', method: '', innovation: '', conclusion: '' }
    }
    return {
      id: props.nodeData.paperId,
      name: paperInfo.title || `论文 ${props.nodeData.paperId}`,
      type: 'paper' as NodeType,
      paperInfo,
      paperId: props.nodeData.paperId,
      content: props.nodeData.content
    }
  }
  return props.nodeData
})

const handleViewPaperDetail = () => {
  if (props.nodeData?.paperId) {
    showPaperDetail.value = true
    ElMessage.info('已切换到论文详情视图')
  } else {
    ElMessage.warning('该节点未关联论文信息')
  }
}

const handleBackToElement = () => {
  showPaperDetail.value = false
}

const handleNavigateToPdf = () => {
  const targetPaperId = displayNodeData.value?.id
  if (targetPaperId) emit('navigate-to-paper', targetPaperId)
}

// 限制编辑：仅非 paper 节点可编辑
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

const cancelEdit = () => {
  isEditing.value = false
}

const submitEdit = async () => {
  if (!props.nodeData) return
  // 再次检查类型
  if (props.nodeData.type === 'paper') {
    ElMessage.warning('系统论文节点不可编辑')
    return
  }
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
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

const handleDeleteNode = async () => {
  if (!props.nodeData) return
  if (props.nodeData.type === 'paper') {
    ElMessage.warning('系统论文节点不可删除')
    return
  }
  try {
    await ElMessageBox.confirm(`确定要删除节点“${props.nodeData.name}”吗？删除后所有关联的边也会被删除。`, '警告', {
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
      <div v-if="showPaperDetail" class="back-button-container">
        <el-button text @click="handleBackToElement">
          <el-icon><Back /></el-icon> 返回要素详情
        </el-button>
      </div>

      <div class="node-type-badge" :class="getTypeClass(displayNodeData.type)">
        {{ getTypeLabel(displayNodeData.type) }}
      </div>

      <!-- 编辑模式 -->
      <div v-if="isEditing" class="edit-form">
        <el-form label-width="80px">
          <el-form-item label="节点名称">
            <el-input v-model="editForm.name" />
          </el-form-item>
          <el-form-item label="分类索引">
            <el-input-number v-model="editForm.category" :min="0" :max="10" />
          </el-form-item>
          <el-form-item label="节点类型">
            <el-input v-model="editForm.node_type" placeholder="custom" />
          </el-form-item>
          <el-form-item>
            <el-button @click="cancelEdit">取消</el-button>
            <el-button type="primary" @click="submitEdit">保存</el-button>
          </el-form-item>
        </el-form>
      </div>

      <template v-else>
        <h2 class="node-name">{{ displayNodeData.name }}</h2>

        <!-- 论文节点 -->
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
          <div class="action-buttons">
            <el-button type="primary" @click="handleNavigateToPdf">
              <el-icon><ArrowRight /></el-icon> 查看 PDF
            </el-button>
          </div>
        </div>

        <!-- 非论文节点（四要素/自定义） -->
        <div v-else class="element-info-section">
          <section class="info-group">
            <label class="info-label">所属论文</label>
            <p class="info-value">{{ displayNodeData.paperTitle }}</p>
          </section>
          <section v-if="displayNodeData.content" class="content-section">
            <label class="info-label">详细内容</label>
            <div class="content-text">{{ displayNodeData.content }}</div>
          </section>
          <div class="action-buttons">
            <el-button type="primary" @click="handleViewPaperDetail" :disabled="!displayNodeData.paperId">
              <el-icon><ArrowRight /></el-icon> 查看论文详情
            </el-button>
          </div>
        </div>
      </template>

      <!-- 操作按钮：仅非论文节点（自定义/四要素）可编辑删除，论文节点不显示编辑删除按钮 -->
      <div v-if="!isEditing && displayNodeData.type !== 'paper'" class="action-buttons edit-delete-buttons">
        <el-button type="warning" plain @click="startEdit">
          <el-icon><Edit /></el-icon> 编辑
        </el-button>
        <el-button type="danger" plain @click="handleDeleteNode">
          <el-icon><Delete /></el-icon> 删除
        </el-button>
      </div>
    </div>
    <div v-else class="empty-state">
      <el-empty description="请选择一个节点查看详情" />
    </div>
  </el-drawer>
</template>

<style scoped>
.node-detail { display: flex; flex-direction: column; gap: 1.2rem; padding: 0 0.5rem; }
.back-button-container { margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--line-soft); }
.node-type-badge { display: inline-block; padding: 0.4rem 0.8rem; border-radius: 999px; font-size: 0.85rem; font-weight: 600; width: fit-content; }
.node-type--paper { background: #4a9d9a; color: white; }
.node-type--background { background: rgba(107, 142, 142, 0.12); color: #6b8e8e; }
.node-type--method { background: rgba(232, 184, 109, 0.12); color: #b88a3e; }
.node-type--innovation { background: rgba(193, 119, 103, 0.12); color: #c17767; }
.node-type--conclusion { background: rgba(74, 157, 154, 0.12); color: #22c55e; }
.node-type--custom { background: rgba(139, 124, 179, 0.12); color: #8b7cb3; }
.node-name { font-size: 1.3rem; font-weight: 600; color: var(--text-primary); margin: 0; line-height: 1.4; }
.info-group { margin-bottom: 0.8rem; }
.info-label { display: block; font-size: 0.85rem; font-weight: 500; color: var(--text-secondary); margin-bottom: 0.3rem; }
.info-value { font-size: 0.95rem; color: var(--text-primary); margin: 0; }
.keypoints-section { margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--line-soft); }
.section-title { font-size: 1.1rem; font-weight: 600; margin: 0 0 1rem 0; }
.keypoint-item { margin-bottom: 1rem; }
.keypoint-label { display: block; font-size: 0.9rem; font-weight: 500; margin-bottom: 0.4rem; }
.keypoint-content { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.6; margin: 0; padding: 0.6rem; background: var(--bg-secondary); border-radius: 6px; }
.content-section { margin-top: 1rem; }
.content-text { font-size: 0.95rem; color: var(--text-primary); line-height: 1.8; padding: 1rem; background: var(--bg-secondary); border-radius: 8px; white-space: pre-wrap; }
.action-buttons { display: flex; gap: 1rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--line-soft); }
.edit-delete-buttons { border-top: none; justify-content: flex-end; }
.empty-state { display: flex; align-items: center; justify-content: center; min-height: 300px; }
.edit-form { background: var(--bg-secondary); padding: 1rem; border-radius: 12px; }
@media (max-width: 768px) {
  .node-detail { padding: 0 0.3rem; }
  .node-name { font-size: 1.1rem; }
  .action-buttons { flex-direction: column; }
}
</style>