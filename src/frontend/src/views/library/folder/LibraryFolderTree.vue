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

folderStore.loadTestData()

const disableTransition = ref(true)
onMounted(() => requestAnimationFrame(() => requestAnimationFrame(() => (disableTransition.value = false))))

const viewMode = ref<'all' | 'recent'>('all')

// 过滤排序后的根文件夹列表
const filteredFolders = computed(() => filterAndSort(folderStore.folders))

const toggleExpand = (id: string) => {
  const copy = new Set(props.expandedFolders)
  copy.has(id) ? copy.delete(id) : copy.add(id)
  emit('update:expandedFolders', copy)
}

const handleSelectFolder = (id: string) => {
  viewMode.value = 'all'
  emit('select-folder', id)
}

const handleTabClick = (tab: 'recent' | 'all') => {
  if (tab === 'all') {
    viewMode.value = 'all'
    emit('select-folder', 'all')
  } else {
    viewMode.value = 'recent'
  }
}

const handleAddRootFolder = () => {
  createRootFolder()
}
</script>

<template>
  <div class="folder-panel">
    <div class="folder-panel__header">
      <div class="title-row">
        <h3 class="folder-panel__title">文库文件夹</h3>
        <div class="title-actions">
          <el-icon class="action-icon" @click="handleAddRootFolder" title="新建根文件夹">
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
      <!-- 搜索栏（仅在全部论文视图显示） -->
      <FolderSearchBar v-if="viewMode === 'all'" v-model="searchQuery" />
    </div>

    <div class="folder-manager">
      <div v-if="viewMode === 'all'" class="folder-list">
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
      </div>
      <div v-else class="recent-placeholder">
        <p>最近论文功能即将开放</p>
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
  display: flex;
  flex-direction: column;
  padding: 16px 16px 8px;
  border-bottom: 1px solid var(--line-soft);
  background: transparent;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
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
  padding: 12px 12px 16px;
  overflow-y: auto;
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
</style>