import request from '../network/request'

import type {LibraryPaper, PaperKeyPoints, PaperNote, NoteListItem, NoteUploadImageResponse, PaperPdfInfo } from '../types/library'
import type { Folder } from '../types/folder'
import type { ApiResponse } from '../types/auth'

/**
 * 获取论文列表
 */
export const fetchLibraryApi = () => request.get('/papers')

/**
 * 获取单个论文详情
 */
export const fetchPaperByIdApi = (paperId: string) =>
  request.get<ApiResponse<LibraryPaper>>(`/papers/${paperId}`)

/**
 * 保存论文关键点
 */
export const saveKeyPointsApi = (paperId: string, keyPoints: PaperKeyPoints) =>
  request.patch(`/papers/${paperId}/key-points`, { keyPoints })

/**
 * 删除论文
 */
export const deletePaperApi = (paperId: string) =>
  request.delete(`/papers/${paperId}`)

/**
 * 获取文件夹列表
 */
export const fetchFoldersApi = () => request.get<ApiResponse<Folder[]>>('/folders/')

/**
 * 创建文件夹
 */
export const createFolderApi = (data: { name: string }) =>
  request.post<ApiResponse<Folder>>('/folders/', data)

/**
 * 获取文件夹详情
 */
export const fetchFolderDetailApi = (folderId: string) =>
  request.get<ApiResponse<Folder>>(`/folders/${folderId}`)

/**
 * 创建子文件夹
 */
export const createSubFolderApi = (parentId: string, data: { name: string }) =>
  request.post<Folder>(`/folders/${parentId}/subfolders`, data)

/**
 * 重命名文件夹
 */
export const updateFolderApi = (folderId: string, data: { name: string }) =>
  request.patch(`/folders/${folderId}`, data)

/**
 * 删除文件夹（删除后文件夹中的论文自动解绑，论文本身不被删除）
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

// ==================== 论文上传 ====================

/** 上传响应中的 data 字段 */
export interface UploadPaperResponse {
  paper_id: string
  filename: string
  file_size: number
  md5: string
  status: string
  task_id: string
}

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

// ==================== PDF预览相关接口 ====================

/**
 * 获取论文PDF信息
 */
export const fetchPaperPdfInfoApi = (paperId: string) =>
  request.get<PaperPdfInfo>(`/papers/${paperId}/pdf-info`)

/**
 * 获取PDF文件二进制流（用于浏览器内预览，避免IDM等下载工具拦截）
 */
export const fetchPaperPdfFileApi = (paperId: string) =>
  request.get(`/papers/${paperId}/pdf-file`, {
    responseType: 'blob',
  }) as Promise<Blob>

/**
 * 获取论文笔记列表（新 API：支持分页）
 */
export const fetchPaperNotesApi = (paperId: string, page = 1, pageSize = 50) =>
  request.get<ApiResponse<{ total: number; items: NoteListItem[] }>>(`/notes/`, {
    params: { paperId, page, pageSize }
  })

/**
 * 创建笔记（新 API）
 */
export const createNoteApi = (data: {
  paperId: string
  title: string
  contentHtml: string
  contentFormat: string
}) =>
  request.post<ApiResponse<PaperNote>>(`/notes/`, data)

/**
 * 获取单个笔记详情
 */
export const fetchNoteDetailApi = (noteId: string) =>
  request.get<ApiResponse<PaperNote>>(`/notes/${noteId}`)

/**
 * 更新笔记
 */
export const updateNoteApi = (noteId: string, data: {
  title: string
  contentHtml: string
  contentFormat: string
}) =>
  request.patch<ApiResponse<PaperNote>>(`/notes/${noteId}`, data)

/**
 * 笔记图片上传
 */
export const uploadNoteImageApi = (
  paperId: string,
  noteId: string,
  file: File
) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<ApiResponse<NoteUploadImageResponse>>(
    `/notes/uploads?paperId=${paperId}&noteId=${noteId}`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
}

// ==================== PDF上传相关接口 ====================

/**
 * 上传PDF论文
 */
export interface UploadPaperResponse {
  paper_id: string
  filename: string
  file_size: number
  md5: string
  status: string
  task_id: string
}

export const uploadPaperApi = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return request.post<ApiResponse<UploadPaperResponse>>(
    '/papers/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
}

// ==================== PDF全文搜索相关接口 ====================

/**
 * 搜索结果项
 */
export interface SearchResultItem {
  page_number: number
  content: string
  score: number
  highlights: string[]
}

/**
 * 搜索结果
 */
export interface SearchResponse {
  keyword: string
  total_results: number
  results: SearchResultItem[]
}

/**
 * 在论文中搜索关键词
 */
export const searchInPaperApi = (
  paperId: string,
  data: {
    keyword: string
    page_number?: number
    limit?: number
  }
) =>
  request.post<ApiResponse<SearchResponse>>(`/papers/${paperId}/search`, data)
