import request from '../network/request'
import type { ApiResponse } from '../types/auth'
import type { ModelProvider, CreateProviderPayload, UpdateProviderPayload } from '../types/settings'

/** GET /api/user/llm-providers — 获取所有模型提供商 */
export const getProvidersApi = () =>
  request.get<ApiResponse<ModelProvider[]>>('/user/llm-providers')

/** POST /api/user/llm-providers — 添加模型提供商 */
export const createProviderApi = (payload: CreateProviderPayload) =>
  request.post<ApiResponse<ModelProvider>>('/user/llm-providers', payload)

/** PATCH /api/user/llm-providers/{id} — 更新模型提供商 */
export const updateProviderApi = (id: string, payload: UpdateProviderPayload) =>
  request.patch<ApiResponse<{ id: string }>>(`/user/llm-providers/${id}`, payload)

/** DELETE /api/user/llm-providers/{id} — 删除模型提供商 */
export const deleteProviderApi = (id: string) =>
  request.delete<ApiResponse<null>>(`/user/llm-providers/${id}`)
