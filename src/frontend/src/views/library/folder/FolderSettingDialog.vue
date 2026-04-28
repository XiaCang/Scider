<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    title="文件夹设置"
    width="480px"
    destroy-on-close
  >
    <div class="settings-form">
      <div class="form-item">
        <label>文件夹名称</label>
        <el-input v-model="name" placeholder="输入名称" />
      </div>
      <div class="form-item">
        <label>移动到</label>
        <el-select v-model="moveToFolderId" placeholder="选择目标文件夹" clearable>
          <el-option
            v-for="f in availableMoveFolders"
            :key="f.id"
            :label="f.name"
            :value="f.id"
          />
        </el-select>
      </div>
      <div class="form-item">
        <label>复制到</label>
        <el-select v-model="copyToFolderId" placeholder="选择目标文件夹" clearable>
          <el-option
            v-for="f in availableCopyFolders"
            :key="f.id"
            :label="f.name"
            :value="f.id"
          />
        </el-select>
      </div>
      <div class="form-actions">
        <el-button type="danger" @click="handleDelete">删除文件夹</el-button>
      </div>
    </div>
    <template #footer>
      <el-button @click="cancel">取消</el-button>
      <el-button type="primary" @click="confirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useFolderStore } from '../../../store/folder'
import { useFolderOperations } from '../../../hooks/useFolderOperations'
import type { Folder } from '../../../types/folder'

const props = defineProps<{
  modelValue: boolean
  folder: Folder
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const folderStore = useFolderStore()


const name = ref(props.folder.name)
const moveToFolderId = ref<string | null>(null)
const copyToFolderId = ref<string | null>(null)

// 扁平化所有文件夹（用于下拉选项）
const allFolders = computed(() => {
  const result: Folder[] = []
  const flatten = (list: Folder[]) => {
    for (const f of list) {
      result.push(f)
      if (f.children) flatten(f.children)
    }
  }
  flatten(folderStore.folders)
  return result
})

// 判断 targetId 是否是 ancestorId 的后代
const isDescendant = (ancestorId: string, descendantId: string): boolean => {
  const ancestors = new Set<string>()
  const findAncestors = (list: Folder[], id: string, path: string[] = []): boolean => {
    for (const f of list) {
      if (f.id === id) {
        path.forEach(p => ancestors.add(p))
        return true
      }
      if (f.children && findAncestors(f.children, id, [...path, f.id])) return true
    }
    return false
  }
  findAncestors(folderStore.folders, descendantId)
  return ancestors.has(ancestorId)
}

// 可移动目标：排除自身及后代
const availableMoveFolders = computed(() =>
  allFolders.value.filter(f => {
    if (f.id === props.folder.id) return false
    return !isDescendant(props.folder.id, f.id)
  })
)

// 可复制目标：排除自身
const availableCopyFolders = computed(() =>
  allFolders.value.filter(f => f.id !== props.folder.id)
)

watch(() => props.folder.name, (val) => { name.value = val })
watch(() => props.modelValue, (val) => {
  if (val) {
    name.value = props.folder.name
    moveToFolderId.value = null
    copyToFolderId.value = null
  }
})

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件夹“${props.folder.name}”及其所有子文件夹吗？此操作不可恢复。`,
      '警告',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await deleteFolder(props.folder)
    emit('update:modelValue', false)
  } catch { /* 取消 */ }
}

const cancel = () => emit('update:modelValue', false)

const confirm = async () => {
  if (name.value.trim() !== props.folder.name) {
    await renameFolder(props.folder.id, name.value.trim())
  }
  if (moveToFolderId.value) {
    await moveFolder(props.folder.id, moveToFolderId.value)
  }
  if (copyToFolderId.value) {
    await copyFolder(props.folder.id, copyToFolderId.value)
  }
  emit('update:modelValue', false)
}
</script>

<style scoped>
.settings-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-item label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
}
.form-actions {
  margin-top: 8px;
}
</style>