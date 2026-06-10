import request from '../network/request'
import type { AuthResponse, LoginPayload, RegisterPayload } from '../types/auth'

const shouldUseFallback = () => import.meta.env.VITE_ENABLE_API_FALLBACK !== 'false'

const createMockResponse = (
  payload: Pick<RegisterPayload, 'name' | 'email'>,
): Promise<AuthResponse> =>
  new Promise((resolve) => {
    window.setTimeout(() => {
      resolve({
        accessToken: `scider-demo-token-${Date.now()}`,
        user: {
          id: `user-${Date.now()}`,
          name: payload.name,
          email: payload.email,
          institution: 'Scider Lab',
        },
      })
    }, 480)
  })

export const loginApi = async (payload: LoginPayload): Promise<AuthResponse> => {
  try {
    return await request.post('/auth/login', payload)
  } catch (error) {
    if (!shouldUseFallback()) {
      throw error
    }

    return createMockResponse({
      name: payload.email.split('@')[0] || 'Researcher',
      email: payload.email,
    })
  }
}

export const registerApi = async (payload: RegisterPayload): Promise<AuthResponse> => {
  try {
    return await request.post('/auth/register', payload)
  } catch (error) {
    if (!shouldUseFallback()) {
      throw error
    }

    return createMockResponse(payload)
  }
}

export const getProfileApi = () => request.get('/auth/profile')
