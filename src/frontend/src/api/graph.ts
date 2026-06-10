// src/api/graph.ts
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

// 自定义节点 CRUD 
export interface GraphNodeData {
  id: string
  name: string
  node_type: string      // 'paper' | 'custom' | 'background' | ...
  category: number
  paper_id?: string | null
  properties?: Record<string, any>
}

export const createGraphNode = (data: {
  name: string
  node_type?: string     // 默认 'custom'
  category?: number      // 默认 0
  paper_id?: string | null
  properties?: Record<string, any>
}) =>
  request.post<ApiResponse<GraphNodeData>>('/graph/edit/nodes', data)

export const updateGraphNode = (nodeId: string, data: {
  name?: string
  node_type?: string
  category?: number
  properties?: Record<string, any>
}) =>
  request.patch<ApiResponse<GraphNodeData>>(`/graph/edit/nodes/${nodeId}`, data)

export const deleteGraphNode = (nodeId: string) =>
  request.delete<ApiResponse<{ deleted_node_id: string; deleted_edges_count: number }>>(`/graph/edit/nodes/${nodeId}`)

// 自定义边 CRUD 
export interface GraphEdgeData {
  id: string
  source_id: string
  target_id: string
  relation_type: string   // 'extends' | 'applies' | 'compares' | 'related' | 'custom'
  label?: string | null
  properties?: Record<string, any>
}

export const createGraphEdge = (data: {
  source_id: string
  target_id: string
  relation_type?: string   // 默认 'related'
  label?: string
  properties?: Record<string, any>
}) =>
  request.post<ApiResponse<GraphEdgeData>>('/graph/edit/edges', data)


export const updateGraphEdge = (edgeId: string, data: {
  relation_type?: string
  label?: string
  properties?: Record<string, any>
}) =>
  request.patch<ApiResponse<GraphEdgeData>>(`/graph/edit/edges/${edgeId}`, data)

export const deleteGraphEdge = (edgeId: string) =>
  request.delete<ApiResponse<{ deleted_edge_id: string }>>(`/graph/edit/edges/${edgeId}`)

// 获取当前用户全部自定义图谱（节点+边）
export interface CustomGraphPayload {
  nodes: Array<{
    id: string
    name: string
    type: string        // 对应 node_type
    category: number
    paperInfo?: {
      id?: string
      properties?: Record<string, any>
    }
  }>
  links: Array<{
    source: string
    target: string
    relationType: string
    label?: string
    properties?: Record<string, any>
  }>
  meta: {
    node_count: number
    edge_count: number
  }
}

export const getCustomGraph = () =>
  request.get<ApiResponse<CustomGraphPayload>>('/graph/edit/graph')