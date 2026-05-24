<script setup lang="ts">
import { ref, watch } from 'vue'
import { DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import { useFolderStore } from '../../store/folder'
import LibraryFolderTree from '../library/folder/LibraryFolderTree.vue'
import GraphPanel from './GraphPanel.vue'

const folderStore = useFolderStore()
const expandedFolders = ref<Set<string>>(new Set())

// 侧边栏折叠状态
const isSidebarCollapsed = ref(false)

// 切换折叠状态
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

// 监听侧边栏折叠状态变化，触发图谱重绘
watch(isSidebarCollapsed, () => {
  // 等待 CSS 过渡动画完成后触发 resize
  setTimeout(() => {
    // 通过自定义事件通知 GraphPanel 重新调整大小
    window.dispatchEvent(new CustomEvent('sidebar-toggle'))
  }, 350) // 略大于 transition 时间（300ms）确保动画完成
})

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
    <aside 
      class="graph-sidebar" 
      :class="{ collapsed: isSidebarCollapsed }"
    >
      <LibraryFolderTree
        :active-folder-id="folderStore.currentFolderId || 'all'"
        :expanded-folders="expandedFolders"
        @select-folder="handleSelectFolder"
        @update:expanded-folders="handleUpdateExpanded"
      />
    </aside>

    <!-- 折叠/展开按钮 -->
    <button 
      class="sidebar-toggle-btn"
      :class="{ collapsed: isSidebarCollapsed }"
      @click="toggleSidebar"
      :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
    >
      <el-icon>
        <DArrowRight v-if="isSidebarCollapsed" />
        <DArrowLeft v-else />
      </el-icon>
    </button>

    <main class="graph-main">
      <GraphPanel />
    </main>
  </div>
</template>

<style scoped>
.graph-page-container {
  display: flex;
  height: 100vh;
  background: var(--bg-page, #f5f7fa);
  position: relative;
}

.graph-sidebar {
  width: 280px;
  min-width: 260px;
  max-width: 280px;
  height: 100%;
  border-right: 1px solid var(--line-soft, #e4e7ed);
  background: #fff;
  overflow-y: auto;
  padding: 10px;
  box-sizing: border-box;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.graph-sidebar.collapsed {
  width: 0;
  min-width: 0;
  max-width: 0;
  padding: 0;
  border-right: none;
  overflow: hidden;
}

/* 折叠/展开按钮 */
.sidebar-toggle-btn {
  position: absolute;
  left: 280px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: white;
  border: 1px solid var(--line-soft, #e4e7ed);
  border-left: none;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all 0.3s ease;
  z-index: 10;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.06);
}

.sidebar-toggle-btn:hover {
  background: var(--brand-soft, rgba(74, 157, 154, 0.1));
  color: var(--brand);
  box-shadow: 2px 0 12px rgba(74, 157, 154, 0.15);
}

.sidebar-toggle-btn.collapsed {
  left: 0;
}

.sidebar-toggle-btn .el-icon {
  font-size: 16px;
}

.graph-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
}
</style>