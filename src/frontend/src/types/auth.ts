/** 通用 API 响应信封 */
export interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

export interface AuthUser {
  userId: string
  username: string
  email?: string
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

/** POST /api/user/login → data */
export interface LoginResponseData {
  token: string
  userInfo: {
    userId: string
    username: string
  }
}

/** POST /api/user/register → data */
export interface RegisterResponseData {
  userId: string
  username: string
  email: string
}

/** GET /api/user/me → data */
export interface ProfileResponseData {
  user: {
    id: string
    email: string
    name: string
  }
}

/** POST /api/user/send-code → data */
export interface SendCodeResponseData {
  email: string
  sent: boolean
}

/** POST /api/user/change-password → data */
export interface ChangePasswordResponseData {
  userId: string
  email: string
}

/** POST /api/user/change-password-by-old → payload */
export interface ChangePasswordByOldPayload {
  old_password: string
  new_password: string
}

/** PUT /api/user/profile → payload */
export interface UpdateProfilePayload {
  username?: string
  avatar?: string
  bio?: string
}

/** GET /api/user/avatar → data */
export interface AvatarResponseData {
  avatarUrl: string | null
}
