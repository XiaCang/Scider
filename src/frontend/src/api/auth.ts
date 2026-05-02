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
} from '../types/auth'

/** POST /api/user/login — 登录 */
export const loginApi = (payload: LoginPayload) =>
  request.post<ApiResponse<LoginResponseData>>('/api/user/login', payload)

/** POST /api/user/register — 注册 */
export const registerApi = (payload: RegisterPayload) =>
  request.post<ApiResponse<RegisterResponseData>>('/api/user/register', payload)

/** POST /api/user/send-code — 获取验证码 */
export const sendCodeApi = (payload: { email: string }) =>
  request.post<ApiResponse<SendCodeResponseData>>('/api/user/send-code', payload)

/** GET /api/user/me — 查询用户信息 */
export const getProfileApi = () =>
  request.get<ApiResponse<ProfileResponseData>>('/api/user/me')

/** POST /api/user/change-password — 忘记密码 */
export const changePasswordApi = (payload: { email: string; code: string; new_password: string }) =>
  request.post<ApiResponse<ChangePasswordResponseData>>('/api/user/change-password', payload)
