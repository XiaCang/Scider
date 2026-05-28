import { describe, it, expect } from 'vitest'
import { useFolderTreeFilter } from './useFolderTreeFilter'
import type { Folder } from '../types/folder'

function createFolders(): Folder[] {
  return [
    { id: '1', name: '机器学习', created_at: '2024-03-01T00:00:00Z' },
    { id: '2', name: '深度学习', created_at: '2024-01-15T00:00:00Z' },
    { id: '3', name: '自然语言处理', created_at: '2024-02-20T00:00:00Z' },
    { id: '4', name: '计算机视觉', created_at: '2024-04-10T00:00:00Z' },
  ]
}

describe('useFolderTreeFilter', () => {
  describe('setSearch / setSort', () => {
    it('setSearch 应更新 searchQuery', () => {
      const filter = useFolderTreeFilter()
      filter.setSearch('机器')
      expect(filter.searchQuery.value).toBe('机器')
    })

    it('setSort 应更新 sortField 和 sortOrder', () => {
      const filter = useFolderTreeFilter()
      filter.setSort('created_at', 'desc')
      expect(filter.sortField.value).toBe('created_at')
      expect(filter.sortOrder.value).toBe('desc')
    })
  })

  describe('filterAndSort', () => {
    it('无搜索条件和排序时应原样返回所有文件夹', () => {
      const filter = useFolderTreeFilter()
      const folders = createFolders()
      const result = filter.filterAndSort(folders)
      expect(result).toHaveLength(4)
    })

    it('应按名称搜索过滤', () => {
      const filter = useFolderTreeFilter()
      filter.setSearch('机器')
      const result = filter.filterAndSort(createFolders())
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('机器学习')
    })

    it('搜索应不区分大小写', () => {
      const filter = useFolderTreeFilter()
      filter.setSearch('语言')
      const result = filter.filterAndSort(createFolders())
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('自然语言处理')
    })

    it('无匹配关键词时应返回空数组', () => {
      const filter = useFolderTreeFilter()
      filter.setSearch('不存在的文件夹')
      const result = filter.filterAndSort(createFolders())
      expect(result).toHaveLength(0)
    })

    it('空搜索词应返回全部', () => {
      const filter = useFolderTreeFilter()
      filter.setSearch('  ')
      const result = filter.filterAndSort(createFolders())
      expect(result).toHaveLength(4)
    })

    it('应按名称升序排序（默认）', () => {
      const filter = useFolderTreeFilter()
      const result = filter.filterAndSort(createFolders())
      const names = result.map(f => f.name)
      expect(names).toEqual([...names].sort((a, b) => a.localeCompare(b)))
    })

    it('应按名称降序排序', () => {
      const filter = useFolderTreeFilter()
      filter.setSort('name', 'desc')
      const result = filter.filterAndSort(createFolders())
      const names = result.map(f => f.name)
      expect(names).toEqual([...names].sort((a, b) => b.localeCompare(a)))
    })

    it('应按创建时间升序排序', () => {
      const filter = useFolderTreeFilter()
      filter.setSort('created_at', 'asc')
      const result = filter.filterAndSort(createFolders())
      expect(result[0].id).toBe('2') // 2024-01-15 最早
      expect(result[3].id).toBe('4') // 2024-04-10 最晚
    })

    it('应按创建时间降序排序', () => {
      const filter = useFolderTreeFilter()
      filter.setSort('created_at', 'desc')
      const result = filter.filterAndSort(createFolders())
      expect(result[0].id).toBe('4') // 2024-04-10 最晚
      expect(result[3].id).toBe('2') // 2024-01-15 最早
    })
  })
})
