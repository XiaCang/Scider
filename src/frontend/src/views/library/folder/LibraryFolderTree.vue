<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useFolderStore } from '../../../store/folder'
import FolderItem from './FolderItem.vue'

interface Props {
  activeFolderId: string
  expandedFolders: Set<string>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:expandedFolders': [value: Set<string>]
  'select-folder': [folderId: string]
}>()

const folderStore = useFolderStore()

folderStore.loadTestData()

const disableTransition = ref(true)
onMounted(() => requestAnimationFrame(() => requestAnimationFrame(() => (disableTransition.value = false))))

// 视图模式：'all' 显示文件夹树，'recent' 显示占位
const viewMode = ref<'all' | 'recent'>('all')

const toggleExpand = (id: string) => {
  const copy = new Set(props.expandedFolders)
  copy.has(id) ? copy.delete(id) : copy.add(id)
  emit('update:expandedFolders', copy)
}

// 文件夹选择
const handleSelectFolder = (id: string) => {
  viewMode.value = 'all'
  emit('select-folder', id)
}

// 顶部选项卡切换
const handleTabClick = (tab: 'recent' | 'all') => {
  if (tab === 'all') {
    viewMode.value = 'all'
    emit('select-folder', 'all')
  } else {
    viewMode.value = 'recent'
  }
}
</script>

<template>
  <div class="folder-panel">
    <div class="folder-panel__header">
      <h3 class="folder-panel__title">文库文件夹</h3>
      <div class="folder-tabs">
        <button
          class="tab-btn"
          :class="{ active: viewMode === 'recent' }"
          @click="handleTabClick('recent')"
        >
          最近论文
        </button>
        <button
          class="tab-btn"
          :class="{ active: viewMode === 'all' }"
          @click="handleTabClick('all')"
        >
          全部论文
        </button>
      </div>
    </div>

    <div class="folder-manager">
      <!-- 文件夹树视图 -->
      <div v-if="viewMode === 'all'" class="folder-list">
        <!-- 直接渲染顶层文件夹（无“全部论文”项） -->
        <FolderItem
          v-for="folder in folderStore.folders"
          :key="folder.id"
          :folder="folder"
          :depth="1"
          :selected-folder-id="activeFolderId"
          :expanded-folders="expandedFolders"
          :show-actions="true"
          @select-folder="handleSelectFolder"
          @toggle-expand="toggleExpand"
        />
      </div>

      <!-- 最近论文占位 -->
      <div v-else class="recent-placeholder">
        <p>最近论文功能即将开放</p>
      </div>
    </div>
  </div>

  <!-- 主内容区插槽 -->
  <section class="library-page">
    <slot></slot>
  </section>
</template>

<style scoped>
.library-page {
  display: flex;
  gap: 0;
  min-height: calc(100vh - 60px);
  position: relative;
}

/* 圆角卡片式文件夹面板 */
.folder-panel {
  width: 280px;
  min-width: 280px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  margin: 20px 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: fixed;
  left: 0;
  top: 64px; /* 主 header 高度 */
  bottom: 20px;
  z-index: 50;
}

.folder-panel__header {
  display: flex;
  flex-direction: column;
  padding: 16px 16px 8px;
  border-bottom: 1px solid var(--line-soft);
  background: transparent;
}

.folder-panel__title {
  margin: 0 0 12px 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.folder-tabs {
  display: flex;
  gap: 0;
  background: var(--bg-soft);
  border-radius: 10px;
  padding: 2px;
}

.tab-btn {
  flex: 1;
  padding: 6px 12px;
  border: none;
  background: transparent;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: white;
  color: var(--brand);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  font-weight: 600;
}

.folder-manager {
  flex: 1;
  overflow-y: auto;
  padding: 12px 12px 16px;
}

.folder-list {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.recent-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  font-size: 0.9rem;
  opacity: 0.8;
}

/* 移除不再需要的触发器样式 */
</style>