<script setup lang="ts">
import { ArrowRight, Delete, EditPen, Folder, FolderAdd, MoreFilled } from '@element-plus/icons-vue'
import { ref, onMounted, onUnmounted } from 'vue'

interface LibraryFolder {
  id: string
  name: string
  paperIds: string[]
  children?: LibraryFolder[]
}

interface Props {
  folder: LibraryFolder
  depth: number
  selectedFolderId: string
  expandedFolders: Set<string>
  allFolders: LibraryFolder[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'select-folder': [folderId: string]
  'toggle-expand': [folderId: string]
  'create-sub-folder': [parentFolder: LibraryFolder]
  'rename-folder': [folder: LibraryFolder]
  'move-folder': [folder: LibraryFolder]
  'copy-folder': [folder: LibraryFolder]
  'delete-folder': [folder: LibraryFolder]
}>()

const dropdownVisible = ref(false)
const dropdownPosition = ref<{ x: number, y: number }>({ x: 0, y: 0 })
const dropdownRef = ref<HTMLElement | null>(null)

const handleSelectFolder = () => {
  emit('select-folder', props.folder.id)
}

const toggleExpand = (event: MouseEvent) => {
  event.stopPropagation()
  if (hasChildren.value) {
    emit('toggle-expand', props.folder.id)
  }
}

const hasChildren = computed(() => {
  return props.folder.children && props.folder.children.length > 0
})

const isExpanded = computed(() => {
  return props.expandedFolders.has(props.folder.id)
})

// 切换下拉菜单显示
const toggleDropdown = (event: MouseEvent) => {
  event.stopPropagation()
  if (dropdownVisible.value) {
    dropdownVisible.value = false
  } else {
    dropdownVisible.value = true
    const target = event.currentTarget as HTMLElement
    const rect = target.getBoundingClientRect()
    dropdownPosition.value = { 
      x: rect.right, 
      y: rect.bottom 
    }
  }
}

// 关闭下拉菜单
const closeDropdown = () => {
  dropdownVisible.value = false
}

// 处理全局点击事件
const handleClickOutside = (event: MouseEvent) => {
  if (!dropdownVisible.value) return
  
  const target = event.target as HTMLElement
  
  // 检查点击是否在下拉菜单内部
  if (dropdownRef.value && dropdownRef.value.contains(target)) {
    return
  }
  
  // 检查点击是否是触发按钮本身
  const moreIcon = document.querySelector('.more-icon')
  if (moreIcon && moreIcon.contains(target)) {
    return
  }
  
  // 点击了外部区域，关闭下拉菜单
  dropdownVisible.value = false
}

// 组件挂载时添加全局点击监听
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// 组件卸载时移除全局点击监听
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 新建子文件夹
const handleCreateSubFolder = async () => {
  closeDropdown()
  emit('create-sub-folder', props.folder)
}

// 重命名文件夹
const handleRenameFolder = () => {
  closeDropdown()
  emit('rename-folder', props.folder)
}

// 移动文件夹
const handleMoveFolder = () => {
  closeDropdown()
  emit('move-folder', props.folder)
}

// 复制文件夹
const handleCopyFolder = () => {
  closeDropdown()
  emit('copy-folder', props.folder)
}

// 删除文件夹
const handleDeleteFolder = () => {
  closeDropdown()
  emit('delete-folder', props.folder)
}

// 计算缩进
const indentStyle = computed(() => {
  return {
    marginLeft: `${props.depth * 1.5}rem`,
    paddingLeft: '0.5rem'
  }
})

import { computed } from 'vue'
</script>

<template>
  <div class="folder-item-wrapper">
    <div
      class="folder-item"
      :class="{ active: selectedFolderId === folder.id }"
      :style="indentStyle"
    >
      <div 
        class="folder-item__content"
        @click="handleSelectFolder"
      >
        <!-- 展开/收起图标 -->
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
        
        <!-- 详情按钮 -->
        <el-icon 
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

    <!-- 递归渲染子文件夹 -->
    <div 
      v-if="hasChildren && isExpanded"
      class="sub-folder-list"
    >
      <FolderItem
        v-for="child in folder.children"
        :key="child.id"
        :folder="child"
        :depth="depth + 1"
        :selected-folder-id="selectedFolderId"
        :expanded-folders="expandedFolders"
        :all-folders="allFolders"
        @select-folder="$emit('select-folder', $event)"
        @toggle-expand="$emit('toggle-expand', $event)"
        @create-sub-folder="$emit('create-sub-folder', $event)"
        @rename-folder="$emit('rename-folder', $event)"
        @move-folder="$emit('move-folder', $event)"
        @copy-folder="$emit('copy-folder', $event)"
        @delete-folder="$emit('delete-folder', $event)"
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
