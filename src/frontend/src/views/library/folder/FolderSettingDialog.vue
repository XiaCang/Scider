<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    title="文件夹设置"
    width="460px"
    destroy-on-close
    class="folder-settings-dialog"
  >
    <div class="settings-form">
      <!-- 标题图标区 -->
      <div class="form-item">
        <label>
          <el-icon><Folder /></el-icon>
          文件夹名称
        </label>
        <el-input
          v-model="name"
          placeholder="输入文件夹名称"
          size="large"
        />
      </div>

      <!-- 移动到 -->
      <div class="form-item">
        <label>
          <el-icon><ArrowRight /></el-icon>
          移动到
        </label>
        <el-select
          v-model="moveToFolderId"
          placeholder="选择目标文件夹"
          clearable
          size="large"
        >
          <el-option
            v-for="f in moveTargets"
            :key="f.id"
            :label="f.name"
            :value="f.id"
          />
        </el-select>
      </div>

      <!-- 复制到 -->
      <div class="form-item">
        <label>
          <el-icon><CopyDocument /></el-icon>
          复制到
        </label>
        <el-select
          v-model="copyToFolderId"
          placeholder="选择目标文件夹"
          clearable
          size="large"
        >
          <el-option
            v-for="f in copyTargets"
            :key="f.id"
            :label="f.name"
            :value="f.id"
          />
        </el-select>
      </div>

      <!-- 危险操作区 -->
      <div class="form-divider"></div>
      <div class="form-actions">
        <el-button
          type="danger"
          @click="handleDelete"
          size="large"
          plain
        >
          <el-icon><Delete /></el-icon>
          删除文件夹
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="cancel" size="large">取消</el-button>
        <el-button type="primary" @click="confirm" size="large">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Folder,
  ArrowRight,
  CopyDocument,
  Delete
} from '@element-plus/icons-vue'
import { useFolderStore } from '../../../store/folder'
import { useFolderOperations, getAllFolders, isDescendant } from '../../../hooks/useFolderOperations'
import type { Folder as LibraryFolder } from '../../../types/folder'

const props = defineProps<{
  modelValue: boolean
  folder: LibraryFolder
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const folderStore = useFolderStore()
const { renameFolder, moveFolder, copyFolder, deleteFolder } = useFolderOperations()

// 表单数据
const name = ref(props.folder.name)
const moveToFolderId = ref<string | null>(null)
const copyToFolderId = ref<string | null>(null)

// 所有文件夹扁平列表
const allFolders = computed(() => getAllFolders(folderStore.folders))

// 移动到可选目标：排除自身及其所有后代
const moveTargets = computed(() =>
  allFolders.value.filter(f => {
    if (f.id === props.folder.id) return false
    return !isDescendant(folderStore.folders, props.folder.id, f.id)
  })
)

// 复制到可选目标：仅排除自身
const copyTargets = computed(() =>
  allFolders.value.filter(f => f.id !== props.folder.id)
)

// 重置表单
watch(() => props.modelValue, (visible) => {
  if (visible) {
    name.value = props.folder.name
    moveToFolderId.value = null
    copyToFolderId.value = null
  }
})

// 删除操作（带确认）
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件夹“${props.folder.name}”及其所有子文件夹吗？此操作不可恢复。`,
      '警告',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteFolder(props.folder.id)
    ElMessage.success('文件夹已删除')
    emit('update:modelValue', false)
  } catch { /* 取消 */ }
}

// 取消
const cancel = () => emit('update:modelValue', false)

// 确定：批量执行修改
const confirm = async () => {
  try {
    // 重命名
    const trimmedName = name.value.trim()
    if (trimmedName && trimmedName !== props.folder.name) {
      await renameFolder(props.folder.id, trimmedName)
    }
    // 移动
    if (moveToFolderId.value) {
      await moveFolder(props.folder.id, moveToFolderId.value)
    }
    // 复制
    if (copyToFolderId.value) {
      await copyFolder(props.folder.id, copyToFolderId.value)
    }
    emit('update:modelValue', false)
  } catch {
    // store 中的操作失败会有其他错误提示
  }
}
</script>

<style scoped>
.folder-settings-dialog :deep(.el-dialog__header) {
  padding: 24px 24px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.folder-settings-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-item label .el-icon {
  font-size: 1rem;
  color: var(--text-secondary);
}

.form-divider {
  height: 1px;
  background: var(--line-soft);
  margin: 4px 0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

<style>
/* 全局样式覆盖（可选，提升下拉框一致性） */
.folder-settings-dialog .el-select {
  width: 100%;
}
</style>