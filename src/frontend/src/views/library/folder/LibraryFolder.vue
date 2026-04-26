<script setup lang="ts">
import { ArrowRight, FolderAdd, Folder } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, ElSelect, ElOption } from 'element-plus'
import { computed, h, ref, onMounted } from 'vue'
import FolderItem from './FolderItem.vue'

interface LibraryFolder {
  id: string
  name: string
  paperIds: string[]
  children?: LibraryFolder[]
}

interface Props {
  folders: LibraryFolder[]
  selectedFolderId: string
  expandedFolders: Set<string>
  folderPanelVisible: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:selectedFolderId': [value: string]
  'update:expandedFolders': [value: Set<string>]
  'update:folderPanelVisible': [value: boolean]
  'create-folder': []
  'create-root-folder': [folder: LibraryFolder]
  'edit-folder': [folder: LibraryFolder]
  'delete-folder': [folder: LibraryFolder]
}>()

// 控制是否禁用过渡动画（用于防止首次挂载时的位移闪烁）
const disableTransition = ref(true)

// 获取所有文件夹（扁平化）用于移动/复制操作
const getAllFolders = (folders: LibraryFolder[]): LibraryFolder[] => {
  let result: LibraryFolder[] = [...folders]
  for (const f of folders) {
    if (f.children) {
      result = result.concat(getAllFolders(f.children))
    }
  }
  return result
}

const allFolders = computed(() => getAllFolders(props.folders))

const handleSelectFolder = (folderId: string) => {
  emit('update:selectedFolderId', folderId)
}

const toggleFolderExpand = (folderId: string) => {
  const newExpanded = new Set(props.expandedFolders)
  if (newExpanded.has(folderId)) {
    newExpanded.delete(folderId)
  } else {
    newExpanded.add(folderId)
  }
  emit('update:expandedFolders', newExpanded)
}

const isFolderExpanded = (folderId: string) => {
  return props.expandedFolders.has(folderId)
}

// 新建根文件夹（在"全部论文"下创建一级文件夹）
const handleCreateRootFolder = async () => {
  let folderName = ''
  
  try {
    await ElMessageBox({
      title: '新建文件夹',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip' }, '请输入文件夹名称：'),
        h('input', {
          class: 'dialog-input',
          value: folderName,
          placeholder: '文件夹名称',
          onInput: (e: Event) => { folderName = (e.target as HTMLInputElement).value }
        })
      ]),
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm') {
          if (!folderName.trim()) {
            ElMessage.warning('文件夹名称不能为空')
            return
          }
          done()
        } else {
          done()
        }
      }
    })
    
    const newFolder: LibraryFolder = {
      id: `folder-${Date.now()}`,
      name: folderName.trim(),
      paperIds: [],
    }
    
    emit('create-root-folder', newFolder)
    ElMessage.success('文件夹创建成功')
  } catch {
    // 用户取消操作
  }
}

// 处理子文件夹创建
const handleCreateSubFolder = async (parentFolder: LibraryFolder) => {
  let folderName = ''
  
  try {
    await ElMessageBox({
      title: '新建子文件夹',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip' }, '请输入子文件夹名称：'),
        h('input', {
          class: 'dialog-input',
          value: folderName,
          placeholder: '子文件夹名称',
          onInput: (e: Event) => { folderName = (e.target as HTMLInputElement).value }
        })
      ]),
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm') {
          if (!folderName.trim()) {
            ElMessage.warning('文件夹名称不能为空')
            return
          }
          done()
        } else {
          done()
        }
      }
    })
    
    const newSubFolder: LibraryFolder = {
      id: `folder-${Date.now()}`,
      name: folderName.trim(),
      paperIds: [],
    }
    
    if (!parentFolder.children) {
      parentFolder.children = []
    }
    parentFolder.children.push(newSubFolder)
    
    // 自动展开父文件夹
    const newExpanded = new Set(props.expandedFolders)
    newExpanded.add(parentFolder.id)
    emit('update:expandedFolders', newExpanded)
    
    ElMessage.success('子文件夹创建成功')
  } catch {
    // 用户取消操作
  }
}

