import type { AuthUser } from '../types/auth'

const ACCESS_TOKEN_KEY = 'scider_access_token'
const PROFILE_KEY = 'scider_user_profile'

export const getAccessToken = (): string => localStorage.getItem(ACCESS_TOKEN_KEY) ?? ''

export const setAccessToken = (token: string) => {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export const clearAccessToken = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}

export const getStoredProfile = (): AuthUser | null => {
  const rawValue = localStorage.getItem(PROFILE_KEY)
  if (!rawValue) {
    return null
  }

  try {
    return JSON.parse(rawValue) as AuthUser
  } catch {
    localStorage.removeItem(PROFILE_KEY)
    return null
  }
}

export const setStoredProfile = (profile: AuthUser) => {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
}

export const clearStoredProfile = () => {
  localStorage.removeItem(PROFILE_KEY)
}

export const clearAuthStorage = () => {
  clearAccessToken()
  clearStoredProfile()
}
