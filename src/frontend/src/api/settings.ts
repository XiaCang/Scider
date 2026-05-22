import request from '../network/request'
import type { ApiResponse } from '../types/auth'
import type { ModelProvider, CreateProviderPayload, UpdateProviderPayload } from '../types/settings'

/** GET /api/settings/providers — 获取所有模型提供商 */
export const getProvidersApi = () =>
  request.get<ApiResponse<ModelProvider[]>>('/settings/providers')

/** POST /api/settings/providers — 添加模型提供商 */
export const createProviderApi = (payload: CreateProviderPayload) =>
  request.post<ApiResponse<ModelProvider>>('/settings/providers', payload)

/** PUT /api/settings/providers/:id — 更新模型提供商 */
export const updateProviderApi = (id: string, payload: UpdateProviderPayload) =>
  request.put<ApiResponse<ModelProvider>>(`/settings/providers/${id}`, payload)

/** DELETE /api/settings/providers/:id — 删除模型提供商 */
export const deleteProviderApi = (id: string) =>
  request.delete<ApiResponse<null>>(`/settings/providers/${id}`)
