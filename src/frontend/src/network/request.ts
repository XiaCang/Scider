import axios, { AxiosError } from 'axios'

import { clearAuthStorage, getAccessToken } from '../utils/storage'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  const token = getAccessToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

request.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError<{ message?: string }>) => {
    if (error.response?.status === 401) {
      clearAuthStorage()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }

    const message =
      error.response?.data?.message ?? error.message ?? 'Request failed, please try again later.'

    return Promise.reject(new Error(message))
  },
)

export default request
