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
 *  PENDING_PARSING → PARSING → PENDING_EXTRACTION → EXTRACTING → PENDING_CONFIRMATION → CONFIRMED
 *  任何阶段失败 → FAILED
 */
export type PaperStatus =
  | 'PENDING_PARSING'
  | 'PARSING'
  | 'PENDING_EXTRACTION'
  | 'EXTRACTING'
  | 'PENDING_CONFIRMATION'
  | 'CONFIRMED'
  | 'FAILED'

export interface LibraryPaper {
  id: string
  title: string
  authors: string
  year: number
  status: PaperStatus
  source: string
  keyPoints: PaperKeyPoints
  created_at?: string
  in_library?: boolean
  abstract?: string
  pdf_url?: string
  doi?: string
  arxiv_id?: string
  url?: string
  doi_url?: string
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
 * 论文笔记（新 API 结构）
 */
export interface PaperNote {
  id: string
  paperId: string
  title: string
  contentHtml: string | null
  contentText?: string | null
  contentFormat: string
  images?: NoteImage[]
  createdAt: string | null
  updatedAt: string | null
}

export interface NoteImage {
  id: string
  url: string
  filename?: string
  orderIndex: number
  createdAt?: string | null
}

export interface NoteListItem {
  id: string
  paperId: string
  title: string
  excerpt: string
  firstImageUrl: string | null
  updatedAt: string
}

/** 笔记图片上传响应 */
export interface NoteUploadImageResponse {
  id: string
  noteId: string
  url: string
  filename: string
  mimeType: string
  size: number
  createdAt: string
}

/** AI 对话消息 */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}
