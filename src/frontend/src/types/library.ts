/**
 * 论文关键点(四维度结构化数据)
 */
export interface PaperKeyPoints {
  background: string      // 研究背景：该研究试图解决什么问题？
  method: string          // 研究方法：采用了何种技术路径或实验设计？
  innovation: string      // 创新点：与现有工作相比，独特贡献是什么？
  conclusion: string      // 结论：研究得出了何种关键发现？
}

/** 后端论文状态流转：
 *  pending_parsing → PARSING → pending_extraction → EXTRACTING → pending_confirmation
 */
export type PaperStatus =
  | 'pending_parsing'
  | 'PARSING'
  | 'pending_extraction'
  | 'EXTRACTING'
  | 'pending_confirmation'

export interface LibraryPaper {
  id: string
  title: string
  authors: string
  year: number
  status: PaperStatus
  source: string
  keyPoints: PaperKeyPoints
}

/**
 * 论文PDF信息
 */
export interface PaperPdfInfo {
  id: string
  title: string
  pdfUrl: string
  pageCount: number
}

/**
 * 论文笔记
 */
export interface PaperNote {
  id: string
  paperId: string
  content: string
  pageNumber: number
  selectedText?: string
  createdAt: string
  updatedAt: string
}