// 重命名文件夹
const handleRenameFolder = async (folder: LibraryFolder) => {
  let newName = folder.name
  
  try {
    await ElMessageBox({
      title: '重命名文件夹',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip' }, '请输入新的文件夹名称：'),
        h('input', {
          class: 'dialog-input',
          value: newName,
          placeholder: '文件夹名称',
          onInput: (e: Event) => { newName = (e.target as HTMLInputElement).value }
        })
      ]),
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm') {
          if (!newName.trim()) {
            ElMessage.warning('文件夹名称不能为空')
            return
          }
          done()
        } else {
          done()
        }
      }
    })
    
    // 更新文件夹名称
    const updateFolderName = (folders: LibraryFolder[], folderId: string, name: string): boolean => {
      const target = folders.find(f => f.id === folderId)
      if (target) {
        target.name = name.trim()
        return true
      }
      for (const f of folders) {
        if (f.children && updateFolderName(f.children, folderId, name)) {
          return true
        }
      }
      return false
    }
    
    if (updateFolderName(props.folders, folder.id, newName)) {
      ElMessage.success('文件夹重命名成功')
    }
  } catch {
    // 用户取消操作
  }
}

// 判断是否是后代文件夹
const isDescendant = (folders: LibraryFolder[], parentId: string, childId: string): boolean => {
  const parent = folders.find(f => f.id === parentId)
  if (!parent || !parent.children) return false
  if (parent.children.some(c => c.id === childId)) return true
  return parent.children.some(c => isDescendant([c], c.id, childId))
}

// 移动文件夹
const handleMoveFolder = async (folder: LibraryFolder) => {
  // 获取所有可用的目标文件夹（排除当前文件夹及其子文件夹）
  const getAvailableFolders = (folders: LibraryFolder[], excludeId: string): LibraryFolder[] => {
    let result: LibraryFolder[] = []
    for (const f of folders) {
      if (f.id !== excludeId && !isDescendant(folders, f.id, excludeId)) {
        result.push(f)
        if (f.children) {
          result = result.concat(getAvailableFolders(f.children, excludeId))
        }
      }
    }
    return result
  }
  
  // 使用 getAllFolders 获取所有层级的文件夹，然后过滤掉当前文件夹及其后代
  const allFoldersList = getAllFolders(props.folders)
  const availableFolders = allFoldersList.filter(f => 
    f.id !== folder.id && !isDescendant(props.folders, folder.id, f.id)
  )
  
  if (availableFolders.length === 0) {
    ElMessage.warning('没有可用的目标文件夹')
    return
  }
  
  let selectedTargetId = ''
  
  try {
    await ElMessageBox({
      title: '移动文件夹',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip' }, `将 "${folder.name}" 移动到：`),
        h(ElSelect, {
          modelValue: selectedTargetId,
          'onUpdate:modelValue': (val: string) => { selectedTargetId = val },
          placeholder: '选择目标文件夹',
          class: 'folder-select'
        }, availableFolders.map(f => 
          h(ElOption, { key: f.id, label: f.name, value: f.id })
        ))
      ]),
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm') {
          if (!selectedTargetId) {
            ElMessage.warning('请选择目标文件夹')
            return
          }
          done()
        } else {
          done()
        }
      }
    })
    
    // 从原位置移除
    const removeFolder = (folders: LibraryFolder[], folderId: string): boolean => {
      const index = folders.findIndex(f => f.id === folderId)
      if (index > -1) {
        folders.splice(index, 1)
        return true
      }
      for (const f of folders) {
        if (f.children && removeFolder(f.children, folderId)) {
          return true
        }
      }
      return false
    }
    
    // 添加到目标位置
    const addFolderToTarget = (folders: LibraryFolder[], targetId: string, folder: LibraryFolder): boolean => {
      const target = folders.find(f => f.id === targetId)
      if (target) {
        if (!target.children) {
          target.children = []
        }
        target.children.push(folder)
        return true
      }
      for (const f of folders) {
        if (f.children && addFolderToTarget(f.children, targetId, folder)) {
          return true
        }
      }
      return false
    }
    
    const folderCopy = JSON.parse(JSON.stringify(folder))
    if (removeFolder(props.folders, folder.id)) {
      addFolderToTarget(props.folders, selectedTargetId, folderCopy)
      ElMessage.success('文件夹移动成功')
    }
  } catch {
    // 用户取消操作
  }
}

