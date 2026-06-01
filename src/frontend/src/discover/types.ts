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
  /** Semantic Scholar 论文 ID */
  semantic_id?: string
  /** 引用次数 */
  citation_count?: number
  /** 来源类型：conference | journal | arXiv */
  source_type?: string
  /** 开放获取 PDF 链接 */
  pdf_url?: string
  /** 推荐理由（仅推荐接口有） */
  reason?: string
  /** 摘要简介（兼容旧推荐接口） */
  description?: string
  /** 完整摘要 */
  abstract?: string
  /** DOI */
  doi?: string
  /** 是否已在用户文库中 */
  in_library?: boolean
}

/** 上下游论文 */
export interface CitationPaper {
  id: string
  title: string
  authors: string
  venue: string
  year: number
  /** Semantic Scholar 论文 ID */
  semantic_id?: string
  /** 引用次数 */
  citation_count: number
  /** 该论文是否已在用户文库中 */
  in_library?: boolean
  /** 摘要简介（兼容旧数据） */
  description?: string
  /** 完整摘要 */
  abstract?: string
  /** DOI */
  doi?: string
  /** 开放获取 PDF 链接 */
  pdf_url?: string
}

/** Discover tab 模式 */
export type DiscoverTab = 'search' | 'citation'

/** 搜索 API 返回的完整响应 data 结构 */
export interface SearchResponseData {
  total: number
  offset: number
  limit: number
  data: SearchResult[]
}

/** 参考文献/引证文献 API 返回的完整响应 data 结构 */
export interface CitationResponseData {
  data: CitationPaper[]
}

/** 单篇导入请求体（对齐 /api/discover/import） */
export interface ImportRequest {
  title: string
  authors?: string | null
  abstract?: string | null
  doi?: string | null
  year?: number | null
  venue?: string | null
  pdf_url?: string | null
}

/** 批量导入请求体（对齐 /api/discover/import/bulk） */
export interface BulkImportRequest {
  papers: ImportRequest[]
}
