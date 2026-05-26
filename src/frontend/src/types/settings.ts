/** 模型提供商 */
export interface ModelProvider {
  id: string
  name: string
  provider: string
  base_url: string
  api_key_masked: string
  default_model: string
  enabled: boolean
  user_id: string | null
  created_at?: string
}

export interface CreateProviderPayload {
  name: string
  provider: string
  base_url: string
  api_key: string
  default_model: string
  enabled: boolean
}

export interface UpdateProviderPayload {
  name?: string
  base_url?: string
  api_key?: string
  enabled?: boolean
}
