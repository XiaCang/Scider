import request from '../network/request'
import type { ApiResponse } from '../types/auth'

/** GET /api/graph/similarity — 基于向量相似度的论文图谱（节点 ≤200） */
export const fetchSimilarityGraphApi = (params?: {
  folder_id?: string | null
  max_nodes?: number
  min_similarity?: number
  top_k?: number
}) =>
  request.get<ApiResponse<SimilarityGraphPayload>>('/graph/similarity', { params })

export interface SimilarityGraphPayload {
  nodes: Array<{
    id: string
    name: string
    type: string
    category: number
    paperInfo?: Record<string, unknown>
  }>
  links: Array<{
    source: string
    target: string
    relationType: string
    label?: string
  }>
  meta: Record<string, unknown>
}
