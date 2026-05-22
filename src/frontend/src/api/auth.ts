import request from '../network/request'
import type {
  ApiResponse,
  LoginPayload,
  RegisterPayload,
  LoginResponseData,
  RegisterResponseData,
  ProfileResponseData,
  SendCodeResponseData,
  ChangePasswordResponseData,
  ChangePasswordByOldPayload,
  UpdateProfilePayload,
} from '../types/auth'

/** POST /api/user/login — 登录 */
export const loginApi = (payload: LoginPayload) =>
  request.post<ApiResponse<LoginResponseData>>('/user/login', payload)

/** POST /api/user/register — 注册 */
export const registerApi = (payload: RegisterPayload) =>
  request.post<ApiResponse<RegisterResponseData>>('/user/register', payload)

/** POST /api/user/send-code — 获取验证码 */
export const sendCodeApi = (payload: { email: string }) =>
  request.post<ApiResponse<SendCodeResponseData>>('/user/send-code', payload)

/** GET /api/user/me — 查询用户信息 */
export const getProfileApi = () =>
  request.get<ApiResponse<ProfileResponseData>>('/user/me')

/** POST /api/user/change-password — 忘记密码 */
export const changePasswordApi = (payload: { email: string; code: string; new_password: string }) =>
  request.post<ApiResponse<ChangePasswordResponseData>>('/user/change-password', payload)

/** POST /api/user/change-password-by-old — 原密码修改密码（设置页） */
export const changePasswordByOldApi = (payload: ChangePasswordByOldPayload) =>
  request.post<ApiResponse<null>>('/user/change-password-by-old', payload)

/** PUT /api/user/profile — 更新个人信息 */
export const updateProfileApi = (payload: UpdateProfilePayload) =>
  request.put<ApiResponse<ProfileResponseData>>('/user/profile', payload)
