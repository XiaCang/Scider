import request from '../network/request'
import type { ApiResponse } from '../types/auth'
import type { ImportRequest, BulkImportRequest } from '../discover/types'

/** GET /api/discover/search — 检索论文 */
export const searchPapersApi = (params: {
  q: string
  offset?: number
  limit?: number
  year_from?: number | null
  year_to?: number | null
  source_type?: string | null
  sort?: string
}) =>
  request.get<ApiResponse<unknown>>('/api/discover/search', { params })

/** 获取推荐（接口未纳入 api.json，保留兼容） */
export const fetchRecommendationsApi = (direction?: string) =>
  request.get('/discover/recommendations', { params: { direction } })

/** GET /api/discover/references/{semantic_id} — 参考文献（上游） */
export const fetchUpstreamPapersApi = (semanticId: string, userId: string) =>
  request.get<ApiResponse<unknown>>(`/api/discover/references/${semanticId}`, { params: { user_id: userId } })

/** GET /api/discover/citations/{semantic_id} — 引证文献（下游） */
export const fetchDownstreamPapersApi = (semanticId: string, userId: string) =>
  request.get<ApiResponse<unknown>>(`/api/discover/citations/${semanticId}`, { params: { user_id: userId } })

/** 获取论文的完整引用图谱（接口未纳入 api.json，保留兼容） */
export const fetchCitationGraphApi = (paperId: string) =>
  request.get('/discover/citations', { params: { paper_id: paperId } })

/** POST /api/discover/import — 单篇导入 */
export const importPaperApi = (data: ImportRequest) =>
  request.post<ApiResponse<unknown>>('/api/discover/import', data)

/** POST /api/discover/import/bulk — 批量导入 */
export const bulkImportPapersApi = (data: BulkImportRequest) =>
  request.post<ApiResponse<unknown>>('/api/discover/import/bulk', data)
