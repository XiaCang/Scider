import { describe, it, expect } from 'vitest'
import { getAllFolders, isDescendant } from './useFolderOperations'
import type { Folder } from '../types/folder'

const tree: Folder[] = [
  {
    id: '1',
    name: '根文件夹',
    created_at: '2024-01-01T00:00:00Z',
    children: [
      {
        id: '1-1',
        name: '子文件夹 A',
        created_at: '2024-01-02T00:00:00Z',
        children: [
          {
            id: '1-1-1',
            name: '子子文件夹',
            created_at: '2024-01-03T00:00:00Z',
          },
        ],
      },
      {
        id: '1-2',
        name: '子文件夹 B',
        created_at: '2024-01-04T00:00:00Z',
      },
    ],
  },
  {
    id: '2',
    name: '另一个根文件夹',
    created_at: '2024-01-05T00:00:00Z',
  },
]

describe('getAllFolders', () => {
  it('应扁平化返回所有文件夹（含嵌套）', () => {
    const all = getAllFolders(tree)
    expect(all).toHaveLength(5)
    expect(all.map(f => f.id)).toEqual(['1', '1-1', '1-1-1', '1-2', '2'])
  })

  it('空树应返回空数组', () => {
    expect(getAllFolders([])).toHaveLength(0)
  })
})

describe('isDescendant', () => {
  it('子文件夹 A 应是根文件夹的后代', () => {
    expect(isDescendant(tree, '1', '1-1')).toBe(true)
  })

  it('子子文件夹应是根文件夹的后代', () => {
    expect(isDescendant(tree, '1', '1-1-1')).toBe(true)
  })

  it('另一个根文件夹不应是根文件夹 1 的后代', () => {
    expect(isDescendant(tree, '1', '2')).toBe(false)
  })

  it('根文件夹不应是自身的后代', () => {
    expect(isDescendant(tree, '1', '1')).toBe(false)
  })

  it('不存在的 parentId 应返回 false', () => {
    expect(isDescendant(tree, 'not-exists', '1-1')).toBe(false)
  })
})
