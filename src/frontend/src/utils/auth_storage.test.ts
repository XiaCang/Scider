import { describe, it, expect, beforeEach, vi } from 'vitest'
import { authStorage } from './auth_storage'
import type { AuthUser } from '../types/auth'

describe('authStorage', () => {
  const mockUser: AuthUser = {
    userId: 'user-1',
    username: 'testuser',
    email: 'test@example.com',
  }

  beforeEach(() => {
    localStorage.clear()
  })

  describe('Token 管理', () => {
    it('setToken / getToken 应正确存取 token', () => {
      authStorage.setToken('my-token')
      expect(authStorage.getToken()).toBe('my-token')
    })

    it('无 token 时应返回空字符串', () => {
      expect(authStorage.getToken()).toBe('')
    })

    it('clearToken 应移除 token', () => {
      authStorage.setToken('my-token')
      authStorage.clearToken()
      expect(authStorage.getToken()).toBe('')
    })
  })

  describe('Profile 管理', () => {
    it('setProfile / getProfile 应正确存取用户信息', () => {
      authStorage.setProfile(mockUser)
      expect(authStorage.getProfile()).toEqual(mockUser)
    })

    it('无 profile 时应返回 null', () => {
      expect(authStorage.getProfile()).toBeNull()
    })

    it('clearProfile 应移除 profile', () => {
      authStorage.setProfile(mockUser)
      authStorage.clearProfile()
      expect(authStorage.getProfile()).toBeNull()
    })

    it('profile JSON 解析失败时应返回 null 并自动清理', () => {
      localStorage.setItem('scider_user_profile', '{invalid json}')
      expect(authStorage.getProfile()).toBeNull()
      expect(localStorage.getItem('scider_user_profile')).toBeNull()
    })
  })

  describe('clearAll', () => {
    it('应同时清除 token 和 profile', () => {
      authStorage.setToken('my-token')
      authStorage.setProfile(mockUser)
      authStorage.clearAll()
      expect(authStorage.getToken()).toBe('')
      expect(authStorage.getProfile()).toBeNull()
    })
  })
})
