import { describe, it, expect, vi, afterEach } from 'vitest'

describe('resolveBackendUrl', () => {
  afterEach(() => {
    // 清除模块缓存，使每个测试重新计算 BACKEND_ORIGIN
    vi.resetModules()
  })

  it('null/undefined 应返回空字符串', async () => {
    import.meta.env.VITE_API_BASE_URL = 'http://localhost:8000/api'
    const { resolveBackendUrl } = await import('./url')
    expect(resolveBackendUrl(null)).toBe('')
    expect(resolveBackendUrl(undefined)).toBe('')
  })

  it('空字符串应返回空字符串', async () => {
    import.meta.env.VITE_API_BASE_URL = 'http://localhost:8000/api'
    const { resolveBackendUrl } = await import('./url')
    expect(resolveBackendUrl('')).toBe('')
  })

  it('绝对 URL 应原样返回', async () => {
    import.meta.env.VITE_API_BASE_URL = 'http://localhost:8000/api'
    const { resolveBackendUrl } = await import('./url')
    expect(resolveBackendUrl('http://example.com/image.png')).toBe('http://example.com/image.png')
    expect(resolveBackendUrl('https://cdn.example.com/img.jpg')).toBe('https://cdn.example.com/img.jpg')
  })

  it('相对路径应拼接后端 origin', async () => {
    import.meta.env.VITE_API_BASE_URL = 'http://localhost:8000/api'
    const { resolveBackendUrl } = await import('./url')
    expect(resolveBackendUrl('/uploads/notes/xxx/yyy.png')).toBe('http://localhost:8000/uploads/notes/xxx/yyy.png')
  })

  it('以 /api 结尾的 BASE_URL 应正确处理', async () => {
    import.meta.env.VITE_API_BASE_URL = 'http://localhost:8000/api/'
    const { resolveBackendUrl } = await import('./url')
    expect(resolveBackendUrl('/uploads/test.png')).toBe('http://localhost:8000/uploads/test.png')
  })

  it('无 BASE_URL 时应返回相对路径本身', async () => {
    // vitest 会保留原有值，用空字符串模拟无 BASE_URL 的情况（!base 为 true）
    import.meta.env.VITE_API_BASE_URL = ''
    const { resolveBackendUrl } = await import('./url')
    expect(resolveBackendUrl('/uploads/test.png')).toBe('/uploads/test.png')
  })

  it('VITE_API_BASE_URL 无 /api 后缀时也应正确', async () => {
    import.meta.env.VITE_API_BASE_URL = 'http://backend:8000'
    const { resolveBackendUrl } = await import('./url')
    expect(resolveBackendUrl('/uploads/test.png')).toBe('http://backend:8000/uploads/test.png')
  })
})
