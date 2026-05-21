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
      <!-- 重命名卡片 -->
      <div class="setting-card">
        <div class="card-header">
          <el-icon class="card-icon rename-icon"><EditPen /></el-icon>
          <div class="card-title">
            <span class="card-label">文件夹名称</span>
            <span class="card-desc">修改后将立即生效</span>
          </div>
        </div>
        <el-input
          v-model="name"
          placeholder="输入文件夹名称"
          size="large"
          class="rename-input"
        />
      </div>

      <!-- 危险操作区 -->
      <div class="danger-zone">
        <div class="danger-header">
          <span class="danger-title">危险操作</span>
        </div>
        <div class="danger-card">
          <div class="danger-card-left">
            <el-icon class="danger-icon"><DeleteFilled /></el-icon>
            <div>
              <div class="danger-label">删除文件夹</div>
              <div class="danger-desc">文件夹及其中的论文关联将被移除，论文本身不受影响</div>
            </div>
          </div>
          <el-button type="danger" @click="handleDelete" plain size="small">
            删除
          </el-button>
        </div>
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
import { EditPen, DeleteFilled } from '@element-plus/icons-vue'
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
  gap: 24px;
}

/* ── 设置卡片 ── */
.setting-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color 0.2s;
}

.setting-card:focus-within {
  border-color: #4a9d9a;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-icon {
  font-size: 1.25rem;
  padding: 6px;
  border-radius: 8px;
}

.rename-icon {
  background: rgba(74, 157, 154, 0.1);
  color: #4a9d9a;
}

.card-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1f2937;
}

.card-desc {
  font-size: 0.78rem;
  color: #94a3b8;
}

.rename-input {
  margin-left: 38px;
  width: calc(100% - 38px);
}

/* ── 危险操作区 ── */
.danger-zone {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.danger-header {
  padding: 0 2px;
}

.danger-title {
  font-size: 0.78rem;
  font-weight: 500;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.danger-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 14px 16px;
  transition: border-color 0.2s;
}

.danger-card:hover {
  border-color: #fca5a5;
}

.danger-card-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.danger-icon {
  font-size: 1.3rem;
  color: #ef4444;
  flex-shrink: 0;
}

.danger-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: #991b1b;
}

.danger-desc {
  font-size: 0.75rem;
  color: #b91c1c;
  opacity: 0.8;
  line-height: 1.3;
}

/* ── 底部按钮 ── */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

<style>
.folder-settings-dialog .el-dialog__header {
  padding: 20px 24px 0;
  font-size: 16px;
  font-weight: 600;
}

.folder-settings-dialog .el-dialog__body {
  padding: 20px 24px;
}
</style>
