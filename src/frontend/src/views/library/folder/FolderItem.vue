<script setup lang="ts">
import { ArrowRight, Delete, EditPen, Folder, FolderAdd, MoreFilled } from '@element-plus/icons-vue'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useFolderOperations } from '../../../hooks/useFolderOperations'
import type { Folder as LibraryFolder } from '../../../types/folder'

interface Props {
  folder: LibraryFolder
  depth: number
  selectedFolderId: string
  expandedFolders: Set<string>
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true
})

const emit = defineEmits<{
  'select-folder': [folderId: string]
  'toggle-expand': [folderId: string]
}>()

// 引入操作逻辑
const { createSubFolder, renameFolder, moveFolder, copyFolder, deleteFolder } = useFolderOperations()

// 本地状态：下拉菜单
const dropdownVisible = ref(false)
const dropdownPosition = ref({ x: 0, y: 0 })
const dropdownRef = ref<HTMLElement | null>(null)

// 基础交互
const handleSelectFolder = () => emit('select-folder', props.folder.id)

const toggleExpand = (event: MouseEvent) => {
  event.stopPropagation()
  if (hasChildren.value) emit('toggle-expand', props.folder.id)
}

// 辅助计算
const hasChildren = computed(() => !!(props.folder.children?.length))
const isExpanded = computed(() => props.expandedFolders.has(props.folder.id))
const indentStyle = computed(() => ({
  marginLeft: `${props.depth * 1.5}rem`,
  paddingLeft: '0.5rem'
}))

// 下拉菜单控制
const toggleDropdown = (event: MouseEvent) => {
  event.stopPropagation()
  if (dropdownVisible.value) {
    dropdownVisible.value = false
    return
  }
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  dropdownPosition.value = { x: rect.right, y: rect.bottom }
  dropdownVisible.value = true
}

const closeDropdown = () => { dropdownVisible.value = false }

// 全局点击关闭
const handleClickOutside = (event: MouseEvent) => {
  if (!dropdownVisible.value) return
  const target = event.target as HTMLElement
  if (dropdownRef.value?.contains(target)) return
  if ((event.target as HTMLElement).closest('.more-icon')) return
  dropdownVisible.value = false
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))

// 文件夹操作 —— 直接调用 composable，无需向上 emit
const handleCreateSubFolder = async () => {
  closeDropdown()
  await createSubFolder(props.folder)
}

const handleRenameFolder = async () => {
  closeDropdown()
  await renameFolder(props.folder)
}

const handleMoveFolder = async () => {
  closeDropdown()
  await moveFolder(props.folder)
}

const handleCopyFolder = async () => {
  closeDropdown()
  await copyFolder(props.folder)
}

const handleDeleteFolder = async () => {
  closeDropdown()
  await deleteFolder(props.folder)
}
</script>

<template>
  <div class="folder-item-wrapper">
    <div
      class="folder-item"
      :class="{ active: selectedFolderId === folder.id }"
      :style="indentStyle"
    >
      <div class="folder-item__content" @click="handleSelectFolder">
        <!-- 展开/收起图标（有子节点时显示） -->
        <el-icon
          v-if="hasChildren"
          class="expand-icon"
          :class="{ 'is-expanded': isExpanded }"
          @click.stop="toggleExpand"
        >
          <ArrowRight />
        </el-icon>
        <span v-else class="expand-placeholder"></span>

        <el-icon><Folder /></el-icon>
        <span class="folder-name">{{ folder.name }}</span>

        <!-- 操作菜单按钮（若 showActions 为 true） -->
        <el-icon
          v-if="showActions"
          class="more-icon"
          @click.stop="toggleDropdown"
        >
          <MoreFilled />
        </el-icon>
      </div>

      <!-- 下拉菜单 -->
      <div
        v-if="dropdownVisible"
        ref="dropdownRef"
        class="folder-dropdown"
        :style="{ top: `${dropdownPosition.y}px`, left: `${dropdownPosition.x}px` }"
      >
        <div class="dropdown-item" @click="handleCreateSubFolder">
          <el-icon><FolderAdd /></el-icon>
          <span>新建子文件夹</span>
        </div>
        <div class="dropdown-item" @click="handleRenameFolder">
          <el-icon><EditPen /></el-icon>
          <span>重命名</span>
        </div>
        <div class="dropdown-item" @click="handleMoveFolder">
          <el-icon><ArrowRight /></el-icon>
          <span>移动到</span>
        </div>
        <div class="dropdown-item" @click="handleCopyFolder">
          <el-icon><Folder /></el-icon>
          <span>复制到</span>
        </div>
        <div class="dropdown-item delete" @click="handleDeleteFolder">
          <el-icon><Delete /></el-icon>
          <span>删除</span>
        </div>
      </div>
    </div>

    <!-- 递归子文件夹 -->
    <div v-if="hasChildren && isExpanded" class="sub-folder-list">
      <FolderItem
        v-for="child in folder.children"
        :key="child.id"
        :folder="child"
        :depth="depth + 1"
        :selected-folder-id="selectedFolderId"
        :expanded-folders="expandedFolders"
        @select-folder="$emit('select-folder', $event)"
        @toggle-expand="$emit('toggle-expand', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.folder-item-wrapper {
  display: flex;
  flex-direction: column;
}

.folder-item {
  display: flex;
  flex-direction: column;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  position: relative;
}

.folder-item:hover {
  background: var(--bg-soft);
  border-color: var(--line-soft);
}

.folder-item.active {
  background: var(--brand-soft);
  border-color: var(--brand);
}

.folder-item__content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  position: relative;
}

.expand-icon {
  font-size: 0.9rem;
  color: var(--text-secondary);
  transition: transform 0.2s ease;
  cursor: pointer;
  min-width: 16px;
}

.expand-icon.is-expanded {
  transform: rotate(90deg);
}

.expand-placeholder {
  min-width: 16px;
}

.folder-name {
  flex: 1;
  font-size: 0.9rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-icon {
  font-size: 1rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  opacity: 0;
}

.folder-item:hover .more-icon {
  opacity: 1;
}

.more-icon:hover {
  background: var(--bg-soft);
  color: var(--text-primary);
}

.sub-folder-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-top: 0.2rem;
  margin-bottom: 0.3rem;
}

/* 下拉菜单样式 */
.folder-dropdown {
  position: fixed;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 0.5rem 0;
  min-width: 180px;
  z-index: 1000;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.dropdown-item:hover {
  background: var(--bg-soft);
}

.dropdown-item.delete {
  color: #f56c6c;
}

.dropdown-item.delete:hover {
  background: #fef0f0;
}

.dropdown-item .el-icon {
  font-size: 1rem;
}
</style>
