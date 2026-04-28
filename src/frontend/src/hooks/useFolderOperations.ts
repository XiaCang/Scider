// composables/useFolderOperations.ts
import { h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFolderStore } from '@/stores/folder'
import type { Folder } from '@/types/folder'

/**
 * 文件夹操作逻辑（仅负责新建操作弹窗，其余操作由 FolderSettingsDialog 承担）
 */
export function useFolderOperations() {
  const folderStore = useFolderStore()

  /**
   * 新建根文件夹（通常在"全部论文"视图下点击"+"触发）
   */
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
            onInput: (e: Event) => (name = (e.target as HTMLInputElement).value),
          }),
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
        },
      })
      // 根文件夹用户ID暂时写死，正式项目应从 auth store 获取
      await folderStore.createRootFolder(name.trim(), 'current-user')
      ElMessage.success('根文件夹创建成功')
    } catch {
      // 取消操作
    }
  }

  /**
   * 新建子文件夹
   * @param parentFolder 父文件夹对象，将自动作为“移动到”的目标
   */
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
            onInput: (e: Event) => (name = (e.target as HTMLInputElement).value),
          }),
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
        },
      })
      await folderStore.createSubFolder(parentFolder.id, name.trim())
      ElMessage.success('子文件夹创建成功')
    } catch {
      // 取消操作
    }
  }


  return {
    createRootFolder,
    createSubFolder
  }
}