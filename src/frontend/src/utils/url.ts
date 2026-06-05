/**
 * 后端图片等静态资源的 URL 处理工具
 *
 * 后端上传的图片存于 UPLOAD_DIR，以 StaticFiles 挂载在 /uploads 路径下，
 * 返回给前端的 URL 是相对路径（如 /uploads/notes/xxx/yyy.png）。
 * 前端需要补全后端服务器地址才能正确显示。
 */

/** 后端服务 origin（不含 path），如 http://39.107.252.200:8000 */
const BACKEND_ORIGIN = (() => {
  const base = import.meta.env.VITE_API_BASE_URL as string | undefined
  if (!base) return ''
  // VITE_API_BASE_URL = "http://xxx:8000/api" → origin = "http://xxx:8000"
  return base.replace(/\/api\/?$/, '')
})()

/**
 * 将后端返回的相对 URL 转为绝对 URL（补上后端 origin）
 * 如果已经是绝对 URL 则原样返回
 */
export function resolveBackendUrl(url: string | null | undefined): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  // 相对路径，拼接后端 origin
  return `${BACKEND_ORIGIN}${url}`
}
