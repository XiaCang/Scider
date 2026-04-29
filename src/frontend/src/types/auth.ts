export interface AuthUser {
  userId: string
  username: string
  email: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  name: string
  code: string
}

export interface AuthResponse {
  accessToken: string
  user: AuthUser
}
