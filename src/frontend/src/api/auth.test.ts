import { describe, it, expect, vi, beforeEach } from 'vitest'

const request = { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() }

vi.mock('../network/request', () => ({ default: request }))

describe('auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('loginApi', () => {
    it('应发送 POST /user/login', async () => {
      const { loginApi } = await import('./auth')
      const resp = { code: 0, msg: 'ok', data: { token: 'jwt', userInfo: { userId: 'u-1', username: 'test' } } }
      request.post.mockResolvedValue(resp)
      const result = await loginApi({ email: 'test@test.com', password: '123456' })
      expect(request.post).toHaveBeenCalledWith('/user/login', { email: 'test@test.com', password: '123456' })
      expect(result.code).toBe(0)
      expect(result.data.token).toBe('jwt')
    })
  })

  describe('registerApi', () => {
    it('应发送 POST /user/register', async () => {
      const { registerApi } = await import('./auth')
      const payload = { email: 'new@test.com', password: 'pw', name: 'new', code: '123456' }
      const resp = { code: 0, msg: 'ok', data: { userId: 'u-1', username: 'new', email: 'new@test.com' } }
      request.post.mockResolvedValue(resp)
      const result = await registerApi(payload)
      expect(request.post).toHaveBeenCalledWith('/user/register', payload)
      expect(result.code).toBe(0)
    })
  })

  describe('sendCodeApi', () => {
    it('应发送 POST /user/send-code', async () => {
      const { sendCodeApi } = await import('./auth')
      const resp = { code: 0, msg: 'ok', data: { email: 'test@test.com', sent: true } }
      request.post.mockResolvedValue(resp)
      await sendCodeApi({ email: 'test@test.com' })
      expect(request.post).toHaveBeenCalledWith('/user/send-code', { email: 'test@test.com' })
    })
  })

  describe('getProfileApi', () => {
    it('应发送 GET /user/me', async () => {
      const { getProfileApi } = await import('./auth')
      const resp = { code: 0, msg: 'ok', data: { user: { id: 'u-1', email: 'test@test.com', name: 'test' } } }
      request.get.mockResolvedValue(resp)
      const result = await getProfileApi()
      expect(request.get).toHaveBeenCalledWith('/user/me')
      expect(result.data.user.id).toBe('u-1')
    })
  })

  describe('changePasswordApi', () => {
    it('应发送 POST /user/change-password', async () => {
      const { changePasswordApi } = await import('./auth')
      const payload = { email: 'test@test.com', code: '123456', new_password: 'newpw' }
      request.post.mockResolvedValue({ code: 0, msg: 'ok', data: { userId: 'u-1', email: 'test@test.com' } })
      await changePasswordApi(payload)
      expect(request.post).toHaveBeenCalledWith('/user/change-password', payload)
    })
  })

  describe('changePasswordByOldApi', () => {
    it('应发送 POST /user/change-password-by-old', async () => {
      const { changePasswordByOldApi } = await import('./auth')
      const payload = { old_password: 'old', new_password: 'new' }
      request.post.mockResolvedValue({ code: 0, msg: 'ok', data: null })
      await changePasswordByOldApi(payload as any)
      expect(request.post).toHaveBeenCalledWith('/user/change-password-by-old', payload)
    })
  })

  describe('updateProfileApi', () => {
    it('应发送 PATCH /user/me', async () => {
      const { updateProfileApi } = await import('./auth')
      const payload = { name: 'newname' }
      request.patch.mockResolvedValue({ code: 0, msg: 'ok', data: null })
      await updateProfileApi(payload)
      expect(request.patch).toHaveBeenCalledWith('/user/me', payload)
    })
  })

  describe('uploadAvatarApi', () => {
    it('应发送 POST /user/avatar 包含 FormData', async () => {
      const { uploadAvatarApi } = await import('./auth')
      const file = new File(['test'], 'avatar.png', { type: 'image/png' })
      const resp = { code: 0, msg: 'ok', data: { avatarUrl: '/avatars/1.png' } }
      request.post.mockResolvedValue(resp)
      const result = await uploadAvatarApi(file)
      expect(request.post).toHaveBeenCalledWith('/user/avatar', expect.any(FormData), {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      expect(result.data.avatarUrl).toBe('/avatars/1.png')
    })
  })

  describe('getAvatarApi', () => {
    it('应发送 GET /user/avatar', async () => {
      const { getAvatarApi } = await import('./auth')
      const resp = { code: 0, msg: 'ok', data: { avatarUrl: '/avatars/1.png' } }
      request.get.mockResolvedValue(resp)
      const result = await getAvatarApi()
      expect(request.get).toHaveBeenCalledWith('/user/avatar')
      expect(result.data.avatarUrl).toBe('/avatars/1.png')
    })
  })

  describe('deleteAvatarApi', () => {
    it('应发送 DELETE /user/avatar', async () => {
      const { deleteAvatarApi } = await import('./auth')
      request.delete.mockResolvedValue({ code: 0, msg: 'ok', data: null })
      await deleteAvatarApi()
      expect(request.delete).toHaveBeenCalledWith('/user/avatar')
    })
  })
})
