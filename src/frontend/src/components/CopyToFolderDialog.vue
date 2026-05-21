<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    title="复制到文件夹"
    width="480px"
    destroy-on-close
    class="copy-to-folder-dialog"
  >
    <div class="dialog-body">
      <p class="dialog-hint">请选择目标文件夹：</p>
      
      <!-- 文件夹树形选择 -->
      <div class="folder-tree-container">
        <div v-if="folders.length === 0" class="empty-state">
          <el-empty description="暂无文件夹" :image-size="80" />
        </div>
        <div v-else class="folder-list">
          <div
            v-for="folder in flattenFolders(folders)"
            :key="folder.id"
            class="folder-item"
            :class="{ selected: selectedFolderId === folder.id }"
            @click="selectFolder(folder.id)"
          >
            <el-icon class="folder-icon"><Folder /></el-icon>
            <span class="folder-name">{{ folder.name }}</span>
            <span v-if="folder.depth > 0" class="folder-path">{{ getFolderPath(folder) }}</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="cancel" size="default">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirm" 
          size="default"
          :disabled="!selectedFolderId"
        >
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Folder } from '@element-plus/icons-vue'
import type { Folder as LibraryFolder } from '../types/folder'

interface FlattenedFolder extends LibraryFolder {
  depth: number
  parentName?: string
}

const props = defineProps<{
  modelValue: boolean
  folders: LibraryFolder[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [folderId: string]
}>()

const selectedFolderId = ref<string | null>(null)

// 重置选中状态
watch(() => props.modelValue, (visible) => {
  if (visible) {
    selectedFolderId.value = null
  }
})

// 扁平化文件夹树（用于展示）
const flattenFolders = (folders: LibraryFolder[], depth = 0, parentName = ''): FlattenedFolder[] => {
  const result: FlattenedFolder[] = []
  for (const folder of folders) {
    result.push({
      ...folder,
      depth,
      parentName: depth > 0 ? parentName : undefined
    })
    if (folder.children && folder.children.length > 0) {
      result.push(...flattenFolders(folder.children, depth + 1, folder.name))
    }
  }
  return result
}

// 获取文件夹路径显示
const getFolderPath = (folder: FlattenedFolder): string => {
  if (!folder.parentName) return ''
  return `(${folder.parentName})`
}

// 选择文件夹
const selectFolder = (folderId: string) => {
  selectedFolderId.value = folderId
}

// 取消
const cancel = () => {
  emit('update:modelValue', false)
}

// 确认
const confirm = () => {
  if (selectedFolderId.value) {
    emit('confirm', selectedFolderId.value)
    emit('update:modelValue', false)
  }
}
</script>

<style scoped>
.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dialog-hint {
  font-size: 0.9rem;
  color: #64748b;
  margin: 0;
}

.folder-tree-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.empty-state {
  padding: 40px 0;
}

.folder-list {
  display: flex;
  flex-direction: column;
}

.folder-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #e2e8f0;
}

.folder-item:last-child {
  border-bottom: none;
}

.folder-item:hover {
  background: #f1f5f9;
}

.folder-item.selected {
  background: rgba(74, 157, 154, 0.08);
  border-left: 3px solid #4a9d9a;
}

.folder-icon {
  font-size: 1.1rem;
  color: #64748b;
  flex-shrink: 0;
}

.folder-item.selected .folder-icon {
  color: #4a9d9a;
}

.folder-name {
  flex: 1;
  font-size: 0.9rem;
  color: #1f2937;
  font-weight: 500;
}

.folder-path {
  font-size: 0.75rem;
  color: #94a3b8;
}

/* 滚动条样式 */
.folder-tree-container::-webkit-scrollbar {
  width: 6px;
}

.folder-tree-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.folder-tree-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.folder-tree-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

<style>
.copy-to-folder-dialog .el-dialog__header {
  padding: 20px 24px 0;
  font-size: 16px;
  font-weight: 600;
}

.copy-to-folder-dialog .el-dialog__body {
  padding: 20px 24px;
}
</style>
