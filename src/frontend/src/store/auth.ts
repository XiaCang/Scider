import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi, getProfileApi, getAvatarApi } from '../api/auth'
import type { AuthUser, LoginPayload, RegisterPayload } from '../types/auth'
import { authStorage } from '../utils/auth_storage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/** 将后端返回的相对路径头像 URL 拼成完整 URL */
function resolveAvatarUrl(path: string | null): string | null {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  try {
    const origin = new URL(API_BASE).origin
    return `${origin}${path}`
  } catch {
    return API_BASE ? `${API_BASE.replace(/\/+$/, '')}${path}` : path
  }
}

export const useAuthStore = defineStore('auth', () => {
  // state
  const token = ref<string>('')
  const user = ref<AuthUser | null>(null)
  const avatarUrl = ref<string | null>(null)
  const hydrated = ref<boolean>(false)
  const initializing = ref<boolean>(false)

  // getters
  const isAuthenticated = computed(() => Boolean(token.value))
  const displayName = computed(() => user.value?.username || '研究者')

  // actions

  /** 从后端获取头像 URL 并更新 store 和 localStorage */
  async function fetchAvatar() {
    try {
      const res = await getAvatarApi()
      avatarUrl.value = resolveAvatarUrl(res.data?.avatarUrl ?? null)
      authStorage.setAvatarUrl(avatarUrl.value)
    } catch {
      avatarUrl.value = null
      authStorage.clearAvatarUrl()
    }
  }

  async function hydrate() {
    if (hydrated.value) return
    hydrated.value = true

    const savedToken = authStorage.getToken()
    if (!savedToken) {
      token.value = ''
      user.value = null
      return
    }

    // 从 localStorage 恢复头像 URL，后续会异步刷新
    avatarUrl.value = authStorage.getAvatarUrl()

    // 向后端验证 token 有效性
    initializing.value = true
    try {
      const profile = await getProfileApi()
      token.value = savedToken
      user.value = {
        userId: profile.data.user.id,
        username: profile.data.user.name,
      }
      // 静默刷新头像 URL
      fetchAvatar()
    } catch {
      // Token 过期或无效，清除
      token.value = ''
      user.value = null
      avatarUrl.value = null
      authStorage.clearAll()
    } finally {
      initializing.value = false
    }
  }

  async function login(payload: LoginPayload) {
    const response = await loginApi({
      email: payload.email,
      password: payload.password,
    })
    // response: { code, msg, data: { token, userInfo: { userId, username } } }
    applySession(
      response.data.token,
      {
        userId: response.data.userInfo.userId,
        username: response.data.userInfo.username,
      },
    )
    // 登录后获取头像
    await fetchAvatar()
    return response
  }

  async function register(payload: RegisterPayload) {
    await registerApi({
      ...payload,
      password: payload.password,
    })
    // 注册成功（无 token），自动登录
    const loginResponse = await loginApi({
      email: payload.email,
      password: payload.password,
    })
    applySession(
      loginResponse.data.token,
      {
        userId: loginResponse.data.userInfo.userId,
        username: loginResponse.data.userInfo.username,
      },
    )
    // 注册后获取头像（新用户无头像，但保持状态一致）
    await fetchAvatar()
    return loginResponse
  }

  function applySession(newToken: string, newUser: AuthUser) {
    token.value = newToken
    user.value = newUser
    hydrated.value = true
    authStorage.setToken(newToken)
    authStorage.setProfile(newUser)
  }

  function setAvatarUrlDirect(url: string | null) {
    avatarUrl.value = url
    authStorage.setAvatarUrl(url)
  }

  function logout() {
    token.value = ''
    user.value = null
    avatarUrl.value = null
    hydrated.value = true
    authStorage.clearAll()
  }

  return {
    // state
    token,
    user,
    avatarUrl,
    hydrated,
    initializing,
    // getters
    isAuthenticated,
    displayName,
    // actions
    hydrate,
    fetchAvatar,
    login,
    register,
    applySession,
    setAvatarUrlDirect,
    logout,
  }
})
