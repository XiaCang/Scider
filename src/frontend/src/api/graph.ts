import request from '../network/request'
import type { ApiResponse } from '../types/auth'

// 基于向量相似度的论文图谱
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

// LLM 结构图谱
export const fetchLLMGraphApi = (params?: {
  folder_id?: string | null
  max_nodes?: number
}) =>
  request.get<ApiResponse<LLMGraphPayload>>('/graph/llm-structure', { params })

export interface LLMGraphPayload {
  nodes: Array<{
    id: string
    name: string
    type: string
    category: number  // 对应 cluster 索引
    paperInfo?: Record<string, unknown>
  }>
  links: Array<{
    source: string
    target: string
    relationType: 'extends' | 'applies' | 'compares' | 'related'
    label?: string
  }>
  clusters: Array<{
    id: string
    name: string
    description: string
    paper_ids: string[]
  }>
  meta: Record<string, unknown>
}