// 复制文件夹
const handleCopyFolder = async (folder: LibraryFolder) => {
  const availableFolders = getAllFolders(props.folders)
  
  if (availableFolders.length === 0) {
    ElMessage.warning('没有可用的目标文件夹')
    return
  }
  
  let selectedTargetId = ''
  
  try {
    await ElMessageBox({
      title: '复制文件夹',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip' }, `将 "${folder.name}" 复制到：`),
        h(ElSelect, {
          modelValue: selectedTargetId,
          'onUpdate:modelValue': (val: string) => { selectedTargetId = val },
          placeholder: '选择目标文件夹',
          class: 'folder-select'
        }, availableFolders.map(f => 
          h(ElOption, { key: f.id, label: f.name, value: f.id })
        ))
      ]),
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm') {
          if (!selectedTargetId) {
            ElMessage.warning('请选择目标文件夹')
            return
          }
          done()
        } else {
          done()
        }
      }
    })
    
    // 深拷贝文件夹
    const folderCopy: LibraryFolder = {
      ...JSON.parse(JSON.stringify(folder)),
      id: `folder-${Date.now()}`,
      name: `${folder.name} (副本)`,
    }
    
    // 添加到目标位置
    const addFolderToTarget = (folders: LibraryFolder[], targetId: string, folder: LibraryFolder): boolean => {
      const target = folders.find(f => f.id === targetId)
      if (target) {
        if (!target.children) {
          target.children = []
        }
        target.children.push(folder)
        return true
      }
      for (const f of folders) {
        if (f.children && addFolderToTarget(f.children, targetId, folder)) {
          return true
        }
      }
      return false
    }
    
    addFolderToTarget(props.folders, selectedTargetId, folderCopy)
    ElMessage.success('文件夹复制成功')
  } catch {
    // 用户取消操作
  }
}

// 删除文件夹
const handleDeleteFolder = async (folder: LibraryFolder) => {
  try {
    await ElMessageBox({
      title: '删除文件夹',
      message: h('div', { class: 'folder-operation-dialog' }, [
        h('p', { class: 'dialog-tip dialog-warning' }, `确定要删除文件夹 "${folder.name}" 吗？`),
        h('p', { class: 'dialog-hint' }, '此操作不可恢复，文件夹内的所有子文件夹也将被删除。')
      ]),
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      showCancelButton: true,
      customClass: 'folder-operation-message-box',
      type: 'warning'
    })
    
    // 递归删除文件夹（支持任意层级）
    const deleteFolderRecursive = (folders: LibraryFolder[], folderId: string): boolean => {
      const index = folders.findIndex(f => f.id === folderId)
      if (index > -1) {
        folders.splice(index, 1)
        return true
      }
      for (const f of folders) {
        if (f.children && deleteFolderRecursive(f.children, folderId)) {
          return true
        }
      }
      return false
    }
    
    if (deleteFolderRecursive(props.folders, folder.id)) {
      ElMessage.success('文件夹已删除')
    }
  } catch {
    // 用户取消操作
  }
}

// 组件挂载后，在下一帧启用过渡动画
onMounted(() => {
  // 使用 requestAnimationFrame 确保在浏览器完成首次渲染和布局计算后启用过渡
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      disableTransition.value = false
    })
  })
})

</script>

<template>
  <!-- 梯形触发器 - 使用 Teleport 提升到 body 层级 -->
  <Teleport to="body">
    <div 
      class="folder-panel__trigger" 
      :class="{ 
        'is-panel-visible': folderPanelVisible,
        'no-transition': disableTransition 
      }"
      @click="$emit('update:folderPanelVisible', !folderPanelVisible)"
    ></div>
    
    <!-- 文件夹管理面板 - 使用 Teleport 提升到 body 层级 -->
    <aside 
      class="folder-panel" 
      :class="{ 
        'is-visible': folderPanelVisible,
        'no-transition': disableTransition 
      }"
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
              @click="handleSelectFolder('all')"
            >
              <!-- 展开/收起图标 -->
              <el-icon 
                class="expand-icon"
                :class="{ 'is-expanded': isFolderExpanded('all') }"
                @click.stop="toggleFolderExpand('all')"
              >
                <ArrowRight />
              </el-icon>
              
              <el-icon><Folder /></el-icon>
              <span class="folder-name">全部论文</span>
              
              <!-- 详情按钮 -->
              <el-icon 
                class="more-icon"
                @click.stop="handleCreateRootFolder"
              >
                <FolderAdd />
              </el-icon>
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
              @select-folder="handleSelectFolder"
              @toggle-expand="toggleFolderExpand"
              @create-sub-folder="handleCreateSubFolder"
              @rename-folder="handleRenameFolder"
              @move-folder="handleMoveFolder"
              @copy-folder="handleCopyFolder"
              @delete-folder="handleDeleteFolder"
            />
          </template>
        </div>
      </div>
    </aside>
  </Teleport>
  
  <!-- 保留原有的 library-page 结构用于主内容区 -->
  <section class="library-page">
    <!-- 主内容区域将由父组件或其他插槽提供 -->
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

