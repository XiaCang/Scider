<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import { updateGraphEdge, deleteGraphEdge } from '../../api/graph'

interface EdgeData {
  id: string
  source: string
  target: string
  relationType: string
  label?: string
  reason?: string
  properties?: Record<string, any>
}

interface Props {
  modelValue: boolean
  edgeData: EdgeData | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const drawerVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const isEditing = ref(false)
const editForm = ref({
  relation_type: '',
  label: '',
})

const startEdit = () => {
  if (!props.edgeData) return
  editForm.value = {
    relation_type: props.edgeData.relationType,
    label: props.edgeData.label || '',
  }
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
}

const submitEdit = async () => {
  if (!props.edgeData) return
  try {
    await updateGraphEdge(props.edgeData.id, {
      relation_type: editForm.value.relation_type,
      label: editForm.value.label,
    })
    ElMessage.success('边更新成功')
    isEditing.value = false
    emit('refresh')
    drawerVisible.value = false
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

const handleDeleteEdge = async () => {
  if (!props.edgeData) return
  try {
    await ElMessageBox.confirm('确定要删除这条关联边吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteGraphEdge(props.edgeData.id)
    ElMessage.success('边已删除')
    emit('refresh')
    drawerVisible.value = false
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleClose = () => {
  isEditing.value = false
  drawerVisible.value = false
}

const relationTypeMap: Record<string, string> = {
  extends: '扩展关系',
  applies: '应用关系',
  compares: '对比关系',
  related: '相关关系',
  semantic: '语义关联',
  ownership: '归属关系',
  custom: '自定义',
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="关联边详情"
    direction="rtl"
    size="450px"
    @close="handleClose"
  >
    <div v-if="edgeData" class="edge-detail">
      <div class="edge-info">
        <div class="info-item">
          <label>源节点 ID</label>
          <span>{{ edgeData.source }}</span>
        </div>
        <div class="info-item">
          <label>目标节点 ID</label>
          <span>{{ edgeData.target }}</span>
        </div>
        <div class="info-item">
          <label>关系类型</label>
          <span>{{ relationTypeMap[edgeData.relationType] || edgeData.relationType }}</span>
        </div>
        <div v-if="edgeData.label" class="info-item">
          <label>标签</label>
          <span>{{ edgeData.label }}</span>
        </div>
        <div v-if="edgeData.reason" class="info-item">
          <label>关联理由</label>
          <span>{{ edgeData.reason }}</span>
        </div>
      </div>

      <div v-if="isEditing" class="edit-form">
        <el-form label-width="80px">
          <el-form-item label="关系类型">
            <el-input v-model="editForm.relation_type" placeholder="extends/applies/compares/related/custom" />
          </el-form-item>
          <el-form-item label="标签">
            <el-input v-model="editForm.label" placeholder="可选" />
          </el-form-item>
          <el-form-item>
            <el-button @click="cancelEdit">取消</el-button>
            <el-button type="primary" @click="submitEdit">保存</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="!isEditing" class="action-buttons">
        <el-button type="warning" plain @click="startEdit">
          <el-icon><Edit /></el-icon> 编辑
        </el-button>
        <el-button type="danger" plain @click="handleDeleteEdge">
          <el-icon><Delete /></el-icon> 删除
        </el-button>
      </div>
    </div>
    <div v-else class="empty-state">
      <el-empty description="请选择一条边" />
    </div>
  </el-drawer>
</template>

<style scoped>
.edge-detail { display: flex; flex-direction: column; gap: 1.5rem; padding: 0 0.5rem; }
.edge-info { background: var(--bg-secondary); border-radius: 12px; padding: 1rem; }
.info-item { display: flex; margin-bottom: 0.8rem; }
.info-item label { width: 100px; font-weight: 500; color: var(--text-secondary); }
.info-item span { flex: 1; color: var(--text-primary); word-break: break-all; }
.edit-form { background: var(--bg-secondary); padding: 1rem; border-radius: 12px; }
.action-buttons { display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1rem; }
.empty-state { display: flex; align-items: center; justify-content: center; min-height: 200px; }
</style>