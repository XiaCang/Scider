/** 模型提供商 */
export interface ModelProvider {
  id: string
  name: string
  api_key: string
  base_url: string
  models?: string[]
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface CreateProviderPayload {
  name: string
  api_key: string
  base_url: string
  models?: string[]
}

export interface UpdateProviderPayload {
  name?: string
  api_key?: string
  base_url?: string
  models?: string[]
  is_active?: boolean
}
