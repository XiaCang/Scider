import axios, { AxiosError } from 'axios'
import type { AxiosRequestConfig, AxiosResponse } from 'axios'
import { authStorage } from '../utils/auth_storage'
import { ElMessage } from 'element-plus'

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
})

instance.interceptors.request.use((config) => {
  const token = authStorage.getToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

/** 从后端响应或 Axios 错误中提取可读的错误信息 */
function extractErrorMessage(error: AxiosError<{ message?: string; msg?: string }>): string {
  // 后端返回的业务错误 (HTTP 4xx/5xx + body 中有 msg 或 message)
  const backendMsg =
    error.response?.data?.msg ||
    error.response?.data?.message
  if (backendMsg) return backendMsg

  // 网络层错误
  if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
    return '网络连接失败，请检查后端服务是否可用'
  }
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return '请求超时，请稍后重试'
  }
  if (error.code === 'ERR_CANCELED') {
    return '请求已取消'
  }

  // 兜底
  return error.message || '请求失败，请稍后重试'
}

instance.interceptors.response.use(
  (response: AxiosResponse<{ code: number; msg?: string; message?: string }>) => {
    const body = response.data

    // 后端返回了业务错误码 (code !== 0)
    if (body && body.code !== undefined && body.code !== 0) {
      const errMsg = body.msg || body.message || `业务错误 (code=${body.code})`
      return Promise.reject(new Error(errMsg))
    }

    return response.data
  },
  (error: AxiosError<{ message?: string; msg?: string }>) => {
    // 401 → 清除 token 并跳转登录
    if (error.response?.status === 401) {
      authStorage.clearToken()
      if (!window.location.pathname.startsWith('/login')) {
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
      }
    }

    const message = extractErrorMessage(error)
    return Promise.reject(new Error(message))
  },
)

// 定义新的请求方法类型
interface CustomRequest {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
}

// 将 instance 断言为 CustomRequest 类型
const request = instance as CustomRequest

export default request
