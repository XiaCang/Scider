import request from '../network/request'

// ==================== 论文相关接口 ====================

export interface LibraryPaper {
  id: string
  title: string
  authors: string
  year: number
  status: 'Processing' | 'Completed' | 'Awaiting Review'
  source: string
  keyPoints: string[]
}

/**
 * 获取论文列表
 */
export const fetchLibraryApi = () => request.get('/papers')

/**
 * 保存论文关键点
 */
export const saveKeyPointsApi = (paperId: string, keyPoints: string[]) =>
  request.patch(`/papers/${paperId}/key-points`, { keyPoints })

// ==================== 文件夹相关接口 ====================

export interface Folder {
  id: string
  name: string
  user_id?: string
  paperIds: string[]
  children?: Folder[]
  created_at?: string
}

/**
 * 获取用户的文件夹树（支持无限层级）
 */
export const fetchFoldersApi = () => request.get<Folder[]>('/folders')

/**
 * 创建根文件夹
 */
export const createFolderApi = (data: { name: string; user_id: string }) =>
  request.post<Folder>('/folders', data)

/**
 * 创建子文件夹
 */
export const createSubFolderApi = (parentId: string, data: { name: string }) =>
  request.post<Folder>(`/folders/${parentId}/subfolders`, data)

/**
 * 更新文件夹名称
 */
export const updateFolderApi = (folderId: string, data: { name: string }) =>
  request.patch<Folder>(`/folders/${folderId}`, data)

/**
 * 删除文件夹（级联删除子文件夹）
 */
export const deleteFolderApi = (folderId: string) =>
  request.delete(`/folders/${folderId}`)

/**
 * 移动文件夹到新的父文件夹
 * @param folderId 要移动的文件夹ID
 * @param newParentId 新的父文件夹ID（null表示移动到根级别）
 */
export const moveFolderApi = (folderId: string, newParentId: string | null) =>
  request.patch(`/folders/${folderId}/move`, { parent_id: newParentId })

/**
 * 复制文件夹及其子文件夹
 * @param folderId 要复制的文件夹ID
 * @param targetParentId 目标父文件夹ID（null表示复制到根级别）
 */
export const copyFolderApi = (folderId: string, targetParentId: string | null) =>
  request.post<Folder>(`/folders/${folderId}/copy`, { target_parent_id: targetParentId })

// ==================== 论文与文件夹关联接口 ====================

/**
 * 将论文添加到文件夹
 */
export const addPaperToFolderApi = (folderId: string, paperId: string) =>
  request.post(`/folders/${folderId}/papers`, { paper_id: paperId })

/**
 * 从文件夹移除论文
 */
export const removePaperFromFolderApi = (folderId: string, paperId: string) =>
  request.delete(`/folders/${folderId}/papers/${paperId}`)

/**
 * 批量添加论文到文件夹
 */
export const batchAddPapersToFolderApi = (folderId: string, paperIds: string[]) =>
  request.post(`/folders/${folderId}/papers/batch`, { paper_ids: paperIds })

/**
 * 获取文件夹内的论文列表
 */
export const fetchFolderPapersApi = (folderId: string) =>
  request.get<LibraryPaper[]>(`/folders/${folderId}/papers`)

/**
 * 移动论文到其他文件夹
 */
export const movePaperToFolderApi = (paperId: string, folderId: string | null) =>
  request.patch(`/papers/${paperId}/folder`, { folder_id: folderId })
