/**
 * PDF 文本高亮工具函数
 * 
 * 功能：
 * 1. 从 pdf.js 提取页面文本内容和坐标
 * 2. 查找关键词在文本中的位置
 * 3. 计算高亮矩形的屏幕坐标
 */

import type { SearchResultItem } from '../api/library'

/**
 * 文本项接口（来自 pdf.js）
 */
interface TextItem {
  str: string
  transform: number[]  // [scaleX, skewY, skewX, scaleY, x, y]
  width: number
  height: number
  dir: string
}

/**
 * 高亮矩形信息
 */
export interface HighlightRect {
  page: number
  x: number
  y: number
  width: number
  height: number
  matchIndex: number  // 匹配项索引
}

/**
 * 从 pdf.js 页面提取文本内容
 * @param pdfPage - pdf.js 页面对象
 * @returns 文本项数组
 */
export async function extractTextFromPage(pdfPage: any): Promise<TextItem[]> {
  try {
    const textContent = await pdfPage.getTextContent()
    return textContent.items.filter((item: any) => item.str && item.str.trim())
  } catch (error) {
    console.error('提取文本失败:', error)
    return []
  }
}

/**
 * 在文本项中查找关键词位置
 * @param textItems - 文本项数组
 * @param keyword - 搜索关键词
 * @returns 匹配的文本项索引和位置信息
 */
export function findKeywordInTextItems(
  textItems: TextItem[],
  keyword: string
): Array<{
  itemIndex: number
  matchStart: number
  matchEnd: number
  matchedText: string
}> {
  const results: Array<{
    itemIndex: number
    matchStart: number
    matchEnd: number
    matchedText: string
  }> = []

  const lowerKeyword = keyword.toLowerCase()

  textItems.forEach((item, index) => {
    const text = item.str
    const lowerText = text.toLowerCase()
    
    let startPos = 0
    while (true) {
      const matchPos = lowerText.indexOf(lowerKeyword, startPos)
      if (matchPos === -1) break
      
      results.push({
        itemIndex: index,
        matchStart: matchPos,
        matchEnd: matchPos + keyword.length,
        matchedText: text.substring(matchPos, matchPos + keyword.length)
      })
      
      startPos = matchPos + 1
    }
  })

  return results
}

/**
 * 计算单个文本项的高亮矩形
 * @param textItem - 文本项
 * @param viewport - pdf.js 视口对象
 * @param matchStart - 匹配起始位置（字符索引）
 * @param matchEnd - 匹配结束位置
 * @param zoomLevel - 缩放比例
 * @returns 高亮矩形坐标
 */
export function calculateHighlightRect(
  textItem: TextItem,
  viewport: any,
  matchStart: number,
  matchEnd: number,
  zoomLevel: number
): HighlightRect | null {
  try {
    const text = textItem.str
    const matchText = text.substring(matchStart, matchEnd)
    
    // 估算匹配文本的宽度比例
    const charRatio = matchText.length / text.length
    
    // 获取文本项的变换矩阵
    const [scaleX, , , scaleY, x, y] = textItem.transform
    
    // 计算高亮区域的宽度和高度
    const width = textItem.width * charRatio
    const height = Math.abs(scaleY) || textItem.height || 12
    
    // PDF 坐标转屏幕坐标
    // pdf.js 的 viewport.convertToViewportPoint 会处理坐标转换
    const [screenX, screenY] = viewport.convertToViewportPoint(x, y)
    
    // 考虑缩放比例
    const finalZoom = zoomLevel / 100
    
    return {
      page: viewport.pageNumber,
      x: screenX * finalZoom,
      y: screenY * finalZoom - height * finalZoom, // Y轴向上调整
      width: width * finalZoom,
      height: height * finalZoom,
      matchIndex: 0 // 由调用者设置
    }
  } catch (error) {
    console.error('计算高亮矩形失败:', error)
    return null
  }
}

/**
 * 为搜索结果计算所有高亮矩形
 * @param pdfDocument - pdf.js 文档对象
 * @param searchResults - 搜索结果列表
 * @param currentPage - 当前页码
 * @param zoomLevel - 缩放比例
 * @returns 高亮矩形数组
 */
export async function calculateHighlightsForPage(
  pdfDocument: any,
  searchResults: SearchResultItem[],
  currentPage: number,
  zoomLevel: number
): Promise<HighlightRect[]> {
  const highlights: HighlightRect[] = []
  
  // 筛选出当前页面的结果
  const pageResults = searchResults.filter(r => r.page_number === currentPage)
  
  if (pageResults.length === 0) return highlights
  
  try {
    // 获取当前页面
    const pdfPage = await pdfDocument.getPage(currentPage)
    const viewport = pdfPage.getViewport({ scale: 1 })
    viewport.pageNumber = currentPage
    
    // 提取文本
    const textItems = await extractTextFromPage(pdfPage)
    
    // 为每个搜索结果查找匹配位置
    let globalMatchIndex = 0
    for (const result of pageResults) {
      const keyword = extractKeywordFromHighlight(result.highlights?.[0])
      if (!keyword) continue
      
      const matches = findKeywordInTextItems(textItems, keyword)
      
      for (const match of matches) {
        const rect = calculateHighlightRect(
          textItems[match.itemIndex],
          viewport,
          match.matchStart,
          match.matchEnd,
          zoomLevel
        )
        
        if (rect) {
          rect.matchIndex = globalMatchIndex++
          highlights.push(rect)
        }
      }
    }
  } catch (error) {
    console.error(`计算第 ${currentPage} 页高亮失败:`, error)
  }
  
  return highlights
}

/**
 * 从高亮HTML中提取关键词
 * @param highlightHtml - 包含 <em class="search-highlight"> 的HTML
 * @returns 关键词文本
 */
function extractKeywordFromHighlight(highlightHtml?: string): string | null {
  if (!highlightHtml) return null
  
  // 使用正则提取 <em class="search-highlight">...</em> 中的内容
  const match = highlightHtml.match(/<em[^>]*class="search-highlight"[^>]*>(.*?)<\/em>/i)
  return match ? match[1] : null
}
