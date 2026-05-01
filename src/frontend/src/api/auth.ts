import request from '../network/request'
import type { AuthResponse, LoginPayload, RegisterPayload } from '../types/auth'

export const loginApi = (payload: LoginPayload): Promise<AuthResponse> =>
  request.post<AuthResponse>('/auth/login', payload)

// 2. 注册
export const registerApi = (payload: RegisterPayload) : Promise<AuthResponse> =>
    request.post<AuthResponse>('/auth/register', payload)

// 验证码
export const sendCodeApi = (payload: { email: string }): Promise<{
  code: number;
  msg: string;
  data: { email: string; sent: boolean };
}> => request.post('/auth/send-code', payload);

// 3. 获取用户信息
export const getProfileApi = (): Promise<any> => 
  request.get('/auth/profile')