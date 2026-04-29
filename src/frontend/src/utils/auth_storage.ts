import type { AuthUser } from '../types/auth'

const KEYS = {
  ACCESS_TOKEN: 'scider_access_token',
  PROFILE: 'scider_user_profile',
} as const

export const authStorage = {
  // --- Token 管理 ---
  getToken(): string {
    return localStorage.getItem(KEYS.ACCESS_TOKEN) ?? ''
  },

  setToken(token: string): void {
    localStorage.setItem(KEYS.ACCESS_TOKEN, token)
  },

  // --- Profile 管理 ---
  getProfile(): AuthUser | null {
    const raw = localStorage.getItem(KEYS.PROFILE)
    if (!raw) return null
    
    try {
      return JSON.parse(raw) as AuthUser
    } catch {
      this.clearProfile() // 解析失败自动清理
      return null
    }
  },

  setProfile(profile: AuthUser): void {
    localStorage.setItem(KEYS.PROFILE, JSON.stringify(profile))
  },

  // --- 清理逻辑 ---
  clearToken(): void {
    localStorage.removeItem(KEYS.ACCESS_TOKEN)
  },

  clearProfile(): void {
    localStorage.removeItem(KEYS.PROFILE)
  },

  clearAll(): void {
    this.clearToken()
    this.clearProfile()
  }
}