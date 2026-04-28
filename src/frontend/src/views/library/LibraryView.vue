<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LibraryFolderTree from './folder/LibraryFolderTree.vue'
import { useFolderStore } from '../../store/folder'

const route = useRoute()
const router = useRouter()
const folderStore = useFolderStore()

const folderPanelVisible = ref(true)
const expandedFolders = ref<Set<string>>(new Set())

const activeFolderId = computed(() => (route.params.folderId as string) || 'all')

const handleSelectFolder = (folderId: string) => {
  folderStore.setCurrentFolder(folderId === 'all' ? null : folderId)
  router.push({ name: 'library-folder', params: { folderId } })
}
</script>

<template>
  <LibraryFolderTree
    :active-folder-id="activeFolderId"
    v-model:expanded-folders="expandedFolders"
    @select-folder="handleSelectFolder"
  >
    <router-view />
  </LibraryFolderTree>
</template>
<style scoped>
.library-layout {
  position: relative;
  min-height: calc(100vh - 60px);
}

.load-test-btn {
  position: absolute;
  top: 12px;
  right: 20px;
  z-index: 10;
  padding: 0.4rem 1rem;
  border-radius: 8px;
  border: 1px dashed var(--brand);
  background: rgba(var(--brand-rgb), 0.05);
  color: var(--brand);
  font-size: 0.9rem;
  cursor: pointer;
}
</style>