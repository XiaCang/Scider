<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useFolderStore } from '../../../store/folder'
import { useFolderOperations } from '../../../hooks/useFolderOperations'
import { useFolderTreeFilter } from '../../../hooks/useFolderTreeFilter'
import FolderItem from './FolderItem.vue'
import FolderSearchBar from '../../../components/FolderSearchBar.vue'
import FolderSortPopover from '../../../components/FolderSortPopover.vue'

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
const { createRootFolder } = useFolderOperations()
const {
  searchQuery,
  sortField,
  sortOrder,
  setSort,
  filterAndSort
} = useFolderTreeFilter()

const showSearch = ref(false)
const disableTransition = ref(true)
onMounted(() => requestAnimationFrame(() => requestAnimationFrame(() => (disableTransition.value = false))))

// 过滤排序后的根文件夹列表
const filteredFolders = computed(() => filterAndSort(folderStore.folders))

const toggleExpand = (id: string) => {
  const copy = new Set(props.expandedFolders)
  copy.has(id) ? copy.delete(id) : copy.add(id)
  emit('update:expandedFolders', copy)
}

const handleSelectFolder = (id: string) => {
  emit('select-folder', id)
}

const handleAddRootFolder = () => {
  createRootFolder()
}
</script>

<template>
  <div class="folder-panel">
    <div class="folder-panel__header">
      <div class="title-row">
        <h3 class="folder-panel__title">文库</h3>
        <div class="title-actions">
          <el-icon class="action-icon" @click="handleAddRootFolder" title="新建文件夹">
            <Plus />
          </el-icon>
          <FolderSortPopover
            :sort-field="sortField"
            :sort-order="sortOrder"
            @update:sort-field="(f) => setSort(f, sortOrder)"
            @update:sort-order="(o) => setSort(sortField, o)"
          />
        </div>
      </div>
    </div>

    <!-- 导航区：最近论文 / 全部论文 -->
    <div class="nav-list">
      <div
        class="nav-item"
        :class="{ active: activeFolderId === 'recent' }"
        @click="handleSelectFolder('recent')"
      >
        <span class="nav-item-icon">🕐</span>
        <span class="nav-item-label">最近论文</span>
      </div>
      <div
        class="nav-item"
        :class="{ active: activeFolderId === 'all' }"
        @click="handleSelectFolder('all')"
      >
        <span class="nav-item-icon">📂</span>
        <span class="nav-item-label">全部论文</span>
      </div>
    </div>

    <!-- 文件夹区域（始终显示） -->
    <div class="folder-section">
      <div class="folder-section-title">文件夹</div>
      <div v-if="showSearch" class="search-bar-wrapper">
        <FolderSearchBar v-model="searchQuery" />
      </div>
      <div class="folder-list">
        <FolderItem
          v-for="folder in filteredFolders"
          :key="folder.id"
          :folder="folder"
          :depth="0"
          :selected-folder-id="activeFolderId"
          :expanded-folders="expandedFolders"
          :show-actions="true"
          @select-folder="handleSelectFolder"
          @toggle-expand="toggleExpand"
        />
        <div v-if="filteredFolders.length === 0" class="empty-hint">
          暂无文件夹
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.folder-panel {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  width: 100%;
}

.folder-panel__header {
  padding: 16px 16px 8px;
  border-bottom: 1px solid var(--line-soft);
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.folder-panel__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.title-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.action-icon {
  font-size: 1.15rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s;
}

.action-icon:hover {
  background: var(--bg-soft);
  color: var(--text-primary);
}

/* ── 导航区 ── */
.nav-list {
  padding: 8px 12px 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.88rem;
  color: var(--text-primary);
}

.nav-item:hover {
  background: var(--bg-soft);
}

.nav-item.active {
  background: var(--brand-soft, rgba(79, 70, 229, 0.1));
  color: var(--brand);
  font-weight: 600;
}

.nav-item-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.nav-item-label {
  flex: 1;
}

/* ── 文件夹区域 ── */
.folder-section {
  padding: 4px 12px 16px;
  flex: 1;
  overflow-y: auto;
}

.folder-section-title {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-secondary, #6b7280);
  padding: 6px 4px 4px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.search-bar-wrapper {
  margin-bottom: 6px;
}

.folder-list {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.empty-hint {
  text-align: center;
  padding: 20px 0;
  font-size: 0.82rem;
  color: var(--text-secondary);
}
</style>
