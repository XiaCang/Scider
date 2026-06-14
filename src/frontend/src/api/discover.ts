import request from '../network/request'
import type { ApiResponse } from '../types/auth'
import type {
  ImportRequest,
  BulkImportRequest,
  SearchResponseData,
  CitationResponseData,
} from '../discover/types'

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
  request.get<ApiResponse<SearchResponseData>>('/discover/search', { params })

/** 获取推荐（接口未纳入 api.json，保留兼容） */
export const fetchRecommendationsApi = (direction?: string) =>
  request.get('/discover/recommendations', { params: { direction } })

/** GET /api/discover/references/{semantic_id} — 参考文献（上游） */
export const fetchUpstreamPapersApi = (semanticId: string) =>
  request.get<ApiResponse<CitationResponseData>>(`/discover/references/${semanticId}`)

/** GET /api/discover/citations/{semantic_id} — 引证文献（下游） */
export const fetchDownstreamPapersApi = (semanticId: string) =>
  request.get<ApiResponse<CitationResponseData>>(`/discover/citations/${semanticId}`)

/** GET /api/discover/references/by-paper/{paper_id} — 通过本地论文 ID 获取参考文献（上游） */
export const fetchUpstreamByPaperApi = (paperId: string) =>
  request.get<ApiResponse<CitationResponseData>>(`/discover/references/by-paper/${paperId}`, {
    timeout: 120000,
  })

/** GET /api/discover/citations/by-paper/{paper_id} — 通过本地论文 ID 获取引用文献（下游） */
export const fetchDownstreamByPaperApi = (paperId: string) =>
  request.get<ApiResponse<CitationResponseData>>(`/discover/citations/by-paper/${paperId}`, {
    timeout: 120000,
  })

/** 获取论文的完整引用图谱（接口未纳入 api.json，保留兼容） */
export const fetchCitationGraphApi = (paperId: string) =>
  request.get('/discover/citations', { params: { paper_id: paperId } })

/** 导入响应中的 data 字段 */
export interface ImportPaperResult {
  paper_id: string
  task_id: string
  status: string
}

/** POST /api/discover/import — 单篇导入（仅元数据，不含 PDF） */
export const importPaperApi = (data: ImportRequest) =>
  request.post<ApiResponse<ImportPaperResult>>('/discover/import', data)

/** POST /api/discover/import/bulk — 批量导入 */
export const bulkImportPapersApi = (data: BulkImportRequest) =>
  request.post<ApiResponse<unknown>>('/discover/import/bulk', data)

/** GET /api/discover/pdf-proxy — 代理下载外部 PDF */
export const downloadDiscoverPdfApi = (pdfUrl: string, arxivId?: string) =>
  request.get('/discover/pdf-proxy', {
    params: { pdf_url: pdfUrl, arxiv_id: arxivId || undefined },
    responseType: 'blob',
    timeout: 120000,
  })
