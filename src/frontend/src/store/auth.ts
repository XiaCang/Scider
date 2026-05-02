import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi } from '../api/auth'
import type { AuthUser, LoginPayload, RegisterPayload } from '../types/auth'
import { authStorage } from '../utils/auth_storage'
import { hashPassword } from '../utils/crypto'

export const useAuthStore = defineStore('auth', () => {
  // state
  const token = ref<string>('')
  const user = ref<AuthUser | null>(null)
  const hydrated = ref<boolean>(false)

  // getters
  const isAuthenticated = computed(() => Boolean(token.value))
  const displayName = computed(() => user.value?.username || 'Researcher')

  // actions
  function hydrate() {
    if (hydrated.value) return

    token.value = authStorage.getToken()
    user.value = authStorage.getProfile()
    hydrated.value = true
  }

  async function login(payload: LoginPayload) {
    const hashedPwd = await hashPassword(payload.password)
    const response = await loginApi({
      email: payload.email,
      password: hashedPwd,
    })
    // response: { code, msg, data: { token, userInfo: { userId, username } } }
    applySession(
      response.data.token,
      {
        userId: response.data.userInfo.userId,
        username: response.data.userInfo.username,
      },
    )
    return response
  }

  async function register(payload: RegisterPayload) {
    const hashedPwd = await hashPassword(payload.password)
    await registerApi({
      ...payload,
      password: hashedPwd,
    })
    // 注册成功（无 token），自动登录
    const loginResponse = await loginApi({
      email: payload.email,
      password: hashedPwd,
    })
    applySession(
      loginResponse.data.token,
      {
        userId: loginResponse.data.userInfo.userId,
        username: loginResponse.data.userInfo.username,
      },
    )
    return loginResponse
  }

  function applySession(newToken: string, newUser: AuthUser) {
    token.value = newToken
    user.value = newUser
    hydrated.value = true
    authStorage.setToken(newToken)
    authStorage.setProfile(newUser)
  }

  function logout() {
    token.value = ''
    user.value = null
    hydrated.value = true
    authStorage.clearAll()
  }

  return {
    // state
    token,
    user,
    hydrated,
    // getters
    isAuthenticated,
    displayName,
    // actions
    hydrate,
    login,
    register,
    applySession,
    logout,
  }
})
