import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from './auth'
import * as authApi from '../api/auth'
import * as authStorageModule from '../utils/auth_storage'

vi.mock('../api/auth', () => ({
  loginApi: vi.fn(),
  registerApi: vi.fn(),
  getProfileApi: vi.fn(),
}))

vi.mock('../utils/auth_storage', () => {
  let store: Record<string, string> = {}
  return {
    authStorage: {
      getToken: vi.fn(() => store['scider_access_token'] ?? ''),
      setToken: vi.fn((t: string) => { store['scider_access_token'] = t }),
      setProfile: vi.fn(),
      clearToken: vi.fn(() => { delete store['scider_access_token'] }),
      clearProfile: vi.fn(),
      clearAll: vi.fn(() => { store = {} }),
    },
  }
})

const mockLoginResponse = {
  code: 0,
  msg: 'ok',
  data: {
    token: 'jwt-token-xxx',
    userInfo: { userId: 'u-1', username: 'testuser' },
  },
}

const mockProfileResponse = {
  code: 0,
  msg: 'ok',
  data: {
    user: { id: 'u-1', email: 'test@example.com', name: 'testuser' },
  },
}

const mockRegisterResponse = {
  code: 0,
  msg: 'ok',
  data: { userId: 'u-1', username: 'testuser', email: 'test@example.com' },
}

describe('authStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应初始化为未登录状态', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
      expect(store.displayName).toBe('研究者')
      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.hydrated).toBe(false)
    })
  })

  describe('login', () => {
    it('登录成功应设置 token 和用户信息', async () => {
      vi.mocked(authApi.loginApi).mockResolvedValue(mockLoginResponse as any)
      const store = useAuthStore()
      await store.login({ email: 'test@example.com', password: 'pw' })
      expect(store.isAuthenticated).toBe(true)
      expect(store.token).toBe('jwt-token-xxx')
      expect(store.user?.userId).toBe('u-1')
      expect(store.user?.username).toBe('testuser')
      expect(store.hydrated).toBe(true)
    })

    it('登录失败应抛出错误', async () => {
      vi.mocked(authApi.loginApi).mockRejectedValue(new Error('邮箱或密码错误'))
      const store = useAuthStore()
      await expect(store.login({ email: 'bad@example.com', password: 'wrong' })).rejects.toThrow('邮箱或密码错误')
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('register', () => {
    it('注册成功后应自动登录', async () => {
      vi.mocked(authApi.registerApi).mockResolvedValue(mockRegisterResponse as any)
      vi.mocked(authApi.loginApi).mockResolvedValue(mockLoginResponse as any)
      const store = useAuthStore()
      await store.register({ email: 'new@example.com', password: 'pw', name: 'newuser', code: '123456' })
      expect(store.isAuthenticated).toBe(true)
      expect(store.token).toBe('jwt-token-xxx')
    })
  })

  describe('hydrate', () => {
    it('无本地 token 时应保持未登录', async () => {
      const store = useAuthStore()
      await store.hydrate()
      expect(store.isAuthenticated).toBe(false)
      expect(store.hydrated).toBe(true)
    })

    it('本地 token 有效时应恢复登录状态', async () => {
      vi.mocked(authStorageModule.authStorage.getToken).mockReturnValue('valid-token')
      vi.mocked(authApi.getProfileApi).mockResolvedValue(mockProfileResponse as any)
      const store = useAuthStore()
      await store.hydrate()
      expect(store.isAuthenticated).toBe(true)
      expect(store.user?.userId).toBe('u-1')
    })

    it('本地 token 过期时应清除状态', async () => {
      vi.mocked(authStorageModule.authStorage.getToken).mockReturnValue('expired-token')
      vi.mocked(authApi.getProfileApi).mockRejectedValue(new Error('401'))
      const store = useAuthStore()
      await store.hydrate()
      expect(store.isAuthenticated).toBe(false)
      expect(store.user).toBeNull()
      expect(store.hydrated).toBe(true)
    })

    it('多次调用 hydrate 应只执行一次', async () => {
      vi.mocked(authStorageModule.authStorage.getToken).mockReturnValue('valid-token')
      vi.mocked(authApi.getProfileApi).mockResolvedValue(mockProfileResponse as any)
      const store = useAuthStore()
      await store.hydrate()
      await store.hydrate() // 第二次调用
      expect(authApi.getProfileApi).toHaveBeenCalledTimes(1)
    })
  })

  describe('applySession', () => {
    it('应直接设置登录会话', () => {
      const store = useAuthStore()
      store.applySession('direct-token', { userId: 'u-2', username: 'direct' })
      expect(store.isAuthenticated).toBe(true)
      expect(store.token).toBe('direct-token')
      expect(store.user?.username).toBe('direct')
    })
  })

  describe('logout', () => {
    it('应清除所有状态', () => {
      const store = useAuthStore()
      store.applySession('some-token', { userId: 'u-1', username: 'test' })
      store.logout()
      expect(store.isAuthenticated).toBe(false)
      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.hydrated).toBe(true)
    })
  })

  describe('displayName', () => {
    it('有用户时应显示用户名', () => {
      const store = useAuthStore()
      store.applySession('t', { userId: 'u-1', username: '小明' })
      expect(store.displayName).toBe('小明')
    })
  })
})
