import { defineStore } from 'pinia'

import { loginApi, registerApi } from '../api/auth'
import type { AuthUser, LoginPayload, RegisterPayload } from '../types/auth'
import {
  clearAuthStorage,
  getAccessToken,
  getStoredProfile,
  setAccessToken,
  setStoredProfile,
} from '../utils/storage'

interface AuthState {
  token: string
  user: AuthUser | null
  hydrated: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: '',
    user: null,
    hydrated: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    displayName: (state) => state.user?.name || 'Researcher',
  },

  actions: {
    hydrate() {
      if (this.hydrated) {
        return
      }

      this.token = getAccessToken()
      this.user = getStoredProfile()
      this.hydrated = true
    },

    async login(payload: LoginPayload) {
      const response = await loginApi(payload)
      this.applySession(response.accessToken, response.user)
      return response
    },

    async register(payload: RegisterPayload) {
      const response = await registerApi(payload)
      this.applySession(response.accessToken, response.user)
      return response
    },

    applySession(token: string, user: AuthUser) {
      this.token = token
      this.user = user
      this.hydrated = true
      setAccessToken(token)
      setStoredProfile(user)
    },

    logout() {
      this.token = ''
      this.user = null
      this.hydrated = true
      clearAuthStorage()
    },
  },
})
