import axios, { AxiosError} from 'axios'
import type { AxiosRequestConfig } from 'axios'
import {authStorage} from '../utils/auth_storage'

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
})

instance.interceptors.request.use((config) => {
  const token = authStorage.getToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.log('[Request Interceptor] Token已添加:', token.substring(0, 20) + '...')
  } else {
    console.warn('[Request Interceptor] 警告: 未找到Token，请求将不包含Authorization头')
  }

  return config
})

instance.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError<{ message?: string; msg?: string }>) => {
    if (error.response?.status === 401) {
      authStorage.clearToken()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }

    // 兼容后端的 msg 字段和前端的 message 字段
    const message =
      error.response?.data?.msg || 
      error.response?.data?.message || 
      error.message || 
      'Request failed, please try again later.';

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
