import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi } from '../api/auth'
import type { AuthUser, LoginPayload, RegisterPayload } from '../types/auth'
import { authStorage } from '../utils/auth_storage'

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
    const response = await loginApi(payload)
    applySession(response.accessToken, response.user)
    return response
  }

  async function register(payload: RegisterPayload) {
    const response = await registerApi(payload)
    applySession(response.accessToken, response.user)
    return response
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