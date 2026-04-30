
import type { LibraryPaper } from "./library"

// --- 类型定义 ---
export type NodeType = 'paper' | 'background' | 'method' | 'innovation' | 'conclusion'
export type RelationType = 'ownership' | 'semantic' | 'citation'


export interface GraphNode {
  id: string
  name: string
  type: NodeType
  category: number // 对应 ECharts categories 索引
  value?: number
  symbol?: string
  paperId?: string  // 关联的论文ID（仅四要素节点有）
  paperTitle?: string  // 论文名称简称（用于显示）
  content?: string  // 要素内容文本
  paperInfo?: LibraryPaper  // 论文完整信息（仅论文节点有）
}

export interface GraphLink {
  source: string
  target: string
  relationType: RelationType
  label?: string
}


export interface GraphNodeData {
  id: string
  name: string
  type: NodeType
  paperId?: string  // 关联的论文ID（仅四要素节点有）
  paperTitle?: string  // 论文名称简称（用于显示）
  content?: string  // 要素内容文本
  paperInfo?: LibraryPaper  // 论文完整信息（仅论文节点有）
}