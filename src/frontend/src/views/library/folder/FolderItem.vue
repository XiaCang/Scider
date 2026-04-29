<script setup lang="ts">
import {
  ArrowRight,
  Folder,
  Plus,
  Setting
} from '@element-plus/icons-vue'
import { ref, computed } from 'vue'
import { useFolderStore } from '../../../store/folder'
import { useFolderOperations } from '../../../hooks/useFolderOperations'
import FolderSettingDialog from './FolderSettingDialog.vue'
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

const folderStore = useFolderStore()
const { createSubFolder } = useFolderOperations()

// 悬停状态（用于切换图标和显示操作按钮）
const isHovering = ref(false)
// 设置对话框可见性
const settingsVisible = ref(false)
// 拖拽相关状态
const isDragOver = ref(false)

// 辅助计算
const hasChildren = computed(() => !!(props.folder.children?.length))
const isExpanded = computed(() => props.expandedFolders.has(props.folder.id))
const indentStyle = computed(() => ({
  marginLeft: `${props.depth * 10}px`,
  paddingLeft: '0.5rem'
}))

// 判断目标文件夹是否是源文件夹的后代（用于拖放校验）
const isDescendant = (ancestorId: string, descendantId: string): boolean => {
  const ancestors = new Set<string>()
  const findAncestors = (list: LibraryFolder[], id: string, path: string[] = []): boolean => {
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

// 基础交互
const handleSelectFolder = () => emit('select-folder', props.folder.id)

const toggleExpand = (event: MouseEvent) => {
  event.stopPropagation()
  if (hasChildren.value) emit('toggle-expand', props.folder.id)
}

// 拖拽事件处理
const onDragStart = (event: DragEvent) => {
  event.dataTransfer!.setData('text/plain', props.folder.id)
  event.dataTransfer!.effectAllowed = 'move'
}

const onDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (!event.dataTransfer) return
  const draggedId = event.dataTransfer.getData('text/plain')
  // 不允许拖到自己或后代上
  if (draggedId === props.folder.id || isDescendant(draggedId, props.folder.id)) {
    event.dataTransfer.dropEffect = 'none'
    return
  }
  isDragOver.value = true
  event.dataTransfer.dropEffect = event.ctrlKey ? 'copy' : 'move'
}

const onDragLeave = () => {
  isDragOver.value = false
}

const onDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  const draggedId = event.dataTransfer!.getData('text/plain')
  if (!draggedId || draggedId === props.folder.id) return
  if (isDescendant(draggedId, props.folder.id)) return

  const ctrlKey = event.ctrlKey || event.metaKey
  if (ctrlKey) {
    // 复制
    folderStore.copyFolder(draggedId, props.folder.id)
  } else {
    // 移动
    folderStore.moveFolder(draggedId, props.folder.id)
  }
}

// 加号按钮：新建子文件夹（自动以当前文件夹为父级）
const handleAdd = async () => {
  await createSubFolder(props.folder)
}

// 齿轮按钮：打开设置对话框
const openSettings = () => {
  settingsVisible.value = true
}
</script>

<template>
  <div class="folder-item-wrapper">
    <div
      class="folder-item"
      :class="{
        active: selectedFolderId === folder.id,
        'drag-over': isDragOver
      }"
      :style="indentStyle"
      draggable="true"
      @dragstart="onDragStart"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
      @mouseenter="isHovering = true"
      @mouseleave="isHovering = false"
    >
      <div class="folder-item__content" @click="handleSelectFolder">
        <!-- 左侧图标：有子级时悬停显示箭头，否则显示文件夹图标；无子级占位隐藏 -->
        <el-icon
          v-if="hasChildren"
          class="expand-icon"
          :class="{ 'is-expanded': isExpanded }"
          @click.stop="toggleExpand"
        >
          <ArrowRight v-if="isHovering" />
          <Folder v-else />
        </el-icon>
        <el-icon v-else class="expand-placeholder">
          <Folder/>
        </el-icon>
        <span class="folder-name">{{ folder.name }}</span>

        <!-- 右侧操作按钮组（hover 或拖放时显示） -->
        <div v-if="showActions" class="action-group" :class="{ 'is-visible': isHovering || isDragOver }">
          <el-icon class="action-btn" @click.stop="handleAdd" title="新建子文件夹">
            <Plus />
          </el-icon>
          <el-icon class="action-btn" @click.stop="openSettings" title="文件夹设置">
            <Setting />
          </el-icon>
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

    <!-- 文件夹设置对话框 -->
    <FolderSettingDialog
      v-if="settingsVisible"
      v-model="settingsVisible"
      :folder="folder"
    />
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
  padding: 0.3rem 0.5rem;    /* 减小上下内边距，让高度更紧凑 */
  border-radius: 6px;        /* 稍微缩小圆角 */
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  position: relative;
  user-select: none;
}

.folder-item:hover {
  background: var(--bg-soft);
  border-color: var(--line-soft);
}

.folder-item.active {
  background: var(--brand-soft);
  border-color: var(--brand);
}

.folder-item.drag-over {
  background: var(--brand-soft);
  border-color: var(--brand);
  box-shadow: 0 0 0 2px var(--brand-light);
}

.folder-item__content {
  display: flex;
  align-items: center;
  gap: 0.3rem;              /* 缩小内部间距，让图标更靠左 */
  width: 100%;
  position: relative;
}

/* 左侧展开图标区域 */
.expand-icon,
.expand-placeholder {
  font-size: 0.9rem;        /* 图标缩小一点 */
  min-width: 16px;          /* 固定最小宽度，保证对齐 */
  color: var(--text-secondary);
  transition: transform 0.2s ease;
  cursor: pointer;
}
.expand-icon.is-expanded {
  transform: rotate(90deg);
}

.folder-icon-static {
  font-size: 0.9rem;        /* 与上方保持一致 */
  color: var(--text-secondary);
  flex-shrink: 0;
}

.folder-name {
  flex: 1;
  font-size: 0.85rem;       /* 字体缩小 */
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 右侧操作按钮组 */
.action-group {
  display: flex;
  gap: 1px;                 /* 缩小按钮间距 */
  opacity: 0;
  transition: opacity 0.15s;
}
.action-group.is-visible {
  opacity: 1;
}
.action-btn {
  font-size: 1.25rem;       /* 按钮图标缩小 */
  color: var(--text-secondary);
  cursor: pointer;
  padding: 2px;             /* 减小内边距 */
  border-radius: 4px;
  transition: all 0.15s;
}
.action-btn:hover {
  background: var(--bg-soft);
  color: var(--text-primary);
}

.sub-folder-list {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;              /* 减小子文件夹之间的垂直间距 */
  margin-top: 0.1rem;
  margin-bottom: 0.1rem;
}

</style>