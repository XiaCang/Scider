import request from '../network/request'
import type { ApiResponse } from '../types/auth'
import type { ChatMessage } from '../types/library'

/**
 * AI 对话接口（若后端未实现则暂存本地）
 */

/** 发送消息，返回 AI 回复 */
export const sendChatMessageApi = async (
  paperId: string,
  message: string,
  contextText?: string,
  pageNumber?: number
): Promise<ChatMessage> => {
  try {
    const resp = await request.post<ApiResponse<{ reply: string }>>(
      `/papers/${paperId}/chat`,
      { message, contextText, pageNumber }
    )
    const data = ('data' in resp ? (resp as any).data : resp) as any
    return {
      id: Date.now().toString(),
      role: 'assistant',
      content: data.reply || data.message || '（AI 暂未响应）',
      createdAt: new Date().toISOString(),
    }
  } catch {
    // API 未实现时返回模拟回复
    return {
      id: Date.now().toString(),
      role: 'assistant',
      content: `收到你的提问：「${message}」\n\nAI 对话功能正在接入中，请稍后重试。`,
      createdAt: new Date().toISOString(),
    }
  }
}

/** 获取历史对话列表 */
export const fetchChatHistoryApi = (
  _paperId: string,
  _page = 1,
  _pageSize = 50
): Promise<ChatMessage[]> => {
  // 暂未实现，返回空数组
  return Promise.resolve([])
}
