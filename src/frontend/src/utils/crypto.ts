/**
 * 使用 SHA-256 对密码进行哈希，确保明文密码不在网络中传输。
 * 服务端收到哈希值后应继续使用 bcrypt 做二次哈希存储。
 */
export async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}
