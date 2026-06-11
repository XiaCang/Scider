<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
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

// 本地响应式副本，保存成功后立即更新，无需等 prop 刷新
const localData = ref<EdgeData | null>(null)
watch(() => props.edgeData, (val) => {
  localData.value = val ? { ...val, properties: val.properties ? { ...val.properties } : undefined } : null
}, { immediate: true })

const displayData = computed(() => localData.value || props.edgeData)

// 行内编辑状态
const editingField = ref<string | null>(null)
const editValue = ref('')

const relationTypeOptions = [
  { value: 'extends', label: '扩展关系' },
  { value: 'applies', label: '应用关系' },
  { value: 'compares', label: '对比关系' },
  { value: 'related', label: '相关关系' },
  { value: 'semantic', label: '语义关联' },
  { value: 'ownership', label: '归属关系' },
  { value: 'custom', label: '自定义' },
]

const relationTypeMap: Record<string, string> = Object.fromEntries(
  relationTypeOptions.map(o => [o.value, o.label])
)

const edgeLabel = computed(() =>
  displayData.value?.label || displayData.value?.reason || displayData.value?.properties?.reason || ''
)

const startEdit = (field: string) => {
  if (!props.edgeData) return
  if (field === 'relation_type') {
    editValue.value = props.edgeData.relationType
  } else if (field === 'label') {
    editValue.value = edgeLabel.value
  }
  editingField.value = field
}

const cancelEdit = () => {
  editingField.value = null
  editValue.value = ''
}

const saving = ref(false)

const saveEdit = async () => {
  if (!props.edgeData || !editingField.value || saving.value) return
  saving.value = true
  try {
    const payload: any = {}
    if (editingField.value === 'relation_type') {
      payload.relation_type = editValue.value
    } else if (editingField.value === 'label') {
      payload.label = editValue.value
    }
    await updateGraphEdge(props.edgeData.id, payload)
    // 立即更新本地数据，无需等 graph 刷新
    if (localData.value) {
      if (editingField.value === 'relation_type') {
        localData.value.relationType = editValue.value
      } else if (editingField.value === 'label') {
        localData.value.label = editValue.value
      }
    }
    ElMessage.success('更新成功')
    editingField.value = null
    editValue.value = ''
    emit('refresh')
  } catch (e: any) {
    const msg = e?.response?.data?.msg || e?.message || '更新失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
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
  editingField.value = null
  drawerVisible.value = false
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
    <div v-if="displayData" class="edge-detail">
      <div class="edge-summary">
        <span class="edge-badge">{{ relationTypeMap[displayData.relationType] || displayData.relationType }}</span>
      </div>

      <div class="info-grid">
        <div class="info-row">
          <span class="info-key">源节点</span>
          <span class="info-val mono">{{ displayData.source }}</span>
        </div>
        <div class="info-row">
          <span class="info-key">目标节点</span>
          <span class="info-val mono">{{ displayData.target }}</span>
        </div>

        <!-- 关系类型（只读） -->
        <div class="info-row">
          <span class="info-key">关系类型</span>
          <span class="info-val">{{ relationTypeMap[displayData.relationType] || displayData.relationType }}</span>
        </div>

        <!-- 关联理由 -->
        <div class="info-row info-row--col">
          <span class="info-key">关联理由</span>
          <template v-if="editingField === 'label'">
            <div class="inline-edit-wrap">
              <el-input v-model="editValue" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="描述这条边的含义" />
              <div class="inline-edit-actions">
                <el-button size="small" type="primary" @click="saveEdit">保存</el-button>
                <el-button size="small" @click="cancelEdit">取消</el-button>
              </div>
            </div>
          </template>
          <template v-else>
            <p class="info-text">{{ edgeLabel || '暂无描述' }}</p>
            <button class="inline-btn" title="修改" @click="startEdit('label')">
              <el-icon :size="12"><Edit /></el-icon>
            </button>
          </template>
        </div>
      </div>

      <div class="actions">
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
.edge-detail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.edge-summary {
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--line-soft);
}

.edge-badge {
  display: inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(74, 157, 154, 0.12);
  color: #4a9d9a;
}

/* ── 信息行 ── */
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-row {
  display: flex;
  gap: 0.75rem;
  font-size: 0.85rem;
  line-height: 1.5;
  align-items: flex-start;
}

.info-row--col {
  flex-direction: column;
  gap: 0.3rem;
}

.info-key {
  flex-shrink: 0;
  min-width: 5em;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-val {
  color: var(--text-primary);
  word-break: break-all;
}

.info-val.mono {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 0.8rem;
}

.info-text {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.65;
  color: var(--text-primary);
  white-space: pre-wrap;
}

/* ── 行内编辑按钮 ── */
.inline-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.12s, color 0.12s;
}

.inline-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-primary);
}

/* ── 行内编辑控件 ── */
.inline-edit-select {
  width: 160px;
}

.inline-edit-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.inline-edit-actions {
  display: flex;
  gap: 6px;
}

/* ── 操作 ── */
.actions {
  display: flex;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line-soft);
}

.actions :deep(.el-button--danger.is-plain:hover) {
  color: #c17767 !important;
  background: rgba(193, 119, 103, 0.08) !important;
  border-color: rgba(193, 119, 103, 0.3) !important;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

@media (max-width: 768px) {
  .actions { flex-direction: column; }
}
</style>
