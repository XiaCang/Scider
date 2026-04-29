// composables/useFolderOperations.ts
import { h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFolderStore } from '../store/folder'
import type { Folder } from '../types/folder'

/**
 * 扁平化所有文件夹，用于下拉列表等
 */
export function getAllFolders(tree: Folder[]): Folder[] {
  let result: Folder[] = []
  for (const node of tree) {
    result.push(node)
    if (node.children) result = result.concat(getAllFolders(node.children))
  }
  return result
}

/**
 * 判断 childId 是否是 parentId 的后代
 */
export function isDescendant(tree: Folder[], parentId: string, childId: string): boolean {
  const parent = tree.find(f => f.id === parentId)
  if (!parent?.children) return false
  return parent.children.some(c => c.id === childId) || parent.children.some(c => isDescendant([c], c.id, childId))
}

export function useFolderOperations() {
  const folderStore = useFolderStore()

  // ------------------- 创建操作（需要对话框） -------------------
  async function createRootFolder() {
    let name = ''
    try {
      await ElMessageBox({
        title: '新建文件夹',
        message: h('div', { class: 'dialog-content' }, [
          h('p', { class: 'dialog-tip' }, '请输入文件夹名称：'),
          h('input', {
            class: 'dialog-input',
            value: name,
            placeholder: '文件夹名称',
            onInput: (e: Event) => (name = (e.target as HTMLInputElement).value)
          })
        ]),
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        showCancelButton: true,
        beforeClose: (action, _instance, done) => {
          if (action === 'confirm' && !name.trim()) {
            ElMessage.warning('名称不能为空')
            return
          }
          done()
        }
      })
      await folderStore.createRootFolder(name.trim(), 'current-user')
      ElMessage.success('根文件夹创建成功')
    } catch {
      // 取消
    }
  }

  async function createSubFolder(parentFolder: Folder) {
    let name = ''
    try {
      await ElMessageBox({
        title: '新建子文件夹',
        message: h('div', { class: 'dialog-content' }, [
          h('p', { class: 'dialog-tip' }, '请输入子文件夹名称：'),
          h('input', {
            class: 'dialog-input',
            value: name,
            placeholder: '子文件夹名称',
            onInput: (e: Event) => (name = (e.target as HTMLInputElement).value)
          })
        ]),
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        showCancelButton: true,
        beforeClose: (action, _instance, done) => {
          if (action === 'confirm' && !name.trim()) {
            ElMessage.warning('名称不能为空')
            return
          }
          done()
        }
      })
      await folderStore.createSubFolder(parentFolder.id, name.trim())
      ElMessage.success('子文件夹创建成功')
    } catch {}
  }

  // ------------------- 纯 store 操作（供 FolderSettingsDialog 调用） -------------------
  async function renameFolder(folderId: string, newName: string) {
    await folderStore.renameFolder(folderId, newName)
  }

  async function moveFolder(folderId: string, targetId: string) {
    await folderStore.moveFolder(folderId, targetId)
  }

  async function copyFolder(folderId: string, targetId: string) {
    await folderStore.copyFolder(folderId, targetId)
  }

  async function deleteFolder(folderId: string) {
    await folderStore.deleteFolder(folderId)
  }

  return {
    createRootFolder,
    createSubFolder,
    renameFolder,
    moveFolder,
    copyFolder,
    deleteFolder,
  }
}