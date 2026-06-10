export interface AuthUser {
  id: string
  name: string
  email: string
  institution?: string
}

export interface LoginPayload {
  email: string
  password: string
  remember?: boolean
}

export interface RegisterPayload {
  name: string
  email: string
  password: string
  institution?: string
}

export interface AuthResponse {
  accessToken: string
  refreshToken?: string
  user: AuthUser
}
