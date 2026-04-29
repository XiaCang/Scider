import { ref } from 'vue'
import type { Folder } from '../types/folder'

export type SortField = 'name' | 'created_at'
export type SortOrder = 'asc' | 'desc'

export function useFolderTreeFilter() {
  const searchQuery = ref('')
  const sortField = ref<SortField>('name')
  const sortOrder = ref<SortOrder>('asc')

  const setSearch = (val: string) => {
    searchQuery.value = val
  }

  const setSort = (field: SortField, order: SortOrder) => {
    sortField.value = field
    sortOrder.value = order
  }

  const filterAndSort = (folders: Folder[]) => {
    let result = [...folders]

    // 按名称搜索（仅匹配根文件夹名称）
    if (searchQuery.value.trim()) {
      const query = searchQuery.value.trim().toLowerCase()
      result = result.filter(f => f.name.toLowerCase().includes(query))
    }

    // 排序
    result.sort((a, b) => {
      let valA: string | undefined
      let valB: string | undefined
      if (sortField.value === 'created_at') {
        valA = a.created_at
        valB = b.created_at
      } else {
        valA = a.name
        valB = b.name
      }

      if (!valA && !valB) return 0
      if (!valA) return 1
      if (!valB) return -1

      const comparison = valA.localeCompare(valB)
      return sortOrder.value === 'asc' ? comparison : -comparison
    })

    return result
  }

  return {
    searchQuery,
    sortField,
    sortOrder,
    setSearch,
    setSort,
    filterAndSort
  }
}