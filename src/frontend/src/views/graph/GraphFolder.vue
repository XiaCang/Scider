<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ArrowRight, Folder as FolderIcon } from '@element-plus/icons-vue'
import FolderItem from '../library/folder/FolderItem.vue'
import type { Folder } from '../../types/folder'

interface Props {
  modelValue: boolean
  selectedFolderId: string
  folders: Folder[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:selectedFolderId': [folderId: string]
  'toggle-expand': [folderId: string]
}>()

// 内部状态管理
const folderPanelVisible = ref(props.modelValue)
const selectedFolderId = ref(props.selectedFolderId)
const expandedFolders = ref<Set<string>>(new Set(['all'])) // 默认展开"全部论文"

// 监听外部 props 变化，同步内部状态
watch(() => props.modelValue, (newVal: boolean) => {
  folderPanelVisible.value = newVal
})

watch(() => props.selectedFolderId, (newVal: string) => {
  selectedFolderId.value = newVal
})

// 监听内部状态变化，通知父组件
watch(folderPanelVisible, (newVal: boolean) => {
  emit('update:modelValue', newVal)
})

watch(selectedFolderId, (newVal: string) => {
  emit('update:selectedFolderId', newVal)
})

// 递归查找文件夹
const findFolderById = (folders: Folder[], folderId: string): Folder | null => {
  for (const folder of folders) {
    if (folder.id === folderId) return folder
    if (folder.children) {
      const found = findFolderById(folder.children, folderId)
      if (found) return found
    }
  }
  return null
}

// 获取所有文件夹（扁平化）用于移动/复制操作
const getAllFolders = (foldersList: Folder[]): Folder[] => {
  let result: Folder[] = [...foldersList]
  for (const f of foldersList) {
    if (f.children) {
      result = result.concat(getAllFolders(f.children))
    }
  }
  return result
}

const toggleFolderExpand = (folderId: string) => {
  const newExpanded = new Set(expandedFolders.value)
  if (newExpanded.has(folderId)) {
    newExpanded.delete(folderId)
  } else {
    newExpanded.add(folderId)
  }
  expandedFolders.value = newExpanded
  emit('toggle-expand', folderId)
}

const isFolderExpanded = (folderId: string) => {
  return expandedFolders.value.has(folderId)
}

// 计算所有文件夹（扁平化）用于FolderItem组件
const allFolders = computed(() => getAllFolders(props.folders))
</script>

<template>
  <Teleport to="body">
    <!-- 梯形触发器 -->
    <div 
      class="folder-panel__trigger" 
      :class="{ 'is-panel-visible': folderPanelVisible }"
      @click="folderPanelVisible = !folderPanelVisible"
    ></div>
    
    <!-- 文件夹管理面板 -->
    <aside 
      class="folder-panel" 
      :class="{ 'is-visible': folderPanelVisible }"
    >
      <div class="folder-panel__header">
        <h3 class="folder-panel__title">文库文件夹</h3>
      </div>

      <div class="folder-manager">
        <div class="folder-list">
          <!-- 全部论文选项（作为根节点） -->
          <div
            class="folder-item level-0"
            :class="{ active: selectedFolderId === 'all' }"
          >
            <div 
              class="folder-item__content"
              @click="selectedFolderId = 'all'"
            >
              <!-- 展开/收起图标 -->
              <el-icon 
                class="expand-icon"
                :class="{ 'is-expanded': isFolderExpanded('all') }"
                @click.stop="toggleFolderExpand('all')"
              >
                <ArrowRight />
              </el-icon>
              
              <el-icon><FolderIcon /></el-icon>
              <span class="folder-name">全部论文</span>
            </div>
          </div>

          <!-- 递归渲染所有文件夹 -->
          <template v-for="folder in folders" :key="folder.id">
            <FolderItem
              v-show="isFolderExpanded('all')"
              :folder="folder"
              :depth="1"
              :selected-folder-id="selectedFolderId"
              :expanded-folders="expandedFolders"
              :all-folders="allFolders"
              :show-actions="false"
              @select-folder="(id) => selectedFolderId = id"
              @toggle-expand="toggleFolderExpand"
            />
          </template>
        </div>
      </div>
    </aside>
  </Teleport>
</template>

<style scoped>
/* 梯形触发器 */
.folder-panel__trigger {
  position: fixed;
  left: 0;
  top: calc(64px + 5px); /* 主导航栏高度 + 偏移 */
  width: 25px;
  height: 80px;
  background: #1e3a5f;
  cursor: pointer;
  clip-path: polygon(0 0, 100% 15%, 100% 85%, 0 100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 60;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.1);
}

.folder-panel__trigger:hover {
  background: #2a4d73;
}

.folder-panel__trigger.is-panel-visible {
  transform: translateX(280px);
}

/* 文件夹管理面板 */
.folder-panel {
  width: 280px;
  min-width: 280px;
  background: white;
  border-right: 1px solid var(--line-soft);
  display: flex;
  flex-direction: column;
  overflow: visible;
  position: fixed;
  left: 0;
  top: 64px; /* 主导航栏高度 */
  bottom: 0;
  z-index: 50;
  transform: translateX(-100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.folder-panel.is-visible {
  transform: translateX(0);
}

.folder-panel__header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--line-soft);
  background: linear-gradient(to bottom, rgba(255,255,255,0.95), rgba(255,255,255,0.8));
}

.folder-panel__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.folder-manager {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.folder-list {
  padding: 0;
}

/* 文件夹项样式 */
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

.folder-item.level-0 {
  margin-left: 0;
  padding-left: 0.75rem;
}

.folder-item__content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  position: relative;
  padding: 0;
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

.expand-icon:hover {
  color: var(--text-primary);
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
  opacity: 0;
  transition: all 0.2s;
  padding: 4px;
  border-radius: 4px;
}

.level-0:hover .more-icon {
  opacity: 1;
}

.more-icon:hover {
  background: var(--bg-soft);
  color: var(--text-primary);
}
</style>
