/** 搜索查询参数（对齐 /api/discover/search） */
export interface SearchQuery {
  q: string
  offset: number
  limit: number
  year_from?: number | null
  year_to?: number | null
  source_type?: string | null
  sort: string
}

/** 搜索/推荐结果中的一篇论文 */
export interface SearchResult {
  id: string
  title: string
  authors: string
  venue: string
  year: number
  description: string
  relation?: string
  reason?: string
  citationCount?: number
}

/** 上下游论文 */
export interface CitationPaper {
  id: string
  title: string
  authors: string
  venue: string
  year: number
  description: string
  citationCount: number
  relation: 'upstream' | 'downstream'
}

/** Discover tab 模式 */
export type DiscoverTab = 'search' | 'citation'

/** 单篇导入请求体（对齐 /api/discover/import） */
export interface ImportRequest {
  title: string
  authors?: string | null
  abstract?: string | null
  doi?: string | null
  year?: number | null
  venue?: string | null
  user_id: string
}

/** 批量导入请求体（对齐 /api/discover/import/bulk） */
export interface BulkImportRequest {
  papers: ImportRequest[]
  user_id: string
}
