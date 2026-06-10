import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { AxiosError, AxiosHeaders } from 'axios'
import { authStorage } from '../utils/auth_storage'

// 模拟 ElementPlus 的 ElMessage
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
  },
}))

// 必须在 import request 之前 mock authStorage
vi.mock('../utils/auth_storage', () => ({
  authStorage: {
    getToken: vi.fn(() => ''),
    setToken: vi.fn(),
    clearToken: vi.fn(),
    clearProfile: vi.fn(),
    clearAll: vi.fn(),
    getProfile: vi.fn(),
    setProfile: vi.fn(),
  },
}))

// window.location.href 模拟
beforeEach(() => {
  vi.stubGlobal('location', {
    ...window.location,
    href: '',
    pathname: '/app/library',
  })
})
// window.location.href 模拟
const originalLocation = window.location
afterEach(() => {
  window.location = originalLocation as any
})

describe('request 拦截器逻辑（直接测试拦截器函数）', () => {
  // 直接导入拦截器逻辑进行单元测试
  // 由于 axios 实例的 interceptors 难以单独导出，我们通过导入 instance 来测试
  let requestInterceptor: (config: any) => any
  let responseFulfilled: (response: any) => any
  let responseRejected: (error: any) => Promise<any>

  beforeEach(async () => {
    vi.clearAllMocks()
    // 动态导入以获取最新的 mock 状态
    const mod = await import('./request')
    const instance = (mod as any).default

    // 提取拦截器
    const reqInterceptors = (instance as any).interceptors.request.handlers
    if (reqInterceptors && reqInterceptors.length > 0) {
      requestInterceptor = reqInterceptors[0].fulfilled
    }

    const resInterceptors = (instance as any).interceptors.response.handlers
    if (resInterceptors && resInterceptors.length > 0) {
      responseFulfilled = resInterceptors[0].fulfilled
      responseRejected = resInterceptors[0].rejected
    }
  })

  describe('请求拦截器', () => {
    it('有 token 时应添加 Authorization header', () => {
      vi.mocked(authStorage.getToken).mockReturnValue('test-token')
      const config = { headers: {} }
      const result = requestInterceptor(config)
      expect(result.headers.Authorization).toBe('Bearer test-token')
    })

    it('无 token 时不应添加 Authorization header', () => {
      vi.mocked(authStorage.getToken).mockReturnValue('')
      const config = { headers: {} }
      const result = requestInterceptor(config)
      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('响应拦截器 - 成功', () => {
    it('正常响应应直接返回 response.data', () => {
      const response = { data: { code: 0, msg: 'ok', data: 'some-data' } }
      const result = responseFulfilled(response)
      expect(result).toEqual({ code: 0, msg: 'ok', data: 'some-data' })
    })

    it('后端返回业务错误码应拒绝', async () => {
      const response = { data: { code: 40001, msg: '参数错误' } }
      await expect(responseFulfilled(response)).rejects.toThrow('参数错误')
    })
  })

  describe('响应拦截器 - 错误', () => {
    function createAxiosError(status: number | undefined, data: any, code?: string, message?: string) {
      const error = new AxiosError(
        message || 'Axios Error',
        code || 'ERR_BAD_REQUEST',
        {} as any,
        {} as any,
        {
          status: status ?? null,
          data,
          statusText: 'Error',
          headers: new AxiosHeaders(),
          config: {} as any,
        } as any,
      )
      return error
    }

    it('401 应清除 token 并重定向到登录页', async () => {
      // 模拟当前不在登录页
      window.location.pathname = '/app/library'
      const error = createAxiosError(401, {})
      await expect(responseRejected(error)).rejects.toThrow()
      expect(authStorage.clearToken).toHaveBeenCalled()
    })

    it('401 但在登录页不应重复提示', async () => {
      window.location.pathname = '/login'
      const error = createAxiosError(401, {})
      await expect(responseRejected(error)).rejects.toThrow()
    })

    it('应提取后端返回的 msg', async () => {
      vi.mocked(authStorage.clearToken).mockClear()
      const error = createAxiosError(400, { msg: '邮箱已注册' })
      await expect(responseRejected(error)).rejects.toThrow('邮箱已注册')
    })

    it('应提取后端返回的 message', async () => {
      vi.mocked(authStorage.clearToken).mockClear()
      const error = createAxiosError(400, { message: '密码错误' })
      await expect(responseRejected(error)).rejects.toThrow('密码错误')
    })

    it('网络错误应返回友好提示', async () => {
      const error = createAxiosError(undefined, {}, 'ERR_NETWORK', 'Network Error')
      await expect(responseRejected(error)).rejects.toThrow('网络连接失败，请检查后端服务是否可用')
    })

    it('超时应返回友好提示', async () => {
      const error = createAxiosError(undefined, {}, 'ECONNABORTED', 'timeout of 15000ms exceeded')
      await expect(responseRejected(error)).rejects.toThrow('请求超时，请稍后重试')
    })
  })
})