/* 文件夹面板样式 - 使用 fixed 定位相对于视口 */
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

/* 禁用过渡动画的类 */
.folder-panel.no-transition {
  transition: none !important;
}
 
.folder-panel.is-visible {
  transform: translateX(0);
}

/* 梯形触发器 - 使用 fixed 定位相对于视口 */
.folder-panel__trigger {
  position: fixed;
  left: 0; /* 基准位置：屏幕左边缘 */
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

/* 禁用过渡动画的类 */
.folder-panel__trigger.no-transition {
  transition: none !important;
}

.folder-panel__trigger:hover {
  background: #2a4d73;
}

/* 当面板可见时，触发器移至面板右边缘 (280px) */
.folder-panel__trigger.is-panel-visible {
  transform: translateX(280px);
}

.folder-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--line-soft);
  background: var(--bg-soft);
}

.folder-panel__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.folder-manager {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem;
}

.folder-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

/* 全部论文项的样式 */
.level-0 {
  margin-left: 0;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.level-0:hover {
  background: var(--bg-soft);
  border-color: var(--line-soft);
}

.level-0.active {
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

.level-0:hover .more-icon {
  opacity: 1;
}

.more-icon:hover {
  background: var(--bg-soft);
  color: var(--text-primary);
}
</style>

<style>
/* 文件夹操作弹窗全局样式 */
.folder-operation-message-box {
  border-radius: 12px;
  overflow: hidden;
}

.folder-operation-message-box .el-message-box__header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--line-soft);
}

.folder-operation-message-box .el-message-box__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.folder-operation-message-box .el-message-box__content {
  padding: 24px;
}

.folder-operation-message-box .el-message-box__btns {
  padding: 16px 24px 24px;
}

.folder-operation-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-tip {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 文件夹选择器样式 - 全局样式以确保正确应用 */
.folder-select {
  width: 100%;
}

.folder-select .el-input__wrapper,
.folder-select .el-select__wrapper {
  background-color: #ffffff !important;
  box-shadow: none !important;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  transition: all 0.2s;
}

.folder-select .el-input__wrapper:hover,
.folder-select .el-select__wrapper:hover {
  box-shadow: 0 0 0 1px var(--brand-light) inset !important;
}

.folder-select .el-input__wrapper.is-focus,
.folder-select .el-select__wrapper.is-focus {
  box-shadow: 0 0 0 1px var(--brand) inset !important;
}

.folder-select .el-input__inner {
  color: var(--text-primary);
  background-color: transparent;
}

.folder-select .el-input__suffix {
  color: var(--text-secondary);
}

.folder-select .el-input__suffix-inner {
  color: var(--text-secondary);
}

/* 下拉选项样式 */
.folder-select .el-select-dropdown {
  background-color: #ffffff;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.folder-select .el-select-dropdown__item {
  color: var(--text-primary);
}

.folder-select .el-select-dropdown__item.hover,
.folder-select .el-select-dropdown__item:hover {
  background-color: var(--bg-secondary);
}

.folder-select .el-select-dropdown__item.selected {
  color: var(--brand);
  font-weight: 600;
}

.dialog-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary);
  background: white;
  transition: all 0.2s;
  outline: none;
}

.dialog-input:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.dialog-input::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
}

.dialog-warning {
  color: var(--danger);
  font-weight: 500;
}

.dialog-hint {
  margin: 8px 0 0 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
</style>
