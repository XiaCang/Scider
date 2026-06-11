<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    title="文件夹设置"
    width="420px"
    destroy-on-close
    class="folder-settings-dialog"
  >
    <div class="settings-body">
      <div class="form-group">
        <label class="form-label">文件夹名称</label>
        <el-input
          v-model="name"
          placeholder="输入文件夹名称"
          size="large"
        />
      </div>

      <div class="divider" />

      <div class="delete-row">
        <div class="delete-info">
          <div class="delete-label">删除文件夹</div>
          <div class="delete-desc">论文关联将被移除，论文本身不受影响</div>
        </div>
        <el-button type="danger" @click="handleDelete" plain>
          删除
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="cancel" size="default">取消</el-button>
        <el-button type="primary" @click="confirm" size="default">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFolderOperations } from '../../../hooks/useFolderOperations'
import type { Folder as LibraryFolder } from '../../../types/folder'

const props = defineProps<{
  modelValue: boolean
  folder: LibraryFolder
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { renameFolder, deleteFolder } = useFolderOperations()

// 表单数据
const name = ref(props.folder.name)

// 重置
watch(() => props.modelValue, (visible) => {
  if (visible) name.value = props.folder.name
})

// 删除
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件夹"${props.folder.name}"吗？论文本身不会被删除。`,
      '删除文件夹',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        draggable: true,
      }
    )
    await deleteFolder(props.folder.id)
    ElMessage.success('文件夹已删除')
    emit('update:modelValue', false)
  } catch (e: any) {
    if (e?.toString()?.includes('cancel') || e?.toString()?.includes('close')) return
    ElMessage.error(e instanceof Error ? e.message : '删除文件夹失败')
  }
}

const cancel = () => emit('update:modelValue', false)

// 确定：只执行重命名
const confirm = async () => {
  const trimmedName = name.value.trim()
  if (!trimmedName) {
    ElMessage.warning('文件夹名称不能为空')
    return
  }
  if (trimmedName === props.folder.name) {
    emit('update:modelValue', false)
    return
  }
  try {
    await renameFolder(props.folder.id, trimmedName)
    ElMessage.success('文件夹已重命名')
    emit('update:modelValue', false)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '重命名失败')
  }
}
</script>

<style scoped>
.settings-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.divider {
  height: 1px;
  background: var(--line-soft);
}

.delete-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.delete-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.delete-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #991b1b;
}

.delete-desc {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  line-height: 1.3;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

<style>
.folder-settings-dialog .el-dialog__header {
  padding: 18px 20px 0;
  font-size: 15px;
  font-weight: 600;
}

.folder-settings-dialog .el-dialog__body {
  padding: 16px 20px;
}

.dialog-content {
  padding: 4px 0;
}

.dialog-tip {
  margin: 0 0 12px;
  font-size: 0.88rem;
  color: var(--text-secondary);
}

.dialog-input {
  display: block;
  width: 100%;
  box-sizing: border-box;
  padding: 10px 14px;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  font-size: 0.9rem;
  font-family: inherit;
  outline: none;
  background: var(--bg-muted);
  color: var(--text-primary);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.dialog-input:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-soft);
}

.dialog-input::placeholder {
  color: var(--text-tertiary);
}
</style>
