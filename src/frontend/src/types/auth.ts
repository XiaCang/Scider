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
  username: string
  email: string
  password: string
}

export interface AuthResponse {
  accessToken: string
  user: AuthUser
}
