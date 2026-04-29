<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LibraryFolderTree from './folder/LibraryFolderTree.vue'
import { useFolderStore } from '../../store/folder'

const route = useRoute()
const router = useRouter()
const folderStore = useFolderStore()

const expandedFolders = ref<Set<string>>(new Set())

const activeFolderId = computed(() => (route.params.folderId as string) || 'all')

const handleSelectFolder = (folderId: string) => {
  folderStore.setCurrentFolder(folderId === 'all' ? null : folderId)
  router.push({ name: 'library-folder', params: { folderId } })
}

// 分割栏状态
const leftWidth = ref(280) // 左侧宽度，单位 px
const minLeftWidth = 240
const maxLeftWidth = 500
const isResizing = ref(false)

const startResize = (e: MouseEvent) => {
  isResizing.value = true
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

const onMouseMove = (e: MouseEvent) => {
  if (!isResizing.value) return
  let newWidth = e.clientX
  if (newWidth < minLeftWidth) newWidth = minLeftWidth
  if (newWidth > maxLeftWidth) newWidth = maxLeftWidth
  leftWidth.value = newWidth
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', stopResize)
}
</script>

<template>
  <div class="library-layout">
    <div class="left-panel" :style="{ width: leftWidth + 'px' }">
      <LibraryFolderTree
        :active-folder-id="activeFolderId"
        v-model:expanded-folders="expandedFolders"
        @select-folder="handleSelectFolder"
      />
    </div>
    <div class="resize-handle" @mousedown="startResize"></div>
    <div class="right-panel">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.library-layout {
  display: flex;
  position: relative;
  min-height: calc(100vh - 60px);
  width: 100%;
  overflow-x: hidden;
}

.left-panel {
  flex-shrink: 0;
  overflow-y: auto;
  height: 100vh;
  padding : 12px;
  border-right: 1px solid var(--line-soft);
}

.resize-handle {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  flex-shrink: 0;
  transition: background 0.2s;
}

.resize-handle:hover {
  background: var(--brand);
}

.right-panel {
  flex: 1;
  overflow-y: auto;
  min-width: 0; /* 防止内容溢出 */
}
</style>