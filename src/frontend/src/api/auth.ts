import request from '../network/request'
import type { AuthResponse, LoginPayload, RegisterPayload } from '../types/auth'

// ---------- Mock 模式控制 ----------
let mockLoginEnabled = true

/**
 * 设置登录 API 是否使用 Mock 数据
 * @param enabled true: 返回假响应，false: 调用真实接口
 */
export const enableMockLogin = (enabled: boolean) => {
  mockLoginEnabled = enabled
}

// 1. 登录（支持 Mock 切换）
export const loginApi = (payload: LoginPayload): Promise<AuthResponse> => {
  if (mockLoginEnabled) {
    // 模拟假响应，延迟 300ms 更接近真实网络体验（可选）
    const fakeResponse: AuthResponse = {
      accessToken: 'mock-jwt-token-' + Date.now(),
      user: {
        userId: 'mock-user-id',
        username: payload.email.split('@')[0] || 'scider_user',
        email: payload.email,
      },
    }
    // 若不需要延迟，直接 Promise.resolve(fakeResponse) 即可
    return new Promise((resolve) => setTimeout(() => resolve(fakeResponse), 300))
  }
  return request.post<AuthResponse>('/auth/login', payload)
}


// 1. 登录
// export const loginApi = (payload: LoginPayload) : Promise<AuthResponse> =>
//     request.post<AuthResponse>('/auth/login', payload)

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