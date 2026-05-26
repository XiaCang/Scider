import { describe, it, expect } from 'vitest'
import { hashPassword } from './crypto'

describe('hashPassword', () => {
  it('应对同一密码返回一致的哈希值', async () => {
    const hash1 = await hashPassword('my-password')
    const hash2 = await hashPassword('my-password')
    expect(hash1).toBe(hash2)
  })

  it('应对不同密码返回不同的哈希值', async () => {
    const hash1 = await hashPassword('password-1')
    const hash2 = await hashPassword('password-2')
    expect(hash1).not.toBe(hash2)
  })

  it('应返回 64 个十六进制字符（SHA-256）', async () => {
    const hash = await hashPassword('test-password')
    expect(hash).toHaveLength(64)
    expect(/^[0-9a-f]{64}$/.test(hash)).toBe(true)
  })

  it('空字符串也应正常产生哈希', async () => {
    const hash = await hashPassword('')
    expect(hash).toHaveLength(64)
  })

  it('中文密码也应正常哈希', async () => {
    const hash = await hashPassword('密码123！@#')
    expect(hash).toHaveLength(64)
    expect(/^[0-9a-f]{64}$/.test(hash)).toBe(true)
  })
})
