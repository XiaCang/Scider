/** 搜索查询参数 */
export interface SearchQuery {
  keyword: string
  year: string
  venue: string
  sortBy: string
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
