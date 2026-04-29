<script setup lang="ts">
import { ref } from 'vue'
import { useFolderStore } from '../../store/folder'
import LibraryFolderTree from '../library/folder/LibraryFolderTree.vue'
import GraphPanel from './GraphPanel.vue'

const folderStore = useFolderStore()
const expandedFolders = ref<Set<string>>(new Set())

// 切换文件夹时同步 store
const handleSelectFolder = (id: string) => {
  if (id === 'all') {
    folderStore.setCurrentFolder(null)
  } else {
    folderStore.setCurrentFolder(id)
  }
}

const handleUpdateExpanded = (value: Set<string>) => {
  expandedFolders.value = value
}
</script>

<template>
  <div class="graph-page-container">
    <aside class="graph-sidebar">
      <LibraryFolderTree
        :active-folder-id="folderStore.currentFolderId || 'all'"
        :expanded-folders="expandedFolders"
        @select-folder="handleSelectFolder"
        @update:expanded-folders="handleUpdateExpanded"
      />
    </aside>

    <main class="graph-main">
      <GraphPanel />
    </main>
  </div>
</template>

<style scoped>
.graph-page-container {
  display: flex;
  height: 100%;
  background: var(--bg-page, #f5f7fa);
}

.graph-sidebar {
  width: 280px;
  min-width: 260px;
  border-right: 1px solid var(--line-soft, #e4e7ed);
  background: #fff;
  overflow-y: auto;
  padding: 10px;
}

.graph-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 10px;
}
</style>