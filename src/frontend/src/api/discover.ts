import request from '../network/request'

/** 搜索论文 */
export const searchPapersApi = (params: { keyword?: string; year?: string; venue?: string; sort_by?: string }) =>
  request.get('/discover/search', { params })

/** 获取推荐 */
export const fetchRecommendationsApi = (direction?: string) =>
  request.get('/discover/recommendations', { params: { direction } })

/** 获取某篇论文的上游(引用)论文 */
export const fetchUpstreamPapersApi = (paperId: string) =>
  request.get(`/discover/papers/${paperId}/upstream`)

/** 获取某篇论文的下游(被引)论文 */
export const fetchDownstreamPapersApi = (paperId: string) =>
  request.get(`/discover/papers/${paperId}/downstream`)

/** 获取论文的完整引用图谱 */
export const fetchCitationGraphApi = (paperId: string) =>
  request.get('/discover/citations', { params: { paper_id: paperId } })
