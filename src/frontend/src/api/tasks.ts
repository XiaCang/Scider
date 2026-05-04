import request from '../network/request'
import type { ApiResponse } from '../types/auth'

/** GET /tasks/{task_id} — 查询任务进度 */
export const fetchTaskResultApi = (taskId: string) =>
  request.get<ApiResponse<unknown>>(`/tasks/${taskId}`)

/** POST /tasks/ping — Ping Celery Worker */
export const pingTaskApi = () =>
  request.post<ApiResponse<unknown>>('/tasks/ping')
