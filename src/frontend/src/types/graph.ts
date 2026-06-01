// src/types/graph.ts
import type { LibraryPaper } from './library'

export type NodeType = 'paper' | 'background' | 'method' | 'innovation' | 'conclusion' | 'custom'
export type RelationType = 'ownership' | 'semantic' | 'citation' | 'extends' | 'applies' | 'compares' | 'related' | 'custom'

export interface GraphNode {
  id: string
  name: string
  type: NodeType
  category: number // 对应 ECharts categories 索引
  value?: number
  symbol?: string
  paperId?: string // 关联的论文ID（仅四要素节点有）
  paperTitle?: string // 论文名称简称（用于显示）
  content?: string // 要素内容文本
  paperInfo?: LibraryPaper // 论文完整信息（仅论文节点有）
  // 自定义节点扩展字段
  node_type?: string
  properties?: Record<string, any>
  x?: number
  y?: number
}

export interface GraphLink {
  source: string
  target: string
  relationType: RelationType
  label?: string
  reason?: string // 语义关联理由
}

export interface GraphNodeData {
  id: string
  name: string
  type: NodeType
  paperId?: string
  paperTitle?: string
  content?: string
  paperInfo?: LibraryPaper
  node_type?: string
  category?: number
  properties?: Record<string, any>
}

export interface GraphCluster {
  id: string
  name: string
  description?: string
  paper_ids: string[]
}